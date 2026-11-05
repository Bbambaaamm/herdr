"""Private per-attempt acceptance intents and bounded legacy migration.

Historical flat bundles remain immutable. A sealed intent is host proof, never
worker data. New publication reserves that proof before creating its flat alias.
Linux directory cookies are resumed only while source inode/metadata is unchanged;
all participating publishers finish migration before changing that directory.
"""
import ctypes
import errno
import fcntl
import json
import os
import re
import stat
import tempfile
import time
from contextlib import contextmanager

from .evidence import EvidenceError, EvidenceMissing, EvidenceUnavailable, binding, canonical, digest

SHA = re.compile(r"[0-9a-f]{64}")
MAX_BYTES = 2_100_000

def private_directory(path):
    if not os.path.lexists(path):
        path.mkdir(mode=0o700)
    info=path.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid() or info.st_mode & 0o077:
        raise EvidenceError("acceptance index directory is not private")

def read_document(path):
    try:
        fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise EvidenceError("acceptance index cannot be safely opened") from exc
    try:
        info=os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid!=os.geteuid()
                or info.st_nlink!=1 or info.st_mode & 0o777!=0o600 or info.st_size>MAX_BYTES):
            raise EvidenceError("acceptance index file is not private and bounded")
        chunks=[];remaining=MAX_BYTES+1
        while remaining:
            chunk=os.read(fd,min(remaining,1048576))
            if not chunk:break
            chunks.append(chunk);remaining-=len(chunk)
        raw=b"".join(chunks)
        after=os.fstat(fd);named=path.lstat()
        if ((info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns,info.st_ctime_ns)
                !=(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns)
                or (named.st_dev,named.st_ino)!=(info.st_dev,info.st_ino)):
            raise EvidenceError("acceptance index changed during read")
        value=json.loads(raw)
        if len(raw)>MAX_BYTES or canonical(value)!=raw or not isinstance(value,dict):
            raise EvidenceError("invalid acceptance index encoding")
        return value
    except (ValueError,TypeError,UnicodeError,RecursionError) as exc:
        raise EvidenceError("invalid acceptance index encoding") from exc
    finally:os.close(fd)

def sync(path):
    fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:os.fsync(fd)
    finally:os.close(fd)

def write_document(path, document, *, immutable=False):
    existing=read_document(path)
    if immutable and existing is not None:
        if existing!=document:raise EvidenceError("conflicting immutable acceptance intent")
        sync(path.parent)
        return
    raw=canonical(document)
    if len(raw)>MAX_BYTES:raise EvidenceError("acceptance index exceeds record bound")
    fd,tmp=tempfile.mkstemp(prefix=".index-publication-",dir=path.parent)
    try:
        with os.fdopen(fd,"wb") as handle:
            handle.write(raw);handle.flush();os.fsync(handle.fileno())
        # All writers hold the private index lock. An existing intent is checked
        # above and never replaced with a different payload.
        os.replace(tmp,path);sync(path.parent)
    finally:
        if os.path.lexists(tmp):os.unlink(tmp)

def source_identity(root):
    info=root.lstat()
    return [info.st_dev,info.st_ino,info.st_mtime_ns,info.st_ctime_ns]

def directory_batch(root,cookie,maximum):
    """Use native Linux telldir cookies; do not rescan an unbounded prefix."""
    class Dirent(ctypes.Structure):
        _fields_=[("inode",ctypes.c_ulong),("offset",ctypes.c_long),
                  ("length",ctypes.c_ushort),("kind",ctypes.c_ubyte),("name",ctypes.c_char*256)]
    lib=ctypes.CDLL(None,use_errno=True)
    lib.fdopendir.argtypes=[ctypes.c_int];lib.fdopendir.restype=ctypes.c_void_p
    lib.readdir.argtypes=[ctypes.c_void_p];lib.readdir.restype=ctypes.POINTER(Dirent)
    lib.seekdir.argtypes=[ctypes.c_void_p,ctypes.c_long]
    lib.telldir.argtypes=[ctypes.c_void_p];lib.telldir.restype=ctypes.c_long
    lib.closedir.argtypes=[ctypes.c_void_p]
    fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    stream=lib.fdopendir(fd)
    if not stream:
        os.close(fd);raise EvidenceUnavailable("legacy directory scan unavailable")
    try:
        lib.seekdir(stream,cookie)
        for _ in range(maximum):
            ctypes.set_errno(0);row=lib.readdir(stream)
            if not row:
                if ctypes.get_errno():raise OSError(ctypes.get_errno(),"legacy directory read failed")
                yield None,lib.telldir(stream)
                return
            name=os.fsdecode(row.contents.name)
            yield name,lib.telldir(stream)
    finally:lib.closedir(stream)

