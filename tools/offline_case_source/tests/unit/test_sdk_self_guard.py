"""Composed inert checks of the actual bootstrap/root/stage2 source delta.

No SDK, model, socket, process, namespace, profile or syscall is executed.
Synthetic OS reads are finite in-memory maps. A bounded bundle fixture supplies
an already verified typed grant; separate tests exercise the real Ed25519
backend when available, while unavailable crypto denies.
"""
from contextlib import ExitStack, contextmanager
from dataclasses import replace
from datetime import UTC, datetime, timedelta
import ast
import base64
import copy
import errno
import hashlib
import importlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path, PurePosixPath
import posixpath
import re
import socket
import stat
import sys
import threading
import time
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[2]
PUBLIC = HERE.parents[1] / ""
_prior_herdr_modules = {name: module for name, module in sys.modules.items()
                        if name == "herdr" or name.startswith("herdr.")}
_prior_fcntl = sys.modules.get("fcntl")
for _name in _prior_herdr_modules:
    sys.modules.pop(_name, None)
package = ModuleType("herdr")
package.__path__ = [str(HERE / "overlays/herdr"), str(PUBLIC / "herdr")]
sys.modules["herdr"] = package
# Windows has no fcntl. Constructors/OS actions are never called; any accidental
# effect through this adapter is an assertion failure, not a successful fake.
if "fcntl" not in sys.modules:
    fcntl = ModuleType("fcntl")
    def forbidden(*args, **kwargs): raise AssertionError("forbidden native effect")
    fcntl.fcntl = fcntl.flock = forbidden
    sys.modules["fcntl"] = fcntl

from herdr import security, capability
from herdr import bootstrap_authority as authority
from herdr import host_bootstrap as host
from herdr import bootstrap_self_observation as guard
from herdr import credential_isolation as credentials
from herdr import credential_ingress_filter as ingress
from herdr import prep_entry, host_configuration, observer_client, host_reference_binding

_guard_modules = {name: module for name, module in sys.modules.items()
                  if name == "herdr" or name.startswith("herdr.")}
for _name in _guard_modules:
    sys.modules.pop(_name, None)
sys.modules.update(_prior_herdr_modules)
if _prior_fcntl is None:
    sys.modules.pop("fcntl", None)

try:
    CRYPTO = security._ed25519()
except security.SecurityError:
    CRYPTO = None


def sha(value): return hashlib.sha256(value).hexdigest()


def selected_module(name, source, names, values):
    tree = ast.parse(source)
    body = [ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0)]
    body += [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in names]
    assert {n.name for n in body if isinstance(n, (ast.FunctionDef, ast.ClassDef))} == set(names)
    module = ModuleType(name); module.__dict__.update(values); sys.modules[name] = module
    exec(compile(ast.fix_missing_locations(ast.Module(body=body, type_ignores=[])), name, "exec"), module.__dict__)
    return module


class Posix(PurePosixPath):
    def resolve(self, strict=False): return self
    def expanduser(self): return self


class MemoryFS:
    def __init__(self):
        self.files = {}; self.directories = {"/"}; self.links = {}; self.calls = []
        self.fd = {}; self.next_fd = 10
        self.worker_policy = (HERE / "overlays/worker-profile.apparmor").read_text()
        self.measurement_fd = 3; self.measurement_live = False; self.measurement_reused = False
        self.fd_targets = {0: "/dev/pts/7", 1: "/dev/pts/7", 2: "/dev/pts/7"}
        self.missing_link = None
        owner = self
        class MemoryPath(Posix):
            def open(self, mode="r", *args, **kwargs):
                raw = owner.read(self)
                return io.BytesIO(raw) if "b" in mode else io.StringIO(raw.decode())
            def read_bytes(self): return owner.read(self)
            def read_text(self, *args, **kwargs): return owner.read(self).decode()
            def lstat(self): return owner.info(self)
            def stat(self, *args, **kwargs): return owner.info(self)
            def is_dir(self): return str(self) in owner.directories
            def is_file(self): return str(self) in owner.files
            def is_symlink(self): return str(self) in owner.links
            def exists(self): return self.is_dir() or self.is_file() or self.is_symlink()
            def iterdir(self):
                if not self.is_dir(): raise FileNotFoundError(str(self))
                return iter(MemoryPath(p) for p in owner.children(str(self)))
        self.Path = MemoryPath
    def add(self, name, body):
        name = str(name); self.files[name] = body
        self.directories.update(str(p) for p in Posix(name).parents)
    def children(self, base):
        return sorted(p for p in self.files.keys() | self.directories | self.links.keys()
                      if p != base and str(Posix(p).parent) == base)
    def read(self, name, maximum=None):
        self.calls.append(("read", str(name)))
        if str(name) not in self.files: raise FileNotFoundError(str(name))
        raw = self.files[str(name)]
        if maximum is not None and len(raw) > maximum: raise ValueError("inert bounded read exceeded")
        return raw
    def info(self, name):
        name = str(name); self.calls.append(("stat", name))
        if name == f"/proc/2/fd/{self.measurement_fd}" and self.measurement_live:
            return self.info("/proc/2/fd")
        if any(name == f"/proc/2/fd/{number}" and target == "/proc/2/fd" for number, target in self.fd_targets.items()):
            return self.info("/proc/2/fd")
        if name not in self.files and name not in self.directories and name not in self.links:
            raise FileNotFoundError(name)
        kind = stat.S_IFDIR if name in self.directories else stat.S_IFLNK if name in self.links else stat.S_IFREG
        return SimpleNamespace(st_mode=kind | (0o755 if kind == stat.S_IFDIR else 0o444), st_uid=0, st_gid=0,
            st_dev=1, st_ino=int(sha(name.encode())[:10], 16), st_size=len(self.files.get(name, b"")), st_nlink=1)
    def directory_allowed(self, directory):
        directory = str(directory).rstrip("/") + "/"
        def expanded(pattern):
            match = re.search(r"\{([^{}]+)\}", pattern)
            if not match: return [pattern]
            return [value for item in match[1].split(",") for value in expanded(pattern[:match.start()] + item + pattern[match.end():])]
        for line in self.worker_policy.splitlines():
            match = re.fullmatch(r"\s*(/\S+/) r,", line)
            if not match: continue
            for rule in expanded(match[1]):
                expression = re.escape(rule).replace(r"\*\*", ".+").replace(r"\*", "[^/]*").replace(r"\[0\-9\]", "[0-9]")
                if re.fullmatch(expression, directory): return True
        return False
    def scandir(self, base):
        base = str(base)
        owner = self
        measurement = base == "/proc/2/fd"
        if base.startswith("/proc/2/root/") and not self.directory_allowed(base):
            raise PermissionError("finite directory read denied")
        if base not in self.directories: raise FileNotFoundError(base)
        class Entry:
            def __init__(self, value): self.path = value; self.name = Posix(value).name
            def is_dir(self, follow_symlinks=True): return self.path in owner.directories
            def is_symlink(self): return self.path in owner.links
        class Entries:
            def __enter__(self):
                owner.measurement_live = measurement
                names = [base + "/" + str(n) for n in sorted(set(owner.fd_targets) | {owner.measurement_fd})] if measurement else owner.children(base)
                self.entries = iter(Entry(name) for name in names); return self
            def __iter__(self): return self
            def __next__(self):
                try: return next(self.entries)
                except StopIteration:
                    if measurement: owner.measurement_live = False
                    raise
            def __exit__(self, *args):
                if measurement: owner.measurement_live = False
        return Entries()
    def walk(self, base, followlinks=False):
        # Run the REAL interpreter's recursive os.walk, with finite virtual
        # scandir and POSIX paths only. No host path is enumerated.
        with patch.object(os, "scandir", side_effect=self.scandir), patch.object(os, "path", posixpath), \
             patch.object(os, "lstat", side_effect=self.info):
            yield from os.walk(str(base), followlinks=followlinks)
    def link(self, name):
        name = str(name)
        if name == self.missing_link: raise FileNotFoundError(errno.ENOENT, "inert raced FD")
        match = re.fullmatch(r"/proc/2/fd/([0-9]+)", name)
        if match:
            number = int(match[1])
            if number == self.measurement_fd and self.measurement_live: return "/proc/2/fd"
            if number in self.fd_targets: return self.fd_targets[number]
            raise FileNotFoundError(errno.ENOENT, "inert missing FD")
        return self.links[name]
    def fstat(self, fd):
        if fd == self.measurement_fd and (self.measurement_live or self.measurement_reused):
            return self.info("/proc/2/fd")
        if fd in self.fd: return self.info(self.fd[fd][0])
        raise OSError(errno.EBADF, "inert closed FD")
    def open(self, name, flags, *args, **kwargs):
        name = str(name); self.info(name); self.next_fd += 1; self.fd[self.next_fd] = [name, 0]; return self.next_fd
    def read_fd(self, fd, count):
        name, offset = self.fd[fd]; result = self.files[name][offset:offset + count]
        self.fd[fd][1] += len(result); return result
    def os(self):
        return SimpleNamespace(path=posixpath, walk=self.walk, scandir=self.scandir, stat=self.info, lstat=self.info, readlink=self.link,
            getpid=lambda: 2, getresuid=lambda: (1001,) * 3, getresgid=lambda: (1001,) * 3,
            open=self.open, read=self.read_fd, close=lambda fd: self.fd.pop(fd),
            fstat=self.fstat, O_RDONLY=0, O_NOFOLLOW=1, O_CLOEXEC=2, O_NONBLOCK=4)


