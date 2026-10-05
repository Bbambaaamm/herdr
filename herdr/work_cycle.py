"""Bounded work contracts using the existing scheduler audit and ArtifactRef."""
from __future__ import annotations

import ast
import copy
import hashlib
import json
import os
import re
import stat
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path, PurePosixPath

from .evidence import EvidenceError, EvidenceUnavailable, canonical, digest, read_only_git
from .policy_launch import _open_relative
from .security import InvocationIdentity
from .workspace import ArtifactRef, WorkspaceManager

_SHA = re.compile(r"^[0-9a-f]{64}$")
_GIT = re.compile(r"^[0-9a-f]{40}$")


class WorkContractError(EvidenceError):
    code = "work_contract_invalid"


class IntentInfoRequired(WorkContractError):
    code = "info_required"


def require(condition, reason):
    if not condition:
        raise WorkContractError(reason)


def relative(path):
    require(isinstance(path, str) and path and len(path) <= 1024 and "\\" not in path
            and "\0" not in path and not PurePosixPath(path).is_absolute()
            and all(x not in {"", ".", "..", ".git"} for x in path.split("/")),
            "work scope path invalid")
    return path


class WorkMode(StrEnum):
    REPAIR = "repair"
    EXPERIMENT = "experiment"


class WorkPhase(StrEnum):
    PREPARE = "prepare"
    DISCOVER = "discover"
    PLAN_GATE = "plan_gate"
    WORK = "work"
    VERIFY = "verify"
    HYGIENE = "hygiene"
    HANDOFF = "handoff"
    FINISHED = "finished"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class FileScope:
    path: str
    subtree: bool = False
    symbols: tuple[str, ...] = ()

    def __post_init__(self):
        relative(self.path)
        require(type(self.subtree) is bool, "scope subtree must be explicit")
        object.__setattr__(self, "symbols", tuple(self.symbols))
        require(len(self.symbols) <= 128 and len(set(self.symbols)) == len(self.symbols)
                and all(isinstance(x, str) and re.fullmatch(r"(?:[A-Za-z_][A-Za-z0-9_]*\.)*(?:[A-Za-z_][A-Za-z0-9_]*|\$module)", x)
                        for x in self.symbols), "symbol scope invalid")
        require(not self.symbols or self.path.endswith(".py") and not self.subtree,
                "symbol-scoped language is unsupported")

    def covers(self, path):
        return path == self.path or self.subtree and path.startswith(self.path + "/")


