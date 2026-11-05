"""Actual pilot writer custody, including the previously exploitable aliases."""
from pathlib import Path
import ast,json,os
import pytest
from herdr import operation_readiness


def writer():
    p=Path(__file__).resolve().parents[2]/'deploy/herdr/native_pilot/init.py'
    fn=next(n for n in ast.parse(p.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='save')
    namespace={'os':os,'json':json,'_readiness_module':operation_readiness}
    exec(compile(ast.Module(body=[fn],type_ignores=[]),str(p),'exec'),namespace)
    return namespace['save']


def test_privileged_response_cannot_follow_a_preseeded_temporary_alias(tmp_path):
    p=tmp_path/'response.json';victim=tmp_path/'protected';victim.write_bytes(b'keep')
    p.with_suffix('.tmp').symlink_to(victim)
    try:writer()(p,{'ok':True},owner=os.geteuid())
    except OSError:pass
    assert victim.read_bytes()==b'keep'


def test_privileged_response_cannot_write_through_a_substituted_ancestor(tmp_path):
    outside=tmp_path/'outside';outside.mkdir();alias=tmp_path/'responses';alias.symlink_to(outside,target_is_directory=True)
    try:writer()(alias/'reply.json',{'ok':True},owner=os.geteuid())
    except OSError:pass
    assert not list(outside.iterdir())
