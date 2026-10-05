"""Explicit host policy doubles for lifecycle tests; physical policy tests use real mounts."""
from herdr.policy_launch import HostPolicyLaunchFactory, PreparedPolicyLaunch, IDENTITY_ENV, CODE_TARGET, RUNTIME_TARGETS
from herdr.security import InvocationIdentity

def policy_fixture(identity, *, modern=False):
    proof={"schema_version":"herdr-policy-launch-2","grant_sha256":"a"*64,"bundle_sha256":"b"*64,
        "bundle_device":1,"bundle_inode":2,"code_sha256":"c"*64,
        "runtime_sha256":dict.fromkeys(map(str,RUNTIME_TARGETS),"d"*64),
        "tree_identities":{str(x):{"device":1,"inode":2} for x in (CODE_TARGET,*RUNTIME_TARGETS)},
        "process_start_ticks":123,"identity":identity.to_json(),"sandbox_attestation_sha256":"e"*64}
    if modern:
        proof["schema_version"]="herdr-policy-launch-3"
        proof["bootstrap"]={"continuation":{"schema_version":"herdr-bootstrap-continuation-1",
            "identity":identity.to_json(),"peer_pid":456,"process_start_ticks":124,
            "proof_sha256":"f"*64,"stage1_sha256":"1"*64,"stage2_sha256":"2"*64,
            "python_sha256":"3"*64,"bundle_sha256":"b"*64,"python_device":1,"python_inode":2},
            "bootstrap_tree":{"device":1,"inode":3,"source_digest":"4"*64}}
    return proof


class FakePreparedPolicyLaunch(PreparedPolicyLaunch):
    def __init__(self, identity):
        self._identity = identity
        self.mount = None
        self.events = []
    @property
    def identity(self):
        return self._identity
    def environment(self):
        return {key:str(getattr(self.identity,field)) for field,key in IDENTITY_ENV.items()}
    def verify_spawn_source(self,pid):
        self.events.append(("startup-source",pid))
    def bind_result_slot(self,path,idempotency_key):
        self.events.append(("result-slot",str(path),idempotency_key))
    def seal(self,pid,attestation,*,tools,permissions):
        self.events.append(("sealed",pid))
        return policy_fixture(self.identity)
    def set_continuation_sink(self,sink):
        self._continuation_sink=sink
    def arm_bootstrap(self):
        pass
    def confirm_bootstrap(self):
        proof=policy_fixture(self.identity,modern=True)
        assert self._continuation_sink(proof) is True
        return proof
    def verify_bootstrap(self):
        pass
    def cleanup_after_pane_closed(self):
        self.events.append(("closed",))

class FakeHostPolicyLaunchFactory(HostPolicyLaunchFactory):
    def __init__(self):
        self.created = []
    def cleanup_orphan(self,identity):
        return False
    def prepare_child(self,**kwargs):
        return self.prepare(**kwargs)
    def prepare(self,*,identity,workspace,tools,permissions):
        launch=FakePreparedPolicyLaunch(identity)
        self.created.append(launch)
        return launch

def install_runtime_policy_fixture(monkeypatch, runtime_class):
    original=runtime_class.__init__
    def init(self,*args,**kwargs):
        if kwargs.get("policy_launch_factory") is None:
            kwargs["policy_launch_factory"]=FakeHostPolicyLaunchFactory()
        original(self,*args,**kwargs)
        for record in getattr(self.scheduler, '_tasks', {}).values():
            if not (record.agent_id and record.run_token and record.fencing_token
                    and record.parent_agent_id and record.parent_task_id):
                continue
            identity=InvocationIdentity(consumer="github:"+record.repo,agent_id=record.agent_id,
                                        parent_agent_id=record.parent_agent_id,
                                        parent_task_id=record.parent_task_id,task_id=record.id,
                                        run_token=record.run_token,fencing_token=record.fencing_token)
            self._policy_launches[record.id]=FakePreparedPolicyLaunch(identity)
    monkeypatch.setattr(runtime_class,"__init__",init)

def install_child_completion_fixture(monkeypatch):
    from herdr.scheduler import DynamicChildScheduler
    from herdr.child_evidence import ChildCompletionAuthority,AcceptedChildReceipt,child_identity,child_spec
    from herdr.evidence import digest
    class Authority(ChildCompletionAuthority):
        def __init__(self): pass
        def prepare(self,rec): pass
        def instructions(self,rec): return ""
        def accepted_handoff(self,rec,**kwargs): return None
        def verify(self,rec,payload):
            return AcceptedChildReceipt(2,child_identity(rec).to_json(),digest(payload),"a"*64,
                "b"*64,child_spec(rec),"c"*64,"verified_worker_result")
    original=DynamicChildScheduler.__init__
    def init(self,*args,**kwargs):
        if kwargs.get("completion_authority") is None: kwargs["completion_authority"]=Authority()
        original(self,*args,**kwargs)
    monkeypatch.setattr(DynamicChildScheduler,"__init__",init)
