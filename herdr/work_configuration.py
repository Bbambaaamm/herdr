"""Fixed host configuration to actual worker work authority; no model selector."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import stat
import ast
from pathlib import Path

from .check_runner import CheckEnvironment
from .evidence import EvidenceStore, binding, canonical, digest
from .host_configuration import HOST_POLICY_CONFIG, _read_configuration, build_host_policy_factory
from .scheduler import AuditLog
from .work_contract_host import HostWorkContractFactory
from .work_cycle import FileScope, ValidationCheck, WorkPlan, WorkMode, require, tree_snapshot, relative, python_symbols
from .policy_launch import _open_relative
from .work_planning import DiscoveryRecord, PlanArtifact, bounded, closed, sha, strings


def definition_target(spec_sha256, definition):
    # An independent review cannot include its own subsequently accepted digest.
    value = copy.deepcopy(definition)
    value["planning"]["verification"]["accepted_review_ref"] = None
    return digest({"spec_sha256": spec_sha256, "definition": value})


def _private_directory(path, *, base=None):
    path = Path(path)
    require(path.is_absolute() and path.resolve() == path, "work host storage cannot use symlinks")
    if base is None:
        base = path
    base = Path(base)
    require(base.is_absolute() and base.resolve(strict=True) == base
            and path.is_relative_to(base), "private storage base mismatch")
    fd = os.open(base, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        def validate(handle):
            info = os.fstat(handle)
            require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.geteuid()
                    and not info.st_mode & 0o077, "work host storage is not private")
        validate(fd)
        for part in path.relative_to(base).parts:
            try:
                os.mkdir(part, mode=0o700, dir_fd=fd)
                os.fsync(fd)
            except FileExistsError:
                pass
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=fd)
            os.close(fd); fd = child
            validate(fd)
    finally:
        os.close(fd)


def _audit(path):
    _private_directory(path.parent)
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600)
    except FileExistsError:
        info = path.lstat()
        require(stat.S_ISREG(info.st_mode) and info.st_uid == os.geteuid()
                and not info.st_mode & 0o077 and info.st_nlink == 1, "work audit is untrusted")
    else:
        os.fsync(fd); os.close(fd)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    return AuditLog(path)


def require_prebuild_review(raw, definition, spec_sha256, writable_roots, identity):
    oracle = definition["planning"]["verification"]
    reference = oracle["accepted_review_ref"]
    if reference is None:
        require(not oracle["prebuild_review_required"], "independent prebuild evidence required")
        return
    records = raw["review_records"]
    require(isinstance(records, dict) and reference in records, "accepted prebuild review source unavailable")
    source = closed(records[reference], ("store", "identity", "plan_hash"), "accepted review source")
    store_path = Path(source["store"])
    require(store_path.is_absolute() and store_path.resolve(strict=True) == store_path,
            "accepted review source is not canonical")
    info = store_path.lstat()
    require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.geteuid()
            and not info.st_mode & 0o077, "accepted review source is not private")
    store = EvidenceStore(store_path); store.protect_from(writable_roots)
    sha(source["plan_hash"], "review plan")
    plan = store.read("plan", digest(source["identity"]))
    bundle, legacy = store.lookup_acceptance(source["identity"], source["plan_hash"])
    require(not legacy and plan["kind"] == "review" and plan["plan_hash"] == source["plan_hash"]
            and bundle is not None and bundle["kind"] == "review"
            and bundle["level"] == "verified_worker_result" and digest(bundle) == reference
            and plan["identity"]["id"] != identity.task_id
            and "github:" + plan["repo"] == identity.consumer
            and isinstance(bundle.get("launch_policy", {}).get("identity", {}).get("agent_id"), str)
            and bundle["launch_policy"]["identity"]["agent_id"] != identity.agent_id,
            "prebuild review is not independently accepted evidence")
    coverage = bundle.get("typed_validation", {}).get("coverage", {})
    target = definition_target(spec_sha256, definition)
    require(plan["criteria"].get("target_contract_sha256") == target
            and coverage.get("target_contract_sha256") == target
            and coverage.get("target_commit") == definition["base_sha"]
            and coverage.get("verdict") == "pass", "prebuild review targets another contract or failed")


def inspect_discovery(workspace, paths, snapshot):
    """Targeted, FD-pinned content inspection; syntax is not behavior evidence."""
    symbols, facts, unknowns, total = {}, [], [], 0
    directory = os.open(workspace, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for name in paths:
            relative(name)
            fd = _open_relative(directory, name)
            try:
                before = os.fstat(fd)
                require(stat.S_ISREG(before.st_mode) and before.st_size <= 262144,
                        "discovery input exceeds bounded inspection")
                chunks, size = [], 0
                while True:
                    chunk = os.read(fd, min(65536, 262145-size))
                    if not chunk:
                        break
                    size += len(chunk); total += len(chunk)
                    require(size <= 262144 and total <= 1048576, "targeted discovery exceeds bound")
                    chunks.append(chunk)
                after = os.fstat(fd)
                stamp = lambda v: (v.st_dev, v.st_ino, v.st_size, v.st_mtime_ns, v.st_ctime_ns)
                raw = b"".join(chunks)
                require(stamp(before) == stamp(after) and len(raw) == before.st_size
                        and hashlib.sha256(raw).hexdigest() == snapshot[name]["sha256"],
                        "discovery input changed during inspection")
            finally:
                os.close(fd)
            try:
                text = raw.decode("utf-8")
            except UnicodeError:
                facts.append("Inspected bounded binary content: " + name)
                unknowns.append("Binary behavior remains UNKNOWN: " + name)
                continue
            facts.append("Inspected UTF-8 content: " + name)
            if name.endswith(".py"):
                try:
                    parsed = python_symbols(text)
                    module = ast.parse(text)
                except (SyntaxError, ValueError, RecursionError) as exc:
                    unknowns.append("Python symbols unavailable in inspected source: " + name)
                    continue
                names = sorted(key for key in parsed if not key.endswith("$module"))
                require(len(names) <= 128 and all(len(key) <= 256 for key in names),
                        "discovery symbols exceed bound")
                symbols[name] = names
                imports = sorted({node.module or "relative" for node in ast.walk(module)
                                  if isinstance(node, ast.ImportFrom)} |
                                 {alias.name for node in ast.walk(module) if isinstance(node, ast.Import)
                                  for alias in node.names})
                if imports:
                    facts.append("Observed import references in " + name + ": " + ", ".join(imports)[:1024])
                if any(isinstance(node, ast.If) and isinstance(node.test, ast.Compare)
                       and isinstance(node.test.left, ast.Name) and node.test.left.id == "__name__"
                       and any(isinstance(value, ast.Constant) and value.value == "__main__"
                               for value in node.test.comparators) for node in module.body):
                    facts.append("Observed __main__ entry guard: " + name)
        unknowns.append("Uninspected files and behavior not demonstrated by checks remain UNKNOWN")
        require(len(facts) <= 128 and len(unknowns) <= 128, "discovery observations exceed bound")
        return {"symbols": symbols, "facts": facts, "unknowns": unknowns}
    finally:
        os.close(directory)


def build_root_work_factory(root, task, *, configuration_path=HOST_POLICY_CONFIG, git=None, recovery=False, spec_sha256=None):
    """Only standalone host code selects the protected configuration path."""
    from agent_completion_evidence import spec_digest
    raw = _read_configuration(configuration_path)
    policy_factory = build_host_policy_factory(configuration_path=configuration_path)
    require(raw == _read_configuration(configuration_path), "host configuration changed during work admission")
    root = Path(root)
    require(root.is_absolute() and root.resolve(strict=True) == root
            and Path(raw["task_store_root"]) == root, "work task store differs from host configuration")
    spec_hash = spec_digest(task) if spec_sha256 is None else spec_sha256
    sha(spec_hash, "exact host work specification")
    workspace = Path(task.get("workspace", ""))
    require(workspace.is_absolute() and workspace.resolve() == workspace, "canonical worktree required")
    storage = Path(raw["storage"]) / "work-contracts" / digest(binding(task))
    for writable in policy_factory.writable_roots:
        require(not storage.is_relative_to(Path(writable).resolve()), "work authority is worker writable")
    require(not storage.is_relative_to(workspace), "work authority is worker writable")
    if recovery:
        require(storage.is_dir() and storage.resolve(strict=True) == storage, "original work admission unavailable")
    _private_directory(storage, base=Path(raw["storage"]))
    if recovery:
        require((storage / "admission").is_dir(), "original work admission unavailable")
    store = EvidenceStore(storage / "admission"); store.protect_from((workspace,))
    if recovery:
        admitted = store.read("plan", digest(binding(task)))
        closed(admitted, ("version", "identity", "spec_sha256", "definition", "environment"), "work admission")
        require(type(admitted["version"]) is int and admitted["version"] == 1
                and admitted["identity"] == binding(task) and admitted["spec_sha256"] == spec_hash,
                "original work admission binding changed")
        definition = admitted["definition"]
        environment = CheckEnvironment(**admitted["environment"])
        catalogue = None
    else:
        require(workspace.resolve(strict=True) == workspace, "canonical worktree required")
        catalogue = closed(raw.get("work_contracts"), ("version", "environment", "plans", "review_records"), "host work catalogue")
        require(type(catalogue["version"]) is int and catalogue["version"] == 1,
                "host work catalogue version unsupported")
        plans = catalogue["plans"]
        require(isinstance(plans, dict) and 1 <= len(plans) <= 16
                and all(isinstance(key, str) and len(key) == 64 for key in plans)
                and spec_hash in plans, "exact work spec is not host approved")
        bounded(plans[spec_hash])
        definition = copy.deepcopy(plans[spec_hash])
        require(isinstance(catalogue["environment"], dict), "approved check environment required")
        environment = CheckEnvironment(**catalogue["environment"])
        require(isinstance(catalogue["review_records"], dict) and len(catalogue["review_records"]) <= 64,
                "bounded prebuild review sources required")
        admitted = {"version": 1, "identity": binding(task), "spec_sha256": spec_hash,
                    "definition": definition, "environment": catalogue["environment"]}
    bounded(definition)
    names = {"spec_version", "policy_version", "base_sha", "files", "criteria", "checks",
             "budget_reference", "mode", "baseline_omission_reason", "phases", "prerequisite_commits",
             "purpose", "baseline_policy", "discovery_files", "planning"}
    closed(definition, names | ({"hygiene"} if "hygiene" in definition else set()), "approved work definition")
    hygiene = None
    if "hygiene" in definition:
        from .work_hygiene import LocalCommitPolicy
        profile = closed(definition["hygiene"], ("version", "config_sha256", "hooks_root", "hooks", "timeout_seconds", "output_bytes", "max_processes"), "approved local commit policy")
        hygiene = LocalCommitPolicy(**profile, environment=environment)
    require(definition["mode"] == "repair", "experiment authority is not configured")
    base = (task.get("completion_plan") or {}).get("base_sha")
    require(base == definition["base_sha"], "work base differs from frozen completion plan")
    if not recovery:
        store.publish("plan", digest(binding(task)), admitted)

    def approve(*, identity, workspace, grant, spec_sha256):
        require(not recovery, "recovered work evidence cannot authorize new implementation")
        require(spec_sha256 == spec_hash and identity.task_id == task["id"]
                and identity.run_token == task["run_token"] and identity.fencing_token == task["fencing_token"],
                "work identity differs from approved parent")
        require_prebuild_review(catalogue, definition, spec_sha256,
                                tuple(Path(path) for path in grant.runtime_assurance.writable_roots), identity)
        inspected = strings(definition["discovery_files"], "targeted discovery files",
                            maximum=128, width=1024, empty=False)
        snapshot = tree_snapshot(workspace, git=git)
        require(set(inspected) <= set(snapshot), "required discovery source is missing")
        observed = inspect_discovery(workspace, inspected, snapshot)
        discovery = DiscoveryRecord({
            "version": 1, "identity": identity.to_json(), "base_sha": definition["base_sha"],
            "inspected_files": {path: snapshot[path]["sha256"] for path in inspected},
            "symbols": observed["symbols"], "facts": observed["facts"],
            "evidence_refs": ["git-base:" + definition["base_sha"]],
            "unknowns": observed["unknowns"], "expansion_reason": None,
        })
        planning = copy.deepcopy(definition["planning"])
        require(isinstance(planning, dict) and not set(planning) & {"identity", "spec_sha256", "base_sha", "discovery"},
                "host fills actual planning identity and discovery")
        planning.update(version=1, identity=identity.to_json(), spec_sha256=spec_sha256,
                        base_sha=definition["base_sha"], discovery=discovery.to_json())
        data = {key: value for key, value in definition.items() if key not in {"discovery_files", "planning", "hygiene"}}
        data["mode"] = WorkMode(data["mode"])
        data["files"] = tuple(FileScope(**item) for item in data["files"])
        data["checks"] = tuple(ValidationCheck(**item) for item in data["checks"])
        plan = WorkPlan(**data, identity=identity, spec_sha256=spec_sha256,
            grant_sha256=grant.hash, environment_sha256=environment.hash, planning=PlanArtifact(planning),
            hygiene_sha256=None if hygiene is None else hygiene.hash)
        plan.planning.require_binding(plan, grant)
        return plan

    factory = HostWorkContractFactory(approve=approve, environment=environment,
                                      storage=storage / "checks", audit_log=_audit(storage / "events.jsonl"), git=git)
    factory.host_admission = admitted
    factory.local_commit_policy = hygiene
    checks=tuple(ValidationCheck(**item) for item in definition["checks"])
    factory.baseline_wall_seconds=sum(check.timeout_seconds+13 for check in checks)+120
    factory.request_wall_seconds=factory.baseline_wall_seconds
    if hygiene is not None:factory.request_wall_seconds+=hygiene.timeout_seconds+13
    require(factory.request_wall_seconds<=900,"full host verification request exceeds bound")
    factory.task_store_root = root
    _private_directory(storage / "results", base=Path(raw["storage"]))
    from .work_result_receipt import WorkResultAuthority
    factory.result_authority = WorkResultAuthority(EvidenceStore(storage / "results"))
    return factory


def prompt_contract(plan):
    value = plan.planning.to_json() if plan.planning is not None else None
    if value is None:
        return ""
    return ("\nGOAL\n" + value["goal"] + "\nCONSTRAINTS / AUTHORITY\n"
            + json.dumps({"constraints": value["constraints"], "files": value["allowed_files"],
                          "tools": value["tools"], "permissions": value["permissions"]}, sort_keys=True)
            + "\nCONTEXT\n" + json.dumps({"discovery": value["discovery"], "assumptions": value["assumptions"],
                                            "uncertainties": value["uncertainties"]}, sort_keys=True)
            + "\nACCEPTANCE / ORACLE\n" + json.dumps({"acceptance": value["acceptance"],
                "verification": value["verification"], "stop_condition": value["stop_condition"]}, sort_keys=True)
            + "\nCAPABILITIES\nChoose appropriate granted tools and skills within the frozen plan. "
              "A new tool/scope requires a revised approved plan and admission.\n"
            + "\nHOST VERIFICATION / HANDOFF\nWhen implementation is ready, call herdr_verify_work with a stable request_id "
              "and handoff={pr_number:<existing exact PR or null>, scope_claim:<when the frozen scope policy requires it>}. "
              "The host runs the frozen oracle, preserves repository hooks, seals the exact local commit and submits the original result. "
              "PASS ends implementation. A failed check needs new evidenced repair authority in the same budget.\n")


def bind_root_handoff(factory, task, launch, cycle):
    """Compose only host-approved local Git authority, before SDK admission."""
    from agent_completion_evidence import store_for
    from .work_handoff import HostWorkHandoff
    from .work_hygiene import HostLocalCommitter, LocalCommitPolicy
    from .workspace import ArtifactRef
    from .evidence import read_only_git
    policy = getattr(factory, "local_commit_policy", None)
    require(isinstance(policy, LocalCommitPolicy), "coding work has no approved local commit profile")
    plan = store_for(factory.task_store_root, task).read("plan", digest(binding(task)))
    root = Path(task["workspace"])
    info = root.stat()
    workspace_identity = f"{info.st_dev}:{info.st_ino}"
    if task.get("work_workspace_identity") is not None:
        require(task["work_workspace_identity"] == workspace_identity, "original worktree pin changed")
    task["work_workspace_identity"] = workspace_identity
    branch = read_only_git(root)(["symbolic-ref", "--short", "HEAD"]).strip()
    require(branch.startswith("herdr/"), "modern coding requires its exact isolated owned branch")
    draft = ArtifactRef(task["id"], binding(task)["attempt"], cycle.plan.base_sha,
                        cycle.plan.base_sha, "", (), branch)
    rule = next((rule for rule in launch.grant.tool_rules if rule.tool == "herdr_submit_result"), None)
    require(rule is not None and rule.result_slot is not None, "immutable SDK result slot required")
    commit_storage = factory.storage.parent / "commits"
    _private_directory(commit_storage, base=factory.storage.parent)
    committer = HostLocalCommitter(policy, commit_storage, draft, completion_plan=plan,
                                  workspace_identity=workspace_identity)
    port = HostWorkHandoff(identity=cycle.plan.identity, task=task, completion_plan=plan,
                          store=factory.result_authority.store, slot=rule.result_slot, committer=committer)
    factory.result_authority.store.publish("plan", digest({"type":"work-handoff-binding", "identity":cycle.plan.identity.to_json()}),
        {"version":1, "identity":cycle.plan.identity.to_json(), "work_plan_sha256":cycle.plan.hash,
         "completion_plan_hash":plan["plan_hash"], "slot":rule.result_slot.to_json(),
         "draft":draft.to_json(), "workspace_identity":workspace_identity})
    factory.bind_handoff(cycle.plan.identity, port)
    return port


def recover_host_handoff(factory, task, cycle, completion_plan):
    from .work_handoff import HostWorkHandoff
    from .work_hygiene import HostLocalCommitter
    from .result_submission import ResultSlot
    from .workspace import ArtifactRef
    key = digest({"type":"work-handoff-binding", "identity":cycle.plan.identity.to_json()})
    record = factory.result_authority.store.read("plan", key)
    closed(record, ("version", "identity", "work_plan_sha256", "completion_plan_hash", "slot", "draft", "workspace_identity"),
           "original handoff binding")
    require(type(record["version"]) is int and record["version"] == 1
            and record["identity"] == cycle.plan.identity.to_json()
            and record["work_plan_sha256"] == cycle.plan.hash
            and record["completion_plan_hash"] == completion_plan["plan_hash"],
            "original handoff binding changed")
    committer = HostLocalCommitter(factory.local_commit_policy, factory.storage.parent/"commits",
        ArtifactRef(**record["draft"]), completion_plan=completion_plan, workspace_identity=record["workspace_identity"])
    port = HostWorkHandoff(identity=cycle.plan.identity, task=task, completion_plan=completion_plan,
        store=factory.result_authority.store, slot=ResultSlot.from_dict(record["slot"]), committer=committer)
    factory.bind_handoff(cycle.plan.identity, port)
    return port


def preflight_handoff(factory, launch, completion_plan, *, require_slot=True):
    from .work_hygiene import LocalCommitPolicy
    require(completion_plan.get("kind") == "coding"
            and isinstance(getattr(factory, "local_commit_policy", None), LocalCommitPolicy),
            "modern coding needs an approved local commit profile")
    from .work_lifetime import require_grant_lifetime
    require_grant_lifetime(launch.grant, getattr(factory,"baseline_wall_seconds",0)
        + getattr(factory,"request_wall_seconds",factory.local_commit_policy.timeout_seconds+13))
    rules = {rule.tool:rule for rule in launch.grant.tool_rules}
    require("herdr_verify_work" in launch.grant.scope.tools
            and "herdr_submit_result" in launch.grant.scope.tools
            and "herdr_verify_work" in rules and "herdr_submit_result" in rules
            and set(rules["herdr_verify_work"].allowed_arg_keys) == {"request_id","handoff"}
            and (not require_slot or rules["herdr_submit_result"].result_slot is not None),
            "closed verification and immutable result capabilities required before baseline")
