"""Private SDK configuration contracts; no provider, native launch or economic authority."""
import hashlib
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from herdr import host_bootstrap, private_profile_namespace as profile
from herdr.policy_launch import FrozenTree
from herdr.security import InvocationIdentity

REPO = Path(__file__).resolve().parents[2]
POLICY = {"schema_version": 1, "managed_scope": "none", "fallback_chain": "empty"}
MEMBER = "herdr-sdk-policy.json"


@pytest.fixture(autouse=True)
def preserve_policy_environment(monkeypatch):
    for key in ("HERMES_HOME", "HERMES_MANAGED_DIR", "HERMES_SAFE_MODE", "HERMES_ENABLE_PROJECT_PLUGINS"):
        monkeypatch.setenv(key, os.environ.get(key, ""))


def make_profile(tmp_path, config=None, policy=POLICY):
    root = tmp_path / "approved"
    root.mkdir()
    values = {"config.yaml": json.dumps(config if config is not None else {
        "fallback_providers": [], "fallback_model": []}).encode(), ".env": b"DUMMY=unit-only\n"}
    if policy is not None:
        values[MEMBER] = json.dumps(policy).encode()
    for name, body in values.items():
        (root / name).write_bytes(body)
    snapshot = profile.PrivateProfileSnapshot.from_approved(root, name="quantlab",
        approved_sha256={name: hashlib.sha256(body).hexdigest() for name, body in values.items()})
    return snapshot, values


def load_stage1():
    loader = importlib.machinery.SourceFileLoader("private_sdk_stage1_unit", str(REPO / "agent-stack/bin/agent-hermes-policy-stage1"))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def test_actual_private_bootstrap_producer_binds_frozen_profile(tmp_path):
    snapshot, values = make_profile(tmp_path)
    code = tmp_path / "code"; code.mkdir()
    names = (host_bootstrap.SHIM_SOURCE, host_bootstrap.STAGE1_SOURCE, host_bootstrap.STAGE2_SOURCE)
    for name in names:
        path = code / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(b"unit-only public code\n")
    storage = tmp_path / "storage"; storage.mkdir()
    frozen = FrozenTree.create(code, target=Path("/run/herdr/policy-code"),
        files={name: hashlib.sha256((code / name).read_bytes()).hexdigest() for name in names},
        executable_files=(), storage=storage, writable_roots=())
    identity = InvocationIdentity("github:unit/repo", "agent", "coordinator", "parent", "task", "run", 1)
    launch = SimpleNamespace(identity=identity, private_profile_snapshot=snapshot,
        mount=SimpleNamespace(code=frozen, runtime=()))
    bootstrap = None
    try:
        bootstrap = host_bootstrap.HostBootstrap.create(launch, storage=storage, writable_roots=())
        assert bootstrap.proof["schema_version"] == "herdr-policy-bootstrap-2"
        assert bootstrap.proof["approved_profile"] == snapshot.identity
    finally:
        if bootstrap is not None: bootstrap.cleanup_after_pane_closed()
        snapshot.close(); frozen.cleanup_after_pane_closed()


def test_actual_stage1_accepts_authenticated_profile_v2(tmp_path, monkeypatch):
    module = load_stage1(); snapshot, _ = make_profile(tmp_path)
    identity = {"consumer":"github:unit/repo","agent_id":"agent","parent_agent_id":"coordinator",
        "parent_task_id":"parent","task_id":"task","run_token":"run","fencing_token":1}
    proof = {"schema_version":"herdr-policy-bootstrap-2", "authority":"herdr-host-frozen-tree",
        "identity":identity,"trees":{str(p):{"device":1,"inode":2,"source_digest":"a"*64,"snapshot_kind":"host-frozen-copy"}
            for p in (module.POLICY_CODE_ROOT,module.HERMES_ROOT,module.PYTHON_ROOT)},"approved_profile":snapshot.identity}
    path = tmp_path / "proof.json"; path.write_text(json.dumps(proof))
    monkeypatch.setattr(module, "_identity_from_env", lambda: identity)
    try: assert module._read_proof(path)[0] == proof
    finally: snapshot.close()


