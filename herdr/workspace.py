"""Herdr v1.3 isolated workspaces and exact artifact handoff.

Coding tasks run in dedicated Git worktrees pinned to one exact base SHA.
Workers have no GitHub write credentials and never push. A sealed result is
bound to task/attempt/base, the local result commit, the changed-file manifest,
and the actual bytes of every changed file.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

GitRunner = Callable[[Sequence[str]], str]
_SHA_RE = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")


class WorkspaceError(RuntimeError):
    """Base class for fail-closed workspace errors."""


class StaleBaseError(WorkspaceError):
    """The task base no longer equals the authoritative integration base."""


class ConflictError(WorkspaceError):
    """Two artifacts cannot be safely integrated together."""


class ArtifactIntegrityError(WorkspaceError):
    """A sealed artifact no longer matches its content or Git state."""


class UnsafePathError(WorkspaceError):
    """A changed-file path escaped the worktree contract."""


@dataclass(frozen=True)
class ArtifactRef:
    task_id: str
    attempt: int
    base_sha: str
    commit_sha: str
    result_sha: str
    changed_files: tuple[str, ...]
    branch: str

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


def _safe_component(value: str, *, limit: int = 28) -> str:
    raw = value.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", raw).strip("-")[:limit] or "task"
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:8]
    return f"{slug}-{digest}"


def _validate_sha(value: str, field: str) -> str:
    if not isinstance(value, str) or not _SHA_RE.fullmatch(value):
        raise WorkspaceError(f"{field} must be a lowercase 40- or 64-character Git SHA")
    return value


def _safe_relative_path(value: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise UnsafePathError("changed-file path is empty or invalid")
    candidate = PurePosixPath(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise UnsafePathError("changed-file path escapes worktree")
    normalized = candidate.as_posix()
    if normalized in {".", ""}:
        raise UnsafePathError("changed-file path is invalid")
    return normalized


@dataclass
class WorkspaceManager:
    root: Path
    git: GitRunner | None = field(default=None, repr=False)
    worktrees_dir: Path | None = None
    artifacts_dir: Path | None = None

    def __post_init__(self) -> None:
        self.root = self.root.resolve()
        if not self.root.exists():
            raise FileNotFoundError(f"repository root not found: {self.root}")
        self.worktrees_dir = (self.worktrees_dir or self.root / ".herdr-worktrees").resolve()
        self.artifacts_dir = (self.artifacts_dir or self.root / ".herdr-artifacts").resolve()
        self.git = self.git or _real_git(self.root)

    def branch_name(
        self, issue: int | str, task_id: str, attempt: int, base_sha: str
    ) -> str:
        if isinstance(attempt, bool) or not isinstance(attempt, int) or attempt < 0:
            raise WorkspaceError("attempt must be a non-negative integer")
        _validate_sha(base_sha, "base_sha")
        issue_slug = _safe_component(str(issue), limit=18)
        task_slug = _safe_component(task_id, limit=24)
        return f"herdr/{issue_slug}/{task_slug}/a{attempt}/b{base_sha[:10]}"

    def worktree_path(
        self, issue: int | str, task_id: str, attempt: int, base_sha: str
    ) -> Path:
        digest = hashlib.sha256(
            f"{issue}\0{task_id}\0{attempt}\0{base_sha}".encode()
        ).hexdigest()[:20]
        return self.worktrees_dir / f"task-{digest}"

    def integration_tip(self) -> str:
        assert self.git is not None
        return _validate_sha(self.git(["rev-parse", "origin/main"]).strip(), "origin/main")

    def _require_fresh_base(self, base_sha: str) -> None:
        _validate_sha(base_sha, "base_sha")
        tip = self.integration_tip()
        if base_sha != tip:
            raise StaleBaseError(
                f"base {base_sha[:12]} is stale; integration base is {tip[:12]}"
            )

    def create(
        self,
        issue: int | str,
        task_id: str,
        *,
        attempt: int,
        base_sha: str,
    ) -> tuple[ArtifactRef, Path]:
        self._require_fresh_base(base_sha)
        branch = self.branch_name(issue, task_id, attempt, base_sha)
        path = self.worktree_path(issue, task_id, attempt, base_sha)
        if path.exists():
            raise WorkspaceError(f"worktree already exists for task {task_id!r}")
        assert self.git is not None
        self.git(["cat-file", "-e", f"{base_sha}^{{commit}}"])
        self.worktrees_dir.mkdir(parents=True, exist_ok=True)
        self.git(["worktree", "add", "-b", branch, str(path), base_sha])
        return (
            ArtifactRef(
                task_id=task_id,
                attempt=attempt,
                base_sha=base_sha,
                commit_sha=base_sha,
                result_sha="",
                changed_files=(),
                branch=branch,
            ),
            path,
        )

    def _git_in(self, worktree: Path, args: Sequence[str]) -> str:
        assert self.git is not None
        return self.git(["-C", str(worktree.resolve()), *args])

    def _manifest(self, worktree: Path, base_sha: str) -> tuple[str, ...]:
        raw = self._git_in(
            worktree,
            ["diff", "--name-only", "-z", f"{base_sha}..HEAD"],
        )
        values = [_safe_relative_path(item) for item in raw.split("\0") if item]
        if len(values) != len(set(values)):
            raise ArtifactIntegrityError("changed-file manifest contains duplicates")
        return tuple(sorted(values))

    def _require_clean_committed_result(self, worktree: Path) -> str:
        status = self._git_in(worktree, ["status", "--porcelain=v1", "-z"])
        if status:
            raise ArtifactIntegrityError(
                "workspace contains uncommitted changes; commit locally before seal"
            )
        return _validate_sha(
            self._git_in(worktree, ["rev-parse", "HEAD"]).strip(),
            "commit_sha",
        )

    @staticmethod
    def _content_record(worktree: Path, relative: str) -> dict[str, Any]:
        path = worktree / relative
        if path.is_symlink():
            raise ArtifactIntegrityError(f"symlink output is not allowed: {relative}")
        if not path.exists():
            return {"path": relative, "kind": "deleted"}
        if not path.is_file():
            raise ArtifactIntegrityError(f"non-file output is not allowed: {relative}")
        data = path.read_bytes()
        return {
            "path": relative,
            "kind": "file",
            "size": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }

    def _result_digest(
        self,
        artifact: ArtifactRef,
        worktree: Path,
        changed_files: tuple[str, ...],
        commit_sha: str,
    ) -> str:
        payload = {
            "task_id": artifact.task_id,
            "attempt": artifact.attempt,
            "base_sha": artifact.base_sha,
            "commit_sha": commit_sha,
            "branch": artifact.branch,
            "files": [
                self._content_record(worktree, relative) for relative in changed_files
            ],
        }
        canonical = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()

    def seal(self, draft: ArtifactRef, worktree: Path) -> ArtifactRef:
        if draft.result_sha:
            raise ArtifactIntegrityError("artifact is already sealed")
        if not worktree.resolve().is_relative_to(self.worktrees_dir):
            raise WorkspaceError("worktree is outside the managed workspace root")
        commit_sha = self._require_clean_committed_result(worktree)
        if commit_sha == draft.base_sha:
            raise ArtifactIntegrityError("coding task produced no result commit")
        changed = self._manifest(worktree, draft.base_sha)
        if not changed:
            raise ArtifactIntegrityError("result commit contains no changed files")
        result_sha = self._result_digest(draft, worktree, changed, commit_sha)
        sealed = ArtifactRef(
            task_id=draft.task_id,
            attempt=draft.attempt,
            base_sha=draft.base_sha,
            commit_sha=commit_sha,
            result_sha=result_sha,
            changed_files=changed,
            branch=draft.branch,
        )
        self._persist_artifact(sealed)
        return sealed

    def verify(self, artifact: ArtifactRef, worktree: Path) -> None:
        _validate_sha(artifact.base_sha, "base_sha")
        _validate_sha(artifact.commit_sha, "commit_sha")
        if not re.fullmatch(r"[0-9a-f]{64}", artifact.result_sha):
            raise ArtifactIntegrityError("result_sha must be SHA-256 hex")
        current_commit = self._require_clean_committed_result(worktree)
        if current_commit != artifact.commit_sha:
            raise ArtifactIntegrityError("workspace HEAD changed after artifact seal")
        changed = self._manifest(worktree, artifact.base_sha)
        if changed != artifact.changed_files:
            raise ArtifactIntegrityError("changed-file manifest changed after artifact seal")
        digest = self._result_digest(artifact, worktree, changed, current_commit)
        if digest != artifact.result_sha:
            raise ArtifactIntegrityError("artifact content hash mismatch")

    def validate_for_integration(self, artifact: ArtifactRef, worktree: Path) -> None:
        self.verify(artifact, worktree)
        self._require_fresh_base(artifact.base_sha)

    @staticmethod
    def assert_compatible(left: ArtifactRef, right: ArtifactRef) -> None:
        if left.base_sha != right.base_sha:
            raise ConflictError("artifacts were produced from different base SHAs")
        overlap = sorted(set(left.changed_files) & set(right.changed_files))
        if overlap:
            raise ConflictError(f"artifacts modify the same files: {overlap}")

    def handoff(self, artifact: ArtifactRef) -> Mapping[str, Any]:
        if not artifact.result_sha:
            raise ArtifactIntegrityError("cannot hand off an unsealed artifact")
        return {
            "task_id": artifact.task_id,
            "attempt": artifact.attempt,
            "base_sha": artifact.base_sha,
            "commit_sha": artifact.commit_sha,
            "result_sha": artifact.result_sha,
            "changed_files": list(artifact.changed_files),
            "branch": artifact.branch,
        }

    def cleanup(self, artifact: ArtifactRef, worktree: Path) -> None:
        self.verify(artifact, worktree)
        assert self.git is not None
        self.git(["worktree", "remove", str(worktree.resolve())])

    def _persist_artifact(self, artifact: ArtifactRef) -> Path:
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        name = (
            f"{_safe_component(artifact.task_id)}-a{artifact.attempt}-"
            f"{artifact.result_sha[:16]}.json"
        )
        path = self.artifacts_dir / name
        if path.exists():
            existing = json.loads(path.read_text(encoding="utf-8"))
            if existing != json.loads(json.dumps(artifact.to_json())):
                raise ArtifactIntegrityError("artifact record collision")
            return path
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        try:
            data = (
                json.dumps(artifact.to_json(), sort_keys=True, separators=(",", ":"))
                + "\n"
            ).encode("utf-8")
            os.write(fd, data)
            os.fsync(fd)
        finally:
            os.close(fd)
        return path


def _real_git(root: Path) -> GitRunner:
    executable = "git"
    denied = {"push", "fetch", "pull", "remote", "ls-remote", "submodule"}

    def run(args: Sequence[str]) -> str:
        command_words = [value for value in args if not value.startswith("-")]
        if any(word in denied for word in command_words):
            raise WorkspaceError(
                "network/remote Git operations are forbidden in worker workspace"
            )
        env = dict(os.environ)
        for key in (
            "GH_TOKEN",
            "GITHUB_TOKEN",
            "GIT_ASKPASS",
            "SSH_ASKPASS",
            "GIT_SSH_COMMAND",
        ):
            env.pop(key, None)
        env["GIT_TERMINAL_PROMPT"] = "0"
        proc = subprocess.run(
            [executable, "-C", str(root), *args],
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )
        return proc.stdout

    def raw(args: Sequence[str]) -> bytes:
        # Used only by trusted artifact collection; return committed binary
        # blobs without text decoding or Git clean/smudge conversion.
        words = [value for value in args if not value.startswith("-")]
        if any(word in denied for word in words):
            raise WorkspaceError("network/remote Git operations are forbidden")
        env = dict(os.environ)
        for key in ("GH_TOKEN", "GITHUB_TOKEN", "GIT_ASKPASS", "SSH_ASKPASS", "GIT_SSH_COMMAND"):
            env.pop(key, None)
        env["GIT_TERMINAL_PROMPT"] = "0"
        return subprocess.run([executable, "-C", str(root), *args], check=True,
                              capture_output=True, env=env).stdout
    run.raw = raw
    return run

