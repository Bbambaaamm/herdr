from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

import pytest

from herdr.workspace import (
    ArtifactIntegrityError,
    ArtifactRef,
    ConflictError,
    StaleBaseError,
    UnsafePathError,
    WorkspaceManager,
)

BASE = "a" * 40
COMMIT = "b" * 40


class FakeGit:
    def __init__(self, tip: str = BASE) -> None:
        self.tip = tip
        self.head = COMMIT
        self.changed = ("src/a.py",)
        self.dirty = False
        self.calls: list[tuple[str, ...]] = []

    def __call__(self, args: Sequence[str]) -> str:
        call = tuple(args)
        self.calls.append(call)
        if call == ("rev-parse", "origin/main"):
            return self.tip + "\n"
        if call[:2] == ("cat-file", "-e"):
            return ""
        if "status" in call and "--porcelain=v1" in call:
            return " M src/a.py\0" if self.dirty else ""
        if "rev-parse" in call and call[-1] == "HEAD":
            return self.head + "\n"
        if "diff" in call and "--name-only" in call:
            return "\0".join(self.changed) + ("\0" if self.changed else "")
        if call[:2] == ("worktree", "add"):
            return ""
        if call[:2] == ("worktree", "remove"):
            return ""
        return ""


def manager(tmp_path: Path, git: FakeGit | None = None) -> tuple[WorkspaceManager, FakeGit]:
    fake = git or FakeGit()
    mgr = WorkspaceManager(
        root=tmp_path,
        git=fake,
        worktrees_dir=tmp_path / "worktrees",
        artifacts_dir=tmp_path / "artifacts",
    )
    return mgr, fake


def create_worktree(mgr: WorkspaceManager, tmp_path: Path, *, content: bytes = b"one"):
    draft, path = mgr.create("4", "coding/task", attempt=1, base_sha=BASE)
    path.mkdir(parents=True)
    (path / "src").mkdir()
    (path / "src/a.py").write_bytes(content)
    return draft, path


def test_branch_and_path_are_deterministic_and_sanitized(tmp_path: Path) -> None:
    mgr, _ = manager(tmp_path)
    a = mgr.branch_name("#4", "../Task Weird", 2, BASE)
    b = mgr.branch_name("#4", "../Task Weird", 2, BASE)
    assert a == b
    assert ".." not in a
    assert a.startswith("herdr/")
    assert mgr.worktree_path("#4", "../Task Weird", 2, BASE) == mgr.worktree_path(
        "#4", "../Task Weird", 2, BASE
    )


def test_stale_base_fails_before_worktree_creation(tmp_path: Path) -> None:
    mgr, fake = manager(tmp_path)
    with pytest.raises(StaleBaseError):
        mgr.create("4", "task", attempt=0, base_sha="c" * 40)
    assert not any(call[:2] == ("worktree", "add") for call in fake.calls)


def test_create_uses_exact_base_without_force(tmp_path: Path) -> None:
    mgr, fake = manager(tmp_path)
    _, path = mgr.create("4", "task", attempt=0, base_sha=BASE)
    call = next(call for call in fake.calls if call[:2] == ("worktree", "add"))
    assert "--force" not in call
    assert call[-1] == BASE
    assert str(path) in call


def test_seal_binds_actual_file_content_and_metadata(tmp_path: Path) -> None:
    mgr, _ = manager(tmp_path)
    draft, path = create_worktree(mgr, tmp_path, content=b"alpha")
    sealed = mgr.seal(draft, path)
    assert sealed.task_id == "coding/task"
    assert sealed.attempt == 1
    assert sealed.base_sha == BASE
    assert sealed.commit_sha == COMMIT
    assert sealed.changed_files == ("src/a.py",)
    assert len(sealed.result_sha) == 64
    record = next((tmp_path / "artifacts").glob("*.json"))
    assert record.stat().st_mode & 0o777 == 0o600
    assert json.loads(record.read_text())["result_sha"] == sealed.result_sha