def profile_api():
    source = (PUBLIC / "herdr/private_profile_namespace.py").read_text()
    from typing import Mapping
    values = {"Mapping": Mapping, "hashlib": hashlib, "json": json, "re": re, "PurePosixPath": PurePosixPath}
    tree = ast.parse(source)
    constants = [n for n in tree.body if isinstance(n, ast.Assign) and any(
        isinstance(t, ast.Name) and t.id in {"_PROFILE", "_HEX", "_MAX_FILES"} for t in n.targets)]
    exec(compile(ast.fix_missing_locations(ast.Module(body=constants, type_ignores=[])), "profile_constants", "exec"), values)
    return selected_module("herdr.private_profile_namespace", source,
        {"PrivateProfileError", "profile_identity", "verified_profile_identity", "_relative", "_need"}, values)


def actual_stage2():
    source = (HERE / "overlays/agent-stack/bin/agent-hermes-policy-run").read_text()
    return selected_module("actual_stage2_self_guard", source,
        {"_AuthenticatedKernelReply", "_verified_bootstrap_reference", "_recv_bootstrap_status", "_canonical_bootstrap", "_startup_descriptor",
         "_requested_self_observation", "_require_host_bootstrap_authority", "_require_held_stage2_source",
         "_require_stage1_continuity", "_verify_runtime", "_sha256_fd"},
        {"json": json, "os": SimpleNamespace(), "Path": Path, "hashlib": hashlib,
         "socket": socket, "MAX_AUTH_RESPONSE": 32768, "MAX_AUTH_REQUEST": 8192,
         "MAX_BUNDLE": 1048576, "BUNDLE_PATH": Posix("/run/herdr-policy/grant.bundle.json"),
         "BOOTSTRAP_PROOF": Posix("/run/herdr-bootstrap/immutable-trees.json"),
         "_BOOTSTRAP_REPLY_TOKEN": object(), "importlib": importlib, "re": re,
         "BOOTSTRAP_AUTH_FD_ENV": "HERDR_BOOTSTRAP_AUTH_FD", "STAGE1_PROOF_ENV": "HERDR_POLICY_STAGE1_PROOF_SHA256",
         "_INTERPRETER_FD_ENV": "HERDR_VERIFIED_PYTHON_FD", "STAGE2_FD_ENV": "HERDR_VERIFIED_STAGE2_FD",
         "_FIXED_STARTUP_DESCRIPTORS": {"HERDR_VERIFIED_PYTHON_FD": 197, "HERDR_VERIFIED_STAGE2_FD": 198, "HERDR_BOOTSTRAP_AUTH_FD": 199},
         "_RETIRED_STARTUP_DESCRIPTORS": set(),
         "secrets": SimpleNamespace(token_hex=lambda n: "8" * (n * 2)),
         "_require_module_origin": lambda *args: None, "POLICY_CODE_ROOT": Posix("/run/herdr/policy-code")})


class ExecRecorded(Exception): pass


class HandleTable:
    """Finite descriptor table; only these synthetic handles can be operated."""
    def __init__(self, sources=(4, 5, 6), duplicate_choices=()):
        self.values = {0: (0, b"tty"), 1: (1, b"tty"), 2: (2, b"tty")}
        self.sources = sources; self.closed = []; self.offsets = {}; self.exec = None
        for fd, (inode, body) in zip(sources, ((71, b"inert audited python"), (72, b"inert held stage2"), (73, b"inert inherited socket"))):
            self.values[fd] = (inode, body)
        self.choices = iter(duplicate_choices); self.tamper = False
        self.environ = {"HOME": "/home/agentops", "HERDR_POLICY_TASK_ID": "task", "HERDR_POLICY_FENCING_TOKEN": "7"}
    def fstat(self, fd):
        if fd not in self.values: raise OSError(errno.EBADF, "inert closed descriptor")
        inode, body = self.values[fd]
        return SimpleNamespace(st_dev=1, st_ino=inode, st_mode=stat.S_IFSOCK | 0o600 if inode == 73 else stat.S_IFREG | 0o444,
            st_rdev=0, st_size=len(body))
    def dup(self, source):
        try: number = next(self.choices)
        except StopIteration: number = next(n for n in range(3, 1024) if n not in self.values)
        if number in self.values: raise AssertionError("inert duplicate collision")
        self.values[number] = self.values[source]; return number
    def dup2(self, source, target, *, inheritable):
        assert inheritable is True
        self.values[target] = self.values[source]
        if self.tamper and target == 198: self.values[target] = (999, b"foreign")
    def close(self, fd):
        if fd not in self.values: raise OSError(errno.EBADF, "inert close reused descriptor")
        self.closed.append(fd); del self.values[fd]
    def set_inheritable(self, fd, value): self.fstat(fd)
    def execve(self, executable, argv, environment):
        self.exec = (executable, list(argv), dict(environment)); raise ExecRecorded()
    def stat(self, name):
        if str(name) == "/proc/self/exe":
            return SimpleNamespace(st_dev=1, st_ino=71)
        match = re.fullmatch(r"/proc/self/fd/([0-9]+)", str(name))
        if not match: raise AssertionError("unlisted inert handle stat")
        return self.fstat(int(match[1]))
    def lseek(self, fd, position, whence):
        self.fstat(fd); assert whence == 0; self.offsets[fd] = position
    def read(self, fd, count):
        self.fstat(fd); offset = self.offsets.get(fd, 0)
        answer = self.values[fd][1][offset:offset + count]; self.offsets[fd] = offset + len(answer); return answer


