"""Trusted completion evidence, shared by the existing durable worker.

Worker-authored producer labels and bundles are never admission authority.
Only the host collector writes records behind the task sandbox's read-only
root. SHA-256 addresses integrity and identity; it is not a signature.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import subprocess
import stat
from pathlib import Path
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse

from .reviewer import EvidenceRecord, ModelReview, ReviewInput, ReviewerGate, ReviewVerdict
from .workspace import ArtifactRef, WorkspaceManager, WorkspaceError
from agent_platform_dashboard.production_sources import command as artifact_command

VERSION = 1
EVIDENCE_VERSION = 2
_SHA = re.compile(r"^[0-9a-f]{64}$")
_REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_GIT_SHA = re.compile(r"^[0-9a-f]{40}$")


class EvidenceError(RuntimeError):
    code = "evidence_invalid"


class EvidenceMissing(EvidenceError):
    code = "evidence_missing"


class EvidenceUnavailable(EvidenceError):
    code = "evidence_unavailable"


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def binding(task: dict) -> dict:
    """Identity comes from the protected host task, never from the result."""
    result = {name: task.get(name) for name in
              ("id", "run_token", "idempotency_key")}
    result["attempt"] = task.get("attempt_id", task.get("attempts", 0))
    result["fencing_token"] = task.get("fencing_token", 0)
    if (any(not isinstance(result[name], str) or not result[name]
            for name in ("id", "run_token", "idempotency_key"))
            or type(result["attempt"]) is not int or result["attempt"] < 0
            or type(result["fencing_token"]) is not int or result["fencing_token"] < 0):
        raise EvidenceError("completion identity is incomplete")
    return result


def parse_artifact(raw: Any) -> ArtifactRef:
    names = {"task_id", "attempt", "base_sha", "commit_sha", "result_sha",
             "changed_files", "branch"}
    if not isinstance(raw, dict) or set(raw) != names:
        raise EvidenceError("a complete immutable ArtifactRef is required")
    if (type(raw["attempt"]) is not int or raw["attempt"] < 0
            or not isinstance(raw["task_id"], str) or not raw["task_id"]
            or not isinstance(raw["branch"], str) or not raw["branch"]
            or not isinstance(raw["changed_files"], (list, tuple))
            or not raw["changed_files"]
            or any(not isinstance(p, str) for p in raw["changed_files"])
            or len(set(raw["changed_files"])) != len(raw["changed_files"])
            or any(not isinstance(raw[n], str) or not _GIT_SHA.fullmatch(raw[n])
                   for n in ("base_sha", "commit_sha"))
            or not isinstance(raw["result_sha"], str) or not _SHA.fullmatch(raw["result_sha"])):
        raise EvidenceError("invalid ArtifactRef")
    return ArtifactRef(**{**raw, "changed_files": tuple(raw["changed_files"])})


class EvidenceStore:
    """Host-owned append-only plans and accepted records, outside writable binds.

    Publication uses fsynced temporary bytes followed by an atomic exclusive rename
    and directory fsync. A restart sees either the complete object or no object.
    It never admits a temporary file or overwrites a prior record.
    """

    def __init__(self, root: Path):
        if root.is_symlink():
            raise EvidenceError("evidence root cannot be a symlink")
        try:
            self.root = root.resolve()
            self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        except OSError as exc:
            raise EvidenceUnavailable("host evidence store is unavailable") from exc

    def protect_from(self, writable_roots: tuple[Path, ...]) -> None:
        for root in writable_roots:
            resolved = root.resolve()
            if self.root == resolved or self.root.is_relative_to(resolved):
                raise EvidenceError("evidence store overlaps a worker-writable root")

    def _path(self, kind: str, key: str) -> Path:
        if kind not in {"plan", "accepted", "work-result", "work-handoff-intent"} or not _SHA.fullmatch(key):
            raise EvidenceError("invalid evidence address")
        return self.root / f"{kind}-{key}.json"

    def read(self, kind: str, key: str) -> dict:
        path = self._path(kind, key)
        try:
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
            try:
                before = os.fstat(fd)
                if (not stat.S_ISREG(before.st_mode) or before.st_uid != os.geteuid()
                        or before.st_nlink != 1 or stat.S_IMODE(before.st_mode) != 0o600
                        or not 0 < before.st_size <= 2_000_000):
                    raise EvidenceError("evidence must be a bounded private regular single-link file")
                chunks, size = [], 0
                while size <= 2_000_000:
                    chunk = os.read(fd, min(65536, 2_000_001-size))
                    if not chunk:
                        break
                    chunks.append(chunk); size += len(chunk)
                raw = b"".join(chunks)
                after = os.fstat(fd); named = path.lstat()
                stamp = lambda value: (value.st_dev,value.st_ino,value.st_size,value.st_mtime_ns,
                                       value.st_ctime_ns,value.st_mode,value.st_uid,value.st_nlink)
                if len(raw) != before.st_size or stamp(before) != stamp(after) or stamp(after) != stamp(named):
                    raise EvidenceError("evidence changed during bounded read")
            finally:
                os.close(fd)
            envelope = json.loads(raw)
            if (set(envelope) != {"payload", "sha256"}
                    or not isinstance(envelope["payload"], dict)
                    or envelope["sha256"] != digest(envelope["payload"])
                    or canonical(envelope) != raw):
                raise EvidenceError("evidence integrity mismatch")
            # Also completes an interrupted exclusive publication whose
            # directory fsync failed before the task queue transition.
            self._sync_directory()
            return envelope["payload"]
        except FileNotFoundError as exc:
            raise EvidenceMissing("evidence does not exist") from exc
        except EvidenceError:
            raise
        except OSError as exc:
            import errno
            if exc.errno in {errno.ELOOP,errno.ENOTDIR,errno.ENXIO}:
                raise EvidenceError("evidence path is not a private regular record") from exc
            raise EvidenceUnavailable("evidence cannot be read") from exc
        except (TypeError, ValueError, KeyError, UnicodeError, RecursionError) as exc:
            raise EvidenceError("invalid evidence encoding") from exc

    def lookup_acceptance(self, identity: dict, plan_hash: str) -> tuple[dict | None, bool]:
        from .accepted_index import AcceptedIndex
        try:
            return AcceptedIndex(self).lookup(identity, plan_hash)
        except OSError as exc:
            raise EvidenceUnavailable("host acceptance index is unavailable") from exc

    def _sync_directory(self) -> None:
        fd = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)

    @staticmethod
    def _exclusive_publish(temporary, destination):
        # Atomic no-replace rename exposes exactly one link from the outset.
        # A link/unlink pair has a two-link window that private readers must deny.
        import ctypes, errno
        try:
            operation = ctypes.CDLL(None, use_errno=True).renameat2
        except (OSError, AttributeError) as exc:
            raise EvidenceUnavailable("atomic exclusive evidence publication unsupported") from exc
        operation.argtypes = [ctypes.c_int,ctypes.c_char_p,ctypes.c_int,ctypes.c_char_p,ctypes.c_uint]
        operation.restype = ctypes.c_int
        if operation(-100,os.fsencode(temporary),-100,os.fsencode(destination),1) != 0:
            code=ctypes.get_errno()
            if code==errno.EEXIST:
                raise FileExistsError(code,"immutable evidence address exists",str(destination))
            raise OSError(code,"exclusive evidence publication failed",str(destination))

    def publish(self, kind: str, key: str, payload: dict) -> str:
        try:
            return self._publish(kind, key, payload)
        except OSError as exc:
            raise EvidenceUnavailable("host evidence publication is unavailable") from exc

    def _publish(self, kind: str, key: str, payload: dict, *, register_index=True) -> str:
        path = self._path(kind, key)
        content_hash = digest(payload)
        data = canonical({"payload": payload, "sha256": content_hash})
        if len(data) > 2_000_000:
            raise EvidenceError("evidence exceeds bounded record size")
        if register_index:
            from .accepted_index import AcceptedIndex
            AcceptedIndex(self).prepare_publication(kind, key, payload)
        fd, tmp = tempfile.mkstemp(prefix=".publication-", dir=self.root)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            try:
                self._exclusive_publish(tmp, path)
            except FileExistsError:
                if canonical(self.read(kind, key)) != canonical(payload):
                    raise EvidenceError("immutable evidence publication conflict")
            self._sync_directory()
        finally:
            try:
                os.unlink(tmp)
            except FileNotFoundError:
                pass
        return content_hash


def network_denial_filter(*, deny_process_creation=False):
    """Return a host-generated BPF FD; fail closed without libseccomp."""
    import ctypes
    import errno
    lib = None
    ctx = None
    fd = None
    try:
        lib = ctypes.CDLL("libseccomp.so.2")
        lib.seccomp_init.argtypes = [ctypes.c_uint32]
        lib.seccomp_init.restype = ctypes.c_void_p
        lib.seccomp_release.argtypes = [ctypes.c_void_p]
        lib.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
        lib.seccomp_syscall_resolve_name.restype = ctypes.c_int
        lib.seccomp_rule_add.argtypes = [ctypes.c_void_p, ctypes.c_uint32,
                                        ctypes.c_int, ctypes.c_uint]
        lib.seccomp_rule_add.restype = ctypes.c_int
        lib.seccomp_export_bpf.argtypes = [ctypes.c_void_p, ctypes.c_int]
        lib.seccomp_export_bpf.restype = ctypes.c_int
        ctx = lib.seccomp_init(0x7fff0000)  # SCMP_ACT_ALLOW; other ABIs fail closed.
        if not ctx:
            raise EvidenceUnavailable("artifact syscall filter cannot initialize")
        names = ("socket", "socketpair", "connect", "accept", "accept4", "bind",
                     "listen", "sendto", "sendmsg", "sendmmsg", "recvfrom", "recvmsg",
                     "recvmmsg", "shutdown", "getsockname", "getpeername",
                     "setsockopt", "getsockopt", "io_uring_setup", "io_uring_enter",
                     "io_uring_register")
        if deny_process_creation:
            names += ("fork", "vfork", "clone", "clone3", "unshare", "setns", "mount", "umount2",
                      "move_mount", "open_tree", "mount_setattr", "fsopen", "fsconfig",
                      "fsmount", "fspick", "pivot_root", "chroot")
        for name in names:
            number = lib.seccomp_syscall_resolve_name(name.encode("ascii"))
            if number == -1:
                if name in {"socket", "connect", "clone"}:
                    raise EvidenceUnavailable("mandatory artifact syscall cannot resolve")
                continue
            if lib.seccomp_rule_add(ctx, 0x00050000 | errno.EPERM, number, 0) != 0:
                raise EvidenceUnavailable("artifact syscall filter rule failed")
        fd = os.memfd_create("herdr-artifact-network-denial", os.MFD_CLOEXEC)
        if lib.seccomp_export_bpf(ctx, fd) != 0:
            raise EvidenceUnavailable("artifact syscall filter cannot export")
        os.lseek(fd, 0, os.SEEK_SET)
        return fd
    except (OSError, AttributeError) as exc:
        if fd is not None:
            os.close(fd)
        raise EvidenceUnavailable("artifact syscall isolation is unavailable") from exc
    except EvidenceError:
        if fd is not None:
            os.close(fd)
        raise
    finally:
        if lib is not None and ctx:
            lib.seccomp_release(ctx)


def read_only_git(root: Path):
    """Untrusted worktree Git configuration never runs in the host namespace.

    Even a configured clean filter has no network, host process visibility,
    credentials in its environment, or writable host mounts. The collector
    remains outside this namespace to publish accepted evidence.
    """
    bwrap, git = Path("/usr/bin/bwrap"), Path("/usr/bin/git")
    if not bwrap.is_file() or not git.is_file():
        raise EvidenceUnavailable("read-only artifact verifier is unavailable")
    def raw(args):
        seccomp_fd = network_denial_filter()
        command = [
            str(bwrap), "--ro-bind", "/", "/", "--dev", "/dev", "--proc", "/proc",
            "--unshare-pid", "--unshare-net", "--seccomp", str(seccomp_fd),
            "--tmpfs", "/tmp", "--clearenv",
            "--setenv", "PATH", "/usr/bin:/bin", "--setenv", "HOME", "/tmp",
            "--", str(git), "--no-optional-locks", "--no-replace-objects",
            "-c", "core.fsmonitor=false", "-c", "core.hooksPath=/dev/null",
            "-c", "diff.external=", "-C", str(root), *args,
        ]
        try:
            from .work_lifetime import remaining_work_seconds
            return artifact_command(command, limit=2_000_000, timeout=remaining_work_seconds(30),
                                    pass_fds=(seccomp_fd,))
        except ValueError as exc:
            if str(exc) == "source_timeout":
                raise EvidenceUnavailable("artifact verifier temporarily timed out") from exc
            raise EvidenceError("bounded artifact metadata or blob output exceeded") from exc
        except (OSError, subprocess.SubprocessError) as exc:
            raise EvidenceUnavailable("artifact verifier execution unavailable") from exc
        finally:
            os.close(seccomp_fd)
    def run(args):
        try:
            return raw(args).decode("utf-8")
        except UnicodeError as exc:
            raise EvidenceError("artifact metadata is not valid UTF-8") from exc
    run.raw = raw
    return run


def verify_committed_bytes(artifact: ArtifactRef, workspace: Path, git) -> None:
    """Bind the result digest to Git blobs and reject filter-hidden dirty bytes.

    Status alone is insufficient: a clean filter may conceal changed physical
    files. Compare every tracked file to the exact committed tree, and derive
    changed-file SHA-256 records from those committed blobs.
    """
    import time
    deadline = time.monotonic() + 60
    total_bytes = 0
    entries = {}
    for item in git(["ls-tree", "-r", "-z", "--full-tree", artifact.commit_sha]).split("\0"):
        if not item:
            continue
        metadata, relative = item.split("\t", 1)
        mode, kind, blob = metadata.split()
        if (mode not in {"100644", "100755"} or kind != "blob"
                or not _GIT_SHA.fullmatch(blob)
                or Path(relative).is_absolute() or ".." in Path(relative).parts):
            raise EvidenceError("unsupported committed output type or path")
        if len(entries) >= 4096 or time.monotonic() > deadline:
            raise EvidenceError("artifact tree exceeds cumulative verification bound")
        entries[relative] = blob
        path = workspace / relative
        if any(parent.is_symlink() for parent in path.parents if parent != workspace and parent.is_relative_to(workspace)):
            raise EvidenceError("tracked file has a symlink parent")
        try:
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            with os.fdopen(fd, "rb") as handle:
                info = os.fstat(handle.fileno())
                size = info.st_size
                if not stat.S_ISREG(info.st_mode) or size > 2_000_000:
                    raise EvidenceError("unsupported or oversized tracked file")
                if bool(info.st_mode & stat.S_IXUSR) != (mode == "100755"):
                    raise EvidenceError("physical executable mode differs from committed tree")
                total_bytes += size
                if total_bytes > 67_108_864 or time.monotonic() > deadline:
                    raise EvidenceError("artifact tree exceeds cumulative verification bound")
                sha = hashlib.sha1(f"blob {size}\0".encode())
                remaining = size
                while remaining:
                    data = handle.read(min(remaining, 1_000_000))
                    if not data:
                        raise EvidenceError("tracked bytes changed during verification")
                    sha.update(data)
                    remaining -= len(data)
                if handle.read(1) or sha.hexdigest() != blob:
                    raise EvidenceError("physical bytes differ from committed tree")
        except OSError as exc:
            raise EvidenceError("committed file is missing or unsafe") from exc
    records = []
    for relative in artifact.changed_files:
        if time.monotonic() > deadline:
            raise EvidenceError("artifact tree exceeds cumulative verification deadline")
        blob = entries.get(relative)
        if blob is None:
            if (workspace / relative).exists() or (workspace / relative).is_symlink():
                raise EvidenceError("committed deletion differs from workspace")
            records.append({"path": relative, "kind": "deleted"})
        else:
            data = git.raw(["cat-file", "blob", blob])
            records.append({"path": relative, "kind": "file", "size": len(data),
                            "sha256": hashlib.sha256(data).hexdigest()})
    if time.monotonic() > deadline:
        raise EvidenceError("artifact tree exceeds cumulative verification deadline")
    payload = {"task_id": artifact.task_id, "attempt": artifact.attempt,
               "base_sha": artifact.base_sha, "commit_sha": artifact.commit_sha,
               "branch": artifact.branch, "files": records}
    if digest(payload) != artifact.result_sha:
        raise EvidenceError("artifact digest differs from committed bytes")


def validate_criteria(kind: str, criteria: Any) -> None:
    if not isinstance(criteria, dict):
        raise EvidenceError(f"typed {kind} immutable artifact criteria are missing")
    common = {"schema", "report_path"}
    contract_review = kind == "review" and criteria.get("schema") == "review-contract-report-v1"
    extra = ({"sections"} if kind == "research" else
             {"target_commit", "target_contract", "target_contract_sha256"} if contract_review else {"target_commit"})
    schema = "review-contract-report-v1" if contract_review else f"{kind}-report-v1"
    path = criteria.get("report_path")
    if (set(criteria) != common | extra
            or criteria.get("schema") != schema
            or not isinstance(path, str) or len(path) > 256
            or not path.startswith(f"reports/{kind}/") or not path.endswith(".json")
            or Path(path).is_absolute() or ":" in path or "\\" in path
            or any(part in {"", ".", ".."} for part in path.split("/"))):
        raise EvidenceError("invalid typed artifact criteria")
    if kind == "research":
        sections = criteria["sections"]
        if (not isinstance(sections, list) or not 1 <= len(sections) <= 32
                or any(not isinstance(x, str) or not x or len(x) > 128 for x in sections)
                or len(set(sections)) != len(sections)):
            raise EvidenceError("research sections are invalid")
    elif not isinstance(criteria["target_commit"], str) or not _GIT_SHA.fullmatch(criteria["target_commit"]):
        raise EvidenceError("review target must be a full commit SHA")

    if contract_review:
        from .work_planning import bounded
        target = criteria["target_contract"]
        bounded(target)
        if (not isinstance(target, dict) or set(target) != {"spec_sha256", "definition"}
                or not isinstance(target["spec_sha256"], str) or not _SHA.fullmatch(target["spec_sha256"])
                or not isinstance(target["definition"], dict)
                or target["definition"].get("base_sha") != criteria["target_commit"]
                or digest(target) != criteria["target_contract_sha256"]):
            raise EvidenceError("prebuild review target contract binding invalid")


def validate_plan(plan: dict) -> None:
    names = {"version", "identity", "repo", "kind", "spec_hash", "policy_hash",
             "plan_hash", "base_sha", "baseline", "workspace_root",
             "required_checks", "reviewer", "environment"}
    if isinstance(plan, dict) and isinstance(plan.get("kind"), str) and plan.get("kind") in {"research", "review"}:
        names.add("criteria")
    if isinstance(plan, dict) and "scope_policy" in plan:
        if plan.get("kind") != "coding":
            raise EvidenceError("scope policy applies to coding artifacts")
        from .scope_evidence import validate_scope_policy
        validate_scope_policy(plan["scope_policy"])
        names.add("scope_policy")
    if not isinstance(plan, dict) or set(plan) != names or type(plan["version"]) is not int or plan["version"] != VERSION:
        raise EvidenceError("unsupported completion plan")
    if (not isinstance(plan["kind"], str) or plan["kind"] not in {"coding", "research", "review"}
            or not isinstance(plan["repo"], str) or not _REPO.fullmatch(plan["repo"])
            or not isinstance(plan["base_sha"], str) or not _GIT_SHA.fullmatch(plan["base_sha"])
            or any(not isinstance(plan[n], str) or not _SHA.fullmatch(plan[n])
                   for n in ("spec_hash", "policy_hash", "plan_hash"))
            or not isinstance(plan["required_checks"], list)
            or (plan["kind"] == "coding" and not plan["required_checks"])
            or (plan["kind"] != "coding" and plan["required_checks"] != ["GitGuardian Security Checks"])
            or any(not isinstance(n, str) or not n or len(n) > 64
                   for n in plan["required_checks"])
            or len(set(plan["required_checks"])) != len(plan["required_checks"])
            or not isinstance(plan["baseline"], list)
            or not isinstance(plan["environment"], dict)
            or plan["reviewer"] != "chatgpt-codex-connector[bot]"
            or not isinstance(plan["workspace_root"], str)
            or not Path(plan["workspace_root"]).is_absolute()):
        raise EvidenceError("invalid completion plan")
    if plan["kind"] != "coding":
        validate_criteria(plan["kind"], plan["criteria"])
    pinned = {k: v for k, v in plan.items() if k not in {"plan_hash", "baseline"}}
    if digest(pinned) != plan["plan_hash"]:
        raise EvidenceError("validation plan changed")


def inspect_typed_artifact(plan: dict, artifact: ArtifactRef, workspace: Path) -> dict:
    criteria = plan["criteria"]
    path = criteria["report_path"]
    if artifact.changed_files != (path,):
        raise EvidenceError("typed report cannot carry implementation or unrelated changes")
    raw = read_only_git(workspace)(["show", f"{artifact.commit_sha}:{path}"])
    if len(raw.encode("utf-8")) > 1_000_000:
        raise EvidenceError("typed report exceeds its size bound")
    try:
        report = json.loads(raw)
    except (TypeError, ValueError) as exc:
        raise EvidenceError("typed report is invalid JSON") from exc
    if not isinstance(report, dict) or type(report.get("version")) is not int or report["version"] != 1 or report.get("kind") != plan["kind"]:
        raise EvidenceError("typed report schema mismatch")
    if plan["kind"] == "research":
        if set(report) != {"version", "kind", "sections"} or not isinstance(report["sections"], list):
            raise EvidenceError("research report is invalid")
        sections = report["sections"]
        if (len(sections) != len(criteria["sections"])
                or any(not isinstance(row, dict) or set(row) != {"id", "summary", "sources"} for row in sections)
                or sorted(row["id"] for row in sections if isinstance(row["id"], str)) != sorted(criteria["sections"])):
            raise EvidenceError("research report does not cover the declared sections")
        for row in sections:
            if (not isinstance(row["summary"], str) or not row["summary"].strip()
                    or not isinstance(row["sources"], list) or not 1 <= len(row["sources"]) <= 32):
                raise EvidenceError("research section requires content and sources")
            for source in row["sources"]:
                if not isinstance(source, dict) or set(source) != {"url", "title"} or not all(isinstance(source[n], str) and source[n].strip() for n in source):
                    raise EvidenceError("research source is invalid")
                url = urlparse(source["url"])
                if url.scheme != "https" or not url.netloc or url.username or url.password:
                    raise EvidenceError("research source must be a credential-free HTTPS reference")
        coverage = {"sections": criteria["sections"], "source_reference_count": sum(len(row["sources"]) for row in sections),
                    "limits": "structure and independent artifact review; source truth is not asserted by schema validation"}
    else:
        contract_keys = {"target_contract_sha256"} if criteria["schema"] == "review-contract-report-v1" else set()
        if (set(report) != {"version", "kind", "target_commit", "summary", "verdict", "findings"} | contract_keys
                or contract_keys and report.get("target_contract_sha256") != criteria["target_contract_sha256"]
                or report["target_commit"] != criteria["target_commit"]
                or report["verdict"] not in {"pass", "block", "needs_replan"}
                or not isinstance(report["summary"], str) or not report["summary"].strip()
                or not isinstance(report["findings"], list) or len(report["findings"]) > 100):
            raise EvidenceError("review report does not match its declared target")
        for finding in report["findings"]:
            if (not isinstance(finding, dict) or set(finding) != {"priority", "summary"}
                    or finding["priority"] not in {"P0", "P1", "P2", "P3"}
                    or not isinstance(finding["summary"], str) or not finding["summary"].strip()):
                raise EvidenceError("review finding is invalid")
        if report["verdict"] == "pass" and any(x["priority"] != "P3" for x in report["findings"]):
            raise EvidenceError("review pass contradicts blocking findings")
        coverage = {"target_commit": report["target_commit"], "verdict": report["verdict"],
                    "limits": "review artifact completion does not approve or merge the reviewed implementation"}
        if contract_keys:
            coverage["target_contract_sha256"] = criteria["target_contract_sha256"]
    return {"schema": criteria["schema"], "report_path": path, "report_hash": digest(report), "coverage": coverage}


def invocation_identity(task):
    from .security import InvocationIdentity, SecurityError
    session = task.get("execution_session")
    if not isinstance(session, dict):
        raise EvidenceError("trusted worker execution session is missing")
    parent_task = task.get("parent_task_id")
    parent_agent = task.get("parent_agent_id") if parent_task else session.get("coordinator_agent")
    if not parent_task:
        parent_task = "coordinator:" + parent_agent if isinstance(parent_agent, str) else ""
    try:
        return InvocationIdentity(consumer="github:"+task["repo"],agent_id=session.get("agent_name"),
            parent_agent_id=parent_agent,parent_task_id=parent_task,task_id=task["id"],
            run_token=task["run_token"],fencing_token=task.get("fencing_token"))
    except (SecurityError, KeyError, TypeError, ValueError) as exc:
        raise EvidenceError("trusted invocation identity is invalid") from exc


def verify_invocation_session(task):
    """Validate current physical proof from protected host state, never result JSON."""
    from .policy_launch import validate_policy_evidence, verify_retained_policy_evidence
    from .security import SecurityError
    identity = invocation_identity(task)
    session = task["execution_session"]
    attestation, policy = session.get("sandbox_attestation"), session.get("invocation_policy")
    if session.get("sandbox_verified") is not True or not isinstance(attestation, dict) or not isinstance(policy, dict):
        raise EvidenceError("trusted publication requires sealed physical invocation proof")
    pid = session.get("sandbox_pid")
    child = bool(task.get("parent_task_id"))
    expected = {"authority":"herdr-runtime" if child else "agent-task-worker", "kind":"bwrap",
        "task_id":identity.task_id,"run_token":identity.run_token,"agent_name":identity.agent_id,
        "pane_id":session.get("pane_id"),"marker":session.get("pane_marker"),
        "fencing_token":identity.fencing_token,"sandbox_pid":pid}
    if (type(pid) is not int or pid <= 0 or not expected["pane_id"] or not expected["marker"]
            or any(attestation.get(k) != v for k,v in expected.items())):
        raise EvidenceError("host sandbox attestation differs from the admitted session")
    try:
        verified_at = datetime.fromisoformat(attestation["verified_at"].replace("Z","+00:00"))
        if verified_at.tzinfo is None or verified_at > datetime.now(UTC):
            raise ValueError("launch timestamp invalid")
        proof = validate_policy_evidence(policy,identity=identity)
        # The runtime seals this exact original attestation before adding its
        # durable CLI-policy/timestamp fields. Root attestation is sealed whole.
        original_names = ("authority","task_id","run_token","sandbox_pid","fencing_token",
                          "agent_name","pane_id","marker","worktree_identity")
        if child and task.get("ownership") is not None:
            original_names += ("ownership_sha256","owned_write_mounts")
        original = {k:attestation[k] for k in original_names} if child else dict(attestation)
        if child and task.get("ownership") is not None:
            from .child_ownership import ChildOwnership
            from .owned_write_mounts import validate_owned_mount_evidence
            ownership = ChildOwnership.from_json(task["ownership"])
            if attestation.get("ownership_sha256") != ownership.hash:
                raise EvidenceError("sealed child ownership differs from admitted contract")
            rows = validate_owned_mount_evidence(ownership, attestation.get("owned_write_mounts"))
            if task.get("owned_write_mounts") != [dict(row) for row in rows]:
                raise EvidenceError("sealed child mounts differ from protected observations")
        verify_retained_policy_evidence(proof,identity=identity,pid=pid,attestation=original,now=verified_at)
        return proof
    except OSError as exc:
        import errno
        if exc.errno in {errno.ENOENT, errno.ESRCH}:
            raise EvidenceError("retained physical invocation is irrecoverably lost; trusted replan required") from exc
        raise EvidenceUnavailable("retained physical invocation is unavailable") from exc
    except (SecurityError, KeyError, TypeError, ValueError) as exc:
        raise EvidenceError("retained physical invocation proof is invalid") from exc


def accept_artifact(task: dict, result: dict, plan: dict, store: EvidenceStore,
                  workspace: Path, collector, *, result_payload_sha256: str | None = None, invocation_verifier=None) -> dict:
    """Reuse WorkspaceManager and ReviewerGate; never consume result.evidence."""
    validate_plan(plan)
    if result_payload_sha256 is not None and (not isinstance(result_payload_sha256,str) or not _SHA.fullmatch(result_payload_sha256)):
        raise EvidenceError("result payload digest invalid")
    if invocation_verifier is not None and not callable(invocation_verifier):
        raise EvidenceError("host invocation verifier required")
    verify_invocation = invocation_verifier or verify_invocation_session
    identity = binding(task)
    if plan["identity"] != identity or plan["repo"] != task.get("repo"):
        raise EvidenceError("plan belongs to another task or attempt")
    artifact = parse_artifact(result.get("artifact"))
    if (artifact.task_id != identity["id"] or artifact.attempt != identity["attempt"]
            or artifact.base_sha != plan["base_sha"]):
        raise EvidenceError("artifact identity or baseline mismatch")
    root = Path(plan["workspace_root"]).resolve()
    workspace = workspace.resolve()
    if not workspace.is_relative_to(root) or workspace == root:
        raise EvidenceError("artifact workspace is outside the declared root")
    store.protect_from((root,))
    key = digest({"identity": identity, "plan_hash": plan["plan_hash"]})
    scope_proof = None
    publication = {"artifact": artifact.to_json(), "workspace": str(workspace),
                   "pr_number": result.get("pr_number")}
    if "scope_policy" in plan:
        from .scope_evidence import verify_scope_self_check
        scope_proof = verify_scope_self_check(plan, artifact, result.get("scope_self_check"))
        publication["scope_report_sha256"] = scope_proof["report_sha256"]
    publication_hash = digest(publication)
    accepted, legacy = store.lookup_acceptance(identity, plan["plan_hash"])
    if accepted is not None:
        if result_payload_sha256 is not None and accepted.get("result_payload_sha256") != result_payload_sha256:
            raise EvidenceError("accepted child result payload changed")
        if (accepted.get("identity") != identity
                or accepted.get("version") != EVIDENCE_VERSION
                or accepted.get("plan_hash") != plan["plan_hash"]
                or accepted.get("artifact") != json.loads(canonical(artifact.to_json()))
                or accepted.get("level") != "verified_worker_result"
                or accepted.get("artifact_workspace") != str(workspace)
                or accepted.get("spec_hash") != plan["spec_hash"]
                or accepted.get("policy_hash") != plan["policy_hash"]
                or scope_proof is not None and accepted.get("scope_self_check") != scope_proof
                or (not legacy and accepted.get("publication_hash") != publication_hash)
                or (legacy and accepted.get("proof", {}).get("review", {}).get("pull_request") != result.get("pr_number"))):
            raise EvidenceError("accepted record binding mismatch")
        from .policy_launch import validate_policy_evidence
        from .security import SecurityError
        try:
            validate_policy_evidence(accepted.get("launch_policy"),identity=invocation_identity(task))
        except (SecurityError, TypeError, ValueError) as exc:
            raise EvidenceError("accepted result lacks exact sealed invocation proof") from exc
        if legacy:
            accepted = {**accepted, "publication_hash": publication_hash}
            store.publish("accepted", key, accepted)
        return {**accepted, "bundle_hash": digest(accepted)}

    launch_policy = verify_invocation(task)
    try:
        manager = WorkspaceManager(workspace, git=read_only_git(workspace), worktrees_dir=root)
    except (OSError, WorkspaceError) as exc:
        raise EvidenceUnavailable("artifact workspace is unavailable") from exc
    try:
        manager.verify(artifact, workspace)
        verify_committed_bytes(artifact, workspace, manager.git)
    except WorkspaceError as exc:
        raise EvidenceError("artifact workspace verification failed") from exc
    if scope_proof is not None:
        from .scope_evidence import verify_shared_contracts
        verify_shared_contracts(plan, artifact, manager.git)
    proof = collector(plan, artifact, result.get("pr_number"))
    required = list(plan["required_checks"])
    if (not isinstance(proof, dict) or set(proof) != {"checks", "review", "source"}
            or proof["source"] != "github-api"):
        raise EvidenceError("unsupported evidence source")
    records = tuple(EvidenceRecord(
        name=n, passed=True, artifact_result_sha=artifact.result_sha,
        producer="trusted-ci", evidence_sha256=digest(proof["checks"][n]),
    ) for n in required)
    typed_proof = None
    if plan["kind"] != "coding":
        typed_proof = inspect_typed_artifact(plan, artifact, workspace)
        required.append("artifact-criteria")
        records += (EvidenceRecord(
            name="artifact-criteria", passed=True, artifact_result_sha=artifact.result_sha,
            producer="trusted-validator", evidence_sha256=digest(typed_proof)),)
    review = proof["review"]
    from .verification_binding import commit_binding
    expected_binding = commit_binding(plan)
    if (review.get("specification_binding") != {**expected_binding, "binding_sha256": digest(expected_binding)}
            or review.get("actor") != plan["reviewer"] or review.get("commit_sha") != artifact.commit_sha):
        raise EvidenceError("review origin or commit mismatch")
    model_review = ModelReview(
        artifact_result_sha=artifact.result_sha,
        evidence_digest=ReviewerGate.evidence_digest(records),
        actor_id=review["actor"], provider="github", model="codex-review",
        verdict=ReviewVerdict.PASS, review_sha256=digest(review), spec_hash=plan["spec_hash"],
    )
    gate = ReviewerGate(required_evidence=tuple(required), require_spec_binding=True)
    decision = gate.review(ReviewInput(
        spec_hash=plan["spec_hash"], artifact=artifact,
        worker_actor=(task.get("execution_session") or {}).get("agent_name", "durable-worker"),
        worker_claim="completed", evidence=records, model_review=model_review,
    ))
    if decision.verdict != ReviewVerdict.PASS:
        raise EvidenceError(f"review gate rejected: {decision.reason.value}")
    # The worker can still be alive while the collector runs; recheck its exact
    # bytes after collection before persisting a proof about those bytes.
    try:
        manager.verify(artifact, workspace)
        verify_committed_bytes(artifact, workspace, manager.git)
    except WorkspaceError as exc:
        raise EvidenceError("artifact changed during collection") from exc
    if verify_invocation(task) != launch_policy:
        raise EvidenceError("invocation policy changed during collection")
    if scope_proof is not None:
        validate_plan(plan)
        verify_shared_contracts(plan, artifact, manager.git)
        if verify_scope_self_check(plan, artifact, result.get("scope_self_check")) != scope_proof:
            raise EvidenceError("scope report changed during collection")
    bundle = {
        "version": EVIDENCE_VERSION, "identity": identity, "repo": plan["repo"],
        "kind": plan["kind"], "level": "verified_worker_result",
        "artifact_workspace": str(workspace), "publication_hash": publication_hash,
        "spec_hash": plan["spec_hash"], "policy_hash": plan["policy_hash"],
        "plan_hash": plan["plan_hash"], "artifact": json.loads(canonical(artifact.to_json())),
        "baseline": plan["baseline"], "environment": plan["environment"],
        "proof": proof, "typed_validation": typed_proof, "review_hash": decision.review_hash,
        "launch_policy": launch_policy,
        "integration": None, "deployment": None,
    }
    if scope_proof is not None:
        bundle["scope_self_check"] = scope_proof
    if result_payload_sha256 is not None:
        bundle["result_payload_sha256"] = result_payload_sha256
    bundle_hash = store.publish("accepted", key, bundle)
    return {**bundle, "bundle_hash": bundle_hash}
