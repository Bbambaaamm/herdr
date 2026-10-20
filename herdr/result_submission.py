"""One immutable attempt-owned result inode; no general filesystem authority."""
from __future__ import annotations
from dataclasses import dataclass
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat

TOOL = "herdr_submit_result"
TOOLSET = "herdr_result"
ARGUMENTS = ("status", "evidence", "summary")
MAX_BYTES = 131072

def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()

def reservation_binding(slot):
    return {"schema_version":"herdr-result-reservation-1",**slot.to_json()}

def verify_empty_reservation_fd(fd, binding):
    """Check the held readable inode, including interrupted submission intent."""
    if not isinstance(binding,dict) or binding.get("schema_version")!="herdr-result-reservation-1":
        raise ValueError("result reservation binding invalid")
    slot=ResultSlot.from_dict({k:v for k,v in binding.items() if k!="schema_version"})
    info=os.fstat(fd)
    if (not stat.S_ISREG(info.st_mode) or info.st_uid!=os.geteuid() or info.st_nlink!=1
            or info.st_mode&0o777!=0o600 or info.st_size!=0
            or (info.st_dev,info.st_ino)!=(slot.device,slot.inode)
            or os.getxattr(fd,"user.herdr.result_reservation")!=_canonical(binding)
            or "user.herdr.result_submission" in os.listxattr(fd)):
        raise ValueError("result reservation changed before delivery")
    stamp=lambda value:(value.st_dev,value.st_ino,value.st_uid,value.st_mode,value.st_nlink,
                        value.st_size,value.st_ctime_ns,value.st_mtime_ns)
    if stamp(os.fstat(fd))!=stamp(info):
        raise ValueError("result reservation changed during check")

def reserve_empty_result(path, identity, idempotency_key):
    """Reserve or reopen an undelivered slot for this exact fenced attempt.

    The xattr is a retry binding, not an authorization. Admission, pinned inode
    validation and signed completion evidence remain the host's authorities.
    Partial, unlabelled and submitted slots require explicit reconciliation.
    """
    path = Path(path)
    if not path.is_absolute() or path.parent.resolve(strict=True) != path.parent:
        raise ValueError("result reservation parent cannot use symlinks")
    parent = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    fd = None
    try:
        flags = os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK
        try:
            fd = os.open(path.name, flags | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=parent)
            created = True
        except FileExistsError:
            fd = os.open(path.name, flags, dir_fd=parent)
            created = False
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid()
                or info.st_nlink != 1 or info.st_mode & 0o777 != 0o600 or info.st_size != 0):
            raise ValueError("result reservation requires an empty private inode")
        slot = ResultSlot(str(path), info.st_dev, info.st_ino,
            hashlib.sha256(_canonical(identity.to_json())).hexdigest(), idempotency_key)
        attribute = "user.herdr.result_reservation"
        stamp = _canonical(reservation_binding(slot))
        if created:
            os.setxattr(fd, attribute, stamp, os.XATTR_CREATE)
        elif os.getxattr(fd, attribute) != stamp:
            raise ValueError("result reservation attempt changed")
        # An interrupted result submission may still have zero bytes. Never
        # reinterpret its durable submission intent as a pre-delivery retry.
        if "user.herdr.result_submission" in os.listxattr(fd):
            raise ValueError("result reservation has submission intent")
        named = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
        current = path.lstat()
        if (named.st_dev, named.st_ino) != (info.st_dev, info.st_ino) or (
                current.st_dev, current.st_ino) != (info.st_dev, info.st_ino):
            raise ValueError("result reservation inode changed")
        os.fsync(fd)
        os.fsync(parent)
        verify_empty_reservation_fd(fd,reservation_binding(slot))
        return path
    finally:
        if fd is not None: os.close(fd)
        os.close(parent)