def actual_stage1_main(fixture, table, *, legacy=False):
    source = (HERE / "overlays/agent-stack/bin/agent-hermes-policy-stage1").read_text()
    names = {"PROOF_ENV", "INTERPRETER_FD_ENV", "STAGE2_FD_ENV", "AUTHORITY_FD_ENV"}
    tree = ast.parse(source); constants = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id in names:
            constants[node.targets[0].id] = ast.literal_eval(node.value)
    assert set(constants) == names
    proof = copy.deepcopy(fixture.proof)
    if legacy:
        proof["schema_version"] = "herdr-policy-bootstrap-2"; proof.pop("self_observation")
    raw = guard.canonical(proof)
    table.sys = SimpleNamespace(argv=["stage1", "-p", "fixture", "chat"])
    values = {**constants, "os": table, "hashlib": hashlib,
        "_require_independent_stage0": lambda: None, "_mount_rows": lambda: fixture.rows,
        "_require_exact_ro_tree": lambda *args: None, "BOOTSTRAP_ROOT": Posix("/run/herdr-bootstrap"),
        "_read_proof": lambda: (proof, raw), "_verify_trees": lambda *args: None,
        "_open_verified_stage2": lambda: table.sources[1], "_open_verified_python": lambda: table.sources[0],
        "_connect_host_authority": lambda *args: table.sources[2], "_fresh_pycache_prefix": lambda: "/run/herdr/policy-code/no-bytecode-cache"}
    return selected_module("actual_stage1_fixed_handoff", source, {"_fixed_v3_descriptors", "main"}, values), proof, raw


