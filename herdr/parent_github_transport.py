"""Bounded parent GitHub transport; credentials never enter the worker repository."""
from pathlib import Path
import json
import os
import re
import resource
import selectors
import shlex
import signal
import stat
import subprocess
import sys
import tempfile
import time
from urllib.parse import quote, urlencode

from .evidence import EvidenceError, EvidenceUnavailable
from .parent_publication import require


_RESOURCE_LAUNCHER = """import os, resource, sys
for kind, cap in ((resource.RLIMIT_CORE, 0),
        (resource.RLIMIT_AS, 2147483648),
        (resource.RLIMIT_FSIZE, 67108864),
        (resource.RLIMIT_NOFILE, 256), (resource.RLIMIT_CPU, 90)):
    inherited = [x for x in resource.getrlimit(kind) if x != resource.RLIM_INFINITY]
    bound = min([cap, *inherited])
    resource.setrlimit(kind, (bound, bound))
os.execv(sys.argv[1], sys.argv[1:])
"""


def _bounded_process(argv, *, env, cwd, data=None, timeout=30, output_limit=2_000_000):
    require(data is None or isinstance(data, bytes) and len(data) <= 4096,
        "bounded parent request input required")
    require(isinstance(argv, list) and argv and Path(argv[0]).is_absolute()
        and all(isinstance(x, str) and "\0" not in x for x in argv),
        "closed parent executable argv required")
    # Do not run Python preexec_fn code after fork in a threaded parent.
    # This fixed trusted launcher clamps inherited limits before client exec.
    process = subprocess.Popen([sys.executable, "-I", "-B", "-S", "-c", _RESOURCE_LAUNCHER, *argv], env=env, cwd=cwd,
        stdin=subprocess.PIPE if data is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    selector = selectors.DefaultSelector()
    stdout, total, sent = bytearray(), 0, 0
    deadline = time.monotonic() + timeout
    try:
        for stream in (process.stdout, process.stderr):
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ)
        if data is not None:
            os.set_blocking(process.stdin.fileno(), False)
            selector.register(process.stdin, selectors.EVENT_WRITE)
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError()
            for key, events in selector.select(min(remaining, 0.2)):
                stream = key.fileobj
                if stream is process.stdin:
                    if sent == len(data):
                        selector.unregister(stream)
                        stream.close()
                        continue
                    sent += os.write(stream.fileno(), data[sent:])
                    continue
                chunk = os.read(stream.fileno(), 65536)
                if not chunk:
                    selector.unregister(stream)
                    stream.close()
                    continue
                total += len(chunk)
                if total > output_limit:
                    raise ValueError("bounded parent output exceeded")
                if stream is process.stdout:
                    stdout.extend(chunk)
        status = process.wait(timeout=max(0.001, deadline-time.monotonic()))
        return status, bytes(stdout)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        raise EvidenceUnavailable("bounded parent transport did not complete") from exc
    finally:
        # The client may exit while a credential helper still owns its group.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        if process.poll() is None:
            process.wait(timeout=3)
        selector.close()
        for stream in (process.stdin, process.stdout, process.stderr):
            if stream is not None and not stream.closed:
                stream.close()


