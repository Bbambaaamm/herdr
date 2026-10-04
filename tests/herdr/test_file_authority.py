from pathlib import Path

import pytest

from herdr.file_authority import FileAuthorityError, RootFDWorkspace


def test_root_fd_remains_on_original_inode_after_path_replacement(tmp_path):
    root = tmp_path / "workspace"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    authority = RootFDWorkspace((str(root),))
    pinned = tmp_path / "workspace-pinned"
    try:
        root.rename(pinned)
        root.symlink_to(outside, target_is_directory=True)
        target = root / "new.txt"
        count, _digest = authority.write_text(str(target), "safe")
        assert count == 4
        assert (pinned / "new.txt").read_text() == "safe"
        assert not (outside / "new.txt").exists()
    finally:
        authority.close()


def test_nofollow_walk_rejects_symlink_component_and_target(tmp_path):
    root = tmp_path / "workspace"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (outside / "secret.txt").write_text("secret")
    authority = RootFDWorkspace((str(root),))
    try:
        (root / "linkdir").symlink_to(outside, target_is_directory=True)
        with pytest.raises((FileAuthorityError, OSError)):
            authority.read_text(str(root / "linkdir" / "secret.txt"))

        (root / "linkfile").symlink_to(outside / "secret.txt")
        with pytest.raises((FileAuthorityError, OSError)):
            authority.write_text(str(root / "linkfile"), "overwrite")
        assert (outside / "secret.txt").read_text() == "secret"
    finally:
        authority.close()


def test_atomic_write_and_move_stay_beneath_pinned_parent_fds(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()
    authority = RootFDWorkspace((str(root),))
    try:
        authority.write_text(str(root / "a" / "one.txt"), "one")
        assert authority.read_text(str(root / "a" / "one.txt")) == "one"
        authority.move_file(str(root / "a" / "one.txt"), str(root / "b" / "two.txt"))
        assert authority.read_text(str(root / "b" / "two.txt")) == "one"
        with pytest.raises(FileNotFoundError):
            authority.read_text(str(root / "a" / "one.txt"))
        authority.delete_file(str(root / "b" / "two.txt"))
        with pytest.raises(FileNotFoundError):
            authority.read_text(str(root / "b" / "two.txt"))
    finally:
        authority.close()

def test_create_is_atomic_no_clobber(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()
    authority = RootFDWorkspace((str(root),))
    try:
        target = root / "new.txt"
        authority.create_text(str(target), "first")
        assert target.read_text() == "first"
        with pytest.raises(FileAuthorityError, match="already exists"):
            authority.create_text(str(target), "second")
        assert target.read_text() == "first"
    finally:
        authority.close()


def test_move_never_replaces_existing_destination(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()
    (root / "source.txt").write_text("source")
    (root / "dest.txt").write_text("dest")
    authority = RootFDWorkspace((str(root),))
    try:
        with pytest.raises(FileAuthorityError, match="already exists"):
            authority.move_file(str(root / "source.txt"), str(root / "dest.txt"))
        assert (root / "source.txt").read_text() == "source"
        assert (root / "dest.txt").read_text() == "dest"
    finally:
        authority.close()


def test_search_directory_walk_never_follows_replaced_root_or_symlink_entry(tmp_path):
    root=tmp_path/"work";outside=tmp_path/"outside";root.mkdir();outside.mkdir()
    (root/"owned.txt").write_text("owned")
    (outside/"outside.txt").write_text("outside")
    (root/"link").symlink_to(outside,target_is_directory=True)
    authority=RootFDWorkspace((str(root),))
    try:
        pinned=tmp_path/"pinned";root.rename(pinned);root.symlink_to(outside,target_is_directory=True)
        assert authority.list_regular_files(str(root))==[str(root/"owned.txt")]
        assert authority.read_text(str(root/"owned.txt"))=="owned"
        with pytest.raises((OSError,FileAuthorityError)):
            authority.list_regular_files(str(root/"link"))
    finally: authority.close()