class Fixture:
    def __init__(self):
        self.fs = MemoryFS(); self.now = datetime.now(UTC); self.start = 902; self.pid = 102
        self.identity = security.InvocationIdentity("fixture", "root-agent", "operator", "parent", "task", "run", 7)
        self.child = security.InvocationIdentity("fixture", "child-agent", "root-agent", "task", "child", "childrun", 8)
        self.program = ingress.filter_bytes()
        self.source = (HERE / "overlays/worker-profile.apparmor").read_bytes()
        self.loaded = b"SYNTHETIC-COMPILED-POLICY-BYTES-never-a-real-kernel-proof"
        self.system = {name: sha(("inert-system:" + name).encode()) for name in credentials.SYSTEM_RUNTIME_FILES}
        self.record = {"schema_version": "herdr-worker-confinement-1", "profile": credentials.WORKER_PROFILE,
            "source_sha256": sha(self.source), "loaded_sha256": sha(self.loaded),
            "filter_sha256": sha(self.program), "system_files": self.system}
        self.mode = {"mode": guard.MODE, "role": "root", "roster_sha256": "1" * 64,
            "worker_source_sha256": sha(self.source), "loaded_policy_sha256": sha(self.loaded),
            "filter_program_sha256": sha(self.program), "system_files_sha256": guard.digest(self.system)}
        self.safe = {"config.yaml": b'{"model":{"default":"synthetic:free"}}', ".env": b"", "herdr-sdk-policy.json": b"{}"}
        self.auth_body = b'{"credential_pool":{"nous":[{"id":"SYNTHETIC-NONCREDENTIAL"}]}}'
        self.profile = profile_api().profile_identity("fixture", {**{n: sha(b) for n, b in self.safe.items()},
            "auth.json": sha(self.auth_body)})
        self.proof = {"schema_version": "herdr-policy-bootstrap-3", "authority": "herdr-host-frozen-tree",
            "identity": self.identity.to_json(), "trees": {}, "approved_profile": self.profile,
            "self_observation": self.mode}
        with patch.object(security, "Path", Posix):
            self.grant = security.SecurityGrant("synthetic-grant", "/work", self.identity,
                capability.CapabilityScope(("nous",), (), (), (), (), (), (), (), (), 0, 1,
                    capability.Egress.NONE, capability.Retention.ZERO, capability.Training.EXCLUDED), (),
                security.ProcessPolicy(False, (), security.NetworkAccess.NONE),
                security.RuntimeAssurance(True, "2" * 64, security.NetworkAccess.NONE, (), True),
                (security.ProviderRoute("nous", "https://inference-api.nousresearch.com/v1", "chat_completions", (), (),
                    capability.Egress.NONE, capability.Retention.ZERO, capability.Training.EXCLUDED,
                    ("pool:nous:SYNTHETIC-NONCREDENTIAL",)),), ("pool:nous:SYNTHETIC-NONCREDENTIAL",), (), (), (self.now - timedelta(seconds=1)).isoformat(),
                (self.now + timedelta(seconds=120)).isoformat())
        # NOT a valid signed runtime grant: this fixture is accepted only by the
        # explicit in-memory verified-bundle adapter below. No production code
        # accepts it, and it cannot be mistaken for Ed25519 test evidence.
        self.bundle = self.signed_bundle(self.grant) if CRYPTO else security.canonical_json_bytes({
            "schema_version": "TEST-ONLY-VERIFIED-BUNDLE-FIXTURE", "grant": self.grant.to_json(), "synthetic_fixture": True})
        self.session = {"proof_sha256": guard.digest(self.proof), "bundle_sha256": sha(self.bundle),
            "stage1_sha256": "3" * 64, "stage2_sha256": "4" * 64, "python_sha256": "5" * 64}
        self.context = {"identity": self.identity.to_json(), "approved_profile": self.profile,
            "plan_sha256": "6" * 64, "slot_sha256": "7" * 64, "child_projection_sha256": None}
        self.before = {"start_ticks": self.start, "namespaces": {k: k + ":[501]" for k in guard.NAMESPACES}}
        self.rows = {"/": {"ro"}, "/proc": {"rw"}, "/home/agentops": {"ro"},
            **{name: {"ro"} for name in self.system},
            **{"/home/agentops/.hermes/profiles/fixture/" + name: {"ro"} for name in self.safe}}
        self.mountinfo = b"".join((f"{n} 0 0:1 / {target} {'ro' if 'ro' in flags else 'rw'} - " +
            ("proc" if target == "/proc" else "tmpfs") + " fixture rw\n").encode()
            for n, (target, flags) in enumerate(self.rows.items(), 1))
        self.environment = b"HOME=/home/agentops\0HERDR_POLICY_TASK_ID=task\0HERDR_POLICY_FENCING_TOKEN=7\0"
        self.roster = SimpleNamespace(sha256=self.mode["roster_sha256"],
            document={"controller": {"pid": 80}, "observer": {}, "deadline": self.now.timestamp() + 120},
            live=lambda **kw: None, slot=lambda role: {"identity": self.identity.to_json()})
        self.policy = {"code": {"files": {host.STAGE1_SOURCE: "3" * 64, host.STAGE2_SOURCE: "4" * 64}},
            "runtime": [{"target": host.PYTHON_TARGET.as_posix(), "files": {host.PYTHON_EXECUTABLE: "5" * 64}}]}
        self.roster.document["host_policy_sha256"] = guard.digest(self.policy)
        self.plan_checked = []
        self.observer = SimpleNamespace(roster=lambda: self.roster, now=lambda: self.now.timestamp(), boot_id=lambda: "boot",
            case_live=lambda roster: None, controller=lambda: {"pid": 80}, verify_observer=lambda record: None,
            metadata=lambda: SimpleNamespace(locate=lambda pid: (self.roster, "root", self.context, {}, self.before)),
            mount_rows=lambda pid: copy.deepcopy(self.rows),
            original_plan=lambda context: SimpleNamespace(verify_mounted=lambda pid, rows: self.plan_checked.append((pid, rows))),
            read_bounded=self.fs.read, target=lambda *args: copy.deepcopy(self.before), self_pid=lambda: 90)
        self.populate()
    def signed_bundle(self, grant):
        Private, _, serialization, _ = CRYPTO
        # Explicit public TEST seed, never an installed key or production issuer.
        key = Private.from_private_bytes(bytes(range(32)))
        envelope = security.sign_grant(grant, key, key_id="PUBLIC-SYNTHETIC-TEST-ONLY")
        public = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        return security.canonical_json_bytes({"schema_version": security.POLICY_BUNDLE_VERSION,
            "envelope": envelope.to_json(), "public_key": base64.b64encode(public).decode()})
    def populate(self):
        self.fs.add(credentials.CONFINEMENT_APPROVAL.as_posix(), guard.canonical(self.record))
        self.fs.add(credentials.CONFINEMENT_SOURCE.as_posix(), self.source)
        kernel = credentials.KERNEL_PROFILES.as_posix() + "/1"
        self.fs.add(kernel + "/name", credentials.WORKER_PROFILE.encode() + b"\n")
        self.fs.add(kernel + "/raw_data", self.loaded)
        for name in self.system: self.fs.add(name, ("inert-system:" + name).encode())
        for pid, private in ((102, 2), (2, 2)):
            root = f"/proc/{pid}/root"
            for name in self.system: self.fs.add(root + name, ("inert-system:" + name).encode())
            for name, body in self.safe.items(): self.fs.add(root + "/home/agentops/.hermes/profiles/fixture/" + name, body)
            self.fs.directories.update({root + "/home/agentops/.hermes/hermes-agent", root + "/home/agentops/.config",
                root + "/home/agentops/.config/herdr", root + "/proc", f"/proc/{pid}/task/{pid}", f"/proc/{pid}/fd"})
            self.fs.add(f"/proc/{pid}/task/{pid}/children", b"")
            if pid != 2:
                for fd in (0, 1, 2): self.fs.links[f"/proc/{pid}/fd/{fd}"] = "/dev/pts/7"
            self.fs.add(f"/proc/{pid}/environ", self.environment)
            self.fs.add(f"/proc/{pid}/mountinfo", self.mountinfo)
            self.fs.add(f"/proc/{pid}/attr/current", (guard.WORKER_LABEL + " (enforce)\n").encode())
            status = f"Uid:\t1001 1001 1001 1001\nGid:\t1001 1001 1001 1001\nNSpid:\t{pid} {private}\n"
            status += "".join(k + ":\t0000000000000000\n" for k in guard.CAPS)
            self.fs.add(f"/proc/{pid}/status", (status + "NoNewPrivs:\t1\nSeccomp:\t2\nSeccomp_filters:\t1\n").encode())
            fields = ["0"] * 50; fields[0] = "S"; fields[19] = str(self.start)
            self.fs.add(f"/proc/{pid}/stat", (str(pid) + " (synthetic) " + " ".join(fields)).encode())
            for name in guard.NAMESPACES: self.fs.links[f"/proc/{pid}/ns/{name}"] = name + ":[501]"
        self.fs.add("/proc/102/root/run/herdr-policy/grant.bundle.json", self.bundle)
        self.fs.add("/proc/102/root/run/herdr-bootstrap/immutable-trees.json", guard.canonical(self.proof))
    @contextmanager
    def installed(self):
        # All imported/executed bytes are overlay or exact PUBLIC inputs. Only
        # low-level OS/filesystem reads change; actual decision functions run.
        plan = selected_module("herdr.policy_launch", (HERE / "overlays/herdr/policy_launch.py").read_text(),
            {"mount_rows", "_verify_root_owned_ancestry"}, {"Path": self.fs.Path, "stat": stat, "os": self.fs.os(),
             "MAX_MOUNT_INFO": 1048576, "_require": guard.require})
        plan.BUNDLE_TARGET = Posix("/run/herdr-policy/grant.bundle.json")
        plan.CODE_TARGET = Posix("/run/herdr/policy-code")
        with ExitStack() as stack:
            for module, key, value in ((credentials, "Path", self.fs.Path), (credentials, "os", self.fs.os()),
                (guard, "Path", self.fs.Path), (guard, "os", self.fs.os()),
                (security, "Path", self.fs.Path), (security, "os", self.fs.os())):
                stack.enter_context(patch.object(module, key, value))
            for key in ("CONFINEMENT_APPROVAL", "CONFINEMENT_SOURCE", "KERNEL_PROFILES"):
                stack.enter_context(patch.object(credentials, key, self.fs.Path(getattr(credentials, key).as_posix())))
            for key in ("BOOTSTRAP_TARGET", "PYTHON_TARGET"):
                stack.enter_context(patch.object(host, key, Posix(getattr(host, key).as_posix())))
            stack.enter_context(patch.dict(sys.modules, {"herdr.policy_launch": plan,
                "herdr.private_profile_namespace": profile_api()}))
            stack.enter_context(patch.object(prep_entry, "protected_bytes", side_effect=self.fs.read))
            stack.enter_context(patch.object(host_configuration, "_read_configuration", return_value=self.policy))
            def verified_bundle_fixture(path, identity, *, expected_attestation_sha256=None, **kwargs):
                if (self.fs.read(path) != self.bundle or identity != self.identity
                    or expected_attestation_sha256 != self.grant.runtime_assurance.sandbox_attestation_sha256
                    or not self.grant.is_active()):
                    raise security.SecurityError("synthetic verified-bundle fixture changed")
                return self.grant
            if CRYPTO is None:
                stack.enter_context(patch.object(security, "load_policy_bundle", side_effect=verified_bundle_fixture))
            yield plan
    def request(self):
        return {"v": guard.KERNEL_REQUEST, "challenge": "8" * 64, "identity": self.identity.to_json(),
            "pid": self.pid, "start_ticks": self.start, "session": copy.deepcopy(self.session),
            "grant_sha256": self.grant.hash, "signed_attestation_sha256": "2" * 64, "mode": copy.deepcopy(self.mode)}
    def observe(self): return guard.process_kernel_request(guard.canonical(self.request()), (80, 1001, 1001), self.observer)["observation"]
    def local(self, value, **kwargs):
        return guard.observe_self_from_bootstrap(value, challenge="8" * 64, grant=self.grant,
            bootstrap_proof=self.proof, bundle_sha256=sha(self.bundle), now_ns=int(self.now.timestamp() * 1e9), **kwargs)


class SelfGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._saved_modules = {name: module for name, module in sys.modules.items()
                              if name == "herdr" or name.startswith("herdr.")}
        for name in cls._saved_modules:
            sys.modules.pop(name, None)
        sys.modules.update(_guard_modules)

    @classmethod
    def tearDownClass(cls):
        for name in list(sys.modules):
            if name == "herdr" or name.startswith("herdr."):
                sys.modules.pop(name, None)
        sys.modules.update(cls._saved_modules)

    def test_actual_root_measurement_and_local_decision_composed(self):
        f = Fixture()
        with f.installed():
            observation = f.observe()
            self.assertEqual(observation["observed_loaded_sha256"], sha(f.loaded))
            self.assertTrue(f.local(observation))
            self.assertGreater(len(f.plan_checked), 0)
            self.assertFalse(any(p.startswith("/etc/herdr") or p.startswith("/sys/kernel/security")
                for action, p in f.fs.calls[f.fs.calls.index(("read", "/proc/2/stat")):]))

    def test_expected_digest_never_substitutes_actual_loaded_policy(self):
        f = Fixture()
        with f.installed():
            self.assertEqual(guard.measured_confinement()[2], sha(f.loaded))
            f.fs.add(str(credentials.KERNEL_PROFILES) + "/1/raw_data", b"DIFFERENT-KERNEL-BYTES")
            with self.assertRaisesRegex(ValueError, "measured_confinement"):
                f.observe()

    def test_root_authentication_and_live_case_rejection(self):
        f = Fixture()
        with f.installed():
            for peer in ((81, 1001, 1001), (80, 0, 0), (80, 1001, 0)):
                with self.subTest(peer=peer), self.assertRaises(ValueError):
                    guard.process_kernel_request(guard.canonical(f.request()), peer, f.observer)
            f.observer.case_live = lambda r: guard.require(False, "fenced_case")
            with self.assertRaisesRegex(ValueError, "fenced_case"): f.observe()

    def test_original_signed_bundle_and_exact_source_proof_required(self):
        for path, body in (("/proc/102/root/run/herdr-policy/grant.bundle.json", b"{}"),
                           ("/proc/102/root/run/herdr-bootstrap/immutable-trees.json", b"{}")):
            f = Fixture()
            with f.installed(), self.subTest(path=path):
                f.fs.add(path, body)
                with self.assertRaises((ValueError, security.SecurityError, KeyError)): f.observe()
        f = Fixture()
        with f.installed():
            bad = json.loads(f.bundle)
            if CRYPTO:
                bad["envelope"]["signature"] = base64.b64encode(bytes(64)).decode()
            else:
                bad = {"FORGED": True}
            raw = security.canonical_json_bytes(bad)
            f.fs.add("/proc/102/root/run/herdr-policy/grant.bundle.json", raw)
            f.session["bundle_sha256"] = sha(raw)
            with self.assertRaisesRegex(security.SecurityError, "authentication|fixture changed"): f.observe()

    def test_real_signed_bundle_foreign_and_stale_or_backend_unavailable_fail_closed(self):
        if CRYPTO is None:
            with self.assertRaisesRegex(security.SecurityError, "verification unavailable"):
                security._ed25519()
            return  # This is an explicit denial test, never counted as crypto acceptance.
        for foreign in (False, True):
            f = Fixture()
            with f.installed(), patch.object(security, "Path", f.fs.Path):
                bad = replace(f.grant, identity=f.child) if foreign else replace(f.grant,
                    issued_at=(f.now - timedelta(seconds=120)).isoformat(),
                    expires_at=(f.now - timedelta(seconds=60)).isoformat())
                raw = f.signed_bundle(bad)
                f.fs.add("/proc/102/root/run/herdr-policy/grant.bundle.json", raw)
                f.session["bundle_sha256"] = sha(raw)
                with self.assertRaisesRegex(security.SecurityError, "identity/fence|not active"):
                    f.observe()

    def test_stale_forged_foreign_role_identity_or_kernel_facts_denied(self):
        f = Fixture()
        with f.installed():
            good = f.observe(); self.assertTrue(f.local(good))
            changes = {"identity": f.child.to_json(), "role": "child", "private_pid": 3, "start_ticks": 903,
                "challenge": "0" * 64, "grant_sha256": "0" * 64, "bundle_sha256": "0" * 64,
                "proof_sha256": "0" * 64, "signed_attestation_sha256": "0" * 64,
                "observed_source_sha256": "0" * 64, "observed_loaded_sha256": "0" * 64,
                "filter_program_sha256": "0" * 64, "roster_sha256": "0" * 64, "profile_manifest_sha256": "0" * 64,
                "label": "unconfined", "capabilities": {**good["capabilities"], "CapEff": 1},
                "no_new_privs": 0, "seccomp": 0, "valid_until_ns": good["issued_at_ns"],
                "namespaces": {**good["namespaces"], "mnt": "mnt:[999]"}, "system_files": {}}
            for key, value in changes.items():
                with self.subTest(key=key):
                    bad = copy.deepcopy(good); bad[key] = value; self.assertFalse(f.local(bad))
            self.assertFalse(f.local({**good, "credentials_isolated": True}))

    def test_local_uid_status_namespace_fd_env_profile_runtime_remain_real(self):
        variants = (lambda f: f.fs.add("/proc/2/environ", f.environment + b"OPENAI_API_KEY=synthetic\0"),
            lambda f: f.fs.add("/proc/2/root/mnt/auth.json", b"SYNTHETIC"),
            lambda f: f.fs.add("/proc/2/root/etc/unapproved", b"EXTRA"),
            lambda f: f.fs.add("/proc/2/root/home/agentops/.hermes/profiles/fixture/auth.json", b"SYNTHETIC"),
            lambda f: f.fs.add("/proc/2/status", f.fs.files["/proc/2/status"].replace(b"NoNewPrivs:\t1", b"NoNewPrivs:\t0")),
            lambda f: f.fs.links.update({"/proc/2/ns/net": "net:[999]"}))
        for change in variants:
            f = Fixture()
            with f.installed():
                good = f.observe(); change(f)
                # Unmounted unknown files outside the five enumerated system
                # trees are inaccessible by source policy; mount aliases are
                # separately tested below rather than asserted from filenames.
                if "/proc/2/root/mnt/auth.json" in f.fs.files:
                    f.fs.add("/proc/2/mountinfo", f.mountinfo + b"80 0 0:1 / /mnt/auth.json ro - tmpfs fixture rw\n")
                self.assertFalse(f.local(good))
        f = Fixture()
        with f.installed():
            f.fs.fd_targets[1] = "/root/secret"
            self.assertFalse(f.local(f.observe()))

    def test_all_actual_runtime_parent_directories_and_recursive_walk_permissions(self):
        f = Fixture()
        parents = {str(parent) for name in credentials.SYSTEM_RUNTIME_FILES for parent in Posix(name).parents if str(parent) != "/"}
        for directory in parents:
            self.assertTrue(f.fs.directory_allowed(directory), directory)
            self.assertTrue(f.fs.directory_allowed("/proc/2/root" + directory), directory)
        self.assertFalse(f.fs.directory_allowed("/proc/2/root/root/credentials"))
        with f.installed():
            facts = f.observe(); self.assertTrue(f.local(facts))
            original = f.fs.worker_policy
            for removed in (",usr/bin", ",lib/x86_64-linux-gnu"):
                f.fs.worker_policy = original.replace(removed, "")
                self.assertFalse(credentials._observed_system_runtime(2, f.rows, f.record), removed)
                self.assertFalse(f.local(facts), removed)
            f.fs.worker_policy = original
            self.assertTrue(f.local(facts))

    def test_self_capture_owned_live_measurement_and_external_legacy_path(self):
        f = Fixture()
        with f.installed():
            self.assertEqual(credentials._capture_fd_links(2), f.fs.fd_targets)
            self.assertFalse(f.fs.measurement_live)
            self.assertEqual(credentials._capture_fd_links(102), {0: "/dev/pts/7", 1: "/dev/pts/7", 2: "/dev/pts/7"})
            f.fs.links["/proc/102/fd/8"] = "/root/foreign"
            self.assertFalse(credentials._fd_links(credentials._capture_fd_links(102)))

    def test_self_capture_foreign_directory_race_reuse_and_unknown_always_deny(self):
        for mutate in (lambda fs: fs.fd_targets.update({4: "/proc/2/fd"}),
            lambda fs: fs.fd_targets.update({4: "/root/foreign"}),
            lambda fs: fs.fd_targets.update({n: "/dev/null" for n in range(4, 40)}),
            lambda fs: setattr(fs, "missing_link", "/proc/2/fd/1"),
            lambda fs: setattr(fs, "measurement_reused", True)):
            f = Fixture()
            with f.installed():
                facts = f.observe(); mutate(f.fs); self.assertFalse(f.local(facts))
        f = Fixture()
        with f.installed(), patch.object(credentials.os, "fstat", side_effect=OSError(errno.EACCES, "unknown measurement FD")):
            with self.assertRaisesRegex(ValueError, "state unknown"): credentials._capture_fd_links(2)
        f = Fixture()
        class NoMeasurement:
            def __enter__(self):
                return iter(SimpleNamespace(name=str(n), path=f"/proc/2/fd/{n}") for n in (0, 1, 2))
            def __exit__(self, *args): pass
        with f.installed(), patch.object(credentials.os, "scandir", return_value=NoMeasurement()):
            with self.assertRaisesRegex(ValueError, "not established"): credentials._capture_fd_links(2)

    def test_fixed_descriptor_handoff_collisions_and_foreign_inode_rejected(self):
        f = Fixture()
        for sources, choices in (((198, 197, 199), ()), ((4, 5, 6), (197, 198, 199, 200))):
            table = HandleTable(sources, choices); stage1, _, _ = actual_stage1_main(f, table)
            with self.assertRaises(ExecRecorded): stage1.main(["-p", "fixture", "chat"])
            self.assertEqual({fd: item[0] for fd, item in table.values.items() if fd > 2}, {197: 71, 198: 72, 199: 73})
            self.assertEqual(table.exec[0], "/proc/self/fd/197")
            self.assertEqual(table.exec[1][5], "/proc/self/fd/198")
            self.assertFalse(any(name in table.exec[2] for name in (stage1.INTERPRETER_FD_ENV, stage1.STAGE2_FD_ENV, stage1.AUTHORITY_FD_ENV)))
        table = HandleTable(); table.tamper = True; stage1, _, _ = actual_stage1_main(f, table)
        with self.assertRaisesRegex(SystemExit, "changed at fixed"): stage1.main([])
        self.assertIsNone(table.exec)

    def test_actual_initial_exec_environment_handle_retirement_and_local_retained_decisions(self):
        f = Fixture(); table = HandleTable(); stage1, proof, raw = actual_stage1_main(f, table)
        with self.assertRaises(ExecRecorded): stage1.main(["-p", "fixture", "chat"])
        initial = table.exec[2]
        proc_initial = b"".join((name + "=" + value).encode() + b"\0" for name, value in initial.items())
        stage2 = actual_stage2(); stage2.os = table; stage2.stat = stat
        table.environ = dict(initial); table.SEEK_SET = 0
        stage2.BOOTSTRAP_PROOF = f.fs.Path("/proc/102/root/run/herdr-bootstrap/immutable-trees.json")
        stage2.__file__ = "/proc/self/fd/198"
        stage2.BOOTSTRAP_ROOT = Posix("/run/herdr-bootstrap")
        stage2._require_production_mount = lambda *args, **kwargs: None
        stage2._load_stage1_module = lambda: SimpleNamespace(_read_proof=lambda path: (proof, raw),
            _mount_rows=lambda: f.rows, _require_exact_ro_tree=lambda *args: None, _verify_trees=lambda *args: None)
        stage2._require_startup_pycache_prefix = lambda: None
        stage2.sys = SimpleNamespace(flags=SimpleNamespace(isolated=True, no_site=True), version_info=(3, 11))
        stage2.PYTHON_PATH = Posix("/runtime/python/bin/python3.11"); stage2.PYTHON_ROOT = Posix("/runtime/python")
        table.path = SimpleNamespace(realpath=lambda path: str(stage2.PYTHON_PATH))
        stage2.PYTHON_SHA256 = sha(b"inert audited python")
        stage2.PYTHON_STDLIB_SHA256 = stage2.SITE_SHA256 = "a" * 64
        stage2._digest_site_packages = lambda path: "a" * 64
        with f.installed():
            # Original inherited socket path still authenticates handle199;
            # this fixture's transport is separately composed above in full.
            self.assertEqual(stage2._startup_descriptor(stage2.BOOTSTRAP_AUTH_FD_ENV, retire=True), 199)
            table.close(199)
            stage2._require_stage1_continuity()
            stage2._verify_runtime(Posix("/runtime/hermes"))
            self.assertEqual(set(table.values), {0, 1, 2})
            self.assertEqual(table.environ, initial)  # No alleged proc scrubbing.
            with self.assertRaisesRegex(SystemExit, "retired"):
                stage2._startup_descriptor(stage2.STAGE2_FD_ENV)
            f.fs.add("/proc/2/environ", proc_initial)
            f.fs.add("/proc/102/environ", proc_initial)
            facts = f.observe()
            self.assertTrue(f.local(facts))
            self.assertTrue(credentials._observe_one(102, f.profile, f.rows, f.grant.workspace_root))
            for key in (stage1.INTERPRETER_FD_ENV, stage1.STAGE2_FD_ENV, stage1.AUTHORITY_FD_ENV):
                contaminated = proc_initial + key.encode() + b"=197\0"
                f.fs.add("/proc/2/environ", contaminated); f.fs.add("/proc/102/environ", contaminated)
                self.assertFalse(f.local(facts)); self.assertFalse(credentials._observe_one(102, f.profile, f.rows, f.grant.workspace_root))
            table.environ[stage1.INTERPRETER_FD_ENV] = "197"
            with self.assertRaisesRegex(SystemExit, "environment forbidden"):
                stage2._startup_descriptor(stage2._INTERPRETER_FD_ENV)
        legacy_table = HandleTable(); legacy_stage1, _, _ = actual_stage1_main(f, legacy_table, legacy=True)
        with self.assertRaises(ExecRecorded): legacy_stage1.main([])
        self.assertEqual({name: legacy_table.exec[2][name] for name in (legacy_stage1.INTERPRETER_FD_ENV,
            legacy_stage1.STAGE2_FD_ENV, legacy_stage1.AUTHORITY_FD_ENV)},
            {legacy_stage1.INTERPRETER_FD_ENV: "4", legacy_stage1.STAGE2_FD_ENV: "5", legacy_stage1.AUTHORITY_FD_ENV: "6"})

    def test_pending_process_replacement_or_source_change_denies_root_reply(self):
        f = Fixture()
        with f.installed():
            f.observer.target = lambda *args: {**f.before, "start_ticks": 999}
            with self.assertRaisesRegex(ValueError, "observation_changed"): f.observe()
        f = Fixture()
        with f.installed():
            f.policy["code"]["files"][host.STAGE2_SOURCE] = "0" * 64
            with self.assertRaises(ValueError): f.observe()

    def test_actual_stage2_transport_consumption_legacy_and_plain_dict_rejection(self):
        f = Fixture(); stage2 = actual_stage2()
        with f.installed():
            facts = f.observe(); payload = {"schema_version": guard.ENVELOPE, "reference": {"unchanged": "reference"}, "self_observation": facts}
            stage2._sha256_regular_path = lambda *args: sha(f.bundle)
            reply = stage2._AuthenticatedKernelReply(payload, "8" * 64, stage2._BOOTSTRAP_REPLY_TOKEN)
            self.assertEqual(stage2._verified_bootstrap_reference(reply, f.proof, f.grant, credentials, sys.modules["herdr.policy_launch"]), payload["reference"])
            with self.assertRaisesRegex(SystemExit, "consumed"):
                stage2._verified_bootstrap_reference(reply, f.proof, f.grant, credentials, sys.modules["herdr.policy_launch"])
            with self.assertRaisesRegex(SystemExit, "inherited authenticated"):
                stage2._verified_bootstrap_reference(payload, f.proof, f.grant, credentials, sys.modules["herdr.policy_launch"])
            legacy = {**f.proof, "schema_version": "herdr-policy-bootstrap-2"}; legacy.pop("self_observation")
            calls = []
            observed = SimpleNamespace(observe_sdk_credentials=lambda *args: calls.append(args) or True)
            stage2.os = SimpleNamespace(getpid=lambda: 2)
            reference = {"original": "flat"}
            self.assertIs(stage2._verified_bootstrap_reference(reference, legacy, f.grant, observed, sys.modules["herdr.policy_launch"]), reference)
            self.assertEqual(len(calls), 1)

    def test_actual_precontinuation_hook_and_original_checks_precede_publication(self):
        f = Fixture()
        expectation = authority.BootstrapExpectation(f.identity.to_json(), *[f.session[k] for k in
            ("proof_sha256", "stage1_sha256", "stage2_sha256", "python_sha256", "bundle_sha256")],
            101, 901, 1, 11, 1, 22, time.time() + 59, guard.MODE)
        session = authority._Session(102, 902, expectation.proof_sha256, expectation.bundle_sha256, 1, 22, expectation)
        key = authority.identity_key(f.identity.to_json()); calls = []
        owner = SimpleNamespace(launch=SimpleNamespace(bootstrap_self_observation=guard.MODE,
            _observe_bootstrap_continuation=lambda receipt: calls.append(("publish", receipt))))
        broker = object.__new__(host._DurableBootstrapAuthority); broker._owner = owner
        broker._lock = threading.RLock(); broker._changed = threading.Condition(broker._lock)
        broker._sessions = {key: session}; broker._continuations = {}; broker._prune = lambda: None
        broker._inspect = lambda pid: authority.PeerProcess(102, 101, 902, 1, 22, ())
        request = {"op": "stage2", "identity": f.identity.to_json(), "proof_sha256": expectation.proof_sha256,
            "bundle_sha256": expectation.bundle_sha256, "self_observation_mode": guard.MODE, "challenge": "8" * 64}
        def produce(*args):
            self.assertFalse(session.continued); self.assertNotIn(key, broker._continuations)
            calls.append(("root_measurement", None)); return {"actual": "fixture-only"}
        with patch.object(guard, "produce_for_bootstrap", side_effect=produce):
            broker._continue(key, session, request)
        self.assertEqual([x[0] for x in calls], ["root_measurement", "publish"])
        self.assertTrue(session.continued)
        with self.assertRaises(authority.BootstrapAuthorityError): broker._continue(key, session, request)
        for field in ("proof_sha256", "bundle_sha256", "identity"):
            session.continued = False; calls.clear(); bad = dict(request)
            bad[field] = f.child.to_json() if field == "identity" else "0" * 64
            with patch.object(guard, "produce_for_bootstrap", side_effect=produce), self.assertRaises(authority.BootstrapAuthorityError):
                broker._continue(key, session, bad)
            self.assertEqual(calls, [])

    def test_actual_host_root_rpc_bootstrap_transport_and_stage2_chain(self):
        f = Fixture(); stage2 = actual_stage2(); events = []
        expectation = authority.BootstrapExpectation(f.identity.to_json(), *[f.session[k] for k in
            ("proof_sha256", "stage1_sha256", "stage2_sha256", "python_sha256", "bundle_sha256")],
            101, 901, 1, 11, 1, 22, time.time() + 59, guard.MODE)
        session = authority._Session(102, 902, expectation.proof_sha256, expectation.bundle_sha256, 1, 22, expectation)
        source_files = []
        synthetic_bodies = {50: f.auth_body, 51: f.safe["config.yaml"], 52: b"", 53: b"{}"}
        for fd, relative in ((50, "auth.json"), (51, "config.yaml"), (52, ".env"), (53, "herdr-sdk-policy.json")):
            source_files.append(SimpleNamespace(fd=fd, relative=relative, size=len(synthetic_bodies[fd]),
                sha256=sha(synthetic_bodies[fd]), verify=lambda: events.append("immutable_profile_file_check")))
        snapshot = SimpleNamespace(name="fixture", identity=f.profile, files=source_files, sdk_files=source_files[1:])
        launch = SimpleNamespace(identity=f.identity, grant=f.grant, sealed=object(), bootstrap_self_observation=guard.MODE,
            private_profile_snapshot=snapshot, _observe_bootstrap_continuation=lambda r: events.append("continuation_published"))
        owner = SimpleNamespace(launch=launch, proof=f.proof, _claimed_peer=(102, 902))
        broker = object.__new__(host._DurableBootstrapAuthority); broker._owner = owner
        broker._lock = threading.RLock(); broker._changed = threading.Condition(broker._lock)
        key = authority.identity_key(f.identity.to_json())
        broker._sessions = {key: session}; broker._continuations = {}; broker._prune = lambda: None
        broker._inspect = lambda pid: authority.PeerProcess(102, 101, 902, 1, 22, ())
        class RootClient:
            peer_pid = 90
            def roster(self): return f.roster
            def exchange(self, packet, roster):
                events.append("root_measures_before_continuation")
                if session.continued: raise AssertionError("circular continuation dependency")
                return guard.canonical(guard.process_kernel_request(packet, (80, 1001, 1001), f.observer))
        class InheritedSocket:
            def __init__(self): self.response = b""; self.closed = False
            def settimeout(self, seconds): assert seconds == 5
            def sendall(self, packet):
                request = json.loads(packet); broker._continue(key, session, request)
                self.response = broker._stage2_response(session)
            def recv(self, count):
                answer, self.response = self.response[:count], self.response[count:]; return answer
            def close(self): self.closed = True; events.append("bootstrap_fd_closed")
        inherited = InheritedSocket()
        with f.installed(), patch.object(observer_client, "LinuxClientOps", RootClient), \
             patch.object(host_reference_binding, "os", SimpleNamespace(pread=lambda fd, size, offset: synthetic_bodies[fd][offset:offset + size])):
            stage2.socket = SimpleNamespace(socket=lambda *, fileno: inherited if fileno == 199 else self.fail("foreign FD"))
            stage2.os = SimpleNamespace(environ={stage2.STAGE1_PROOF_ENV: f.session["proof_sha256"]},
                close=lambda fd: self.fail("unexpected FD close"))
            stage2.BOOTSTRAP_PROOF = f.fs.Path("/proc/102/root/run/herdr-bootstrap/immutable-trees.json")
            stage2._raw_identity_from_env = lambda: f.identity.to_json()
            stage2._sha256_regular_path = lambda *args: sha(f.bundle)
            receipt = stage2._require_host_bootstrap_authority()
            self.assertTrue(inherited.closed)
            self.assertNotIn(stage2.BOOTSTRAP_AUTH_FD_ENV, stage2.os.environ)
            reference = stage2._verified_bootstrap_reference(receipt, f.proof, f.grant, credentials, sys.modules["herdr.policy_launch"])
            self.assertEqual(set(reference), {"provider", "entry_id", "credential_ref", "endpoint", "api_mode", "model",
                "profile_sha256", "projection_sha256", "grant_hash", "workspace", "fence", "lineage", "tag"})
            self.assertEqual(reference["grant_hash"], f.grant.hash)
            self.assertNotIn("self_observation", reference)
        self.assertLess(events.index("root_measures_before_continuation"), events.index("continuation_published"))
        self.assertLess(events.index("continuation_published"), events.index("bootstrap_fd_closed"))

    def test_transport_bound_malformed_stale_and_cross_role_envelope_rejected(self):
        f = Fixture(); stage2 = actual_stage2()
        with f.installed():
            facts = f.observe(); stage2._sha256_regular_path = lambda *args: sha(f.bundle)
            good = {"schema_version": guard.ENVELOPE, "reference": {"fixture": True}, "self_observation": facts}
            for mutate in (lambda p: p.update(extra=True), lambda p: p.update(schema_version="unknown"),
                lambda p: p["self_observation"].update(challenge="0" * 64),
                lambda p: p["self_observation"].update(role="child"),
                lambda p: p["self_observation"].update(valid_until_ns=1)):
                bad = copy.deepcopy(good); mutate(bad)
                receipt = stage2._AuthenticatedKernelReply(bad, "8" * 64, stage2._BOOTSTRAP_REPLY_TOKEN)
                with self.assertRaises(SystemExit):
                    stage2._verified_bootstrap_reference(receipt, f.proof, f.grant, credentials, sys.modules["herdr.policy_launch"])
            for raw in (b"stage2-ok {}\ntrailing", b"stage2-ok " + b"x" * 32768, b"stage2-ok { \"x\": 1 }\n"):
                reader = io.BytesIO(raw)
                with self.assertRaises(SystemExit): stage2._recv_bootstrap_status(SimpleNamespace(recv=reader.read), b"stage2-ok\n")

    def test_actual_retained_proof_reconstructs_v3_from_host_evidence(self):
        f = Fixture()
        with f.installed() as plan:
            trees = {str(plan.CODE_TARGET): {"device": 1, "inode": 2, "source_digest": "a" * 64, "snapshot_kind": "host-frozen-copy"}}
            proof = host.bootstrap_proof(f.identity, trees, approved_profile=f.profile, self_observation=f.mode)
            evidence = {"approved_profile": f.profile, "code_sha256": "a" * 64, "runtime_sha256": {},
                "tree_identities": {str(plan.CODE_TARGET): {"device": 1, "inode": 2}},
                "bootstrap": {"self_observation": f.mode}}
            raw = security.canonical_json_bytes(proof)
            self.assertEqual(host.retained_bootstrap_proof(evidence, f.identity, raw), proof)
            evidence["bootstrap"]["self_observation"] = {**f.mode, "role": "child"}
            with self.assertRaises(security.SecurityError): host.retained_bootstrap_proof(evidence, f.identity, raw)

    def test_host_effect_authority_and_reference_sources_are_byte_identical(self):
        for name in ("work_authority.py", "host_model_transport.py", "host_reference_binding.py", "security.py"):
            self.assertEqual((HERE / "overlays/herdr" / name).read_bytes(), (PUBLIC / "herdr" / name).read_bytes(), name)
        source = (HERE / "overlays/herdr/bootstrap_self_observation.py").read_text()
        tree = ast.parse(source)
        root = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "process_kernel_request")
        self.assertNotIn("credentials_isolated", {n.value for n in ast.walk(root) if isinstance(n, ast.Constant) and isinstance(n.value, str)})
        effect = (PUBLIC / "herdr/host_model_transport.py").read_text()
        self.assertNotIn("bootstrap_self_observation", effect)
        self.assertNotIn("self_observation", effect)

    def test_worker_permission_closure_and_new_exact_source_pin(self):
        source = (HERE / "overlays/worker-profile.apparmor").read_bytes(); text = source.decode()
        self.assertEqual(sha(source), guard.WORKER_SOURCE)
        self.assertEqual(sha(source), credentials.WORKER_PROFILE_SOURCE_SHA256)
        for root in ("/run/herdr/policy-code/", "/home/agentops/", "/home/agentops/.hermes/hermes-agent/",
                     "/home/agentops/.hermes/hermes-agent/venv/lib/python3.11/site-packages/"):
            self.assertIn("  " + root + " r,", text)
        for denied in ("audit deny capability,", "audit deny mount,", "audit deny userns,", "audit deny change_profile,"):
            self.assertIn(denied, text)
        self.assertNotIn("/etc/herdr/", text); self.assertNotIn("/sys/kernel/security/", text)
        self.assertNotIn("network inet", text); self.assertIsNone(re.search(r"(?m)^\s*/\*\*\s+r,", text))


if __name__ == "__main__": unittest.main(verbosity=2)
