"""One-shot attestation of the installed Capacity Watcher on its host."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import os
import socket
import time

from . import operation_readiness as readiness
from .operational_adapters import _object, capacity_snapshot
from .operational_incidents import IncidentError, Scope, epoch, require, token

RECEIPT_PATH = "/run/herdr/capacity-exporter/receipt.json"
RECEIPT_SCHEMA = "herdr-capacity-receipt-2"
MAX_RECEIPT_BYTES = 4096
MAX_ATTESTATION_AGE = 30
FLOOR = 9663676416
START_GUARD = 134217728
FILESYSTEM = "/"


def _receipt(raw, event_at, facts, server, scope):
    require(facts["required_bytes"] == FLOOR + START_GUARD, "capacity policy mismatch")
    return {
        "schema_version": RECEIPT_SCHEMA, "method": "host-fstatvfs-exact",
        "filesystem": FILESYSTEM, "server": server, **asdict(scope),
        "event_at": event_at, "source_sha256": hashlib.sha256(raw).hexdigest(),
        "available_bytes": facts["available_bytes"], "required_bytes": facts["required_bytes"],
    }


def verify_receipt(body, raw, event_at, facts, server, scope):
    """Verify a receipt already read through the protected host boundary."""
    require(type(body) is bytes and len(body) <= MAX_RECEIPT_BYTES, "invalid capacity receipt size")
    expected = _receipt(raw, event_at, facts, server, scope)
    value, _ = _object(body, set(expected))
    require(value == expected and all(type(value[key]) is int for key in
                                     ("event_at", "available_bytes", "required_bytes")),
            "capacity receipt binding mismatch")
    return expected


def _host_capacity():
    fd = os.open(FILESYSTEM, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        fs = os.fstatvfs(fd)
    finally:
        os.close(fd)
    require(fs.f_frsize > 0 and 0 <= fs.f_bavail <= fs.f_blocks,
            "invalid host filesystem counters")
    return readiness.capacity(fs.f_bavail * fs.f_frsize, floor=FLOOR, start_guard=START_GUARD)


def attest(server, scope):
    """Publish once at the reserved path. Host policy supplies the expected identities."""
    token(server)
    require(type(scope) is Scope, "capacity scope required")
    require(os.geteuid() == 0 and socket.gethostname() == server, "capacity host identity mismatch")
    raw = readiness.read_capacity_report()
    started = epoch(int(time.time()))
    row, _ = capacity_snapshot(raw, scope, now=started, max_age=MAX_ATTESTATION_AGE)
    measured = _host_capacity()
    require(readiness.read_capacity_report() == raw, "capacity report changed during attestation")
    now = epoch(int(time.time()))
    require(started <= now <= row.event_at + MAX_ATTESTATION_AGE,
            "capacity report outside attestation window")
    require(socket.gethostname() == server, "capacity host identity changed")
    facts = dict(row.facts)
    require(all(facts[key] == measured[key] for key in ("available_bytes", "required_bytes")),
            "capacity report disagrees with independent host measurement")
    value = _receipt(raw, row.event_at, facts, server, scope)
    readiness.write_owned_json(RECEIPT_PATH, value, group=0, protected_ancestry=True)
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server", required=True)
    parser.add_argument("--consumer", required=True)
    parser.add_argument("--project", required=True)
    args = parser.parse_args()
    try:
        attest(args.server, Scope(args.consumer, args.project))
    except (OSError, AttributeError, IncidentError, readiness.ReadinessError) as exc:
        parser.exit(1, f"capacity attestation blocked: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
