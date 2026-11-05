"""Only a declared, copied runtime closure enters an oracle/hook namespace."""
from pathlib import Path
from .policy_launch import FrozenTree
from .work_cycle import require

class FrozenCheckRuntime:
    def __init__(self, environment, storage, *, writable_roots):
        self.environment=environment
        environment.verify_inputs()
        self.tree=FrozenTree.create(Path("/"),target=Path("/runtime"),
            files={path.lstrip("/"):sha for path,sha in environment.system_files},
            storage=Path(storage),writable_roots=tuple(Path(path) for path in writable_roots),
            executable_files=[path.lstrip("/") for path in (*environment.executables,*environment.runtime_executables)],
            max_bytes=134217728,max_file_bytes=67108864)
        self.fd=self.tree.fd
        try:
            executables=set(environment.executables)|set(environment.runtime_executables)
            for name,sha in self.tree.files:
                (self.tree.path/name).chmod(0o555 if "/"+name in executables else 0o444)
            for directory in self.tree.path.rglob("*"):
                if directory.is_dir(): directory.chmod(0o555)
            self.tree.path.chmod(0o555)
            environment.verify_inputs()
            self.tree.verify()
        except Exception:
            self.close()
            raise

    def arguments(self):
        names={path for path,sha in self.environment.system_files}
        parents={str(parent) for path in names for parent in Path(path).parents if str(parent)!="/"}
        aliases=self.environment.runtime_aliases
        parents.update(str(parent) for path,target in aliases for parent in Path(path).parents if str(parent)!="/")
        require(not names & parents,"runtime files cannot replace another input directory")
        require(not {alias for alias,target in aliases} & (names|parents),"runtime alias overlaps declared input")
        args=[]
        for directory in sorted(parents,key=lambda path:(len(Path(path).parts),path)):
            args.extend(("--dir",directory))
        for path in sorted(names):
            args.extend(("--ro-bind",f"/proc/self/fd/{self.fd}/{path.lstrip('/')}",path))
        for alias,target in aliases:
            args.extend(("--symlink",target,alias))
        return args

    def verify(self):
        self.tree.verify()
        self.environment.verify_inputs()

    def close(self):
        self.tree.cleanup_after_pane_closed()