def test_worker_uses_protected_root_model_projection(tmp_path):
    """Compile exact worker argv/continuation fragments; not ordinary-worker execution."""
    import ast
    from herdr.work_configuration import reviewed_root_model_arguments
    from herdr.work_cycle import WorkContractError
    tree = ast.parse((REPO / "agent-stack/bin/agent-task-worker").read_text())
    assignments = [node for node in ast.walk(tree) if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "root_model_args" for target in node.targets)]
    starts = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name) and node.func.id == "start_sandbox_agent"]
    continuations = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
        and node.name == "publish_continuation"]
    assert len(assignments) == len(starts) == len(continuations) == 1
    snapshot, _ = make_profile(tmp_path)
    factory = model_factory(tmp_path)
    task = {"model": "attacker/model", "parent_tools": []}
    events = []
    def bind_original(*args, **kwargs):
        assert args[:2] == (factory, task) and kwargs["recheck"] is True
        events.append("bind")
    def persist_actual_task(value):
        assert value is task
        events.append("persist")
    namespace = {"reviewed_root_model_arguments": reviewed_root_model_arguments,
        "work_factory": factory, "private_snapshot": snapshot, "task": task,
        "profile": "quantlab", "session_name": "unit-session", "workspace": str(tmp_path),
        "launch": object(), "session": {}, "bind_reviewed_parent": bind_original,
        "persist_execution_session": persist_actual_task}
    try:
        exec(compile(ast.Module(body=assignments, type_ignores=[]), "worker-model-assignment", "exec"), namespace)
        argv = eval(compile(ast.Expression(body=starts[0].args[5]), "worker-hermes-argv", "eval"), namespace)
        assert argv[:5] == ["-p", "quantlab", "chat", "--model", "unit/model"]
        assert argv.count("--model") == 1 and "attacker/model" not in argv
        assert not any(arg in ("--no-fallback", "--fallback-model") for arg in argv)
        exec(compile(ast.Module(body=continuations, type_ignores=[]), "worker-continuation", "exec"), namespace)
        task["model"] = "another/attacker"
        assert namespace["publish_continuation"]({"unit": "evidence"}) is True
        assert events == ["bind", "persist"]
        events.clear()
        factory.budget_quotes["unit-route"]["model"] = "drift/route"
        with pytest.raises(WorkContractError):
            namespace["publish_continuation"]({"unit": "changed"})
        assert events == ["bind"]  # Drift is denied before persistence/ACK.
        assert not (tmp_path / "unused.jsonl").exists()
    finally:
        snapshot.close()


@pytest.mark.parametrize("mutation", ["unknown", "bool-version", "bad-mode", "duplicate", "bad-json"])
def test_present_invalid_policy_is_denied_without_raw_config(tmp_path, mutation):
    raw = json.dumps(POLICY).encode()
    if mutation == "unknown": raw = b'{"schema_version":1,"managed_scope":"none","fallback_chain":"empty","secret":"DONT-EXPORT"}'
    elif mutation == "bool-version": raw = b'{"schema_version":true,"managed_scope":"none","fallback_chain":"empty"}'
    elif mutation == "bad-mode": raw = b'{"schema_version":1,"managed_scope":"host","fallback_chain":"empty"}'
    elif mutation == "duplicate": raw = b'{"schema_version":1,"managed_scope":"none","managed_scope":"none","fallback_chain":"empty"}'
    else: raw = b'BROKEN-DONT-EXPORT'
    config = b'{"fallback_providers":[],"fallback_model":[],"private":"DONT-EXPORT"}'
    files = {MEMBER:hashlib.sha256(raw).hexdigest(),"config.yaml":hashlib.sha256(config).hexdigest(),".env":"a"*64}
    with pytest.raises(profile.PrivateProfileError) as caught:
        profile.private_sdk_policy(profile.profile_identity("quantlab", files), raw, config)
    assert "DONT-EXPORT" not in str(caught.value)


@pytest.mark.parametrize("config", [
    {"fallback_providers":[]}, {"fallback_providers":[],"fallback_model":None},
    {"fallback_providers":[{"provider":"unit","model":"${LATER}"}],"fallback_model":[]},
    {"fallback_providers":[],"fallback_model":[{"provider":"unit","model":"other"}]},
    {"fallback_providers":"${CHAIN}","fallback_model":[]},
])
def test_literal_empty_fields_required_even_if_env_currently_empty(tmp_path, config):
    with pytest.raises(profile.PrivateProfileError,match="fallback_not_empty"):
        make_profile(tmp_path,config=config)


