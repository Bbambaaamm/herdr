import importlib.util
import json
from pathlib import Path
import pytest


def module():
    p=Path(__file__).resolve().parents[2]/'deploy/herdr/check_capacity.py'
    spec=importlib.util.spec_from_file_location('capacity_watch',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def test_capacity_watch_reports_only_readiness_and_never_deletes(tmp_path):
    m=module();sentinel=tmp_path/'keep';sentinel.write_bytes(b'keep')
    value=m.observation(tmp_path,0,0,0)
    report=tmp_path/'status.json';out=m.publish(report,value)
    assert out['ready'] and out['model_calls']==0 and out['cleanup_performed'] is False
    assert json.loads(report.read_bytes())==out and sentinel.read_bytes()==b'keep'


def test_capacity_report_never_follows_a_foreign_symlink(tmp_path):
    m=module();target=tmp_path/'private';target.write_text('keep')
    report=tmp_path/'status.json';report.symlink_to(target)
    with pytest.raises(ValueError):m.publish(report,{})
    assert target.read_text()=='keep'
