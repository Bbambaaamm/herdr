"""Typed closed original-startup observation; metadata is never a work grant."""
from dataclasses import dataclass
from pathlib import Path
import os
from offline_case.case import NONCE, require, canonical, parse, pinned_bytes, sha
from .security import SecurityGrant, InvocationIdentity

CONTEXT=Path('/var/lib/herdr-offline-observer-03414499dd0d1986/contexts')

@dataclass(frozen=True)
class AuthenticatedStartupObservation:
    kind: str
    challenge: str

    def verify(self, grant, pane_pid):
        from .case_roster import load_roster
        from .host_configuration import _read_configuration
        from offline_case.admission import _process_read
        def process_start_ticks(pid):
            # The PID was matched to the immutable root observation before
            # this bounded public stat read. Reuse the original peer helper;
            # never route controller/native ancestry into worker-only RPC.
            raw = _process_read(Path("/proc") / str(pid) / "stat", 8192)
            require(b") " in raw and len(raw.rsplit(b") ", 1)[1].split()) > 19,
                    "owned native start identity unavailable")
            ticks = int(raw.rsplit(b") ", 1)[1].split()[19])
            require(ticks > 0, "owned native start identity invalid")
            return ticks
        require(type(self) is AuthenticatedStartupObservation and self.kind in {'root-startup-source','child-parent-startup-source'}
                and isinstance(grant,SecurityGrant), 'typed original startup observation required')
        row=parse(pinned_bytes(CONTEXT/(self.kind+'.json'),root_owned=True),65536)
        require(set(row)=={'schema','kind','binding','value','projection_sha256'} and row['kind']==self.kind and
                row['projection_sha256']==sha(canonical({k:v for k,v in row.items() if k!='projection_sha256'})),
                'immutable original root startup projection changed')
        value=row['value'];roster=load_roster(_read_configuration,InvocationIdentity)
        doc=roster.document;root=InvocationIdentity.from_dict(roster.slot('root')['identity'])
        require(set(value)=={'identity','pane_id','shell_pid','shell_start_ticks','controller_pid','controller_start_ticks',
                'roster_sha256','native_sha256','challenge','root_grant_sha256','plan_sha256','root_context_sha256'} and
                value['challenge']==self.challenge and value['roster_sha256']==roster.sha256 and
                row['binding']==doc['case_binding'] and row['binding']['nonce']==NONCE and
                value['identity']==root.to_json() and value['shell_pid']==pane_pid and
                process_start_ticks(pane_pid)==value['shell_start_ticks'] and
                value['controller_pid']==os.getpid()==doc['controller']['pid'] and
                process_start_ticks(os.getpid())==value['controller_start_ticks']==doc['controller']['start_ticks'],
                'startup PID/start/case/slot/challenge changed')
        from offline_case.native_source import NATIVE_TARGET,NATIVE_SHA256
        require(value['native_sha256']==NATIVE_SHA256 and
                sha(pinned_bytes(NATIVE_TARGET,maximum=32_000_000,root_owned=True))==NATIVE_SHA256,
                'native source changed since original root startup guard')
        if self.kind=='root-startup-source':
            require(grant.identity==root and grant.workspace_root==roster.slot('root')['workspace'] and value['root_grant_sha256'] is None and value['plan_sha256'] is None and value['root_context_sha256'] is None,
                    'initial ROOT source cannot authorize a child')
        else:
            context=parse(pinned_bytes(CONTEXT/'root.json',root_owned=True),262144)
            require(context['identity']==root.to_json() and context['plan_sha256']==value['plan_sha256'] and
                    sha(canonical(context))==value['root_context_sha256'], 'original root custody source changed')
            require(grant.parent_grant_hash==value['root_grant_sha256'] and
                    grant.identity.parent_task_id==root.task_id and grant.identity.parent_agent_id==root.agent_id,
                    'startup observation does not match actual canonical child parent')
        from .canonical_case_effects import CanonicalHostEffects
        CanonicalHostEffects.require_live_case(object.__new__(CanonicalHostEffects),row['binding'])
        # No True/assurance/token is issued. The ORIGINAL method continues only
        # after this typed root-owned source decision was checked again.