class AcceptedIndex:
    def __init__(self,store):
        self.store=store
        self.root=store.root/".acceptance-index"
        private_directory(self.root)
        self.receipts=self.root/"receipts"
        private_directory(self.receipts)

    @contextmanager
    def locked(self):
        fd=os.open(self.root/"writer.lock",os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW|os.O_NONBLOCK,0o600)
        try:
            info=os.fstat(fd)
            if (not stat.S_ISREG(info.st_mode) or info.st_uid!=os.geteuid()
                    or info.st_nlink!=1 or info.st_mode & 0o777!=0o600):
                raise EvidenceError("acceptance index lock is not private")
            fcntl.flock(fd,fcntl.LOCK_EX)
            yield
        finally:os.close(fd)

    def receipt_path(self,key):
        if not isinstance(key,str) or not SHA.fullmatch(key):raise EvidenceError("invalid acceptance index key")
        bucket=self.receipts/key[:2];private_directory(bucket)
        return bucket/(key+".json")

    def register(self,address,payload):
        identity=payload.get("identity");plan_hash=payload.get("plan_hash")
        # Non-semantic codec objects cannot match a task acceptance binding.
        if not isinstance(identity,dict) or not isinstance(plan_hash,str) or not SHA.fullmatch(plan_hash):
            return
        if (set(identity)!={"id","run_token","attempt","idempotency_key","fencing_token"}
                or binding({**identity,"attempt_id":identity.get("attempt")})!=identity
                or any(len(identity[k])>1024 for k in ("id","run_token","idempotency_key"))):
            raise EvidenceError("invalid indexed completion identity")
        key=digest({"identity":identity,"plan_hash":plan_hash})
        if payload.get("level")=="verified_worker_result":
            legacy=digest({"identity":identity,"plan_hash":plan_hash,"artifact":payload.get("artifact")})
        elif payload.get("level")=="control_cycle":
            proof=payload.get("proof")
            if not isinstance(proof,dict):raise EvidenceError("invalid legacy control proof")
            result_hash=proof.get("result_digest")
            if not isinstance(result_hash,str) or not SHA.fullmatch(result_hash):
                raise EvidenceError("invalid legacy control result digest")
            legacy=digest({"identity":identity,"plan_hash":plan_hash,"result_hash":result_hash})
        else:raise EvidenceError("unsupported indexed completion level")
        if address not in {key,legacy}:raise EvidenceError("legacy completion address does not bind its payload")
        comparable=digest({k:v for k,v in payload.items() if k!="publication_hash"})
        path=self.receipt_path(key);old=read_document(path)
        if old is not None:
            self.validate_receipt(key,old)
            if old["comparable_sha256"]!=comparable:
                raise EvidenceError("conflicting legacy and unique attempt records require trusted replan")
            return
        row={"version":1,"key":key,"address":address,"comparable_sha256":comparable,
             "payload":payload,"payload_sha256":digest(payload)}
        write_document(path,row,immutable=True)

    def validate_receipt(self,key,row):
        if (set(row)!={"version","key","address","comparable_sha256","payload","payload_sha256"}
                or type(row["version"]) is not int or row["version"]!=1 or row["key"]!=key
                or not isinstance(row["address"],str) or not SHA.fullmatch(row["address"])
                or not isinstance(row["payload"],dict) or digest(row["payload"])!=row["payload_sha256"]
                or digest({k:v for k,v in row["payload"].items() if k!="publication_hash"})!=row["comparable_sha256"]
                or digest({k:row["payload"].get(k) for k in ("identity","plan_hash")})!=key):
            raise EvidenceError("acceptance index receipt binding is invalid")
        payload=row["payload"]
        identity=payload.get("identity")
        if not isinstance(identity,dict):
            raise EvidenceError("acceptance intent identity is invalid")
        if payload.get("level")=="verified_worker_result":
            legacy=digest({"identity":identity,"plan_hash":payload.get("plan_hash"),"artifact":payload.get("artifact")})
        elif payload.get("level")=="control_cycle" and isinstance(payload.get("proof"),dict):
            result_hash=payload["proof"].get("result_digest")
            if not isinstance(result_hash,str) or not SHA.fullmatch(result_hash):
                raise EvidenceError("acceptance intent control proof is invalid")
            legacy=digest({"identity":identity,"plan_hash":payload.get("plan_hash"),"result_hash":result_hash})
        else:raise EvidenceError("acceptance intent level is invalid")
        if row["address"] not in {key,legacy}:
            raise EvidenceError("acceptance intent address is not bound to its original payload")

    def ready(self):
        progress=self.root/"migration.json"
        state=read_document(progress)
        source=source_identity(self.store.root)
        if state is not None:
            if (set(state)!={"version","source","cookie","complete"} or type(state["version"]) is not int or state["version"]!=1
                    or not isinstance(state["source"],list) or len(state["source"])!=4
                    or any(type(x) is not int or x<0 for x in state["source"])
                    or type(state["cookie"]) is not int or not 0<=state["cookie"]<2**63
                    or type(state["complete"]) is not bool):
                raise EvidenceError("invalid durable acceptance migration checkpoint")
            if state["complete"]:return
        if state is None or state["source"]!=source:
            state={"version":1,"source":source,"cookie":0,"complete":False}
        deadline=time.monotonic()+1
        total=0
        for name,cookie in directory_batch(self.store.root,state["cookie"],512):
            if name is None:
                state["complete"]=True;break
            state["cookie"]=cookie
            if name.startswith("accepted-") and name.endswith(".json"):
                address=name[len("accepted-"):-len(".json")]
                if not SHA.fullmatch(address):raise EvidenceError("invalid legacy evidence address")
                record=self.store.read("accepted",address)
                total+=len(canonical(record));self.register(address,record)
            if total>=8_000_000 or time.monotonic()>=deadline:break
        if source_identity(self.store.root)!=source:
            # Never bless an incomplete scan while an old writer mutates source.
            state={"version":1,"source":source_identity(self.store.root),"cookie":0,"complete":False}
        write_document(progress,state)
        if not state["complete"]:
            raise EvidenceUnavailable("bounded legacy acceptance migration is pending on this same attempt")

    def prepare_publication(self,kind,key,payload):
        with self.locked():
            self.ready()
            if kind=="accepted":self.register(key,payload)

    def lookup(self,identity,plan_hash):
        key=digest({"identity":identity,"plan_hash":plan_hash})
        with self.locked():
            self.ready()
            row=read_document(self.receipt_path(key))
            try:unique=self.store.read("accepted",key)
            except EvidenceMissing:unique=None
            if row is None:
                if unique is not None:
                    self.register(key,unique)
                return unique,False
            self.validate_receipt(key,row)
            if unique is not None:
                if digest({k:v for k,v in unique.items() if k!="publication_hash"})!=row["comparable_sha256"]:
                    raise EvidenceError("conflicting legacy and unique attempt records require trusted replan")
                return unique,False
            if row["address"]==key:
                # Resume the exact protected intent after a crash between the
                # intent fsync and flat bundle link, without repeating validators.
                self.store._publish("accepted",key,row["payload"],register_index=False)
                return row["payload"],False
            try:legacy=self.store.read("accepted",row["address"])
            except EvidenceMissing as exc:raise EvidenceError("indexed legacy proof disappeared") from exc
            if legacy!=row["payload"]:raise EvidenceError("indexed legacy proof changed")
            return legacy,True