@pytest.mark.parametrize("raw", [b'fallback_providers: []\nfallback_model: []\n',
    b'{"fallback_providers":[],"fallback_model":[],"fallback_model":[]}',
    b'{"fallback_providers":[],"fallback_model":[],"x":NaN}'])
def test_json_only_no_yaml_or_duplicate_or_nonfinite_fallback(tmp_path, raw):
    policy = json.dumps(POLICY).encode()
    files={MEMBER:hashlib.sha256(policy).hexdigest(),"config.yaml":hashlib.sha256(raw).hexdigest(),".env":"a"*64}
    with pytest.raises(profile.PrivateProfileError):
        profile.private_sdk_policy(profile.profile_identity("quantlab",files),policy,raw)


def test_legacy_profile_yaml_without_member_is_unchanged(tmp_path):
    snapshot,_=make_profile(tmp_path,policy=None)
    try: assert snapshot.sdk_policy() is None
    finally: snapshot.close()


def proof_fixture(module, approved=None, version=2):
    identity={"consumer":"github:unit/repo","agent_id":"agent","parent_agent_id":"coordinator",
        "parent_task_id":"parent","task_id":"task","run_token":"run","fencing_token":1}
    value={"schema_version":"herdr-policy-bootstrap-"+str(version),"authority":"herdr-host-frozen-tree",
        "identity":identity,"trees":{str(p):{"device":1,"inode":2,"source_digest":"a"*64,"snapshot_kind":"host-frozen-copy"}
        for p in (module.POLICY_CODE_ROOT,module.HERMES_ROOT,module.PYTHON_ROOT)}}
    if version==2:value["approved_profile"]=approved
    return value


@pytest.mark.parametrize("mutation", ["missing", "hash", "unknown", "path", "bool", "future-version"])
def test_stage1_private_proof_closed_denials(tmp_path,monkeypatch,mutation):
    module=load_stage1();snapshot,_=make_profile(tmp_path)
    try:
        value=proof_fixture(module,snapshot.identity)
        if mutation=="missing":value.pop("approved_profile")
        elif mutation=="hash":value["approved_profile"]["manifest_sha256"]="f"*64
        elif mutation=="unknown":value["approved_profile"]["unused"]=1
        elif mutation=="path":value["approved_profile"]["files"]["../config"]="a"*64
        elif mutation=="bool":value["approved_profile"]["files"]["config.yaml"]=True
        else:value["schema_version"]="herdr-policy-bootstrap-3"
        path=tmp_path/"proof.json";path.write_text(json.dumps(value))
        monkeypatch.setattr(module,"_identity_from_env",lambda:value["identity"])
        with pytest.raises(SystemExit):module._read_proof(path)
    finally:snapshot.close()


def test_stage1_historical_private_v1_stays_readable(tmp_path,monkeypatch):
    module=load_stage1();value=proof_fixture(module,version=1)
    path=tmp_path/"proof.json";path.write_text(json.dumps(value))
    monkeypatch.setattr(module,"_identity_from_env",lambda:value["identity"])
    assert module._read_proof(path)[0]==value


def load_launcher():
    loader=importlib.machinery.SourceFileLoader("private_sdk_launcher_unit",str(REPO/"agent-stack/bin/agent-hermes-policy-run"))
    spec=importlib.util.spec_from_loader(loader.name,loader);module=importlib.util.module_from_spec(spec);loader.exec_module(module)
    return module


def mounted_fixture(tmp_path,monkeypatch):
    module=load_launcher();home=tmp_path/"home";root=home/".hermes/profiles/quantlab";root.mkdir(parents=True)
    values={MEMBER:json.dumps(POLICY).encode(),"config.yaml":b'{"fallback_providers":[],"fallback_model":[]}',".env":b'DUMMY=unit\n'}
    for name,body in values.items():(root/name).write_bytes(body)
    approved=profile.profile_identity("quantlab",{name:hashlib.sha256(body).hexdigest() for name,body in values.items()})
    monkeypatch.setattr(profile,"_HOME",home)
    monkeypatch.setattr(profile,"MANAGED_SENTINEL",tmp_path/"immutable-code/no-managed")
    monkeypatch.setattr(module,"POLICY_CODE_ROOT",REPO)
    monkeypatch.setattr(module,"_covering_mount",lambda path:(home,{"ro"}))
    monkeypatch.setattr(module,"_mountpoint_count",lambda path:1)
    checks=[]
    monkeypatch.setattr(module,"_require_production_mount",lambda path,**kw:checks.append((path,kw)))
    return module,home,root,approved,checks