@dataclass(frozen=True)
class ResultSlot:
    path: str
    device: int
    inode: int
    identity_sha256: str
    idempotency_key: str
    max_bytes: int = MAX_BYTES

    def __post_init__(self):
        import re
        if (not isinstance(self.path, str) or not Path(self.path).is_absolute()
                or str(Path(self.path)) != self.path or ".." in Path(self.path).parts
                or any(type(x) is not int or not 0 < x < 2**64 for x in (self.device, self.inode))
                or not isinstance(self.identity_sha256, str) or not re.fullmatch("[0-9a-f]{64}", self.identity_sha256)
                or not isinstance(self.idempotency_key, str) or not re.fullmatch("[A-Za-z0-9._:/+-]{1,256}", self.idempotency_key)
                or type(self.max_bytes) is not int or not 1024 <= self.max_bytes <= MAX_BYTES):
            raise ValueError("invalid result slot")

    def to_json(self):
        return dict(path=self.path, device=self.device, inode=self.inode,
                    identity_sha256=self.identity_sha256, idempotency_key=self.idempotency_key,
                    max_bytes=self.max_bytes)

    @classmethod
    def from_dict(cls, raw):
        if not isinstance(raw, dict) or set(raw) != {"path","device","inode","identity_sha256","idempotency_key","max_bytes"}:
            raise ValueError("closed result slot required")
        return cls(**raw)

    @classmethod
    def bind(cls, path, identity, idempotency_key):
        path = Path(path)
        if path.resolve(strict=True) != path:
            raise ValueError("result slot cannot use symlinks")
        info = path.lstat()
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid()
                or info.st_nlink != 1 or info.st_mode & 0o777 != 0o600 or info.st_size > MAX_BYTES):
            raise ValueError("private regular result inode required")
        return cls(str(path), info.st_dev, info.st_ino,
                   hashlib.sha256(_canonical(identity.to_json())).hexdigest(), idempotency_key)

def arguments(raw):
    if not isinstance(raw, dict) or set(raw) - set(ARGUMENTS) or not {"status","evidence"} <= set(raw):
        raise ValueError("closed result arguments required")
    value = json.loads(_canonical(raw))
    if value["status"] not in {"completed","blocked","failed"}:
        raise ValueError("candidate status required")
    evidence = value["evidence"]
    if not isinstance(evidence, list) or not 1 <= len(evidence) <= 128:
        raise ValueError("bounded nonempty evidence required")
    summary = value.get("summary", "")
    if not isinstance(summary, str) or len(summary.encode()) > 8192:
        raise ValueError("bounded summary required")
    if len(_canonical(value)) > MAX_BYTES - 4096:
        raise ValueError("result exceeds bound")
    return value

