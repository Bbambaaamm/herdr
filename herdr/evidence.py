"""Trusted completion evidence, shared by the existing durable worker.

Worker-authored producer labels and bundles are never admission authority.
Only the host collector writes records behind the task sandbox's read-only
root. SHA-256 addresses integrity and identity; it is not a signature.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .reviewer import EvidenceRecord, ModelReview, ReviewInput, ReviewerGate, ReviewVerdict
from .workspace import ArtifactRef, WorkspaceManager, WorkspaceError
from agent_platform_dashboard.production_sources import command as artifact_command

VERSION = 1
_SHA = re.compile(r"^[0-9a-f]{64}$")
_REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_GIT_SHA = re.compile(r"^[0-9a-f]{40}$")


class EvidenceError(RuntimeError):
    code = "evidence_invalid"


class EvidenceMissing(EvidenceError):
    code = "evidence_missing"


class EvidenceUnavailable(EvidenceError):
    code = "evidence_unavailable"


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def binding(task: dict) -> dict:
    """Identity comes from the protected host task, never from the result."""
    result = {name: task.get(name) for name in
              ("id", "run_token", "idempotency_key")}
    result["attempt"] = task.get("attempt_id", task.get("attempts", 0))
    result["fencing_token"] = task.get("fencing_token", 0)
    if (any(not isinstance(result[name], str) or not result[name]
            for name in ("id", "run_token", "idempotency_key"))
            or type(result["attempt"]) is not int or result["attempt"] < 0
            or type(result["fencing_token"]) is not int or result["fencing_token"] < 0):
        raise EvidenceError("completion identity is incomplete")
    return result


def parse_artifact(raw: Any) -> ArtifactRef:
    names = {"task_id", "attempt", "base_sha", "commit_sha", "result_sha",
             "changed_files", "branch"}
    if not isinstance(raw, dict) or set(raw) != names:
        raise EvidenceMissing("a complete ArtifactRef is required")
    if (type(raw["attempt"]) is not int or raw["attempt"] < 0
            or not isinstance(raw["task_id"], str) or not raw["task_id"]
            or not isinstance(raw["branch"], str) or not raw["branch"]
            or not isinstance(raw["changed_files"], (list, tuple))
            or not raw["changed_files"]
            or any(not isinstance(p, str) for p in raw["changed_files"])
            or len(set(raw["changed_files"])) != len(raw["changed_files"])
            or any(not isinstance(raw[n], str) or not _GIT_SHA.fullmatch(raw[n])
                   for n in ("base_sha", "commit_sha"))
            or not isinstance(raw["result_sha"], str) or not _SHA.fullmatch(raw["result_sha"])):
        raise EvidenceError("invalid ArtifactRef")
    return ArtifactRef(**{**raw, "changed_files": tuple(raw["changed_files"])})


class EvidenceStore:
    """Host-owned append-only plans and accepted records, outside writable binds.

    Publication uses fsynced temporary bytes followed by an atomic exclusive link
    and directory fsync. A restart sees either the complete object or no object.
    It never admits a temporary file or overwrites a prior record.
    """

    def __init__(self, root: Path):
        if root.is_symlink():
            raise EvidenceError("evidence root cannot be a symlink")
        self.root = root.resolve()
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)

    def protect_from(self, writable_roots: tuple[Path, ...]) -> None:
        for root in writable_roots:
            resolved = root.resolve()
            if self.root == resolved or self.root.is_relative_to(resolved):
                raise EvidenceError("evidence store overlaps a worker-writable root")

    def _path(self, kind: str, key: str) -> Path:
        if kind not in {"plan", "accepted"} or not _SHA.fullmatch(key):
            raise EvidenceError("invalid evidence address")
        return self.root / f"{kind}-{key}.json"

    def read(self, kind: str, key: str) -> dict:
        path = self._path(kind, key)
        try:
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
            with os.fdopen(fd, "rb") as handle:
                raw = handle.read(2_000_001)
            if len(raw) > 2_000_000:
                raise EvidenceError("evidence exceeds bounded record size")
            envelope = json.loads(raw)
            if (set(envelope) != {"payload", "sha256"}
                    or not isinstance(envelope["payload"], dict)
                    or envelope["sha256"] != digest(envelope["payload"])
                    or canonical(envelope) != raw):
                raise EvidenceError("evidence integrity mismatch")
            return envelope["payload"]
        except FileNotFoundError as exc:
            raise EvidenceMissing("evidence does not exist") from exc
        except EvidenceError:
            raise
        except OSError as exc:
            raise EvidenceUnavailable("evidence cannot be read") from exc
        except (TypeError, ValueError, KeyError) as exc:
            raise EvidenceError("invalid evidence encoding") from exc

    def publish(self, kind: str, key: str, payload: dict) -> str:
        path = self._path(kind, key)
        content_hash = digest(payload)
        data = canonical({"payload": payload, "sha256": content_hash})
        if len(data) > 2_000_000:
            raise EvidenceError("evidence exceeds bounded record size")
        fd, tmp = tempfile.mkstemp(prefix=".publication-", dir=self.root)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            try:
                os.link(tmp, path, follow_symlinks=False)
            except FileExistsError:
                if self.read(kind, key) != payload:
                    raise EvidenceError("immutable evidence publication conflict")
            dir_fd = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        finally:
            os.unlink(tmp)
        return content_hash


def read_only_git(root: Path):
    """Untrusted worktree Git configuration never runs in the host namespace.

    Even a configured clean filter has no network, host process visibility,
    credentials in its environment, or writable host mounts. The collector
    remains outside this namespace to publish accepted evidence.
    """
    bwrap, git = Path("/usr/bin/bwrap"), Path("/usr/bin/git")
    if not bwrap.is_file() or not git.is_file():
        raise EvidenceUnavailable("read-only artifact verifier is unavailable")
    def run(args):
        command = [
            str(bwrap), "--ro-bind", "/", "/", "--dev", "/dev", "--proc", "/proc",
            "--unshare-pid", "--unshare-net", "--tmpfs", "/tmp", "--clearenv",
            "--setenv", "PATH", "/usr/bin:/bin", "--setenv", "HOME", "/tmp",
            "--", str(git), "--no-optional-locks",
            "-c", "core.fsmonitor=false", "-c", "core.hooksPath=/dev/null",
            "-c", "diff.external=", "-C", str(root), *args,
        ]
        try:
            return artifact_command(command, limit=2_000_000, timeout=30).decode("utf-8")
        except (OSError, subprocess.SubprocessError, ValueError) as exc:
            raise EvidenceUnavailable("artifact verifier execution unavailable") from exc
    return run


def validate_criteria(kind: str, criteria: Any) -> None:
    if not isinstance(criteria, dict):
        raise EvidenceMissing(f"typed {kind} artifact criteria are missing")
    common = {"schema", "report_path"}
    extra = {"sections"} if kind == "research" else {"target_commit"}
    path = criteria.get("report_path")
    if (set(criteria) != common | extra
            or criteria.get("schema") != f"{kind}-report-v1"
            or not isinstance(path, str) or len(path) > 256
            or not path.startswith(f"reports/{kind}/") or not path.endswith(".json")
            or Path(path).is_absolute() or ":" in path or "\\" in path
            or any(part in {"", ".", ".."} for part in path.split("/"))):
        raise EvidenceError("invalid typed artifact criteria")
    if kind == "research":
        sections = criteria["sections"]
        if (not isinstance(sections, list) or not 1 <= len(sections) <= 32
                or any(not isinstance(x, str) or not x or len(x) > 128 for x in sections)
                or len(set(sections)) != len(sections)):
            raise EvidenceError("research sections are invalid")
    elif not isinstance(criteria["target_commit"], str) or not _GIT_SHA.fullmatch(criteria["target_commit"]):
        raise EvidenceError("review target must be a full commit SHA")


def validate_plan(plan: dict) -> None:
    names = {"version", "identity", "repo", "kind", "spec_hash", "policy_hash",
             "plan_hash", "base_sha", "baseline", "workspace_root",
             "required_checks", "reviewer", "environment"}
    if isinstance(plan, dict) and isinstance(plan.get("kind"), str) and plan.get("kind") in {"research", "review"}:
        names.add("criteria")
    if not isinstance(plan, dict) or set(plan) != names or type(plan["version"]) is not int or plan["version"] != VERSION:
        raise EvidenceError("unsupported completion plan")
    if (not isinstance(plan["kind"], str) or plan["kind"] not in {"coding", "research", "review"}
            or not isinstance(plan["repo"], str) or not _REPO.fullmatch(plan["repo"])
            or not isinstance(plan["base_sha"], str) or not _GIT_SHA.fullmatch(plan["base_sha"])
            or any(not isinstance(plan[n], str) or not _SHA.fullmatch(plan[n])
                   for n in ("spec_hash", "policy_hash", "plan_hash"))
            or not isinstance(plan["required_checks"], list)
            or (plan["kind"] == "coding" and not plan["required_checks"])
            or (plan["kind"] != "coding" and plan["required_checks"] != ["GitGuardian Security Checks"])
            or any(not isinstance(n, str) or not n or len(n) > 64
                   for n in plan["required_checks"])
            or len(set(plan["required_checks"])) != len(plan["required_checks"])
            or not isinstance(plan["baseline"], list)
            or not isinstance(plan["environment"], dict)
            or plan["reviewer"] != "chatgpt-codex-connector[bot]"
            or not isinstance(plan["workspace_root"], str)
            or not Path(plan["workspace_root"]).is_absolute()):
        raise EvidenceError("invalid completion plan")
    if plan["kind"] != "coding":
        validate_criteria(plan["kind"], plan["criteria"])
    pinned = {k: v for k, v in plan.items() if k not in {"plan_hash", "baseline"}}
    if digest(pinned) != plan["plan_hash"]:
        raise EvidenceError("validation plan changed")


def inspect_typed_artifact(plan: dict, artifact: ArtifactRef, workspace: Path) -> dict:
    criteria = plan["criteria"]
    path = criteria["report_path"]
    if artifact.changed_files != (path,):
        raise EvidenceError("typed report cannot carry implementation or unrelated changes")
    raw = read_only_git(workspace)(["show", f"{artifact.commit_sha}:{path}"])
    if len(raw.encode("utf-8")) > 1_000_000:
        raise EvidenceError("typed report exceeds its size bound")
    try:
        report = json.loads(raw)
    except (TypeError, ValueError) as exc:
        raise EvidenceError("typed report is invalid JSON") from exc
    if not isinstance(report, dict) or type(report.get("version")) is not int or report["version"] != 1 or report.get("kind") != plan["kind"]:
        raise EvidenceError("typed report schema mismatch")
    if plan["kind"] == "research":
        if set(report) != {"version", "kind", "sections"} or not isinstance(report["sections"], list):
            raise EvidenceError("research report is invalid")
        sections = report["sections"]
        if (len(sections) != len(criteria["sections"])
                or any(not isinstance(row, dict) or set(row) != {"id", "summary", "sources"} for row in sections)
                or sorted(row["id"] for row in sections if isinstance(row["id"], str)) != sorted(criteria["sections"])):
            raise EvidenceError("research report does not cover the declared sections")
        for row in sections:
            if (not isinstance(row["summary"], str) or not row["summary"].strip()
                    or not isinstance(row["sources"], list) or not 1 <= len(row["sources"]) <= 32):
                raise EvidenceError("research section requires content and sources")
            for source in row["sources"]:
                if not isinstance(source, dict) or set(source) != {"url", "title"} or not all(isinstance(source[n], str) and source[n].strip() for n in source):
                    raise EvidenceError("research source is invalid")
                url = urlparse(source["url"])
                if url.scheme != "https" or not url.netloc or url.username or url.password:
                    raise EvidenceError("research source must be a credential-free HTTPS reference")
        coverage = {"sections": criteria["sections"], "source_reference_count": sum(len(row["sources"]) for row in sections),
                    "limits": "structure and independent artifact review; source truth is not asserted by schema validation"}
    else:
        if (set(report) != {"version", "kind", "target_commit", "summary", "verdict", "findings"}
                or report["target_commit"] != criteria["target_commit"]
                or report["verdict"] not in {"pass", "block", "needs_replan"}
                or not isinstance(report["summary"], str) or not report["summary"].strip()
                or not isinstance(report["findings"], list) or len(report["findings"]) > 100):
            raise EvidenceError("review report does not match its declared target")
        for finding in report["findings"]:
            if (not isinstance(finding, dict) or set(finding) != {"priority", "summary"}
                    or finding["priority"] not in {"P0", "P1", "P2", "P3"}
                    or not isinstance(finding["summary"], str) or not finding["summary"].strip()):
                raise EvidenceError("review finding is invalid")
        if report["verdict"] == "pass" and any(x["priority"] != "P3" for x in report["findings"]):
            raise EvidenceError("review pass contradicts blocking findings")
        coverage = {"target_commit": report["target_commit"], "verdict": report["verdict"],
                    "limits": "review artifact completion does not approve or merge the reviewed implementation"}
    return {"schema": criteria["schema"], "report_path": path, "report_hash": digest(report), "coverage": coverage}


def accept_artifact(task: dict, result: dict, plan: dict, store: EvidenceStore,
                  workspace: Path, collector) -> dict:
    """Reuse WorkspaceManager and ReviewerGate; never consume result.evidence."""
    validate_plan(plan)
    identity = binding(task)
    if plan["identity"] != identity or plan["repo"] != task.get("repo"):
        raise EvidenceError("plan belongs to another task or attempt")
    artifact = parse_artifact(result.get("artifact"))
    if (artifact.task_id != identity["id"] or artifact.attempt != identity["attempt"]
            or artifact.base_sha != plan["base_sha"]):
        raise EvidenceError("artifact identity or baseline mismatch")
    root = Path(plan["workspace_root"]).resolve()
    workspace = workspace.resolve()
    if not workspace.is_relative_to(root) or workspace == root:
        raise EvidenceError("artifact workspace is outside the declared root")
    store.protect_from((root,))
    key = digest({"identity": identity, "plan_hash": plan["plan_hash"],
                  "artifact": artifact.to_json()})
    try:
        accepted = store.read("accepted", key)
    except EvidenceMissing:
        accepted = None
    if accepted is not None:
        if (accepted.get("identity") != identity
                or accepted.get("plan_hash") != plan["plan_hash"]
                or accepted.get("artifact") != json.loads(canonical(artifact.to_json()))
                or accepted.get("level") != "verified_worker_result"
                or accepted.get("artifact_workspace") != str(workspace)):
            raise EvidenceError("accepted record binding mismatch")
        return {**accepted, "bundle_hash": digest(accepted)}

    try:
        manager = WorkspaceManager(workspace, git=read_only_git(workspace), worktrees_dir=root)
    except (OSError, WorkspaceError) as exc:
        raise EvidenceUnavailable("artifact workspace is unavailable") from exc
    try:
        manager.verify(artifact, workspace)
    except WorkspaceError as exc:
        raise EvidenceError("artifact workspace verification failed") from exc
    proof = collector(plan, artifact, result.get("pr_number"))
    required = list(plan["required_checks"])
    if (not isinstance(proof, dict) or set(proof) != {"checks", "review", "source"}
            or proof["source"] != "github-api"):
        raise EvidenceError("unsupported evidence source")
    records = tuple(EvidenceRecord(
        name=n, passed=True, artifact_result_sha=artifact.result_sha,
        producer="trusted-ci", evidence_sha256=digest(proof["checks"][n]),
    ) for n in required)
    typed_proof = None
    if plan["kind"] != "coding":
        typed_proof = inspect_typed_artifact(plan, artifact, workspace)
        required.append("artifact-criteria")
        records += (EvidenceRecord(
            name="artifact-criteria", passed=True, artifact_result_sha=artifact.result_sha,
            producer="trusted-validator", evidence_sha256=digest(typed_proof)),)
    review = proof["review"]
    if review.get("actor") != plan["reviewer"] or review.get("commit_sha") != artifact.commit_sha:
        raise EvidenceError("review origin or commit mismatch")
    model_review = ModelReview(
        artifact_result_sha=artifact.result_sha,
        evidence_digest=ReviewerGate.evidence_digest(records),
        actor_id=review["actor"], provider="github", model="codex-review",
        verdict=ReviewVerdict.PASS, review_sha256=digest(review),
    )
    gate = ReviewerGate(required_evidence=tuple(required))
    decision = gate.review(ReviewInput(
        spec_hash=plan["spec_hash"], artifact=artifact,
        worker_actor=(task.get("execution_session") or {}).get("agent_name", "durable-worker"),
        worker_claim="completed", evidence=records, model_review=model_review,
    ))
    if decision.verdict != ReviewVerdict.PASS:
        raise EvidenceError(f"review gate rejected: {decision.reason.value}")
    # The worker can still be alive while the collector runs; recheck its exact
    # bytes after collection before persisting a proof about those bytes.
    try:
        manager.verify(artifact, workspace)
    except WorkspaceError as exc:
        raise EvidenceError("artifact changed during collection") from exc
    bundle = {
        "version": VERSION, "identity": identity, "repo": plan["repo"],
        "kind": plan["kind"], "level": "verified_worker_result",
        "artifact_workspace": str(workspace),
        "spec_hash": plan["spec_hash"], "policy_hash": plan["policy_hash"],
        "plan_hash": plan["plan_hash"], "artifact": json.loads(canonical(artifact.to_json())),
        "baseline": plan["baseline"], "environment": plan["environment"],
        "proof": proof, "typed_validation": typed_proof, "review_hash": decision.review_hash,
        "integration": None, "deployment": None,
    }
    bundle_hash = store.publish("accepted", key, bundle)
    return {**bundle, "bundle_hash": bundle_hash}
