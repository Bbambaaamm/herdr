"""Pinned external SDK components; portable tests do not require its installation.

The child runs actual SDK dispatch or only the original CLI constructor, never
main/run/chat/conversation/agent constructor/model/native/server.
"""
from pathlib import Path
import json
import os
import subprocess

import pytest

SDK = Path("/opt/herdr/releases/p0-5035d92-test/hermes")
PYTHON = Path("/opt/herdr/releases/p0-5035d92-test/python/bin/python3.11")
PINS = {'cli.py': '267c7566b53c079b9f9c69794231d4f8e5907939f6167a2f96e4cff671c18b25', 'agent/turn_facade.py': '09675cbc96c72d8f01a2a44712da2b508b2fda5d35c1b6f004edc781a588f38c', 'agent/tool_executor.py': '38585996a589dd87406bd6206e05b49c3e0e1c9fa2321f874c1c4d5c891b0e9e', 'tools/file_tools_paths.py': 'd82790c20d643c94b374f962065c26a254307b78ba3a9b86cda200b7afffbf2d'}

SCRIPT = r"""
from pathlib import Path
from types import SimpleNamespace
import hashlib,json,os,socket,subprocess,sys,traceback
repo,sdk,scratch=map(Path,sys.argv[1:4])
case=sys.argv[4]
sys.path[:0]=[str(repo),str(sdk),str(sdk/"venv/lib/python3.11/site-packages")]
for member,expected in json.loads(sys.argv[6]).items():
    assert hashlib.sha256((sdk/member).read_bytes()).hexdigest()==expected
network_attempts=[]
blocked_local_bootstrap=[]
unexpected_process_attempts=[]
def forbidden(*args,**kwargs):
    network_attempts.append(True)
    raise AssertionError("network forbidden in SDK component")
def forbidden_process(*args,**kwargs):
    # The original SDK lazily bootstraps its local file backend, then catches
    # this denial. Never run that optional shell in a file-identity component.
    names={frame.name for frame in traceback.extract_stack(limit=12)}
    if "_run_bash" in names and "init_session" in names:
        blocked_local_bootstrap.append(True)
    else:
        unexpected_process_attempts.append(True)
    raise AssertionError("process forbidden in SDK component")
socket.socket.connect=forbidden
socket.socket.connect_ex=forbidden
socket.create_connection=forbidden
socket.getaddrinfo=forbidden
subprocess.Popen=forbidden_process
os.system=forbidden_process
home=Path(os.environ["HOME"]);profile=Path(os.environ["HERMES_HOME"])
profile.mkdir(parents=True)
raw=json.dumps({"display":{"cli_multiline_shortcuts":False},
                "fallback_models":[],"auxiliary":{"fallback_models":[]}}).encode()
(profile/"config.yaml").write_bytes(raw)
from herdr.security import InvocationGuard,SecurityGrant
from herdr.hermes_cli_identity import CLIInvocationBinding
from herdr.hermes_guard import install_hermes_guard
from herdr import hermes_terminal_transport as transport
from run_agent import AIAgent
from cli import HermesCLI
from agent import tool_executor
from agent.tool_guardrails import ToolCallGuardrailController
import model_tools
from tools import terminal_tool
item=InvocationGuard(SecurityGrant.from_dict(json.loads(sys.argv[5])))
phase_calls=[]
if case=="work":
    from herdr.work_contract_host import WorkInvocationGuard
    def phase(identity,grant_sha256,**kwargs):
        phase_calls.append((identity,grant_sha256))
        return True  # Explicit unit host-phase port, no IPC/authority.
    item=WorkInvocationGuard(item.grant,work_authority=phase)
workspace=Path(item.grant.workspace_root);workspace.mkdir()
binding=CLIInvocationBinding(item)
installation=install_hermes_guard(item,cli_invocation_binding=binding)
try:
    if case=="constructor":
        from herdr import private_profile_namespace as private
        private._HOME=home  # Existing synthetic sealed-profile filesystem seam.
        sealed=profile/"profiles/native";sealed.mkdir(parents=True)
        (sealed/"config.yaml").write_bytes(raw)
        policy=private.PrivateSDKPolicy("native","b"*64,hashlib.sha256(raw).hexdigest())
        original_init=HermesCLI.__init__
        original_run=AIAgent.run_conversation
        original_chat=HermesCLI.chat
        with transport.native_cli_transport_factory(
                HermesCLI,item,private_sdk_policy=policy):
            native_init=HermesCLI.__init__
            with binding.factory(HermesCLI,AIAgent):
                cli=HermesCLI(model="unit-model",provider="openai",
                    api_key="unit-not-a-credential",
                    base_url="https://unit.example.invalid/v1",max_turns=1,run_budget=1,
                    toolsets=["file"],ignore_rules=True)
                assert cli.agent is None  # No agent constructor or model call.
                assert cli.session_id and cli.config["display"]["cli_multiline_shortcuts"] is False
                assert AIAgent.run_conversation.__wrapped__ is original_run
                assert HermesCLI.chat is original_chat
                handle=cli._tui_handle_enter.__self__
                assert handle._installed
                assert any(ref() is cli for ref in binding._owners)
            assert HermesCLI.__init__ is native_init
        assert HermesCLI.__init__ is original_init
        assert AIAgent.run_conversation is original_run
        assert not handle._installed
        print(json.dumps({"constructor_composition":True,"original_methods_restored":True,
                          "sdk_main_or_agent_calls":0,"network_attempts":len(network_attempts),
                          "blocked_local_bootstrap_attempts":len(blocked_local_bootstrap)}))
    else:
        elsewhere=scratch/"different-default";elsewhere.mkdir()
        (workspace/"component.txt").write_text("before\n")
        (elsewhere/"component.txt").write_text("wrong-default\n")
        cli=object.__new__(HermesCLI);cli.session_id="actual-sdk-session"
        agent=object.__new__(AIAgent);agent.session_id=cli.session_id;agent.platform="cli"
        agent._tool_guardrails=ToolCallGuardrailController()
        agent.quiet_mode=True;agent.verbose_logging=False;agent.tool_progress_mode="off"
        agent.tool_progress_callback=agent.tool_start_callback=None
        agent._checkpoint_mgr=SimpleNamespace(enabled=False);agent._session_db=None
        cli.agent=agent
        binding._active=True;binding._agent_type=AIAgent;binding._register(cli)
        terminal_tool.record_session_cwd(cli.session_id,str(workspace))
        terminal_tool.record_session_cwd(item.grant.identity.task_id,str(elsewhere))
        def dispatch(name,args):
            return tool_executor._run_agent_tool_execution_middleware(
                agent,function_name=name,function_args=args,effective_task_id=cli.session_id,
                tool_call_id="unit-call",execute=lambda final:
                model_tools.handle_function_call(name,final,task_id=cli.session_id))
        assert "HERDR_SECURITY_DENIED" in str(model_tools.handle_function_call(
            "read_file",{"path":"component.txt"},task_id=cli.session_id))
        with binding.turn(agent,cli.session_id):
            result=dispatch("read_file",{"path":"component.txt","offset":1,"limit":10})
            assert "before" in str(result.result) and "wrong-default" not in str(result.result)
            result=dispatch("write_file",{"path":"component.txt","content":"after\n"})
            assert "HERDR_SECURITY_DENIED" not in str(result.result)
            assert (workspace/"component.txt").read_text()=="after\n"
            assert (elsewhere/"component.txt").read_text()=="wrong-default\n"
            assert "after" in str(dispatch("read_file",{"path":"component.txt","offset":1,"limit":10}).result)
            assert cli.session_id==agent.session_id!=item.grant.identity.task_id
        result=dispatch("write_file",{"path":"component.txt","content":"DENIED\n"})
        assert "HERDR_SECURITY_DENIED" in str(result.result)
        assert (workspace/"component.txt").read_text()=="after\n"
        if case=="work":
            assert phase_calls and all(i==item.grant.identity and h==item.grant.hash for i,h in phase_calls)
        terminal_tool.clear_session_cwd(cli.session_id)
        terminal_tool.clear_session_cwd(item.grant.identity.task_id)
        print(json.dumps({"actual_sdk_file_flow":True,"original_session_namespace":True,
                          "work_guard":case=="work","network_attempts":len(network_attempts),
                          "blocked_local_bootstrap_attempts":len(blocked_local_bootstrap)}))
    assert not network_attempts and not unexpected_process_attempts
    assert len(blocked_local_bootstrap)==(0 if case=="constructor" else 2)
finally:
    installation.uninstall()
    binding.close()
"""