def test_stage2_authenticated_manifest_enables_only_exact_selected_profile(tmp_path,monkeypatch):
    module,home,root,approved,checks=mounted_fixture(tmp_path,monkeypatch)
    value={"schema_version":"herdr-policy-bootstrap-2","approved_profile":approved}
    policy=module._verified_private_sdk_policy(value,["-p","quantlab","chat"])
    assert policy.profile_sha256==approved["manifest_sha256"]
    assert set(path for path,_ in checks)=={root/MEMBER,root/"config.yaml",REPO}
    assert os.environ["HERMES_HOME"]==str(root)
    assert os.environ["HERMES_MANAGED_DIR"]==str(profile.MANAGED_SENTINEL)
    assert "DUMMY" not in repr(policy)


@pytest.mark.parametrize("mutation",["body","config-body","alias","profile","duplicate-profile","mount","sentinel","manifest"])
def test_stage2_member_path_hash_mount_and_selection_spoofs_deny(tmp_path,monkeypatch,mutation):
    module,home,root,approved,_=mounted_fixture(tmp_path,monkeypatch)
    value={"schema_version":"herdr-policy-bootstrap-2","approved_profile":approved};args=["-p","quantlab","chat"]
    if mutation=="body":(root/MEMBER).write_text('{"changed":true}')
    elif mutation=="config-body":(root/"config.yaml").write_text('{"fallback_providers":[],"fallback_model":["changed"]}')
    elif mutation=="alias":(root/MEMBER).rename(root/"original");(root/MEMBER).symlink_to(root/"original")
    elif mutation=="profile":args=["-p","other","chat"]
    elif mutation=="duplicate-profile":args.extend(["--profile","quantlab"])
    elif mutation=="mount":monkeypatch.setattr(module,"_covering_mount",lambda path:(home,{"rw"}))
    elif mutation=="sentinel":profile.MANAGED_SENTINEL.parent.mkdir();profile.MANAGED_SENTINEL.mkdir()
    else:approved["manifest_sha256"]="b"*64
    with pytest.raises(SystemExit,match="private SDK configuration rejected"):
        module._verified_private_sdk_policy(value,args)


def test_v2_without_approved_member_cannot_opt_in_by_same_named_file(tmp_path, monkeypatch):
    module, home, root, approved, _ = mounted_fixture(tmp_path, monkeypatch)
    files = dict(approved["files"]); files.pop(MEMBER)
    approved = profile.profile_identity("quantlab", files)
    monkeypatch.setenv("HERMES_MANAGED_DIR", str(tmp_path / "attacker"))
    monkeypatch.setattr(module.os, "open", lambda *a, **k: pytest.fail("unapproved member must not be read"))
    assert module._verified_private_sdk_policy(
        {"schema_version": "herdr-policy-bootstrap-2", "approved_profile": approved},
        ["-p", "quantlab"]) is None
    assert os.environ["HERMES_MANAGED_DIR"] == str(tmp_path / "attacker")


def test_historical_v1_same_named_ro_file_or_environment_cannot_opt_in(tmp_path,monkeypatch):
    module=load_launcher()
    monkeypatch.setenv("HERMES_MANAGED_DIR",str(tmp_path/"attacker"))
    monkeypatch.setattr(module.os,"open",lambda *a,**k:pytest.fail("v1 must not inspect a policy member"))
    assert module._verified_private_sdk_policy({"schema_version":"herdr-policy-bootstrap-1"},["-p","quantlab"]) is None
    assert os.environ["HERMES_MANAGED_DIR"]==str(tmp_path/"attacker")