def payload_for_slot(identity, slot, raw):
    from .security import InvocationIdentity, PolicyDenied
    value = arguments(raw)
    if (not isinstance(identity, InvocationIdentity) or not isinstance(slot, ResultSlot)
            or slot.identity_sha256 != hashlib.sha256(_canonical(identity.to_json())).hexdigest()):
        raise PolicyDenied("result_slot_unbound")
    evidence = value["evidence"]
    evidence_sha = hashlib.sha256(json.dumps(evidence, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()
    payload = dict(task_id=identity.task_id, run_token=identity.run_token,
        fencing_token=identity.fencing_token, idempotency_key=slot.idempotency_key,
        status=value["status"], evidence=evidence, artifact_sha256=evidence_sha,
        summary=value.get("summary", ""))
    if len(_canonical(payload)) > slot.max_bytes:
        raise PolicyDenied("result_exceeds_slot")
    return payload

def submit(guard, raw, *, consume_approval=True):
    from .security import PolicyDenied
    value = arguments(raw)
    _, checked = guard.authorize_tool_call(TOOL, value, consume_approval=consume_approval)
    rule = next(rule for rule in guard.grant.tool_rules if rule.tool == TOOL)
    slot = rule.result_slot
    identity = guard.grant.identity
    if slot is None or slot.identity_sha256 != hashlib.sha256(_canonical(identity.to_json())).hexdigest():
        raise PolicyDenied("result_slot_unbound")
    payload = payload_for_slot(identity, slot, value)
    evidence_sha = payload["artifact_sha256"]
    encoded = _canonical(payload)
    if len(encoded) > slot.max_bytes:
        raise PolicyDenied("result_exceeds_slot")
    return publish_slot_payload(identity, slot, payload)

def publish_slot_payload(identity, slot, payload):
    """Host reconciliation may publish only the same original pinned candidate."""
    from .security import PolicyDenied
    if not isinstance(payload, dict):
        raise PolicyDenied("result_payload_invalid")
    raw = {name:payload.get(name) for name in ("status", "evidence", "summary")}
    expected = payload_for_slot(identity, slot, raw)
    if _canonical(payload) != _canonical(expected):
        raise PolicyDenied("result_payload_binding_changed")
    encoded = _canonical(payload)
    evidence_sha = payload["artifact_sha256"]
    fd = os.open(slot.path, os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        info = os.fstat(fd)
        named = Path(slot.path).lstat()
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid() or info.st_nlink != 1
                or info.st_mode & 0o777 != 0o600
                or (info.st_dev,info.st_ino) != (slot.device,slot.inode)
                or (named.st_dev,named.st_ino) != (slot.device,slot.inode)
                or info.st_size > slot.max_bytes):
            raise PolicyDenied("result_slot_replaced")
        existing = os.read(fd, slot.max_bytes + 1)
        # Durable intent metadata belongs to this same private inode. It pins
        # the entire first candidate before any result bytes are written.
        import errno
        intent = _canonical({"identity_sha256":slot.identity_sha256,
            "idempotency_key":slot.idempotency_key,
            "payload_sha256":hashlib.sha256(encoded).hexdigest()})
        attribute = "user.herdr.result_submission"
        try:
            committed_intent = os.getxattr(fd, attribute)
        except OSError as exc:
            if exc.errno != errno.ENODATA: raise
            committed_intent = None
        if committed_intent is None:
            # A complete legacy result authenticates itself against exact bytes;
            # an unauthenticated partial legacy result stays quarantined.
            if existing and existing != encoded:
                raise PolicyDenied("result_already_submitted")
            os.setxattr(fd, attribute, intent, flags=os.XATTR_CREATE)
            os.fsync(fd)
        elif committed_intent != intent:
            raise PolicyDenied("result_already_submitted")
        if existing and existing != encoded:
            # A prefix is an interrupted uncommitted candidate, not acceptance.
            # Repair only an exact prefix of this same identity-bound submission.
            if len(existing) >= len(encoded) or not encoded.startswith(existing):
                raise PolicyDenied("result_already_submitted")
            try:
                json.loads(existing)
            except (ValueError, UnicodeError):
                pass
            else:
                raise PolicyDenied("result_already_submitted")
        if existing != encoded:
            os.lseek(fd,0,os.SEEK_SET)
            pending=memoryview(encoded)
            while pending:
                written=os.write(fd,pending)
                if written<=0: raise OSError("result write made no progress")
                pending=pending[written:]
            os.ftruncate(fd,len(encoded))
        os.fsync(fd)
    finally:
        os.close(fd)
    return dict(submitted=True, evidence_sha256=evidence_sha,
                acceptance="requires_shared_85_acceptance")

SCHEMA = {"name":TOOL, "description":"Submit bounded result evidence for this exact task attempt. Submission is a candidate; shared host checks decide completion.",
          "parameters":{"type":"object","additionalProperties":False,"required":["status","evidence"],
              "properties":{"status":{"type":"string","enum":["completed","blocked","failed"]},
                            "evidence":{"type":"array","minItems":1,"maxItems":128,"items":{}},
                            "summary":{"type":"string","maxLength":8192}}}}

def register_result_tool(installation, registry, authorized_call, call_digest):
    from .security import PolicyDenied, SecurityError
    from .policy_launch import IDENTITY_ENV
    guard=installation.guard
    if TOOL not in guard.grant.scope.tools:
        return
    rule=next(rule for rule in guard.grant.tool_rules if rule.tool==TOOL)
    if rule.result_slot is None:
        raise SecurityError("result tool requires a bound attempt inode")
    if registry.get_entry(TOOL) is not None:
        raise SecurityError("result tool registration collision")
    def handle(raw,task_id=None):
        try:
            if not installation.installed:
                raise PolicyDenied("result_guard_inactive")
            if (os.environ.get("HERDR_DURABLE_SANDBOX") != "1" or
                    any(os.environ.get(key) != str(getattr(guard.grant.identity,field)) for field,key in IDENTITY_ENV.items())):
                raise PolicyDenied("result_identity_mismatch")
            guard.authorize_tool_call(TOOL, raw, caller_task_id=task_id,
                consume_approval=authorized_call.get() != (guard.grant.hash,TOOL,call_digest(TOOL,raw)))
            return json.dumps(submit(guard,raw,consume_approval=False),sort_keys=True)
        except PolicyDenied as exc:
            return json.dumps({"error":exc.reason})
        except (SecurityError,ValueError,OSError,TypeError,RecursionError):
            return json.dumps({"error":"result_contract_denied"})
    registry.register(name=TOOL,toolset=TOOLSET,schema=SCHEMA,handler=handle,
                      description=SCHEMA["description"],max_result_size_chars=2048)
    current=registry.get_entry(TOOL)
    if current is None or current.handler is not handle:
        raise SecurityError("result tool registration unavailable")
    installation.finalizers.append(lambda:registry.restore_registration(TOOL,current,None))
