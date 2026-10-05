"""Finite child write/decision contracts; TaskGraph remains execution authority."""
from __future__ import annotations
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from .context import SecretRedactor

class OwnershipError(ValueError):
    pass

def require(ok, code):
    if not ok: raise OwnershipError(code)

def name(value, maximum=256):
    require(isinstance(value,str) and re.fullmatch(r"[A-Za-z0-9._:/@+-]{1,"+str(maximum)+"}",value)
            and SecretRedactor().redact(value)==value,"ownership_name")

def sha(value):
    require(isinstance(value,str) and re.fullmatch(r"[0-9a-f]{64}",value),"ownership_digest")

def sequence(values,typ,maximum=64):
    require(isinstance(values,(tuple,list)) and len(values)<=maximum
            and all(isinstance(x,typ) for x in values),"ownership_bound")
    require(len(set(values))==len(values),"ownership_duplicate")
    return tuple(values)

@dataclass(frozen=True)
class WriteScope:
    kind: str
    key: str
    def __post_init__(self):
        require(self.kind in {"file","directory","resource"},"write_scope_kind")
        name(self.key,512)
        require(not self.key.startswith("/") and ":" not in self.key and
                all(x not in {"",".",".."} for x in self.key.split("/")),"write_scope_key")
    def contains(self,other):
        # Case folding is conservative for a shared contract spanning hosts.
        a,b=self.key.casefold(),other.key.casefold()
        if self.kind=="resource" or other.kind=="resource":
            return self.kind==other.kind and a==b
        return a==b or self.kind=="directory" and b.startswith(a+"/")
    def overlaps(self,other):
        return self.contains(other) or other.contains(self)

@dataclass(frozen=True)
class DecisionScope:
    key: str
    version: int
    contract_sha256: str
    def __post_init__(self):
        name(self.key)
        require(type(self.version) is int and 1<=self.version<=2**63-1,"decision_version")
        sha(self.contract_sha256)

@dataclass(frozen=True)
class FrozenContract:
    key: str
    version: int
    contract_sha256: str
    integration_owner: str
    def __post_init__(self):
        DecisionScope(self.key,self.version,self.contract_sha256)
        name(self.integration_owner)

@dataclass(frozen=True)
class ChildOwnership:
    write_scope: tuple[WriteScope,...]
    decision_scope: tuple[DecisionScope,...]
    hard_dependencies: tuple[str,...]
    shared_dependencies: tuple[FrozenContract,...]
    integration_owner: str
    handoff_ref: str
    def __post_init__(self):
        for attr,typ in (("write_scope",WriteScope),("decision_scope",DecisionScope),
                         ("hard_dependencies",str),("shared_dependencies",FrozenContract)):
            object.__setattr__(self,attr,sequence(getattr(self,attr),typ))
        for x in self.hard_dependencies: name(x)
        for x in (self.integration_owner,self.handoff_ref): name(x)
        for attr in ("decision_scope","shared_dependencies"):
            vals=getattr(self,attr)
            require(len({x.key for x in vals})==len(vals),"duplicate_decision_key")
        require(len(json.dumps(self.to_json(),sort_keys=True).encode())<=32768,"ownership_bytes")

    @property
    def read_only(self): return not self.write_scope and not self.decision_scope

    @property
    def hash(self):
        return hashlib.sha256(json.dumps(self.to_json(),sort_keys=True,separators=(",",":")).encode()).hexdigest()

    def to_json(self):
        value=asdict(self)
        for key in ("write_scope","decision_scope","hard_dependencies","shared_dependencies"):
            value[key]=list(value[key])
        return value

    @classmethod
    def from_json(cls,value):
        require(isinstance(value,dict) and set(value)==set(cls.__dataclass_fields__),"closed_child_ownership")
        def records(key,typ):
            raw=value[key]
            require(isinstance(raw,list) and len(raw)<=64,"ownership_bound")
            require(all(isinstance(x,dict) and set(x)==set(typ.__dataclass_fields__) for x in raw),"closed_scope")
            try:return tuple(typ(**x) for x in raw)
            except TypeError: raise OwnershipError("scope_type") from None
        return cls(records("write_scope",WriteScope),records("decision_scope",DecisionScope),
                   value["hard_dependencies"],records("shared_dependencies",FrozenContract),
                   value["integration_owner"],value["handoff_ref"])

    def conflict(self,other):
        require(isinstance(other,ChildOwnership),"typed_ownership")
        if any(a.overlaps(b) for a in self.write_scope for b in other.write_scope):
            return "write_scope_conflict"
        if set(x.key for x in self.decision_scope)&set(x.key for x in other.decision_scope):
            return "decision_scope_conflict"
        # A contract writer conflicts with readers of that frozen contract too.
        if (set(x.key for x in self.decision_scope)&set(x.key for x in other.shared_dependencies)
            or set(x.key for x in other.decision_scope)&set(x.key for x in self.shared_dependencies)):
            return "shared_contract_writer"
        return None


