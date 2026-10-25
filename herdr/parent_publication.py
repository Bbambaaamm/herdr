"""Parent-only publication of a protected, host-verified local handoff.

This port does not implement work, grant worker network access, accept a result,
merge a PR, or redispatch an SDK. Its effect intents survive lost replies.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
import copy
import fcntl
import hashlib
import json
import os
import re
import stat
import time

from .evidence import (EvidenceError, EvidenceMissing, EvidenceUnavailable, EvidenceStore, binding,
    canonical, digest, invocation_identity, parse_artifact, read_only_git,
    valid_completion_base_branch, validate_plan, verify_committed_bytes)
from .result_candidate import completion_candidate
from .verification_binding import verify_commit_binding
from .work_contract_host import HostWorkContractFactory
from .work_cycle import WorkPhase
from .workspace import WorkspaceManager


def require(condition, reason):
    if not condition:
        raise EvidenceError(reason)


@dataclass(frozen=True)
class ParentPublicationPermit:
    """Created by host composition; never deserialized from a worker payload."""
    identity: dict
    repo: str
    spec_hash: str
    plan_hash: str
    base_sha: str
    base_branch: str
    head_branch: str
    expires_at_epoch: int
    public_summary: str

    def __post_init__(self):
        object.__setattr__(self, "identity", copy.deepcopy(self.identity))
        require(isinstance(self.identity, dict) and set(self.identity) ==
            {"id", "run_token", "idempotency_key", "attempt", "fencing_token"},
            "closed parent publication identity required")
        expected = binding({"id": self.identity["id"],
            "run_token": self.identity["run_token"],
            "idempotency_key": self.identity["idempotency_key"],
            "attempt_id": self.identity["attempt"],
            "fencing_token": self.identity["fencing_token"]})
        require(expected == self.identity, "invalid parent publication identity")
        require(isinstance(self.repo, str) and re.fullmatch(
            r"[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9][A-Za-z0-9_.-]*", self.repo),
            "canonical publication repository required")
        require(all(isinstance(value, str) and re.fullmatch("[0-9a-f]{64}", value)
            for value in (self.spec_hash, self.plan_hash)),
            "exact publication specification and plan required")
        require(isinstance(self.base_sha, str) and re.fullmatch("[0-9a-f]{40}", self.base_sha),
            "exact publication base required")
        require(valid_completion_base_branch(self.base_branch)
            and valid_completion_base_branch(self.head_branch)
            and self.head_branch not in {"main", "master", self.base_branch},
            "distinct approved result branch required")
        require(type(self.expires_at_epoch) is int and self.expires_at_epoch > 0,
            "finite parent publication authorization required")
        require(isinstance(self.public_summary, str) and self.public_summary.strip()
            and len(self.public_summary.encode("utf-8")) <= 8192
            and all(ord(char) >= 32 or char in "\n\t" for char in self.public_summary),
            "bounded host-approved public review context required")

    @property
    def hash(self):
        return digest(asdict(self))

    def require_plan(self, task, plan, artifact):
        validate_plan(plan)
        require(plan["kind"] == "coding" and binding(task) == self.identity
            and plan["identity"] == self.identity and plan["repo"] == self.repo
            and task.get("repo") == self.repo and plan["spec_hash"] == self.spec_hash
            and plan["plan_hash"] == self.plan_hash and plan["base_sha"] == self.base_sha
            and plan.get("base_branch", "main") == self.base_branch
            and artifact.base_sha == self.base_sha and artifact.branch == self.head_branch
            and artifact.task_id == self.identity["id"]
            and artifact.attempt == self.identity["attempt"],
            "result differs from the parent publication permit")


@contextmanager
def _publication_lock(store):
    info = store.root.lstat()
    require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.geteuid()
        and stat.S_IMODE(info.st_mode) == 0o700,
        "parent publication storage must be private")
    directory = os.open(store.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    fd = None
    try:
        fd = os.open("publication.lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW
            | os.O_NONBLOCK | os.O_CLOEXEC, 0o600, dir_fd=directory)
        held = os.fstat(fd)
        require(stat.S_ISREG(held.st_mode) and held.st_uid == os.geteuid()
            and held.st_nlink == 1 and stat.S_IMODE(held.st_mode) == 0o600,
            "unsafe parent publication lock")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise EvidenceUnavailable("parent publication is already being reconciled") from exc
        named = os.stat("publication.lock", dir_fd=directory, follow_symlinks=False)
        require((held.st_dev, held.st_ino) == (named.st_dev, named.st_ino),
            "parent publication lock was replaced")
        yield
    finally:
        if fd is not None:
            os.close(fd)
        os.close(directory)


class ParentArtifactPublisher:
    """Use existing host receipt authority and an explicitly supplied parent transport.

    Transport observe() returns a complete bounded view: base_sha, head_sha and
    pull_requests. push() receives only an exact-head incremental Git bundle,
    never a credential-bearing command running in the worker's repository.
    """
    def __init__(self, *, permit, receipt_store, transport, clock=time.time):
        require(isinstance(permit, ParentPublicationPermit)
            and isinstance(receipt_store, EvidenceStore)
            and all(callable(getattr(transport, name, None))
                for name in ("observe", "push", "create_pull_request")) and callable(clock),
            "host parent publication ports required")
        self.permit = permit
        self.store = receipt_store
        self.transport = transport
        self.clock = clock

    def _require_live(self):
        require(self.clock() < self.permit.expires_at_epoch,
            "parent publication authorization expired")

    def _key(self, stage):
        return digest({"type": "parent-artifact-publication-1",
            "identity": self.permit.identity, "repo": self.permit.repo,
            "plan_hash": self.permit.plan_hash, "stage": stage})

    def _read(self, stage):
        try:
            return self.store.read("plan", self._key(stage))
        except EvidenceMissing:
            return None

    def _write(self, stage, value):
        self.store.publish("plan", self._key(stage), value)

    def _observe(self, artifact):
        self._require_live()
        value = self.transport.observe(self.permit, artifact)
        require(isinstance(value, dict) and set(value) ==
            {"base_sha", "head_sha", "pull_requests"}
            and value["base_sha"] == self.permit.base_sha
            and (value["head_sha"] is None or value["head_sha"] == artifact.commit_sha)
            and isinstance(value["pull_requests"], list)
            and len(value["pull_requests"]) < 100,
            "publication target moved or remote observation is incomplete")
        matches = []
        for row in value["pull_requests"]:
            require(isinstance(row, dict) and set(row) ==
                {"number", "repo", "base_sha", "base_branch", "head_sha", "head_branch", "state"}
                and type(row["number"]) is int and row["number"] > 0,
                "bounded exact pull request observation required")
            if (row["repo"], row["base_sha"], row["base_branch"], row["head_sha"], row["head_branch"]) == (
                    self.permit.repo, self.permit.base_sha, self.permit.base_branch,
                    artifact.commit_sha, self.permit.head_branch):
                require(row["state"] == "open", "original result pull request is closed")
                matches.append(row)
        require(len(matches) <= 1, "ambiguous exact result pull requests")
        if matches:
            require(value["head_sha"] == artifact.commit_sha,
                "result pull request lacks its exact remote branch")
        return value, matches

    def publish(self, *, task, payload, plan, factory):
        task, payload, plan = copy.deepcopy((task, payload, plan))
        candidate = completion_candidate(payload, workspace=task.get("workspace"))
        artifact = parse_artifact(candidate.get("artifact"))
        self.permit.require_plan(task, plan, artifact)
        workspace = Path(task["workspace"])
        self.store.protect_from((Path(plan["workspace_root"]), workspace))
        expected = {"version": 1, "permit_sha256": self.permit.hash,
            "identity": binding(task), "plan_hash": plan["plan_hash"],
            "result_payload_sha256": digest(payload),
            "artifact": json.loads(canonical(artifact.to_json()))}
        with _publication_lock(self.store):
            previous = self._read("receipt")
            if previous is not None:
                require(set(previous) == set(expected) | {"pull_request"}
                    and {key: previous[key] for key in expected} == expected
                    and type(previous["pull_request"]) is int and previous["pull_request"] > 0,
                    "parent publication receipt conflicts with the original result")
                return previous
            self._require_live()
            if callable(getattr(self.transport, "protect_from", None)):
                self.transport.protect_from((Path(plan["workspace_root"]), workspace))
            require(isinstance(factory, HostWorkContractFactory),
                "original host work factory required for publication")
            cycle = factory.cycle(invocation_identity(task))
            require(cycle.phase is WorkPhase.HANDOFF,
                "parent publication requires an already committed local PASS")
            cycle.committed(artifact)
            verifier = factory.result_authority.verifier(task, payload, plan,
                work_plan_sha256=cycle.plan.hash)
            verifier(task)
            git = read_only_git(workspace)
            manager = WorkspaceManager(workspace, git=git,
                worktrees_dir=Path(plan["workspace_root"]), artifacts_dir=self.store.root/"artifacts")
            manager.verify(artifact, workspace)
            verify_committed_bytes(artifact, workspace, git)
            verify_commit_binding(plan, artifact, {"sha": artifact.commit_sha,
                "commit": {"message": git(["show", "-s", "--format=%B", artifact.commit_sha])}})
            intent = self._read("candidate")
            require(intent is None or intent == expected, "parent publication candidate changed")
            self._write("candidate", expected)
            snapshot, matches = self._observe(artifact)
            if not matches and snapshot["head_sha"] is None:
                require(self._read("push-intent") is None,
                    "original push outcome is unknown; reconcile without another push")
                bundle = git.raw(["bundle", "create", "-", "HEAD", "^" + artifact.base_sha])
                manager.verify(artifact, workspace)
                verify_committed_bytes(artifact, workspace, git)
                verifier(task)
                self._require_live()
                self._write("push-intent", {**expected,
                    "bundle_sha256": hashlib.sha256(bundle).hexdigest()})
                self._require_live()
                self.transport.push(self.permit, artifact, bundle)
                snapshot, matches = self._observe(artifact)
                require(snapshot["head_sha"] == artifact.commit_sha,
                    "push not observed; reconcile original without retry")
            if not matches:
                require(snapshot["head_sha"] == artifact.commit_sha,
                    "exact result branch required before opening its pull request")
                require(self._read("pr-intent") is None,
                    "original PR creation outcome is unknown; reconcile without another creation")
                request = {"title": "Herdr verified local result: " + task["id"],
                    "body": "Approved bounded task:\n\n" + self.permit.public_summary + "\n\n"
                        + "Host-verified local coding result. Independent CI and review remain required.\n\n"
                        + "Base commit: " + artifact.base_sha + "\n"
                        + "Result commit: " + artifact.commit_sha + "\n",
                    "base": self.permit.base_branch, "head": self.permit.head_branch}
                self._write("pr-intent", {**expected, "request": request})
                verifier(task)
                self._require_live()
                self.transport.create_pull_request(self.permit, artifact, request)
                snapshot, matches = self._observe(artifact)
            require(len(matches) == 1, "original PR is not observed; reconcile without another creation")
            manager.verify(artifact, workspace)
            verify_committed_bytes(artifact, workspace, git)
            verifier(task)
            receipt = {**expected, "pull_request": matches[0]["number"]}
            self._write("receipt", receipt)
            return receipt