def test_same_file_list_different_content_changes_result_sha(tmp_path: Path) -> None:
    root1 = tmp_path / "one"
    root1.mkdir()
    mgr1, _ = manager(root1)
    d1, p1 = create_worktree(mgr1, root1, content=b"alpha")
    a1 = mgr1.seal(d1, p1)

    root2 = tmp_path / "two"
    root2.mkdir()
    mgr2, _ = manager(root2)
    d2, p2 = create_worktree(mgr2, root2, content=b"beta")
    a2 = mgr2.seal(d2, p2)
    assert a1.changed_files == a2.changed_files
    assert a1.result_sha != a2.result_sha


def test_uncommitted_workspace_fails_closed(tmp_path: Path) -> None:
    fake = FakeGit()
    fake.dirty = True
    mgr, _ = manager(tmp_path, fake)
    draft, path = create_worktree(mgr, tmp_path)
    with pytest.raises(ArtifactIntegrityError, match="uncommitted"):
        mgr.seal(draft, path)


def test_post_seal_tamper_invalidates_artifact(tmp_path: Path) -> None:
    mgr, _ = manager(tmp_path)
    draft, path = create_worktree(mgr, tmp_path, content=b"alpha")
    artifact = mgr.seal(draft, path)
    (path / "src/a.py").write_bytes(b"tampered")
    with pytest.raises(ArtifactIntegrityError, match="hash mismatch"):
        mgr.verify(artifact, path)


def test_stale_before_integration_fails_closed(tmp_path: Path) -> None:
    fake = FakeGit()
    mgr, _ = manager(tmp_path, fake)
    draft, path = create_worktree(mgr, tmp_path)
    artifact = mgr.seal(draft, path)
    fake.tip = "c" * 40
    with pytest.raises(StaleBaseError):
        mgr.validate_for_integration(artifact, path)


def test_same_file_is_explicit_conflict() -> None:
    a = ArtifactRef("a", 1, BASE, "b" * 40, "1" * 64, ("x.py",), "a")
    b = ArtifactRef("b", 1, BASE, "c" * 40, "2" * 64, ("x.py",), "b")
    with pytest.raises(ConflictError, match="same files"):
        WorkspaceManager.assert_compatible(a, b)


def test_different_files_same_base_are_compatible() -> None:
    a = ArtifactRef("a", 1, BASE, "b" * 40, "1" * 64, ("x.py",), "a")
    b = ArtifactRef("b", 1, BASE, "c" * 40, "2" * 64, ("y.py",), "b")
    WorkspaceManager.assert_compatible(a, b)


def test_different_bases_are_conflict() -> None:
    a = ArtifactRef("a", 1, BASE, "b" * 40, "1" * 64, ("x.py",), "a")
    b = ArtifactRef("b", 1, "c" * 40, "d" * 40, "2" * 64, ("y.py",), "b")
    with pytest.raises(ConflictError, match="different base"):
        WorkspaceManager.assert_compatible(a, b)


def test_unsafe_or_symlink_output_fails_closed(tmp_path: Path) -> None:
    fake = FakeGit()
    fake.changed = ("../escape",)
    mgr, _ = manager(tmp_path, fake)
    draft, path = create_worktree(mgr, tmp_path)
    with pytest.raises(UnsafePathError):
        mgr.seal(draft, path)

    fake.changed = ("src/link.py",)
    (path / "src/link.py").symlink_to(path / "src/a.py")
    with pytest.raises(ArtifactIntegrityError, match="symlink"):
        mgr.seal(draft, path)


def test_cleanup_preserves_branch_and_artifact_record(tmp_path: Path) -> None:
    mgr, fake = manager(tmp_path)
    draft, path = create_worktree(mgr, tmp_path)
    artifact = mgr.seal(draft, path)
    mgr.cleanup(artifact, path)
    remove = next(call for call in fake.calls if call[:2] == ("worktree", "remove"))
    assert "--force" not in remove
    assert not any("branch" in call and "-D" in call for call in fake.calls)
    assert next((tmp_path / "artifacts").glob("*.json")).exists()
    assert mgr.handoff(artifact)["commit_sha"] == COMMIT

