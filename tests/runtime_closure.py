"""Explicit test-only manifest of installed Python/Git/shell runtime inputs."""
from functools import lru_cache
from pathlib import Path
import hashlib
import re
import subprocess

@lru_cache(maxsize=1)
def approved_runtime():
    python=Path("/usr/bin/python3").resolve(strict=True)
    # Paths observed from the trusted installed interpreter, never repository code.
    roots=subprocess.check_output([str(python),"-I","-S","-c",
        "import sys,json; print(json.dumps([p for p in sys.path if p and 'python' in p]))"],text=True)
    import json
    files={python,Path("/usr/bin/bwrap").resolve(strict=True),Path("/usr/bin/git").resolve(strict=True),
           Path("/bin/sh").resolve(strict=True),Path("/usr/bin/env").resolve(strict=True)}
    for name in json.loads(roots):
        base=Path(name)
        if not base.is_dir():continue
        for path in base.rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts:
                files.add(path.resolve(strict=True))
    aliases={}
    for logical in ("/usr/bin/python3","/bin/sh","/usr/bin/sh"):
        target=str(Path(logical).resolve(strict=True))
        if target!=logical:aliases[logical]=target
    for path in list(files):
        if path.suffix==".so" or path in {python,Path("/usr/bin/git"),Path("/usr/bin/dash"),Path("/usr/bin/env")}:
            output=subprocess.run(["/usr/bin/ldd",str(path)],capture_output=True,text=True,check=False).stdout
            for logical in re.findall(r"(/[^\s()]+)",output):
                source=Path(logical)
                if source.is_file():
                    actual=source.resolve(strict=True);files.add(actual)
                    if str(actual)!=logical:aliases[logical]=str(actual)
    manifest=tuple((str(path),hashlib.sha256(path.read_bytes()).hexdigest()) for path in sorted(files))
    helpers=tuple(sorted({str(Path(name).resolve(strict=True)) for name in ("/usr/bin/git","/bin/sh","/usr/bin/env")}
                         | {str(path) for path in files if path.name.startswith("ld-linux")}))
    return manifest,tuple(sorted(aliases.items())),helpers
