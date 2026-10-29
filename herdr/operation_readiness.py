"""Operational readiness only; admission and accounting stay in the host factory."""
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import stat


class ReadinessError(RuntimeError):
    pass


class SnapshotChanged(ReadinessError):
    """A read-only observation changed; this conveys no execution authority."""


def _task_stamp(info):
    return (info.st_dev, info.st_ino, info.st_uid, info.st_gid, info.st_mode,
            info.st_nlink, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def _task_directory(path):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts, 'absolute_task_queue_required')
    fd = os.open('/', os.O_PATH | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        for part in path.parts[1:]:
            child = os.open(part, os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=fd)
            os.close(fd)
            fd = child
        return fd
    except BaseException:
        os.close(fd)
        raise


def observe_task(queue, task_id, expected_identity, *, owner=1001):
    """One bounded consistent observation, never admission or acceptance.

    Callers may poll SnapshotChanged only inside their original deadline. A
    stable absence/duplicate, unsafe file or identity mismatch remains fatal.
    """
    from herdr.evidence import binding
    require(isinstance(task_id, str) and task_id not in ('', '.', '..')
            and '/' not in task_id and '\\' not in task_id, 'task_name_required')
    require(isinstance(expected_identity, dict) and expected_identity.get('id') == task_id
            and set(expected_identity) == {'id', 'run_token', 'idempotency_key', 'attempt', 'fencing_token'},
            'trusted_task_identity_required')
    queue = Path(queue)
    states = ('running', 'blocked', 'failed', 'done', 'pending')
    name = task_id + '.json'
    for _ in range(3):
        held = []
        try:
            root = _task_directory(queue)
            held.append(root)
            root_info = os.fstat(root)
            require(root_info.st_uid == owner and not root_info.st_mode & 0o022, 'task_queue_owner_required')
            directories = {}
            for state in states:
                fd = os.open(state, os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=root)
                held.append(fd)
                info = os.fstat(fd)
                require(info.st_uid == owner and not info.st_mode & 0o022, 'task_state_owner_required')
                directories[state] = (fd, _task_stamp(info))
            def unchanged():
                if _task_stamp(os.fstat(root)) != _task_stamp(root_info):
                    return False
                for state, (fd, stamp) in directories.items():
                    if stamp != _task_stamp(os.fstat(fd)):
                        return False
                    if stamp != _task_stamp(os.stat(state, dir_fd=root, follow_symlinks=False)):
                        return False
                named = _task_directory(queue)
                try:
                    return _task_stamp(os.fstat(named)) == _task_stamp(root_info)
                finally:
                    os.close(named)
            matches = []
            for state, (fd, _) in directories.items():
                try:
                    info = os.stat(name, dir_fd=fd, follow_symlinks=False)
                except FileNotFoundError:
                    continue
                require(stat.S_ISREG(info.st_mode) and info.st_uid == owner and info.st_nlink == 1
                        and not info.st_mode & 0o022 and 0 < info.st_size <= 1048576, 'safe_task_file_required')
                matches.append((state, info))
            if not unchanged():
                continue
            require(len(matches) == 1, 'canonical task count differs from one')
            state, before = matches[0]
            try:
                fd = os.open(name, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC,
                             dir_fd=directories[state][0])
            except FileNotFoundError:
                if not unchanged():
                    continue
                raise
            held.append(fd)
            if _task_stamp(os.fstat(fd)) != _task_stamp(before):
                continue
            body = bytearray()
            while len(body) <= before.st_size:
                chunk = os.read(fd, min(65536, before.st_size + 1 - len(body)))
                if not chunk:
                    break
                body.extend(chunk)
            if _task_stamp(os.fstat(fd)) != _task_stamp(before) or not unchanged():
                continue
            require(len(body) == before.st_size, 'task_snapshot_shortened')
            task = json.loads(body)
            require(isinstance(task, dict) and binding(task) == expected_identity, 'task_identity_changed')
            return queue / state / name, task
        finally:
            for fd in reversed(held):
                os.close(fd)
    raise SnapshotChanged('canonical task snapshot changed during observation')


def require(ok, reason):
    if not ok:
        raise ReadinessError(reason)


@dataclass(frozen=True)
class Lifetimes:
    grant_seconds: int
    work_seconds: int
    preparation_seconds: int
    cleanup_seconds: int
    skew_seconds: int = 30

    def credential_seconds(self):
        values = tuple(self.__dict__.values())
        require(all(type(v) is int and v > 0 for v in values), "invalid_lifetime")
        return max(self.grant_seconds, self.work_seconds + self.cleanup_seconds) + self.preparation_seconds + self.skew_seconds

    def require_admin(self, remaining):
        require(remaining >= self.preparation_seconds + self.work_seconds + self.cleanup_seconds + self.skew_seconds,
                "administrator_window_insufficient")


def capacity(available, *, floor, start_guard, preparation_peak=0, growth_allowance=0, warning_margin=268435456):
    values = (available, floor, start_guard, preparation_peak, growth_allowance, warning_margin)
    require(all(type(v) is int and v >= 0 for v in values), "invalid_capacity")
    required = floor + start_guard + preparation_peak + growth_allowance
    return {"ready": available >= required, "available_bytes": available, "required_bytes": required,
            "missing_bytes": max(0, required - available), "margin_bytes": available - required,
            "capacity_warning": available < required + warning_margin}


def read_protected(path, *, owner=0, limit=1048576):
    """No writable or symlinked ancestor; snapshot the final regular file once."""
    path = Path(path)
    require(path.is_absolute() and ".." not in path.parts, "absolute_protected_path_required")
    fd = os.open("/", os.O_PATH | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        for index, part in enumerate(path.parts[1:]):
            info = os.fstat(fd)
            require(info.st_uid == owner and not info.st_mode & 0o022, "protected_ancestry_required")
            last = index == len(path.parts) - 2
            flags = os.O_RDONLY | os.O_NONBLOCK if last else os.O_PATH | os.O_DIRECTORY
            nxt = os.open(part, flags | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=fd)
            os.close(fd)
            fd = nxt
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_uid == owner and before.st_nlink == 1
                and not before.st_mode & 0o222 and 0 < before.st_size <= limit, "protected_file_required")
        body = bytearray()
        while len(body) < before.st_size:
            block = os.read(fd, min(1048576, before.st_size - len(body)))
            require(bool(block), "protected_snapshot_shortened")
            body.extend(block)
        stamp=lambda info:(info.st_dev,info.st_ino,info.st_uid,info.st_gid,info.st_mode,info.st_nlink,
                           info.st_size,info.st_mtime_ns,info.st_ctime_ns)
        require(not os.read(fd, 1) and stamp(before) == stamp(os.fstat(fd)), "protected_snapshot_changed")
        return bytes(body)
    finally:
        os.close(fd)


def load_composition(path, expected_sha256):
    body = read_protected(path)
    require(hashlib.sha256(body).hexdigest() == expected_sha256, "composition_digest_changed")
    value = json.loads(body)
    require(set(value) == {"schema_version", "runtime", "files", "lifetimes", "capacity", "pilot"}
            and value["schema_version"] == "herdr-approved-pilot-composition-1", "composition_schema")
    require(type(value["files"]) is dict and 1 <= len(value["files"]) <= 64, "composition_files")
    for source, expected in value["files"].items():
        require(hashlib.sha256(read_protected(source, limit=33554432)).hexdigest() == expected,
                "composition_source_changed")
    Lifetimes(**value["lifetimes"]).credential_seconds()
    return value


def require_new_failure_evidence(previous, current):
    """A repeated preparation failure without new evidence requires reconciliation."""
    if previous and previous["reason_code"] == current["reason_code"]:
        require(previous["evidence_sha256"] != current["evidence_sha256"], "unchanged_failure_requires_reconciliation")


def require_offline_acceptance(proof, composition_sha256, *, now_epoch):
    fields={"schema_version","composition_sha256","checked_at_epoch","ordinary_worker_used","actual_sdk_used",
            "host_ipc_used","work_tools_verified","validation_verified","local_result_accepted","external_provider_http_requests",
            "external_authentication_http_requests","fixture_only"}
    require(set(proof)==fields and proof["schema_version"]=="herdr-ordinary-offline-acceptance-1", "offline_proof_schema")
    require(proof["composition_sha256"]==composition_sha256, "offline_proof_composition_changed")
    for field in ("ordinary_worker_used","actual_sdk_used","host_ipc_used","work_tools_verified",
                  "validation_verified","local_result_accepted","fixture_only"):
        require(proof[field] is True, "offline_cycle_not_accepted")
    require(type(proof["external_provider_http_requests"])is int and proof["external_provider_http_requests"]==0
            and type(proof["external_authentication_http_requests"])is int and proof["external_authentication_http_requests"]==0,
            "offline_external_effect_recorded")
    at=proof["checked_at_epoch"]
    require(type(at) in (int,float) and 0<=now_epoch-at<=86400, "offline_proof_stale")


def host_action_command(python, script, composition_path, composition_sha256, request, gh_fd, guard_fd):
    """Credential mounts must occur in a distinct host-action mount namespace."""
    require(all(Path(value).is_absolute() for value in (python,script,composition_path,request)), "host_action_absolute_paths")
    require(type(gh_fd)is int and type(guard_fd)is int and gh_fd>=0 and guard_fd>=0, "host_action_descriptors")
    return ['/usr/bin/unshare','--mount','--fork',str(python),'-I','-B',str(script),
            str(composition_path),composition_sha256,str(request),str(gh_fd),str(guard_fd)]


def write_owned_json(path, value, *, owner=0, group=1001, mode=0o444):
    """Atomic descriptor-relative writes; never follow a caller's temp alias."""
    path = Path(path)
    require(path.is_absolute() and ".." not in path.parts, "absolute_output_required")
    raw = (json.dumps(value, sort_keys=True, allow_nan=False) + "\n").encode()
    require(len(raw) <= 1048576, "bounded_output_required")
    directory = os.open("/", os.O_PATH | os.O_DIRECTORY | os.O_CLOEXEC)
    temporary = None
    try:
        for part in path.parts[1:-1]:
            child = os.open(part, os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=directory)
            os.close(directory)
            directory = child
        info = os.fstat(directory)
        require(info.st_uid == os.geteuid() and not info.st_mode & 0o022, "owned_output_directory_required")
        sync_fd = os.open(".", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC, dir_fd=directory)
        try:
            temporary = ".herdr-json-" + os.urandom(16).hex()
            fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                         0o600, dir_fd=directory)
            with os.fdopen(fd, "wb") as stream:
                stream.write(raw)
                stream.flush()
                if os.geteuid() == 0:
                    os.fchown(stream.fileno(), owner, group)
                else:
                    require(owner == os.geteuid(), "output_owner_change_denied")
                os.fchmod(stream.fileno(), mode)
                os.fsync(stream.fileno())
            os.replace(temporary, path.name, src_dir_fd=directory, dst_dir_fd=directory)
            temporary = None
            os.fsync(sync_fd)
        finally:
            os.close(sync_fd)
    finally:
        if temporary is not None:
            try:
                os.unlink(temporary, dir_fd=directory)
            except FileNotFoundError:
                pass
        os.close(directory)
