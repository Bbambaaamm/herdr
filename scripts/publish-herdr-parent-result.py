#!/usr/bin/env python3
"""Parent host command: publish one verified result; never start an SDK or merge."""
from pathlib import Path
import argparse
import importlib.machinery
import importlib.util
import json
import os
import stat
import sys

CODE = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(CODE), str(CODE/"agent-stack"/"bin")]

from herdr.evidence import EvidenceError, EvidenceStore, binding, digest
from herdr.host_configuration import read_canonical_parent
from herdr.parent_publication import ParentArtifactPublisher, ParentPublicationPermit
from herdr.parent_github_transport import GitHubParentTransport
from herdr.policy_launch import _verify_root_owned_ancestry


def read_private_json(path, *, root_owned=False, maximum=131072):
    path = Path(path)
    if root_owned:
        if not path.is_absolute() or path.resolve(strict=True) != path:
            raise EvidenceError("canonical root publication configuration required")
        _verify_root_owned_ancestry(path.parent)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        before = os.fstat(fd)
        expected_owner = 0 if root_owned else os.geteuid()
        if (not stat.S_ISREG(before.st_mode) or before.st_uid != expected_owner
                or before.st_nlink != 1 or before.st_mode & 0o022
                or not root_owned and stat.S_IMODE(before.st_mode) != 0o600
                or not 0 < before.st_size <= maximum):
            raise EvidenceError("unsafe bounded parent publication input")
        chunks, total = [], 0
        while total <= maximum:
            chunk = os.read(fd, min(65536, maximum+1-total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
        def stamp(s):
            return (s.st_dev, s.st_ino, s.st_mode, s.st_uid, s.st_nlink,
                s.st_size, s.st_mtime_ns, s.st_ctime_ns)
        raw = b"".join(chunks)
        if (len(raw) != before.st_size or stamp(before) != stamp(os.fstat(fd))
                or stamp(before) != stamp(path.lstat())):
            raise EvidenceError("parent publication input changed during read")
        def unique(pairs):
            value = {}
            for key, item in pairs:
                if key in value:
                    raise ValueError("duplicate parent input field")
                value[key] = item
            return value
        return json.loads(raw, object_pairs_hook=unique)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise EvidenceError("invalid parent publication input") from exc
    finally:
        os.close(fd)


def load_permit(path):
    raw = read_private_json(path, root_owned=True)
    if (not isinstance(raw, dict) or set(raw) != {"version", "permit", "transport"}
            or type(raw["version"]) is not int or raw["version"] != 1
            or not isinstance(raw["transport"], dict)
            or set(raw["transport"]) not in ({"gh", "home"}, {"mode", "address", "root_pid"})):
        raise EvidenceError("closed root-approved parent publication configuration required")
    try:
        permit = ParentPublicationPermit(**raw["permit"])
    except TypeError as exc:
        raise EvidenceError("closed parent publication permit required") from exc
    transport = raw["transport"]
    if set(transport) == {"mode", "address", "root_pid"}:
        if (transport["mode"] != "root-peer" or type(transport["root_pid"]) is not int
                or transport["root_pid"] <= 0 or type(transport["address"]) is not str
                or not transport["address"].startswith("herdr-parent-") or len(transport["address"]) > 100):
            raise EvidenceError("closed root publication peer required")
    else:
        for name in ("gh", "home"):
            value = transport[name]
            if not isinstance(value, str) or not Path(value).is_absolute() or "\0" in value:
                raise EvidenceError("approved absolute parent client path required")
    return permit, raw["transport"]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--permit", type=Path, required=True)
    parser.add_argument("--inspect", action="store_true")
    args = parser.parse_args(argv)
    permit, transport_config = load_permit(args.permit)
    if args.inspect:
        print(json.dumps({"configuration_valid": True, "task_id": permit.identity["id"],
            "repo": permit.repo, "expires_at_epoch": permit.expires_at_epoch,
            "sdk_started": False, "provider_calls": 0, "remote_effects": 0}))
        return
    # Load the original worker as a host library. Its __main__ is not executed;
    # only its existing protected cold recovery is used.
    loader = importlib.machinery.SourceFileLoader("herdr_parent_original_worker",
        str(CODE/"agent-stack"/"bin"/"agent-task-worker"))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    worker = importlib.util.module_from_spec(spec)
    loader.exec_module(worker)
    task = read_canonical_parent(worker.ROOT, permit.identity["id"], permit.identity["run_token"])
    if (task is None or binding(task) != permit.identity
            or type(task.get("work_contract_version")) is not int
            or task["work_contract_version"] != 1):
        raise EvidenceError("original modern parent task is unavailable")
    from agent_completion_evidence import store_for
    plan = store_for(worker.ROOT, task).read("plan", digest(binding(task)))
    payload = read_private_json(worker.result_path(task["id"]))
    factory, cycle = worker._recover_root_work_cycle(task)
    # Receipt-backed recovery already exists in the original worker. This
    # command neither allocates a work budget nor invokes the oracle/model.
    store = EvidenceStore(factory.result_authority.store.root/"parent-publication")
    if transport_config.get("mode") == "root-peer":
        from herdr.parent_github_peer import GitHubParentTransportProxy
        transport = GitHubParentTransportProxy(permit=permit, address=transport_config["address"],
                                               root_pid=transport_config["root_pid"])
    else:
        transport = GitHubParentTransport(repo=permit.repo, scratch=store.root/"transport",
            gh=Path(transport_config["gh"]), home=Path(transport_config["home"]))
    receipt = ParentArtifactPublisher(permit=permit, receipt_store=store,
        transport=transport).publish(task=task, payload=payload, plan=plan, factory=factory)
    print(json.dumps({"published": True, "task_id": task["id"],
        "commit_sha": receipt["artifact"]["commit_sha"], "pull_request": receipt["pull_request"],
        "completion_level": "reviewable_pull_request", "semantic_acceptance": False,
        "sdk_started": False, "provider_calls": 0}))


if __name__ == "__main__":
    main()

