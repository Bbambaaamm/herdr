"""Single offline case operator entrypoint; default is data only."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from .case import CaseDriver, Denied, parse, pinned_bytes, plan, validate_build
from .custody import RootCustody
from .admission import NativeAdmission
from .native import NativeHost

OWN_ROOT = Path("/opt/agent-platform/herdr-offline-03414499dd0d1986")
OWN_CUSTODY = Path("/var/lib/herdr-offline-03414499dd0d1986")


def main(argv=None, *, host=None, custody_type=RootCustody, clock=None):
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--dry-run", action="store_true")
    action.add_argument("--execute", action="store_true")
    action.add_argument("--cleanup", action="store_true")
    parser.add_argument("--build", type=Path)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--baseline-index", type=Path)
    args = parser.parse_args(argv)
    root = args.root or OWN_ROOT
    baseline = args.baseline or root / "accepted-source"
    build_path = args.build or root / "integration-manifest.json"
    if args.dry_run:
        build = parse(pinned_bytes(build_path), 262144)
        validate_build(build, root, baseline=baseline, baseline_index=args.baseline_index,
                       installed=(root == OWN_ROOT))
        print(json.dumps(plan(build), sort_keys=True))
        return 0
    if root != OWN_ROOT or build_path != OWN_ROOT / "integration-manifest.json" or \
            baseline != OWN_ROOT / "accepted-source" or args.baseline_index is not None:
        raise Denied("physical entry uses only the pinned installation paths")
    build = parse(pinned_bytes(build_path, root_owned=True), 262144)
    validate_build(build, root, baseline=baseline, root_owned=True, installed=True)
    import sys
    sys.path.insert(0, str(OWN_ROOT / "composed-core"))
    sys.path.insert(0, str(OWN_ROOT / "composed-core/agent-stack/bin"))
    with custody_type(OWN_CUSTODY) as custody:
        # The root observer talks to a separate, kernel-identified UID 1001
        # host process.  Constructing the client cannot mint a grant or start
        # that process; a missing published selector fails closed.
        actual_host = host if host is not None else NativeHost(
            build=build, admission=NativeAdmission.from_configuration(build=build))
        driver = CaseDriver(custody, actual_host, **({"clock": clock} if clock else {}))
        if args.cleanup:
            print(json.dumps(driver.cleanup(), sort_keys=True))
        else:
            print(json.dumps(driver.start(build, root=root, baseline=baseline,
                                          root_owned=True), sort_keys=True))
    return 0


if __name__ == "__main__":
    main()