def model_factory(tmp_path,model="unit/model",fallback=None):
    from herdr.check_runner import CheckEnvironment
    from herdr.scheduler import AuditLog
    from herdr.taskgraph import TaskGraph
    from herdr.work_contract_host import HostWorkContractFactory
    executable=Path(__import__("sys").executable).resolve()
    env=CheckEnvironment("inert-model-projection",((str(executable),hashlib.sha256(executable.read_bytes()).hexdigest()),),(str(executable),))
    def no_operation(**kwargs):pytest.fail("projection must not invoke a work/budget authority")
    factory=HostWorkContractFactory(approve=no_operation,environment=env,storage=tmp_path/"unused",audit_log=AuditLog(tmp_path/"unused.jsonl"))
    graph=TaskGraph.parse_planner_output({"envelope":{"issue":"unit/repo#1","spec_hash":"a"*64,"graph_version":"1.1.0","created_at":"2026-10-21T00:00:00Z","planner":"unit-only","max_nodes":1,"max_depth":1,"max_fanout":1,"policy_profile":"quantlab-paper"},
        "nodes":[{"id":"root","parent_id":None,"type":"task","role":"writer","objective":"Synthetic model projection only","inputs":[],"expected_outputs":[],"priority":0,"resource_class":"small","dependencies":[],"model_policy":{"model":model,"fallback_model":fallback},"tools":[],"permissions":[],"timeout_seconds":30,"max_attempts":1}]})
    quote={"provider":"unit","model":model,"api_mode":"openai","base_url":"https://unit.invalid/v1","max_tokens":100,"max_output_tokens":10,"max_request_bytes":90,"max_cost_microusd":0,"max_work_ms":1000}
    factory.host_admission={"definition":{"reviewed_graph":{"version":1,"graph_sha256":graph.graph_hash(),"graph":graph.to_planner_json()},"budget":{"model_quotes":[quote]}}}
    factory.budget_quotes={"unit-route":dict(quote)}
    return factory


def test_root_model_from_original_admission_ignores_task_model(tmp_path):
    from herdr.work_configuration import reviewed_root_model_arguments
    snapshot,_=make_profile(tmp_path);factory=model_factory(tmp_path)
    task={"model":"attacker/model"};factory.task=task
    try:
        assert reviewed_root_model_arguments(factory,snapshot)==["--model","unit/model"]
        task["model"]="changed/again"
        assert reviewed_root_model_arguments(factory,snapshot)==["--model","unit/model"]
        assert not (tmp_path/"unused.jsonl").exists() and factory.budget_authority is None
    finally:snapshot.close()


@pytest.mark.parametrize("mutation",["wrong-model","duplicate","no-quotes","runtime-quote","graphhash","nonnull-fallback","missing-policy"])
def test_root_model_route_or_null_policy_drift_denied(tmp_path,mutation):
    from herdr.work_configuration import reviewed_root_model_arguments
    from herdr.work_cycle import WorkContractError
    snapshot,_=make_profile(tmp_path,policy=None if mutation=="missing-policy" else POLICY)
    factory=model_factory(tmp_path,fallback="other" if mutation=="nonnull-fallback" else None)
    d=factory.host_admission["definition"]
    if mutation=="wrong-model":d["budget"]["model_quotes"][0]["model"]="other"
    elif mutation=="duplicate":d["budget"]["model_quotes"]*=2
    elif mutation=="no-quotes":d["budget"]["model_quotes"]=[]
    elif mutation=="runtime-quote":factory.budget_quotes["unit-route"]["base_url"]="https://other.invalid"
    elif mutation=="graphhash":d["reviewed_graph"]["graph_sha256"]="f"*64
    try:
        with pytest.raises(WorkContractError):reviewed_root_model_arguments(factory,snapshot)
        assert not (tmp_path/"unused.jsonl").exists()
    finally:snapshot.close()


def test_legacy_no_reviewed_graph_keeps_model_arguments_unchanged(tmp_path):
    from herdr.work_configuration import reviewed_root_model_arguments
    factory=model_factory(tmp_path);factory.host_admission["definition"].pop("reviewed_graph")
    assert reviewed_root_model_arguments(None,None)==[]
    assert reviewed_root_model_arguments(factory,None)==[]


@pytest.mark.parametrize("chain", [None, {}, [{"provider":"unit","model":"other"}]])
def test_guard_checks_actual_agent_chain_before_any_request(tmp_path,monkeypatch,chain):
    import sys,types
    from herdr import hermes_guard
    module,home,root,approved,_=mounted_fixture(tmp_path,monkeypatch)
    policy=module._verified_private_sdk_policy({"schema_version":"herdr-policy-bootstrap-2","approved_profile":approved},["-p","quantlab"])
    package=types.ModuleType("hermes_cli");config=types.ModuleType("hermes_cli.config")
    config.get_config_path=lambda:root/"config.yaml";package.config=config
    monkeypatch.setitem(sys.modules,"hermes_cli",package);monkeypatch.setitem(sys.modules,"hermes_cli.config",config)
    with pytest.raises(Exception,match="private_sdk_fallback_not_empty"):
        hermes_guard._check_private_sdk_agent(policy,SimpleNamespace(_fallback_chain=chain))
    hermes_guard._check_private_sdk_agent(policy,SimpleNamespace(_fallback_chain=[]))