@pytest.mark.parametrize("case", ("invocation", "work", "constructor"))
def test_actual_pinned_sdk_identity_component(tmp_path, case):
    if not SDK.is_dir() or not PYTHON.is_file():
        pytest.skip("fixed pinned Hermes SDK component is not installed")
    from test_hermes_cli_identity import guard
    repo = Path(__file__).resolve().parents[2]
    home = tmp_path / "home"
    home.mkdir()
    item = guard(tmp_path / "allowed")
    result = subprocess.run(
        [str(PYTHON), "-I", "-B", "-c", SCRIPT, str(repo), str(SDK),
         str(tmp_path), case, json.dumps(item.grant.to_json()), json.dumps(PINS)],
        stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=45,
        env={"PATH": "/usr/bin:/bin", "HOME": str(home),
             "HERMES_HOME": str(home / ".hermes"), "HERMES_SAFE_MODE": "1",
             "HERMES_ENABLE_PROJECT_PLUGINS": "0", "TERMINAL_ENV": "local",
             "PYTHONDONTWRITEBYTECODE": "1", "LANG": "C.UTF-8"})
    assert result.returncode == 0, result.stderr
    observed = json.loads(result.stdout.splitlines()[-1])
    assert observed["network_attempts"] == 0
    assert observed["blocked_local_bootstrap_attempts"] == (0 if case == "constructor" else 2)
    if case == "constructor":
        assert observed == {"constructor_composition": True,
                            "original_methods_restored": True,
                            "sdk_main_or_agent_calls": 0, "network_attempts": 0,
                            "blocked_local_bootstrap_attempts": 0}
    else:
        assert observed == {"actual_sdk_file_flow": True,
                            "original_session_namespace": True,
                            "work_guard": case == "work", "network_attempts": 0,
                            "blocked_local_bootstrap_attempts": 2}
