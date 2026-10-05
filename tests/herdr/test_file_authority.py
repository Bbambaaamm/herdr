import os
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

def test_search_streams_entry_bound_before_materializing_names(tmp_path,monkeypatch):
    from types import SimpleNamespace
    from contextlib import contextmanager
    import herdr.file_authority as module
    root=tmp_path/"workspace";root.mkdir()
    authority=module.RootFDWorkspace((str(root),))
    seen=[]
    @contextmanager
    def scan(fd):
        def entries():
            for number in range(100000):
                seen.append(number)
                yield SimpleNamespace(name=f"entry-{number}")
        yield entries()
    try:
        monkeypatch.setattr(module.os,"scandir",scan)
        with pytest.raises(module.FileAuthorityError,match="entry count"):
            authority.list_regular_files(str(root))
        assert len(seen)==4097
    finally: authority.close()

def test_search_deadline_applies_during_directory_enumeration(tmp_path,monkeypatch):
    from types import SimpleNamespace
    from contextlib import contextmanager
    import herdr.file_authority as module
    root=tmp_path/"workspace";root.mkdir()
    authority=module.RootFDWorkspace((str(root),));seen=[]
    @contextmanager
    def scan(fd):
        def entries():
            for number in range(100000):
                seen.append(number)
                yield SimpleNamespace(name=f"entry-{number}")
        yield entries()
    try:
        monkeypatch.setattr(module.os,"scandir",scan)
        monkeypatch.setattr(module.time,"monotonic",lambda:10)
        with pytest.raises(module.FileAuthorityError,match="elapsed"):
            authority.list_regular_files(str(root),deadline=9)
        assert seen==[0]
    finally: authority.close()

@pytest.mark.parametrize("preimage",["old","stale",""])
def test_conditional_shared_workspace_replace_denies_without_any_publication(tmp_path,monkeypatch,preimage):
    import herdr.file_authority as module
    root=tmp_path/"workspace";root.mkdir();target=root/"file.txt";target.write_text("concurrent data")
    authority=module.RootFDWorkspace((str(root),))
    published=[]
    monkeypatch.setattr(module.os,"replace",lambda *args,**kwargs:published.append(args))
    try:
        with pytest.raises(module.FileAuthorityError,match="conditional replacement unavailable"):
            authority.write_text(str(target),"proposed patch",expected_content=preimage)
        assert target.read_text()=="concurrent data"
        assert not published and sorted(item.name for item in root.iterdir())==["file.txt"]
    finally: authority.close()

@pytest.mark.parametrize("mode",[0o644,0o755])
def test_explicit_write_preserves_existing_mode_under_restrictive_umask(tmp_path,mode):
    import os,stat
    from herdr.file_authority import RootFDWorkspace
    target=tmp_path/"entry";target.write_text("old");target.chmod(mode)
    authority=RootFDWorkspace((str(tmp_path),));previous=os.umask(0o077)
    try:
        authority.write_text(str(target),"new")
        assert target.read_text()=="new"
        assert stat.S_IMODE(target.stat().st_mode)==mode
    finally:
        os.umask(previous);authority.close()


def test_exact_file_root_permits_only_pinned_inode_without_parent_write(tmp_path):
    target=tmp_path/"owned.txt";target.write_text("before")
    foreign=tmp_path/"foreign.txt";foreign.write_text("foreign")
    before=target.stat().st_ino
    authority=RootFDWorkspace((str(target),))
    try:
        assert authority.read_text(str(target))=="before"
        authority.write_text(str(target),"after")
        assert target.read_text()=="after" and target.stat().st_ino==before
        assert authority.list_regular_files(str(target))==[str(target)]
        with pytest.raises(FileAuthorityError):authority.write_text(str(foreign),"escape")
        with pytest.raises(FileAuthorityError):authority.write_text(str(target/"child"),"escape")
        assert foreign.read_text()=="foreign"
    finally:authority.close()


def test_exact_file_root_rejects_replacement_and_new_hardlink(tmp_path):
    target=tmp_path/"owned.txt";target.write_text("before")
    authority=RootFDWorkspace((str(target),))
    try:
        target.rename(tmp_path/"original")
        target.write_text("new")
        with pytest.raises(FileAuthorityError,match="binding"):authority.write_text(str(target),"escape")
        assert target.read_text()=="new"
    finally:authority.close()
    authority=RootFDWorkspace((str(target),))
    try:
        os.link(target,tmp_path/"alias")
        with pytest.raises(FileAuthorityError,match="binding"):authority.write_text(str(target),"escape")
        assert target.read_text()=="new" and (tmp_path/"alias").read_text()=="new"
    finally:authority.close()
