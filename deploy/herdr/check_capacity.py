"""Publish nonsecret disk readiness; never clean storage or admit work."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import time


def observation(path, floor, guard, warning):
    spec=importlib.util.spec_from_file_location('_capacity_readiness',Path(__file__).resolve().parents[2]/'herdr/operation_readiness.py')
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    fs=os.statvfs(path)
    return module.capacity(fs.f_bavail*fs.f_frsize,floor=floor,start_guard=guard,warning_margin=warning)


def publish(report, value):
    report=Path(report)
    if not report.is_absolute() or report.parent.is_symlink() or report.is_symlink():
        raise ValueError('capacity_report_path_denied')
    value=dict(value,checked_at_epoch=time.time(),model_calls=0,cleanup_performed=False)
    temporary=report.with_name(report.name+'.new')
    fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o644)
    with os.fdopen(fd,'w') as stream:
        json.dump(value,stream,sort_keys=True);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    os.replace(temporary,report)
    return value


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args()
    value=observation('/',9663676416,134217728,268435456)
    previous={}
    if args.report.is_file():
        previous=json.loads(args.report.read_bytes())
    result=publish(args.report,value)
    if any(previous.get(key)!=result[key] for key in ('ready','capacity_warning')):
        print(json.dumps(result,sort_keys=True))
    return 0


if __name__=='__main__':raise SystemExit(main())