@dataclass(frozen=True)
class ValidationCheck:
    id: str
    command: tuple[str, ...]
    criterion_ids: tuple[str, ...]
    expected_baseline_failure: bool = False
    timeout_seconds: int = 300
    output_bytes: int = 1_048_576
    expected_baseline_output_sha256: str | None = None
    protected_inputs: tuple[tuple[str,str], ...] = ()

    def __post_init__(self):
        object.__setattr__(self, "command", tuple(self.command))
        object.__setattr__(self, "criterion_ids", tuple(self.criterion_ids))
        object.__setattr__(self, "protected_inputs", tuple(tuple(x) for x in self.protected_inputs))
        require(len(self.protected_inputs)<=256 and len({x[0] for x in self.protected_inputs})==len(self.protected_inputs),
                "verification input manifest invalid")
        for path,sha in self.protected_inputs:
            relative(path)
            require(isinstance(sha,str) and _SHA.fullmatch(sha),"verification input digest invalid")
        require(isinstance(self.id, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", self.id),
                "check identity invalid")
        require(1 <= len(self.command) <= 128 and Path(self.command[0]).is_absolute()
                and all(isinstance(x, str) and "\0" not in x and len(x) <= 8192 for x in self.command),
                "approved check command invalid")
        require(self.criterion_ids and len(set(self.criterion_ids)) == len(self.criterion_ids)
                and all(isinstance(x, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", x)
                        for x in self.criterion_ids), "check criteria invalid")
        require(type(self.expected_baseline_failure) is bool
                and type(self.timeout_seconds) is int and 1 <= self.timeout_seconds <= 900
                and type(self.output_bytes) is int and 1 <= self.output_bytes <= 1_048_576,
                "check limits invalid")
        require(not self.expected_baseline_failure or isinstance(self.expected_baseline_output_sha256,str)
                and _SHA.fullmatch(self.expected_baseline_output_sha256),
                "expected baseline failure needs a predeclared output fingerprint")


@dataclass(frozen=True)
class WorkPlan:
    identity: InvocationIdentity
    spec_version: str
    spec_sha256: str
    policy_version: str
    base_sha: str
    files: tuple[FileScope, ...]
    criteria: tuple[str, ...]
    checks: tuple[ValidationCheck, ...]
    grant_sha256: str
    environment_sha256: str
    budget_reference: str
    mode: WorkMode = WorkMode.REPAIR
    baseline_omission_reason: str | None = None
    phases: tuple[str, ...] = ("work", "verify", "handoff")
    prerequisite_commits: tuple[str, ...] = ()
    purpose: str = "bounded approved implementation"
    baseline_policy: str = "required"
    planning: object = None
    hygiene_sha256: str | None = None

    def __post_init__(self):
        require(isinstance(self.identity, InvocationIdentity), "admitted work identity required")
        for name in ("files", "criteria", "checks", "phases", "prerequisite_commits"):
            object.__setattr__(self, name, tuple(getattr(self, name)))
        require(isinstance(self.mode, WorkMode), "typed work mode required")
        require(self.mode is WorkMode.REPAIR, "experiment series authority is not yet configured")
        require(all(isinstance(x, str) and re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", x)
                    for x in (self.spec_version, self.policy_version)), "work versions invalid")
        require(all(isinstance(x, str) and _SHA.fullmatch(x) for x in (
            self.spec_sha256, self.grant_sha256, self.environment_sha256, self.budget_reference)),
            "work authority references invalid")
        require(isinstance(self.base_sha, str) and _GIT.fullmatch(self.base_sha), "exact base required")
        require(1 <= len(self.files) <= 256 and all(isinstance(x, FileScope) for x in self.files)
                and len({x.path for x in self.files}) == len(self.files), "file scope required")
        require(1 <= len(self.criteria) <= 128 and len(set(self.criteria)) == len(self.criteria)
                and all(isinstance(x, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", x)
                        for x in self.criteria), "acceptance criteria invalid")
        require(1 <= len(self.checks) <= 32 and all(isinstance(x, ValidationCheck) for x in self.checks)
                and len({x.id for x in self.checks}) == len(self.checks)
                and set(self.criteria) == {x for check in self.checks for x in check.criterion_ids},
                "every criterion needs its approved check")
        require(set(self.phases) <= {"discovery", "architecture", "data_model", "work", "verify", "release", "handoff"}
                and {"work", "verify", "handoff"} <= set(self.phases)
                and len(self.phases) == len(set(self.phases)), "phase template invalid")
        require(len(self.prerequisite_commits) <= 128
                and all(isinstance(x, str) and _GIT.fullmatch(x) for x in self.prerequisite_commits),
                "prerequisite commits invalid")
        require(self.baseline_omission_reason is None or isinstance(self.baseline_omission_reason, str)
                and 1 <= len(self.baseline_omission_reason) <= 512, "baseline omission must be explicit")
        require(self.baseline_policy in {"required","host-approved-omission"}
                and (self.baseline_omission_reason is None) == (self.baseline_policy == "required"),
                "baseline omission needs explicit host policy and reason")
        require(isinstance(self.purpose,str) and 1 <= len(self.purpose) <= 1024, "work purpose required")
        order = ("discovery","architecture","data_model","work","verify","release","handoff")
        require(self.phases == tuple(x for x in order if x in self.phases), "work phase order invalid")
        if self.planning is not None:
            from .work_planning import PlanArtifact
            if isinstance(self.planning, dict):
                object.__setattr__(self, "planning", PlanArtifact(self.planning))
            require(isinstance(self.planning, PlanArtifact), "immutable planning artifact required")
            self.planning.require_binding(self)
        require(self.hygiene_sha256 is None or isinstance(self.hygiene_sha256, str)
                and _SHA.fullmatch(self.hygiene_sha256), "hygiene policy binding invalid")
        require(len(canonical(self.to_json())) <= 131072, "work plan exceeds bound")

    def to_json(self):
        value = asdict(self)
        if self.planning is not None:
            value["planning"] = self.planning.to_json()
        if self.hygiene_sha256 is not None:
            return {"version": 3, **value}
        value.pop("hygiene_sha256")
        if self.planning is None:
            value.pop("planning")
            return {"version": 1, **value}
        return {"version": 2, **value}

    @classmethod
    def from_json(cls, raw):
        from dataclasses import fields
        names = {x.name for x in fields(cls)}
        require(isinstance(raw, dict) and type(raw.get("version")) is int
                and ((raw["version"] == 1 and set(raw) == {"version", *(names - {"planning", "hygiene_sha256"})})
                     or (raw["version"] == 2 and set(raw) == {"version", *(names - {"hygiene_sha256"})}
                         and isinstance(raw["planning"], dict))
                     or (raw["version"] == 3 and set(raw) == {"version", *names}
                         and isinstance(raw["hygiene_sha256"], str))), "work plan schema invalid")
        return cls(**{**{k:v for k,v in raw.items() if k!="version"},
            "identity":InvocationIdentity.from_dict(raw["identity"]),
            "mode":WorkMode(raw["mode"]),
            "files":tuple(FileScope(**x) for x in raw["files"]),
            "checks":tuple(ValidationCheck(**x) for x in raw["checks"])})

    @property
    def hash(self):
        return digest(self.to_json())


@dataclass(frozen=True)
class CheckResult:
    check_id: str
    plan_sha256: str
    environment_sha256: str
    tree_sha256: str
    exit_code: int
    output_sha256: str
    truncated: bool
    duration_ms: int
    isolation_sha256: str

    def __post_init__(self):
        require(all(isinstance(x, str) and _SHA.fullmatch(x) for x in (
            self.plan_sha256, self.environment_sha256, self.tree_sha256, self.output_sha256, self.isolation_sha256)),
            "check proof digest invalid")
        require(type(self.exit_code) is int and -128 <= self.exit_code <= 255
                and type(self.truncated) is bool and type(self.duration_ms) is int
                and 0 <= self.duration_ms <= 901000, "check proof limits invalid")

    @property
    def hash(self):
        return digest(asdict(self))


def tree_snapshot(root, *, git=None, max_bytes=67_108_864):
    """Read physical tracked/unignored bytes without clean filters or symlinks."""
    root = Path(root)
    query = git or read_only_git(root)
    names = query(["ls-files", "-z", "--cached", "--others", "--exclude-standard"]).split("\0")
    names = sorted(set(x for x in names if x))
    require(len(names) <= 4096, "work tree file count exceeded")
    directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    records, total = {}, 0
    try:
        for name in names:
            relative(name)
            try:
                fd = _open_relative(directory, name)
            except FileNotFoundError:
                continue
            try:
                before = os.fstat(fd)
                require(stat.S_ISREG(before.st_mode), "work tree contains a nonregular input")
                total += before.st_size
                require(total <= max_bytes, "work tree bytes exceeded")
                hasher, read = hashlib.sha256(), 0
                while True:
                    chunk = os.read(fd, min(1_048_576, max_bytes-read+1))
                    if not chunk:
                        break
                    hasher.update(chunk)
                    read += len(chunk)
                    require(read <= before.st_size and read <= max_bytes, "work input grew during read")
                after = os.fstat(fd)
                require((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)
                        == (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns)
                        and read == before.st_size, "work input changed during read")
                records[name] = {"sha256": hasher.hexdigest(), "mode": 0o755 if before.st_mode & 0o111 else 0o644}
            finally:
                os.close(fd)
    finally:
        os.close(directory)
    return records


def python_symbols(text):
    module = ast.parse(text)
    result = {}
    def walk(body, prefix=""):
        ordinary = []
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = prefix + node.name
                require(name not in result,"duplicate Python symbols cannot be scoped safely")
                if isinstance(node, ast.ClassDef):
                    header = copy.copy(node)
                    header.body = []
                    result[name] = ast.dump(header, include_attributes=False)
                    walk(node.body, name+".")
                else:
                    result[name] = ast.dump(node, include_attributes=False)
            else:
                ordinary.append(node)
        result[prefix+"$module"] = ast.dump(ast.Module(body=ordinary,type_ignores=[]),include_attributes=False)
    walk(module.body)
    return result


class WorkCycle:
    """Lifecycle guard on the existing ledger; no new queue or scheduler."""
    def __init__(self, plan, root, audit_log, *, git=None):
        require(isinstance(plan, WorkPlan), "host work plan required")
        self.plan, self.root, self.audit_log = plan, Path(root), audit_log
        self.git = git or read_only_git(self.root)
        self.phase, self.baseline, self.verified_tree = WorkPhase.PREPARE, None, None
        self.verified_checks, self.commit_sha = {}, None
        self.artifact, self.bundle_hash = None, None
        self.verification_requests = {}
        self.verification_open = True
        self._restore()

    def _events(self):
        return [x for x in self.audit_log.replay() if x.get("work_cycle") == self.plan.identity.to_json()]

    def _record(self, kind, **data):
        self.audit_log.append({"event":"work_"+kind, "work_cycle":self.plan.identity.to_json(),
                               "plan_sha256":self.plan.hash, **data})
        self.audit_log.flush()

    def _restore(self):
        for event in self._events():
            require(event.get("plan_sha256") == self.plan.hash, "work plan changed during restart")
            kind = event["event"]
            if kind == "work_plan":
                require(event.get("plan") == json.loads(canonical(self.plan.to_json())), "persisted work plan changed")
            elif kind == "work_discovery":
                require(self.plan.planning is not None and self.phase is WorkPhase.PREPARE
                        and event.get("discovery") == self.plan.planning.to_json()["discovery"],
                        "discovery replay binding invalid")
                self.phase = WorkPhase.DISCOVER
            elif kind == "work_plan_gate":
                require(self.plan.planning is not None and self.phase is WorkPhase.DISCOVER
                        and event.get("planning_sha256") == self.plan.planning.hash
                        and event.get("grant_sha256") == self.plan.grant_sha256
                        and event.get("budget_reference") == self.plan.budget_reference
                        and event.get("verdict") == "auto_admitted", "plan gate replay invalid")
                self.phase = WorkPhase.PLAN_GATE
            elif kind == "work_baseline":
                expected = WorkPhase.PLAN_GATE if self.plan.planning is not None else WorkPhase.PREPARE
                require(self.phase is expected and isinstance(event.get("tree"),dict), "baseline replay invalid")
                tree = digest(event["tree"])
                if self.plan.baseline_omission_reason is None:
                    require(len(event.get("checks",[])) == len(self.plan.checks), "baseline checks incomplete")
                    for check, raw in zip(self.plan.checks,event["checks"]):
                        proof = CheckResult(**raw)
                        self._validate_check(proof,check,tree)
                        self._validate_baseline(proof,check)
                else:
                    require(event.get("checks") == [] and event.get("omission") == self.plan.baseline_omission_reason,
                            "baseline omission replay invalid")
                self.baseline = event["tree"]
                self.phase = WorkPhase.WORK
            elif kind == "work_verification_requested":
                key = event.get("request_id")
                require(isinstance(key, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", key)
                        and key not in self.verification_requests
                        and self.phase in {WorkPhase.WORK, WorkPhase.VERIFY}
                        and not self.verified_checks and self.verification_open
                        and isinstance(event.get("tree_sha256"), str) and _SHA.fullmatch(event["tree_sha256"]),
                        "verification request replay invalid")
                require(not any(value is None for value in self.verification_requests.values()),
                        "previous verification delivery is unknown")
                self.verification_requests[key] = None
                self.verification_open = False
                self.phase = WorkPhase.VERIFY
            elif kind == "work_verification_finished":
                key, outcome = event.get("request_id"), event.get("outcome")
                require(key in self.verification_requests and self.verification_requests[key] is None
                        and isinstance(outcome, dict) and outcome.get("plan_sha256") == self.plan.hash
                        and outcome.get("status") in {"pass", "failed", "unavailable"}
                        and ((outcome["status"] == "pass") == (self.phase is WorkPhase.HYGIENE))
                        and set(outcome) == {"status", "plan_sha256", "tree_sha256", "checks", "evidence_sha256", "next_action"}
                        and outcome["checks"] == [{name:raw[name] for name in ("check_id", "exit_code", "output_sha256", "truncated")}
                            for raw in self.verified_checks.values()]
                        and outcome["evidence_sha256"] == digest(outcome["checks"])
                        and isinstance(outcome["tree_sha256"], str) and _SHA.fullmatch(outcome["tree_sha256"])
                        and (outcome["status"] != "pass" or outcome["tree_sha256"] == self.verified_tree)
                        and outcome["next_action"] == {"pass":"hygiene", "failed":"evidenced_repair_authorization_required",
                                                       "unavailable":"host_reconciliation_required"}[outcome["status"]]
                        and len(canonical(outcome)) <= 8192, "verification outcome replay invalid")
                self.verification_requests[key] = outcome
            elif kind == "work_check":
                require(self.phase in {WorkPhase.WORK,WorkPhase.VERIFY}, "check replay phase invalid")
                proof = CheckResult(**event["check"])
                check = next((x for x in self.plan.checks if x.id == proof.check_id),None)
                require(check is not None, "unknown replayed check")
                self._validate_check(proof,check,proof.tree_sha256)
                self.phase = WorkPhase.VERIFY
                self.verified_checks[proof.check_id] = event["check"]
            elif kind == "work_pass":
                require(self.phase is WorkPhase.VERIFY, "PASS replay phase invalid")
                tree = event["tree_sha256"]
                require(isinstance(tree,str) and _SHA.fullmatch(tree)
                        and set(self.verified_checks) == {x.id for x in self.plan.checks}
                        and all((x["exit_code"] == 0 or self.plan.planning is not None
                                 and x["check_id"] not in self.plan.planning.hard_check_ids)
                                and not x["truncated"] and x["tree_sha256"] == tree
                                for x in self.verified_checks.values()), "incomplete PASS replay")
                self.verified_tree = tree
                self.phase = WorkPhase.HYGIENE
            elif kind in {"work_local_commit_requested", "work_local_commit_ready"}:
                require(self.phase is WorkPhase.HYGIENE and self.plan.hygiene_sha256 is not None
                        and event.get("policy_sha256") == self.plan.hygiene_sha256
                        and event.get("tree_sha256") == self.verified_tree
                        and isinstance(event.get("private_repository"), str)
                        and Path(event["private_repository"]).is_absolute(), "local commit replay binding invalid")
                if kind == "work_local_commit_ready":
                    require(isinstance(event.get("commit_sha"), str) and _GIT.fullmatch(event["commit_sha"]),
                            "local commit replay digest invalid")
            elif kind == "work_commit":
                require(self.phase is WorkPhase.HYGIENE, "commit replay phase invalid")
                from .evidence import parse_artifact
                artifact = parse_artifact(event["artifact"])
                require(artifact.task_id == self.plan.identity.task_id and artifact.base_sha == self.plan.base_sha
                        and artifact.commit_sha == event["commit_sha"], "commit replay identity mismatch")
                self.artifact = event["artifact"]
                self.commit_sha, self.phase = event["commit_sha"], WorkPhase.HANDOFF
            elif kind == "work_handoff":
                require(self.phase is WorkPhase.HANDOFF, "handoff replay phase invalid")
                require(isinstance(event.get("bundle_sha256"),str) and _SHA.fullmatch(event["bundle_sha256"]),
                        "handoff replay digest invalid")
                self.bundle_hash, self.phase = event["bundle_sha256"], WorkPhase.FINISHED
            elif kind == "work_invalidate":
                require(self.phase in {WorkPhase.HYGIENE,WorkPhase.VERIFY},"invalidation replay phase invalid")
                self.verified_tree, self.verified_checks = None, {}
                self.verification_open = True
                self.phase = WorkPhase.VERIFY
            elif kind in {"work_blocked","work_rollback"}:
                require(self.phase is not WorkPhase.FINISHED,"finished work cannot be reopened")
                self.phase = WorkPhase.BLOCKED
            else:
                raise WorkContractError("unknown work cycle event")

    def start(self, runner):
        if self.phase not in {WorkPhase.PREPARE, WorkPhase.DISCOVER, WorkPhase.PLAN_GATE}:
            return
        require(self.git(["rev-parse","HEAD"]).strip() == self.plan.base_sha
                and not self.git(["status","--porcelain","-z"]), "work begins only from exact clean base")
        for commit in self.plan.prerequisite_commits:
            require(self.git(["merge-base",self.plan.base_sha,commit]).strip() == commit,
                    "required artifact is not integrated in base")
        if not any(event.get("event") == "work_plan" for event in self._events()):
            self._record("plan",plan=json.loads(canonical(self.plan.to_json())))
        snapshot = tree_snapshot(self.root,git=self.git)
        self._protected_inputs(snapshot)
        if self.plan.planning is not None:
            self.plan.planning.require_binding(self.plan)
            discovery = self.plan.planning.to_json()["discovery"]
            require(all(snapshot.get(path, {}).get("sha256") == content_hash
                        for path, content_hash in discovery["inspected_files"].items()),
                    "inspected discovery inputs changed")
            if self.phase is WorkPhase.PREPARE:
                self._record("discovery", discovery=discovery)
                self.phase = WorkPhase.DISCOVER
            if self.phase is WorkPhase.DISCOVER:
                self._record("plan_gate", planning_sha256=self.plan.planning.hash,
                             grant_sha256=self.plan.grant_sha256,
                             budget_reference=self.plan.budget_reference, verdict="auto_admitted")
                self.phase = WorkPhase.PLAN_GATE
        proofs = []
        if self.plan.baseline_omission_reason is None:
            for check in self.plan.checks:
                proof = runner(check,self.root,self.plan,digest(snapshot))
                self._validate_check(proof,check,digest(snapshot))
                proofs.append(asdict(proof))
                try:
                    self._validate_baseline(proof,check)
                except WorkContractError:
                    self._record("blocked",reason="baseline_validation_failed",tree_sha256=digest(snapshot),checks=proofs)
                    self.phase = WorkPhase.BLOCKED
                    raise
        require(tree_snapshot(self.root,git=self.git) == snapshot, "baseline modified work inputs")
        self._record("baseline",tree=snapshot,checks=proofs,omission=self.plan.baseline_omission_reason)
        self.baseline, self.phase = snapshot, WorkPhase.WORK

    def implementation_allowed(self):
        return self.phase is WorkPhase.WORK

    def _validate_baseline(self,proof,check):
        require(not proof.truncated,"baseline check exceeded declared limits")
        if check.expected_baseline_failure:
            require(proof.exit_code == 1 and proof.output_sha256 == check.expected_baseline_output_sha256,
                    "unrelated or unanticipated baseline failure")
        else:
            require(proof.exit_code == 0, "unrelated or unanticipated baseline failure")

    def _validate_check(self, proof, check, tree):
        require(isinstance(proof,CheckResult) and proof.check_id == check.id
                and proof.plan_sha256 == self.plan.hash and proof.environment_sha256 == self.plan.environment_sha256
                and proof.tree_sha256 == tree and proof.duration_ms <= check.timeout_seconds*1000+3000,
                "check origin/plan/environment/tree mismatch")

    def _protected_inputs(self,snapshot):
        for check in self.plan.checks:
            for path,sha in check.protected_inputs:
                require(snapshot.get(path,{}).get("sha256")==sha,
                        "verification input changed; independent reviewed replan required")

    def verify_scope(self):
        current = tree_snapshot(self.root,git=self.git)
        self._protected_inputs(current)
        require(self.baseline is not None, "baseline required")
        changed = [name for name in set(current)|set(self.baseline) if current.get(name) != self.baseline.get(name)]
        for name in changed:
            scopes = [x for x in self.plan.files if x.covers(name)]
            require(scopes, "changed file escaped approved work scope")
            if all(x.symbols for x in scopes):
                require(name in current and name in self.baseline and not current[name].get("deleted"),
                        "symbol-scoped file cannot be created or deleted")
                base = self.git(["show",self.plan.base_sha+":"+name])
                require(current[name]["mode"] == self.baseline[name]["mode"],"symbol-scoped file mode changed")
                directory=os.open(self.root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
                fd=None
                try:
                    fd=_open_relative(directory,name)
                    data=os.read(fd,4_194_305)
                    require(len(data)<=4_194_304 and not os.read(fd,1),"symbol-scoped source exceeds bound")
                    live=data.decode("utf-8")
                finally:
                    if fd is not None: os.close(fd)
                    os.close(directory)
                before, after = python_symbols(base), python_symbols(live)
                altered = {key for key in set(before)|set(after) if before.get(key) != after.get(key)}
                require(altered <= {symbol for scope in scopes for symbol in scope.symbols},
                        "changed Python symbol escaped scope")
        return current

    def verify(self, runner):
        require(self.phase in {WorkPhase.WORK,WorkPhase.VERIFY}, "implementation already ended")
        snapshot = self.verify_scope()
        tree = digest(snapshot)
        for check in self.plan.checks:
            proof = runner(check,self.root,self.plan,tree)
            self._validate_check(proof,check,tree)
            require(tree_snapshot(self.root,git=self.git) == snapshot, "validation changed tested inputs")
            self._record("check",check=asdict(proof))
            self.phase = WorkPhase.VERIFY
            self.verified_checks[check.id] = asdict(proof)
            hard = self.plan.planning is None or check.id in self.plan.planning.hard_check_ids
            require((proof.exit_code == 0 or not hard) and not proof.truncated,
                    "approved hard check failed; evidenced repair authorization required")
        self._record("pass",tree_sha256=tree)
        self.verified_tree, self.phase = tree, WorkPhase.HYGIENE

    def request_verification(self, request_id, runner):
        require(isinstance(request_id, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", request_id),
                "bounded verification request identity required")
        if request_id in self.verification_requests:
            outcome = self.verification_requests[request_id]
            return outcome or {"status": "unknown", "plan_sha256": self.plan.hash,
                               "next_action": "host_reconciliation_required"}
        require(self.phase in {WorkPhase.WORK, WorkPhase.VERIFY} and not self.verified_checks and self.verification_open
                and not any(value is None for value in self.verification_requests.values()),
                "new verification requires evidenced repair or invalidated checks")
        require(sum(check.timeout_seconds+13 for check in self.plan.checks) <= 900,
                "host verification aggregate time exceeds bound")
        tree = digest(self.verify_scope())
        self._record("verification_requested", request_id=request_id, tree_sha256=tree)
        self.verification_requests[request_id] = None
        self.verification_open = False
        self.phase = WorkPhase.VERIFY
        try:
            self.verify(runner)
        except EvidenceUnavailable:
            status, action = "unavailable", "host_reconciliation_required"
        except WorkContractError:
            status, action = "failed", "evidenced_repair_authorization_required"
        else:
            status, action = "pass", "hygiene"
        checks = [{key: raw[key] for key in ("check_id", "exit_code", "output_sha256", "truncated")}
                  for raw in self.verified_checks.values()]
        outcome = {"status": status, "plan_sha256": self.plan.hash, "tree_sha256": tree,
                   "checks": checks, "evidence_sha256": digest(checks), "next_action": action}
        self._record("verification_finished", request_id=request_id, outcome=outcome)
        self.verification_requests[request_id] = outcome
        return outcome

    def committed(self, artifact):
        if self.phase in {WorkPhase.HANDOFF,WorkPhase.FINISHED}:
            require(isinstance(artifact,ArtifactRef) and json.loads(canonical(artifact.to_json())) == self.artifact,
                    "replayed artifact differs from committed handoff")
            return
        require(isinstance(artifact,ArtifactRef) and self.phase is WorkPhase.HYGIENE,
                "commit is allowed only after approved checks pass")
        require(artifact.task_id == self.plan.identity.task_id and artifact.base_sha == self.plan.base_sha,
                "commit artifact belongs to another work plan")
        manager = WorkspaceManager(self.root,git=self.git)
        manager.verify(artifact,self.root)
        from .evidence import verify_committed_bytes
        verify_committed_bytes(artifact,self.root,self.git)
        if digest(self.verify_scope()) != self.verified_tree:
            self._record("invalidate",reason="committed_tree_changed")
            self.verified_tree, self.verified_checks, self.phase = None, {}, WorkPhase.VERIFY
            raise WorkContractError("commit hook or hygiene changed tested content")
        self._record("commit",commit_sha=artifact.commit_sha,artifact=artifact.to_json())
        self.artifact = json.loads(canonical(artifact.to_json()))
        self.commit_sha, self.phase = artifact.commit_sha, WorkPhase.HANDOFF

    def handed_off(self, bundle_hash):
        if self.phase is WorkPhase.FINISHED:
            require(bundle_hash == self.bundle_hash, "replayed handoff digest differs")
            return
        require(self.phase is WorkPhase.HANDOFF and isinstance(bundle_hash,str) and _SHA.fullmatch(bundle_hash),
                "immutable completion bundle required before handoff")
        self._record("handoff",bundle_sha256=bundle_hash)
        self.bundle_hash, self.phase = bundle_hash, WorkPhase.FINISHED

    def rollback_owned(self,authority):
        """Only a host authority with a quiesced exact writer can attest ownership."""
        require(self.phase in {WorkPhase.WORK,WorkPhase.VERIFY,WorkPhase.BLOCKED}
                and self.baseline is not None and callable(authority),"owned rollback authority required")
        require(self.git(["rev-parse","HEAD"]).strip()==self.plan.base_sha
                and not self.git(["diff","--cached","--name-only"]),
                "rollback cannot change committed or staged work")
        current=tree_snapshot(self.root,git=self.git)
        edits=authority(self.plan.identity,self.plan.hash,digest(self.baseline),digest(current))
        require(isinstance(edits,tuple) and edits and len(edits)<=256
                and all(isinstance(x,OwnedChange) for x in edits)
                and len({x.path for x in edits})==len(edits),"host-owned edit receipts required")
        prepared=[]
        for edit in edits:
            require(any(scope.covers(edit.path) for scope in self.plan.files),"rollback path escaped scope")
            require(self.baseline.get(edit.path,{}).get("sha256")==edit.before_sha256
                    and current.get(edit.path,{}).get("sha256")==edit.after_sha256,
                    "rollback ownership is ambiguous")
            require(edit.after_sha256 is not None,"deleted file rollback needs separately attested creation")
            raw=None if edit.before_sha256 is None else self.git.raw(
                ["show",self.plan.base_sha+":"+edit.path])
            require(raw is None or hashlib.sha256(raw).hexdigest()==edit.before_sha256,
                    "rollback baseline changed")
            prepared.append((edit,raw))
        directory=os.open(self.root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        try:
            for edit,raw in prepared:
                fd=_open_relative(directory,edit.path)
                try:
                    actual=os.fstat(fd)
                    require(hashlib.sha256(os.read(fd,67_108_865)).hexdigest()==edit.after_sha256,
                            "rollback ownership changed")
                    parts=edit.path.split("/")
                    parent=os.dup(directory)
                    try:
                        for part in parts[:-1]:
                            child=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=parent)
                            os.close(parent)
                            parent=child
                        named=os.stat(parts[-1],dir_fd=parent,follow_symlinks=False)
                        require((named.st_dev,named.st_ino)==(actual.st_dev,actual.st_ino),"rollback path replaced")
                        if raw is None:
                            os.unlink(parts[-1],dir_fd=parent)
                        else:
                            write_fd=os.open(parts[-1],os.O_WRONLY|os.O_NOFOLLOW,dir_fd=parent)
                            try:
                                held=os.fstat(write_fd)
                                require((held.st_dev,held.st_ino)==(actual.st_dev,actual.st_ino),"rollback writer replaced")
                                offset=0
                                while offset<len(raw):
                                    offset+=os.write(write_fd,raw[offset:])
                                os.ftruncate(write_fd,len(raw))
                                os.fchmod(write_fd,self.baseline[edit.path]["mode"])
                                os.fsync(write_fd)
                            finally:
                                os.close(write_fd)
                        os.fsync(parent)
                    finally:
                        os.close(parent)
                finally:
                    os.close(fd)
        finally:
            os.close(directory)
        self._record("rollback",paths=[x.path for x in edits],reason="host_attested_owned_changes")
        self.phase=WorkPhase.BLOCKED


@dataclass(frozen=True)
class OwnedChange:
    path: str
    before_sha256: str | None
    after_sha256: str | None
    def __post_init__(self):
        relative(self.path)
        require(all(x is None or isinstance(x,str) and _SHA.fullmatch(x)
                    for x in (self.before_sha256,self.after_sha256)),"owned edit digest invalid")