class GitHubParentTransport:
    """The host selects these paths; queue/model fields never select executables.

    Existing GitHub guard/auth configuration is used by the selected gh client.
    Git itself receives a new bare directory and a closed configuration. The
    worker directory is never the cwd of a credential-bearing operation.
    """
    def __init__(self, *, repo, scratch, gh, home, git=Path("/usr/bin/git")):
        self.repo, self.scratch = repo, Path(scratch)
        self.gh, self.git, self.home = Path(gh), Path(git), Path(home)
        for path in (self.gh, self.git):
            require(path.is_absolute() and path.resolve(strict=True).is_file(),
                "approved parent client executable required")
        require(self.scratch.is_absolute() and self.scratch.resolve() == self.scratch,
            "canonical parent transport storage required")
        self.scratch.mkdir(mode=0o700, parents=False, exist_ok=True)
        info = self.scratch.lstat()
        require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.geteuid()
            and stat.S_IMODE(info.st_mode) == 0o700,
            "private parent transport storage required")
        self.env = {"PATH": "/usr/bin:/bin", "HOME": str(self.home), "LANG": "C.UTF-8",
            "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_TERMINAL_PROMPT": "0", "GIT_ASKPASS": "/bin/false"}

    def protect_from(self, writable_roots):
        require(all(not self.scratch.is_relative_to(Path(root).resolve())
            for root in writable_roots), "parent transport storage is worker writable")

    def _run(self, permit, argv, *, cwd=None, data=None, timeout=30):
        require(permit.repo == self.repo, "parent transport repository changed")
        remaining = permit.expires_at_epoch - time.time()
        require(remaining > 0, "parent transport authorization expired")
        return _bounded_process(argv, env=self.env, cwd=cwd or self.scratch, data=data,
            timeout=min(timeout, remaining))

    def _api(self, permit, method, path, *, request=None, missing=False):
        data = None if request is None else json.dumps(request, separators=(",", ":")).encode()
        argv = [str(self.gh), "api", "--hostname", "github.com", "--method", method, "--include", path]
        if data is not None:
            argv.extend(["--input", "-"])
        status, raw = self._run(permit, argv, data=data)
        header, separator, body = raw.replace(b"\r\n", b"\n").partition(b"\n\n")
        first = header.split(b"\n", 1)[0]
        match = re.fullmatch(rb"HTTP/[^ ]+ ([0-9]{3})(?: .*)?", first)
        if not separator or match is None:
            raise EvidenceUnavailable("parent GitHub response has no bounded HTTP status")
        code = int(match.group(1))
        if code == 404 and missing:
            return None
        if status != 0 or not 200 <= code < 300:
            raise EvidenceUnavailable(f"parent GitHub {method} returned HTTP {code}")
        try:
            return json.loads(body)
        except (ValueError, UnicodeError) as exc:
            raise EvidenceUnavailable("parent GitHub response is not JSON") from exc

    def observe(self, permit, artifact):
        prefix = "repos/" + permit.repo
        def ref(branch, missing=False):
            row = self._api(permit, "GET", prefix+"/git/ref/heads/"+quote(branch, safe="/"), missing=missing)
            if row is None:
                return None
            require(isinstance(row, dict) and isinstance(row.get("object"), dict)
                and isinstance(row["object"].get("sha"), str)
                and re.fullmatch("[0-9a-f]{40}", row["object"]["sha"]),
                "exact GitHub branch observation required")
            return row["object"]["sha"]
        base, head = ref(permit.base_branch), ref(permit.head_branch, missing=True)
        query = urlencode({"state": "all", "head": permit.repo.split("/")[0]+":"+permit.head_branch,
            "per_page": 100})
        rows = self._api(permit, "GET", prefix+"/pulls?"+query)
        require(isinstance(rows, list) and len(rows) < 100,
            "parent pull request observation exceeds its complete window")
        result = []
        for row in rows:
            try:
                if (row["head"]["repo"]["full_name"], row["base"]["repo"]["full_name"]) != (
                        permit.repo, permit.repo):
                    continue
                result.append({"number": row["number"], "repo": permit.repo,
                    "base_sha": row["base"]["sha"], "base_branch": row["base"]["ref"],
                    "head_sha": row["head"]["sha"], "head_branch": row["head"]["ref"],
                    "state": row["state"]})
            except (KeyError, TypeError) as exc:
                raise EvidenceUnavailable("parent pull request observation is incomplete") from exc
        return {"base_sha": base, "head_sha": head, "pull_requests": result}

    def push(self, permit, artifact, bundle):
        require(isinstance(bundle, bytes) and 0 < len(bundle) <= 2_000_000,
            "bounded verified result bundle required")
        with tempfile.TemporaryDirectory(prefix="parent-publication-", dir=self.scratch) as name:
            private = Path(name)
            bundle_file = private/"result.bundle"
            bundle_file.write_bytes(bundle)
            bundle_file.chmod(0o600)
            bare = private/"repository.git"
            bare.mkdir(mode=0o700)
            common = [str(self.git), "-C", str(bare), "-c", "core.hooksPath=/dev/null",
                "-c", "core.fsmonitor=false", "-c", "fetch.recurseSubmodules=false",
                "-c", "credential.helper=", "-c", "credential.helper=!"+shlex.quote(str(self.gh))+" auth git-credential",
                "-c", "credential.useHttpPath=true"]
            def git(*args, timeout=30):
                code, output = self._run(permit, common+list(args), cwd=private, timeout=timeout)
                if code != 0:
                    raise EvidenceUnavailable("isolated parent Git operation did not complete")
                return output.decode("utf-8").strip()
            git("init", "--bare", "--template=", "--object-format=sha1")
            url = "https://github.com/" + permit.repo + ".git"
            git("fetch", "--no-tags", "--no-write-fetch-head", "--no-recurse-submodules",
                url, permit.base_sha+":refs/heads/approved-base", timeout=60)
            git("-c", "protocol.file.allow=always", "fetch", "--no-tags", "--no-write-fetch-head",
                "--no-recurse-submodules", str(bundle_file), "HEAD:refs/heads/publication")
            require(git("rev-parse", "refs/heads/publication") == artifact.commit_sha
                and git("rev-list", "--parents", "-n", "1", artifact.commit_sha).split() ==
                    [artifact.commit_sha, permit.base_sha],
                "result bundle differs from the approved single-commit handoff")
            # Empty lease only creates a previously absent ref. No overwrite,
            # non-fast-forward fallback, source Git config, checkout or hooks.
            ref = "refs/heads/" + permit.head_branch
            git("push", "--porcelain", "--force-with-lease="+ref+":", url,
                artifact.commit_sha+":"+ref, timeout=60)

    def create_pull_request(self, permit, artifact, request):
        self._api(permit, "POST", "repos/"+permit.repo+"/pulls", request=request)

