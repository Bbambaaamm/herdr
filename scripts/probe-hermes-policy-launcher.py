#!/usr/bin/env python3
"""Verify that direct/parameterized launcher entry cannot reach Hermes."""
import argparse,importlib.machinery,importlib.util,json,sys
from pathlib import Path
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--repo-root",default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--hermes-root",required=True)
    ns=parser.parse_args()
    path=Path(ns.repo_root).resolve()/"agent-stack/bin/agent-hermes-policy-run"
    loader=importlib.machinery.SourceFileLoader("closed_launcher_probe",str(path))
    spec=importlib.util.spec_from_loader(loader.name,loader)
    module=importlib.util.module_from_spec(spec);loader.exec_module(module)
    try: module.bootstrap([],bundle_path=Path("/tmp/self-signed.json"))
    except TypeError: pass
    else: raise AssertionError("parameterized escape")
    try: module.bootstrap(["--version"])
    except SystemExit: pass
    else: raise AssertionError("direct launch escaped host authority")
    assert not hasattr(module,"_exec_verified_interpreter")
    print(json.dumps({"status":"PASS","direct_and_parameterized_launch_denied":True,
                      "live_provider_used":False,"live_config_changed":False},sort_keys=True))
    return 0
if __name__=="__main__":raise SystemExit(main())
