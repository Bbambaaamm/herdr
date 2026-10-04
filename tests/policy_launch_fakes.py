"""Explicit host policy doubles for lifecycle tests; physical policy tests use real mounts."""
from herdr.policy_launch import HostPolicyLaunchFactory, PreparedPolicyLaunch, IDENTITY_ENV
from herdr.security import InvocationIdentity

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
    def seal(self,pid,attestation,*,tools,permissions):
        self.events.append(("sealed",pid))
        return {"schema_version":"test-host-policy", "identity":self.identity.to_json(),
                "bundle_sha256":"b"*64}
    def cleanup_after_pane_closed(self):
        self.events.append(("closed",))

class FakeHostPolicyLaunchFactory(HostPolicyLaunchFactory):
    def __init__(self):
        self.created = []
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
