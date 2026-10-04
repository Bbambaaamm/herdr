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

def test_stale_expected_content_preserves_concurrent_write_at_publication(tmp_path,monkeypatch):
    import herdr.file_authority as module
    root=tmp_path/"workspace";root.mkdir();target=root/"file.txt";target.write_text("old")
    authority=module.RootFDWorkspace((str(root),));original=module.os.fsync;changed=[False]
    def changed_during_preparation(fd):
        original(fd)
        if not changed[0]:
            changed[0]=True;target.write_text("concurrent edit")
    try:
        monkeypatch.setattr(module.os,"fsync",changed_during_preparation)
        with pytest.raises(module.FileAuthorityError,match="stale"):
            authority.write_text(str(target),"my patch",expected_content="old")
        assert target.read_text()=="concurrent edit"
        assert sorted(item.name for item in root.iterdir())==["file.txt"]
    finally: authority.close()

def test_concurrent_root_fd_writers_cannot_both_replace_one_preimage(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    import herdr.file_authority as module
    root=tmp_path/"workspace";root.mkdir();target=root/"file.txt";target.write_text("old")
    authorities=[module.RootFDWorkspace((str(root),)) for _ in range(2)]
    def write(number):
        try:
            authorities[number].write_text(str(target),f"writer-{number}",expected_content="old")
            return "written"
        except module.FileAuthorityError: return "stale"
    try:
        with ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(write,range(2)))
        assert sorted(results)==["stale","written"]
        assert target.read_text() in {"writer-0","writer-1"}
    finally:
        for authority in authorities: authority.close()


def test_conditional_write_serializes_independent_processes(tmp_path):
    import subprocess,sys
    from pathlib import Path
    path=tmp_path/"shared.txt"
    path.write_text("original")
    code="""import sys
from herdr.file_authority import RootFDWorkspace,FileAuthorityError
root,path,value=sys.argv[1:]
workspace=RootFDWorkspace((root,))
print('ready',flush=True)
sys.stdin.readline()
try:
    workspace.write_text(path,value,expected_content='original')
    print('published',flush=True)
except FileAuthorityError as exc:
    if 'stale file content' not in str(exc): raise
    print('stale',flush=True)
finally: workspace.close()
"""
    children=[subprocess.Popen([sys.executable,"-c",code,str(tmp_path),str(path),value],
        cwd=Path(__file__).resolve().parents[2],stdin=subprocess.PIPE,stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,text=True) for value in ('first','second')]
    try:
        for child in children: assert child.stdout.readline().strip()=='ready'
        for child in children: child.stdin.write('go\n');child.stdin.flush()
        outcomes=[]
        for child in children:
            out,err=child.communicate(timeout=5)
            assert child.returncode==0,err
            outcomes.append(out.strip())
        assert sorted(outcomes)==['published','stale']
        assert path.read_text() in ('first','second')
        assert not list(tmp_path.glob('.herdr-policy-*'))
    finally:
        for child in children:
            if child.poll() is None: child.kill();child.wait(timeout=5)