def ownership_schema():
    def record(fields):
        return {"type":"object","additionalProperties":False,"required":list(fields),"properties":fields}
    token={"type":"string","minLength":1,"maxLength":256}
    digest={"type":"string","pattern":"^[0-9a-f]{64}$"}
    version={"type":"integer","minimum":1,"maximum":2**63-1}
    decision={"key":token,"version":version,"contract_sha256":digest}
    def array(items):
        return {"type":"array","maxItems":64,"uniqueItems":True,"items":items}
    return record({
        "write_scope":array(record({"kind":{"enum":["file","directory","resource"]},
            "key":{"type":"string","minLength":1,"maxLength":512}})),
        "decision_scope":array(record(decision)),
        "hard_dependencies":array(token),
        "shared_dependencies":array(record({**decision,"integration_owner":token})),
        "integration_owner":token,"handoff_ref":token,
    })


class OwnershipRegistry:
    """Host resource reservations shared by parent ledgers, never an execution queue.

    Model/tool handlers cannot publish contracts or release claims. Those mutations
    require an injected host verifier against canonical TaskGraph/evidence truth.
    A crash retains a reservation even before its claim identity is bound.
    """
    MAX_BYTES=4*1024*1024
    MAX_RECORDS=1024

    def __init__(self,root,*,verify_contract=None,verify_release=None,verify_legacy=None):
        import os,stat
        from pathlib import Path
        self.root=Path(root).absolute()
        self.verify_contract,self.verify_release=verify_contract,verify_release
        require(verify_legacy is None or callable(verify_legacy),"ownership_host_inventory")
        self.verify_legacy=verify_legacy
        require(self.root.resolve(strict=True)==self.root,"ownership_symlink_root")
        info=self.root.lstat()
        require(stat.S_ISDIR(info.st_mode) and info.st_uid==os.getuid()
                and not info.st_mode&0o022,"ownership_host_root")
        self.directory=self.root/"child-ownership"
        self.directory.mkdir(mode=0o700,exist_ok=True)
        info=self.directory.lstat()
        require(stat.S_ISDIR(info.st_mode) and info.st_uid==os.getuid()
                and stat.S_IMODE(info.st_mode)==0o700,"ownership_private_directory")
        self._directory_identity=(info.st_dev,info.st_ino)
        parent=os.open(self.root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        try:os.fsync(parent)
        finally:os.close(parent)

    @staticmethod
    def key(parent,task_id):
        from .security import InvocationIdentity
        require(isinstance(parent,InvocationIdentity),"ownership_parent_identity")
        name(task_id)
        return hashlib.sha256(json.dumps({"parent":parent.to_json(),"task_id":task_id},
            sort_keys=True,separators=(",",":")).encode()).hexdigest()

    def _transaction(self):
        import os,stat,fcntl
        from contextlib import contextmanager
        @contextmanager
        def locked():
            directory=os.open(self.directory,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
            lock=None
            try:
                info=os.fstat(directory)
                require(info.st_uid==os.getuid() and stat.S_IMODE(info.st_mode)==0o700
                        and (info.st_dev,info.st_ino)==self._directory_identity,"ownership_private_directory")
                lock=os.open("registry.lock",os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW|os.O_CLOEXEC|os.O_NONBLOCK,0o600,dir_fd=directory)
                self._private_file(lock)
                fcntl.flock(lock,fcntl.LOCK_EX)
                os.fsync(lock);os.fsync(directory)
                data=self._read(directory)
                yield data
                self._write(directory,data)
            finally:
                if lock is not None:os.close(lock)
                os.close(directory)
        return locked()

    @staticmethod
    def _private_file(fd):
        import os,stat
        info=os.fstat(fd)
        require(stat.S_ISREG(info.st_mode) and info.st_uid==os.getuid()
                and stat.S_IMODE(info.st_mode)==0o600 and info.st_nlink==1,"ownership_private_file")
        return info

    def _read(self,directory):
        import os
        from .security import InvocationIdentity
        try:fd=os.open("registry.json",os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC|os.O_NONBLOCK,dir_fd=directory)
        except FileNotFoundError:return {"version":1,"reservations":{},"contracts":{}}
        try:
            require(self._private_file(fd).st_size<=self.MAX_BYTES,"ownership_store_bound")
            chunks=[];remaining=self.MAX_BYTES+1
            while remaining:
                part=os.read(fd,min(65536,remaining))
                if not part:break
                chunks.append(part);remaining-=len(part)
            raw=b"".join(chunks);require(len(raw)<=self.MAX_BYTES,"ownership_store_bound")
            def unique(pairs):
                value={}
                for key,item in pairs:
                    require(key not in value,"ownership_duplicate_store_key");value[key]=item
                return value
            data=json.loads(raw,object_pairs_hook=unique,parse_constant=lambda _:require(False,"ownership_nonfinite"))
        except OwnershipError:raise
        except (ValueError,UnicodeError):raise OwnershipError("ownership_corrupt_store") from None
        finally:os.close(fd)
        require(isinstance(data,dict) and set(data)=={"version","reservations","contracts"}
                and type(data["version"]) is int and data["version"]==1,"ownership_store_schema")
        require(isinstance(data["reservations"],dict) and len(data["reservations"])<=self.MAX_RECORDS
                and isinstance(data["contracts"],dict) and len(data["contracts"])<=self.MAX_RECORDS,"ownership_store_bound")
        for key,entry in data["contracts"].items():
            sha(key)
            require(isinstance(entry,dict) and set(entry)=={"owner","contract"},"ownership_contract_schema")
            owner=InvocationIdentity.from_dict(entry["owner"])
            contract=FrozenContract(**entry["contract"])
            require(contract.integration_owner==owner.task_id
                    and key==self.contract_key(owner.consumer,contract.key),"ownership_contract_owner")
        for key,row in data["reservations"].items():
            sha(key)
            require(isinstance(row,dict) and set(row)=={"parent","task_id","ownership","read_only","identity","state"},
                    "ownership_reservation_schema")
            parent=InvocationIdentity.from_dict(row["parent"])
            require(key==self.key(parent,row["task_id"]) and type(row["read_only"]) is bool
                    and row["state"] in {"reserved","claimed","released","quarantined"},"ownership_reservation_schema")
            if row["ownership"] is not None:
                owner=ChildOwnership.from_json(row["ownership"])
                require(owner.read_only==row["read_only"] and owner.integration_owner==parent.task_id,"ownership_parent_owner")
            if row["identity"] is not None:
                child=InvocationIdentity.from_dict(row["identity"])
                require((child.consumer,child.parent_task_id,child.parent_agent_id,child.task_id)==
                        (parent.consumer,parent.task_id,parent.agent_id,row["task_id"]),"ownership_claim_identity")
        return data

    def _write(self,directory,data):
        import os,uuid
        raw=json.dumps(data,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
        require(len(raw)<=self.MAX_BYTES,"ownership_store_bound")
        temporary=".registry-"+uuid.uuid4().hex
        fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600,dir_fd=directory)
        try:
            try:
                offset=0
                while offset<len(raw):
                    size=os.write(fd,raw[offset:]);require(size>0,"ownership_short_write");offset+=size
                os.fsync(fd)
            finally:os.close(fd)
            os.replace(temporary,"registry.json",src_dir_fd=directory,dst_dir_fd=directory)
            os.fsync(directory)
        finally:
            try:os.unlink(temporary,dir_fd=directory)
            except FileNotFoundError:pass

    @staticmethod
    def contract_key(consumer,key):
        return hashlib.sha256(json.dumps([consumer,key],separators=(",",":")).encode()).hexdigest()

    @classmethod
    def _contract_current(cls,data,ownership,consumer):
        if ownership is None:return True
        for ref in ownership.shared_dependencies:
            stored=data["contracts"].get(cls.contract_key(consumer,ref.key))
            if stored is None or stored["contract"]!=asdict(ref):return False
        for ref in ownership.decision_scope:
            stored=data["contracts"].get(cls.contract_key(consumer,ref.key))
            if stored is not None and any(stored["contract"][key]!=getattr(ref,key)
                    for key in ("version","contract_sha256")):return False
        return True

    def reserve(self,parent,task_id,ownership,*,read_only=False):
        require(ownership is None or isinstance(ownership,ChildOwnership),"typed_ownership")
        require(type(read_only) is bool,"ownership_read_only")
        if ownership is not None:
            require(ownership.integration_owner==parent.task_id,"ownership_integration_owner")
            read_only=ownership.read_only
        key=self.key(parent,task_id)
        row={"parent":parent.to_json(),"task_id":task_id,
             "ownership":None if ownership is None else ownership.to_json(),
             "read_only":read_only,"identity":None,"state":"reserved"}
        with self._transaction() as data:
            if not read_only and self.verify_legacy is not None:
                require(self.verify_legacy(data) is True,"ownership_legacy_writer_quarantined")
            previous=data["reservations"].get(key)
            if previous is not None:
                require(all(previous[k]==row[k] for k in ("parent","task_id","ownership","read_only")),
                        "ownership_idempotency_conflict")
                require(previous["state"] in {"reserved","claimed"} and self._contract_current(data,ownership,parent.consumer),
                        "ownership_stale_or_released")
                return key
            require(len(data["reservations"])<self.MAX_RECORDS,"ownership_capacity")
            require(self._contract_current(data,ownership,parent.consumer),"ownership_shared_contract_stale")
            for other in data["reservations"].values():
                if other["state"]=="released" or other["parent"]["consumer"]!=parent.consumer:continue
                known=ChildOwnership.from_json(other["ownership"]) if other["ownership"] is not None else None
                if ownership is None or known is None:
                    require(read_only and other["read_only"],"ownership_unknown_serialize")
                else:
                    conflict=ownership.conflict(known)
                    require(conflict is None,conflict or "ownership_conflict")
            data["reservations"][key]=row
        return key

    def bind_claim(self,key,identity):
        from .security import InvocationIdentity
        sha(key);require(isinstance(identity,InvocationIdentity),"ownership_claim_identity")
        with self._transaction() as data:
            row=data["reservations"].get(key);require(row is not None,"ownership_unreserved")
            parent=InvocationIdentity.from_dict(row["parent"])
            require((identity.consumer,identity.parent_agent_id,identity.parent_task_id,identity.task_id)==
                    (parent.consumer,parent.agent_id,parent.task_id,row["task_id"]),"ownership_claim_identity")
            require(row["state"] in {"reserved","claimed"} and
                    row["identity"] in (None,identity.to_json()),"ownership_claim_rebind")
            owner=ChildOwnership.from_json(row["ownership"]) if row["ownership"] is not None else None
            require(self._contract_current(data,owner,parent.consumer),"ownership_shared_contract_stale")
            row["identity"]=identity.to_json();row["state"]="claimed"

    def require_current(self,key,identity):
        sha(key)
        with self._transaction() as data:
            row=data["reservations"].get(key)
            require(row is not None and row["state"]=="claimed"
                    and row["identity"]==identity.to_json(),"ownership_claim_unavailable")
            if not row["read_only"] and self.verify_legacy is not None:
                require(self.verify_legacy(data) is True,"ownership_legacy_writer_quarantined")
            owner=ChildOwnership.from_json(row["ownership"]) if row["ownership"] is not None else None
            require(self._contract_current(data,owner,row["parent"]["consumer"]),"ownership_shared_contract_stale")
        return True

    def publish_contract(self,owner,contract,evidence):
        require(isinstance(contract,FrozenContract) and contract.integration_owner==owner.task_id,"ownership_contract_owner")
        require(callable(self.verify_contract) and self.verify_contract(owner,contract,evidence) is True,
                "ownership_host_contract_evidence")
        with self._transaction() as data:
            key=self.contract_key(owner.consumer,contract.key)
            previous=data["contracts"].get(key)
            if previous is not None:
                require(previous["owner"]==owner.to_json(),"ownership_contract_single_owner")
                if previous["contract"]==asdict(contract):return
                require(contract.version>previous["contract"]["version"],"ownership_contract_monotonic_version")
            data["contracts"][key]={"owner":owner.to_json(),"contract":asdict(contract)}
            require(len(data["contracts"])<=self.MAX_RECORDS,"ownership_contract_capacity")
            for row in data["reservations"].values():
                if row["state"]=="released" or row["ownership"] is None:continue
                ownership=ChildOwnership.from_json(row["ownership"])
                if not self._contract_current(data,ownership,row["parent"]["consumer"]):row["state"]="quarantined"

    def release(self,key,identity,evidence):
        sha(key)
        require(callable(self.verify_release) and self.verify_release(identity,evidence) is True,
                "ownership_host_release_evidence")
        with self._transaction() as data:
            row=data["reservations"].get(key)
            require(row is not None and row["identity"]==identity.to_json(),"ownership_release_identity")
            row["state"]="released"

    def snapshot(self):
        with self._transaction() as data:
            return json.loads(json.dumps(data))