@pytest.mark.parametrize("full_guard", [False, True])
def test_pinned_sdk_dotenv_managed_and_effective_reload_without_external_calls(tmp_path, full_guard):
    """One optional SDK component case; the remaining contracts need neither SDK nor bwrap.

    Executes config/dotenv functions only, never Hermes.main(), CLI.run(), auth or a model.
    Socket/DNS tripwires supplement the controlled dummy inputs; no physical NET claim.
    """
    import subprocess
    sdk=Path('/opt/herdr/releases/p0-5035d92-test/hermes')
    python=Path('/opt/herdr/releases/p0-5035d92-test/python/bin/python3.11')
    if not sdk.is_dir() or not python.is_file():pytest.skip("pinned public SDK component unavailable")
    script=r"""
import ast,hashlib,json,os,re,socket,sys
from pathlib import Path
repo,sdk,tmp=map(Path,sys.argv[1:4])
full_guard=sys.argv[5]=="1"
sys.path[:0]=[str(repo),str(sdk),str(sdk/'venv/lib/python3.11/site-packages')]
def network_denied(*a,**k):raise AssertionError('component attempted external network')
socket.socket.connect=network_denied
socket.socket.connect_ex=network_denied
socket.getaddrinfo=network_denied
home=tmp/'home';selected=home/'.hermes/profiles/quantlab';selected.mkdir(parents=True)
config={'fallback_providers':[],'fallback_model':[],'model':{'provider':'none','default':'unit-only'}}
raw=json.dumps(config).encode();(selected/'config.yaml').write_bytes(raw)
it=tmp/'host-managed';it.mkdir();(it/'config.yaml').write_text('fallback_model:\n  provider: unit\n  model: forbidden\n')
(it/'.env').write_text('MANAGED_DUMMY=must-not-load\n')
(selected/'.env').write_text('HERMES_MANAGED_DIR='+str(it)+'\nHERMES_HOME='+str(tmp/'wrong')+'\n')
os.environ.update(HOME=str(home),HERMES_HOME=str(selected),HERMES_MANAGED_DIR=str(tmp/'absent-initial'),HERMES_SAFE_MODE='1',HERMES_ENABLE_PROJECT_PLUGINS='0')
from herdr import private_profile_namespace as p,hermes_guard as guard
p._HOME=home;p.MANAGED_SENTINEL=tmp/'immutable-code/no-managed-scope'
policy=p.PrivateSDKPolicy('quantlab','a'*64,hashlib.sha256(raw).hexdigest());policy.reassert()
if full_guard:
 from herdr.security import InvocationGuard,SecurityGrant
 installation=guard.install_hermes_guard(InvocationGuard(SecurityGrant.from_dict(json.loads(sys.argv[4]))),private_sdk_policy=policy)

# Execute exact selected public profile-parser functions, not main's unrelated import-time startup.
source=sdk/'hermes_cli/main.py'
assert hashlib.sha256(source.read_bytes()).hexdigest()=='5f24d7022c1c5213d9d3fcec8b4c21280cc2778e23c7d339d157ced8223c3f74'
tree=ast.parse(source.read_text())
names={'_inside_mcp_add_args','_looks_like_hermes_invocation','_exit_invalid_profile_name','_looks_like_option_value','_scan_profile_flag','_apply_profile_override'}
body=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name in names]
assert len(body)==len(names)
namespace={'os':os,'sys':sys,'Path':Path,'re':re,'_PROFILE_NAME_RE':r'^[a-z0-9][a-z0-9_-]{0,63}$'}
exec(compile(ast.Module(body=body,type_ignores=[]),str(source),'exec'),namespace)
sys.argv=['hermes','-p','quantlab','chat'];namespace['_apply_profile_override']()
assert os.environ['HERMES_HOME']==str(selected),os.environ['HERMES_HOME']
assert sys.argv==['hermes','chat']
from hermes_cli import config as c,env_loader,managed_scope,config_effective,fallback_config
if not full_guard:
 # The legitimate managed layer still works when this explicit policy is absent.
 os.environ['HERMES_MANAGED_DIR']=str(it)
 assert fallback_config.get_fallback_chain(c.load_config())[0]['model']=='forbidden'
 policy.reassert()
 installation=guard.GuardInstallation(guard=None,surface={})
 guard._install_dotenv_environment(installation,policy)
 guard._install_private_sdk_configuration(installation,policy)
# A source changes relocation values AFTER dotenv layers, immediately before managed lookup.
def external_source(_):
 os.environ['HERMES_MANAGED_DIR']=str(it);os.environ['HERMES_HOME']=str(tmp/'wrong')
env_loader._apply_external_secret_sources=external_source
for turn in range(3):
 env_loader.load_hermes_dotenv(hermes_home=selected,load_external_secrets=True)
 assert os.environ['HERMES_HOME']==str(selected)
 assert os.environ['HERMES_MANAGED_DIR']==str(p.MANAGED_SENTINEL)
 assert 'MANAGED_DUMMY' not in os.environ
 assert c.get_config_path()==selected/'config.yaml'
 assert fallback_config.get_fallback_chain(c.load_config())==[]
 assert fallback_config.get_fallback_chain(config_effective.load_user_config_effective(fail_closed=True))==[]
 assert (selected/'config.yaml').read_bytes()==raw
from hermes_constants import set_hermes_home_override,reset_hermes_home_override
token=set_hermes_home_override(tmp/'wrong')
try:
 try:c.get_config_path()
 except p.PrivateProfileError:pass
 else:raise AssertionError('context-local config relocation accepted')
finally:reset_hermes_home_override(token)
print(json.dumps({'pinned_sdk_config_reload':True,'turns':3,'explicit_profile_same_home':True,'managed_env_blocked':True,'context_override_denied':True,'sdk_main_or_model_run':False}))
"""
    from tests.herdr.test_security import grant as unit_grant
    workspace=tmp_path/'workspace';workspace.mkdir()
    grant_json=json.dumps(unit_grant(workspace).to_json())
    env={'PATH':'/usr/bin:/bin','HOME':str(tmp_path/'launch-home'),'LANG':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1'}
    result=subprocess.run([str(python),'-I','-B','-c',script,str(REPO),str(sdk),str(tmp_path),grant_json,"1" if full_guard else "0"],
        capture_output=True,text=True,env=env,timeout=45)
    assert result.returncode==0,result.stdout+result.stderr
    assert json.loads(result.stdout.splitlines()[-1])['turns']==3


@pytest.mark.parametrize("version", [1,2])
def test_actual_retained_projection_reads_historical_v1_and_binds_v2(tmp_path,version):
    identity=InvocationIdentity("github:unit/repo","agent","coordinator","parent","task","run",1)
    snapshot,_=make_profile(tmp_path)
    try:
        approved=snapshot.identity
        evidence={"approved_profile":approved,"code_sha256":"a"*64,
            "runtime_sha256":{"/runtime":"b"*64},"tree_identities":{
                "/run/herdr/policy-code":{"device":1,"inode":2},"/runtime":{"device":3,"inode":4}}}
        trees={name:{**row,"source_digest":evidence["code_sha256"] if name=="/run/herdr/policy-code" else evidence["runtime_sha256"][name],"snapshot_kind":"host-frozen-copy"} for name,row in evidence["tree_identities"].items()}
        proof=host_bootstrap.bootstrap_proof(identity,trees,approved_profile=approved if version==2 else None)
        raw=json.dumps(proof,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
        assert host_bootstrap.retained_bootstrap_proof(evidence,identity,raw)==proof
        if version==2:
            changed=dict(evidence);changed["approved_profile"]=profile.profile_identity("other",approved["files"])
            with pytest.raises(Exception,match="retained bootstrap profile/identity mismatch"):
                host_bootstrap.retained_bootstrap_proof(changed,identity,raw)
        else:
            # Old private evidence cannot smuggle a profile/member into proof1.
            assert "approved_profile" not in proof
    finally:snapshot.close()


def test_v2_producer_profile_payload_is_detached(tmp_path):
    identity=InvocationIdentity("github:unit/repo","agent","coordinator","parent","task","run",1)
    snapshot,_=make_profile(tmp_path)
    try:
        original=snapshot.identity;proof=host_bootstrap.bootstrap_proof(identity,{},approved_profile=original)
        original["files"]["config.yaml"]="b"*64
        assert proof["approved_profile"]==snapshot.identity
    finally:snapshot.close()
