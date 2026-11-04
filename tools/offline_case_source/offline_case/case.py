"""Exact, once-only admission and lifecycle for the proposed offline case.

Effect methods are supplied by the root host integration. None is called by
import, plan, or validation. The host integration remains subject to review.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import stat
import time
from pathlib import Path

NONCE = "03414499dd0d1986968b2393d44275d0"
CASE = "herdr-offline-03414499dd0d1986.service"
CLEANUP = "herdr-offline-cleanup-03414499dd0d1986.service"
TIMER = "herdr-offline-cleanup-03414499dd0d1986.timer"
OPERATOR = "herdr-offline-operator-03414499dd0d1986.service"
PROFILE = "herdr189-reference-lifetime"
OBSERVER = "herdr-offline-observer-03414499dd0d1986"
PREP = "herdr-offline-prep-03414499dd0d1986"
HOST_PROFILE = "herdr-offline-controller-03414499dd0d1986"
OPERATOR_PROFILE = "herdr-offline-operator-03414499dd0d1986"
ACCEPTED_PROFILE_SOURCE = "66ad58859e0f5c141ddf7943c9ee369e37c0ba2d33115eb17ad872555778c226"
PROFILE_SOURCE = "42c8d021a856eb5e9c59b9f335695f296ea17b91eb3a04044ca6ef0e7bdf6d62"
OBSERVER_SOURCE = "2603d4702b54ff4c594565a52b3e149a16ed36a0b91bcc98d16425629d70ae42"
PREP_SOURCE = "13afa1e6cb520262772832ae2de33381638bde7cc5f612f3359e907d4daa90ea"
INSTALL_ROOT = "/opt/agent-platform/herdr-offline-03414499dd0d1986"
COMPOSED_CORE = INSTALL_ROOT + "/composed-core"
BASELINE = "bb22b15461ba38457112c4388eaf80e4c31e2ca546c0f134b5fa3986905e7ed1"
BASELINE_STATE = "83222adb878adb9bc079a88c978708fa8119b1a773b32586015cb188a22008e7"
BASELINE_INDEX = "c44b4461ef15b3b9e4ef98f98f19d05d6df189f9df0aa8958471a18a8218a49f"
RUNTIME_INDEX = "b90fda83a05f04e5b555d6a6faf91c6d425decf37f2503b0cfe36dccf5b4c54a"
CORE_BASE_INDEX = "07341cbd524b30d42a4e06d105ae9c174b185fd7988ceb9c7010acd7db3406a5"
EXECUTOR = "hermes:0.21.5:sha256:2595bcb2445260b5783865c876ed4f0f03ab3e6cc99c84e29ad39e1008dade88"
DEADLINE = 1793810588
REQUIRED_FREE = 10 * 1024**3 + 256 * 1024**2 + 128 * 1024**2
BUDGET = {"attempts": 1, "case_seconds": 1800, "work_seconds": 900,
          "managed_children": 1, "depth": 2, "fanout": 1,
          "fixture_http": 16, "external_model": 0, "external_auth": 0,
          "external_github": 0, "herdr_model_calls": 0, "herdr_model_cost": 0}
AUTH_KEYS = frozenset({"operator_profile", "operator_source_sha256", "operator_compiled_sha256", "schema", "purpose", "nonce", "case_unit", "cleanup_unit",
    "cleanup_timer", "profile", "profile_source_sha256", "compiled_profile_sha256",
    "observer", "observer_source_sha256", "observer_compiled_sha256",
    "host_profile", "host_profile_source_sha256", "host_compiled_sha256",
    "preparer", "prep_source_sha256", "prep_compiled_sha256",
    "baseline_sha256", "baseline_state_sha256", "executor", "build_sha256",
    "driver_sha256", "payload_sha256", "config_sha256", "projection_sha256",
    "runtime_sha256", "host_selector_sha256", "boot_id", "challenge",
    "not_before", "deadline", "budget"})


class Denied(RuntimeError):
    pass


def require(ok: bool, message: str) -> None:
    if not ok:
        raise Denied(message)


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                      allow_nan=False).encode("ascii")


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def hex64(value: object) -> bool:
    return type(value) is str and re.fullmatch("[0-9a-f]{64}", value) is not None


def unique_pairs(rows):
    result = {}
    for key, value in rows:
        require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def parse(raw: bytes, maximum=65536) -> dict:
    require(type(raw) is bytes and 0 < len(raw) <= maximum, "bounded JSON required")
    try:
        value = json.loads(raw, object_pairs_hook=unique_pairs,
                           parse_constant=lambda _: (_ for _ in ()).throw(Denied("nonfinite JSON")))
    except (UnicodeError, ValueError, TypeError) as exc:
        raise Denied("invalid JSON") from exc
    require(type(value) is dict, "JSON object required")
    return value


def pinned_bytes(path: Path, maximum=16_777_216, *, root_owned=False) -> bytes:
    """Reject link aliases and a file changed during the bounded source read."""
    path = Path(path)
    require(path.is_absolute() and ".." not in path.parts, "absolute pinned path required")
    directory = os.open("/", os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        for part in path.parts[1:-1]:
            child = os.open(part, os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                            dir_fd=directory)
            os.close(directory)
            directory = child
            ancestor = os.fstat(directory)
            if root_owned:
                require(ancestor.st_uid == 0 and not ancestor.st_mode & 0o022,
                        "root input ancestry writable")
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                     dir_fd=directory)
        try:
            before = os.fstat(fd)
            require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and
                    0 < before.st_size <= maximum, "unsafe pinned source")
            if root_owned:
                require(before.st_uid == 0 and not before.st_mode & 0o022,
                        "root input owner or mode invalid")
            raw = bytearray()
            while len(raw) < before.st_size:
                part = os.read(fd, before.st_size - len(raw))
                require(bool(part), "short pinned source")
                raw.extend(part)
            after = os.fstat(fd)
            entry = os.stat(path.name, dir_fd=directory, follow_symlinks=False)
            stamp = lambda s: (s.st_dev, s.st_ino, s.st_mode, s.st_nlink,
                               s.st_size, s.st_mtime_ns, s.st_ctime_ns)
            require(not os.read(fd, 1) and stamp(before) == stamp(after) == stamp(entry),
                    "pinned source changed")
            if root_owned:
                require(after.st_uid == 0 and entry.st_uid == 0 and
                        not (after.st_mode | entry.st_mode) & 0o022,
                        "root input permissions changed")
            return bytes(raw)
        finally:
            os.close(fd)
    finally:
        os.close(directory)


def _authority_bindings(a: dict, build: dict) -> None:
    require(type(a) is dict and set(a) == AUTH_KEYS, "unknown authority schema")
    require(type(a["schema"]) is int and a["schema"] == 2 and
            a["purpose"] == "SINGLE_OFFLINE_PHYSICAL_CASE",
            "unissued or legacy authority")
    expected = {"operator_profile": OPERATOR_PROFILE,
        "operator_source_sha256": build["files"]["overlays/operator-profile.apparmor"], "nonce": NONCE, "case_unit": CASE, "cleanup_unit": CLEANUP,
        "cleanup_timer": TIMER, "profile": PROFILE, "profile_source_sha256": PROFILE_SOURCE,
        "observer": OBSERVER, "observer_source_sha256": OBSERVER_SOURCE,
        "host_profile": HOST_PROFILE,
        "host_profile_source_sha256": build["files"]["overlays/host-profile.apparmor"],
        "preparer": PREP, "prep_source_sha256": PREP_SOURCE,
        "baseline_sha256": BASELINE, "baseline_state_sha256": BASELINE_STATE,
        "executor": EXECUTOR, "budget": BUDGET, "deadline": DEADLINE,
        "build_sha256": sha(canonical(build)),
        "driver_sha256": build["files"]["offline_case/driver.py"],
        "payload_sha256": build["files"]["offline_case/payload.py"]}
    require(all(a.get(k) == v for k, v in expected.items()) and
            type(a["budget"]) is dict and
            all(type(value) is int for value in a["budget"].values()),
            "authority pin mismatch")
    for key in ("operator_compiled_sha256", "compiled_profile_sha256", "observer_compiled_sha256", "prep_compiled_sha256",
                "host_compiled_sha256",
                "config_sha256", "projection_sha256",
                "runtime_sha256", "host_selector_sha256", "challenge"):
        require(hex64(a[key]), "unknown or invalid authority digest")


def validate_retirement_authority(a: dict, build: dict, *, boot: str) -> dict:
    """Same original immutable source binding; expiry never renews execution."""
    _authority_bindings(a, build)
    require(type(boot) is str and bool(boot) and a["boot_id"] == boot, "retirement boot mismatch")
    return a


def validate_authority(a: dict, build: dict, *, now: int, free: int, boot: str) -> dict:
    """Original live capacity/time gate remains mandatory for every new birth."""
    _authority_bindings(a, build)
    require(type(a["not_before"]) is int and type(now) is int and
            a["not_before"] <= now and now + BUDGET["case_seconds"] <= DEADLINE,
            "authority expired or outside case window")
    require(type(free) is int and free >= REQUIRED_FREE, "fresh ROOT capacity insufficient")
    require(type(boot) is str and bool(boot) and a["boot_id"] == boot,
            "boot identity mismatch")
    return a


def validate_build(build: dict, root: Path, *, baseline: Path,
                   baseline_index: Path | None = None, root_owned=False,
                   installed=False) -> None:
    root, baseline = Path(root), Path(baseline)
    require(root.is_absolute() and baseline.is_absolute() and
            root.resolve(strict=True) == root and baseline.resolve(strict=True) == baseline and
            baseline == root / "accepted-source",
            "aliased source roots")
    require(type(build) is dict and set(build) == {"kind", "schema", "files", "core_files",
            "core_base_index_sha256", "metadata_install_targets", "baseline",
            "baseline_state", "baseline_index_sha256", "runtime_index_sha256", "executor", "profile_source",
            "observer_source", "prep_source", "host_source", "overlay_targets", "install_targets",
            "installed_modes"},
            "build manifest schema")
    require(build["kind"] == "SOURCE_ONLY_SINGLE_CASE" and
            type(build["schema"]) is int and build["schema"] == 1 and
            build["baseline"] == BASELINE and build["baseline_state"] == BASELINE_STATE and
            build["baseline_index_sha256"] == BASELINE_INDEX and
            build["runtime_index_sha256"] == RUNTIME_INDEX and
            build["executor"] == EXECUTOR and build["profile_source"] == PROFILE_SOURCE and
            build["observer_source"] == OBSERVER_SOURCE and
            build["prep_source"] == PREP_SOURCE,
            "build baseline mismatch")
    require(build["core_base_index_sha256"] == CORE_BASE_INDEX and
            build["metadata_install_targets"] == {
                "integration-manifest.json": INSTALL_ROOT + "/integration-manifest.json",
                "accepted-source-index.json": INSTALL_ROOT + "/accepted-source-index.json",
                "runtime-input-index.json": INSTALL_ROOT + "/runtime-input-index.json",
                "canonical-core-index.json": INSTALL_ROOT + "/canonical-core-index.json"},
            "closed metadata installation map required")
    files = build["files"]
    require(build["host_source"] == files.get("overlays/host-profile.apparmor"),
            "candidate host profile changed")
    require(build['overlay_targets'] == {'composed-core/agent-stack/bin/agent-herdr-fd-launch': 'overlays/agent-stack/bin/agent-herdr-fd-launch', 'composed-core/agent-stack/bin/agent-hermes-policy-run': 'overlays/agent-stack/bin/agent-hermes-policy-run', 'composed-core/agent-stack/bin/agent-hermes-policy-stage1': 'overlays/agent-stack/bin/agent-hermes-policy-stage1', 'composed-core/agent-stack/bin/agent-task-worker': 'overlays/agent-stack/bin/agent-task-worker', 'composed-core/agent-stack/bin/agent_completion_evidence.py': 'overlays/agent-stack/bin/agent_completion_evidence.py', 'composed-core/agent-stack/bin/agent_durable_sandbox.py': 'overlays/agent-stack/bin/agent_durable_sandbox.py', 'composed-core/agent-stack/bin/offline-case-host-entry': 'overlays/agent-stack/bin/offline-case-host-entry', 'composed-core/herdr/bootstrap_authority.py': 'overlays/herdr/bootstrap_authority.py', 'composed-core/herdr/bootstrap_self_observation.py': 'overlays/herdr/bootstrap_self_observation.py', 'composed-core/herdr/canonical_case_claim.py': 'overlays/herdr/canonical_case_claim.py', 'composed-core/herdr/canonical_case_effects.py': 'overlays/herdr/canonical_case_effects.py', 'composed-core/herdr/canonical_case_probe.py': 'overlays/herdr/canonical_case_probe.py', 'composed-core/herdr/canonical_case_recovery.py': 'overlays/herdr/canonical_case_recovery.py', 'composed-core/herdr/canonical_case_runtime.py': 'overlays/herdr/canonical_case_runtime.py', 'composed-core/herdr/canonical_startup_observation.py': 'overlays/herdr/canonical_startup_observation.py', 'composed-core/herdr/case_roster.py': 'overlays/herdr/case_roster.py', 'composed-core/herdr/child_projection.py': 'overlays/herdr/child_projection.py', 'composed-core/herdr/credential_isolation.py': 'overlays/herdr/credential_isolation.py', 'composed-core/herdr/host_bootstrap.py': 'overlays/herdr/host_bootstrap.py', 'composed-core/herdr/host_configuration.py': 'overlays/herdr/host_configuration.py', 'composed-core/herdr/host_model_transport.py': 'overlays/herdr/host_model_transport.py', 'composed-core/herdr/host_reference_binding.py': 'overlays/herdr/host_reference_binding.py', 'composed-core/herdr/launch_environment.py': 'overlays/herdr/launch_environment.py', 'composed-core/herdr/launch_plan_issuer.py': 'overlays/herdr/launch_plan_issuer.py', 'composed-core/herdr/metadata_provider.py': 'overlays/herdr/metadata_provider.py', 'composed-core/herdr/native_lifetime.py': 'overlays/herdr/native_lifetime.py', 'composed-core/herdr/native_preparation.py': 'overlays/herdr/native_preparation.py', 'composed-core/herdr/native_preparation_transport.py': 'overlays/herdr/native_preparation_transport.py', 'composed-core/herdr/native_preparation_transport_v2.py': 'overlays/herdr/native_preparation_transport_v2.py', 'composed-core/herdr/native_ticket_v2.py': 'overlays/herdr/native_ticket_v2.py', 'composed-core/herdr/observed_proc.py': 'overlays/herdr/observed_proc.py', 'composed-core/herdr/observer_client.py': 'overlays/herdr/observer_client.py', 'composed-core/herdr/offline_case_host.py': 'overlays/herdr/offline_case_host.py', 'composed-core/herdr/ownership_release.py': 'overlays/herdr/ownership_release.py', 'composed-core/herdr/policy_launch.py': 'overlays/herdr/policy_launch.py', 'composed-core/herdr/prep_entry.py': 'overlays/herdr/prep_entry.py', 'composed-core/herdr/preparation_contract.py': 'overlays/herdr/preparation_contract.py', 'composed-core/herdr/private_mount_plan.py': 'overlays/herdr/private_mount_plan.py', 'composed-core/herdr/private_sdk_credentials.py': 'overlays/herdr/private_sdk_credentials.py', 'composed-core/herdr/resolver_namespace.py': 'overlays/herdr/resolver_namespace.py', 'composed-core/herdr/runtime.py': 'overlays/herdr/runtime.py', 'composed-core/herdr/scheduler.py': 'overlays/herdr/scheduler.py', 'composed-core/herdr/sdk_phase.py': 'overlays/herdr/sdk_phase.py', 'composed-core/herdr/security.py': 'overlays/herdr/security.py', 'composed-core/herdr/trusted_observer.py': 'overlays/herdr/trusted_observer.py', 'composed-core/herdr/unit_templates.py': 'overlays/herdr/unit_templates.py', 'composed-core/herdr/work_authority.py': 'overlays/herdr/work_authority.py', 'composed-core/herdr/taskgraph.py': 'overlays/herdr/taskgraph.py', 'composed-core/herdr/work_configuration.py': 'overlays/herdr/work_configuration.py', 'composed-core/provenance/CANONICAL_SOURCE_MANIFEST.sha256': 'overlays/provenance/CANONICAL_SOURCE_MANIFEST.sha256', 'composed-core/tests/herdr/test_native_namespace_contract.py': 'overlays/tests/herdr/test_native_namespace_contract.py', 'composed-core/tests/herdr/test_claimed_child_contracts.py': 'overlays/tests/herdr/test_claimed_child_contracts.py', 'composed-core/tests/herdr/test_taskgraph.py': 'overlays/tests/herdr/test_taskgraph.py', 'composed-core/tests/herdr/test_clean_envelope.py': 'overlays/tests/herdr/test_clean_envelope.py', 'composed-core/tests/herdr/test_compact_policy_evidence.py': 'overlays/tests/herdr/test_compact_policy_evidence.py', 'composed-core/tests/herdr/test_external_knowledge_sandbox.py': 'overlays/tests/herdr/test_external_knowledge_sandbox.py', 'composed-core/tests/herdr/test_file_authority.py': 'overlays/tests/herdr/test_file_authority.py', 'composed-core/tests/herdr/test_hermes_guard.py': 'overlays/tests/herdr/test_hermes_guard.py', 'composed-core/tests/herdr/test_host_policy_launch.py': 'overlays/tests/herdr/test_host_policy_launch.py', 'composed-core/tests/herdr/test_launch_environment.py': 'overlays/tests/herdr/test_launch_environment.py', 'composed-core/tests/herdr/test_launch_plan_handoff.py': 'overlays/tests/herdr/test_launch_plan_handoff.py', 'composed-core/tests/herdr/test_native_cli_bootstrap_wiring.py': 'overlays/tests/herdr/test_native_cli_bootstrap_wiring.py', 'composed-core/tests/herdr/test_offline_provider.py': 'overlays/tests/herdr/test_offline_provider.py', 'composed-core/tests/herdr/test_p0_launch_regressions.py': 'overlays/tests/herdr/test_p0_launch_regressions.py', 'composed-core/tests/herdr/test_policy_bootstrap.py': 'overlays/tests/herdr/test_policy_bootstrap.py', 'composed-core/tests/herdr/test_private_host_composition.py': 'overlays/tests/herdr/test_private_host_composition.py', 'composed-core/tests/herdr/test_private_mount_plan.py': 'overlays/tests/herdr/test_private_mount_plan.py', 'composed-core/tests/herdr/test_private_profile_fd_bridge.py': 'overlays/tests/herdr/test_private_profile_fd_bridge.py', 'composed-core/tests/herdr/test_private_profile_namespace.py': 'overlays/tests/herdr/test_private_profile_namespace.py', 'composed-core/tests/herdr/test_private_profile_sdk_initialization.py': 'overlays/tests/herdr/test_private_profile_sdk_initialization.py', 'composed-core/tests/herdr/test_security.py': 'overlays/tests/herdr/test_security.py', 'composed-core/tests/herdr/test_trusted_profile_handoff.py': 'overlays/tests/herdr/test_trusted_profile_handoff.py', 'composed-core/tests/herdr/test_work_cycle.py': 'overlays/tests/herdr/test_work_cycle.py', 'composed-core/tests/physical/clean_envelope.py': 'overlays/tests/physical/clean_envelope.py', 'composed-core/tests/physical/offline_case_inputs.json': 'overlays/tests/physical/offline_case_inputs.json', 'composed-core/tests/physical/offline_pilot.py': 'overlays/tests/physical/offline_pilot.py', 'composed-core/tests/physical/offline_provider.py': 'overlays/tests/physical/offline_provider.py'}, "closed runtime overlay composition required")
    require(type(files) is dict and set(files) == {'core_bridge.py', 'native/case_roster.py', 'native/prep_entry.py', 'native/prep_entry_v2.py', 'native/preparation_contract.py', 'native/trusted_prepare.py', 'native_preparation.py', 'native_preparation_transport.py', 'observer/case_roster.py', 'observer/metadata_provider.py', 'observer/observer_entry.py', 'observer/prep_entry.py', 'observer/trusted_observer.py', 'offline_case/__init__.py', 'offline_case/admission.py', 'offline_case/case.py', 'offline_case/case_anchor.py', 'offline_case/custody.py', 'offline_case/driver.py', 'offline_case/historical_holders.py', 'offline_case/host_service.py', 'offline_case/native.py', 'offline_case/native_source.py', 'offline_case/outer_lifecycle.py', 'offline_case/payload.py', 'offline_case/profile_observations.py', 'offline_case/publication.py', 'offline_case/publisher.py', 'offline_case/root_effects.py', 'offline_case/runtime_inputs.py', 'overlays/agent-stack/bin/agent-herdr-fd-launch', 'overlays/agent-stack/bin/agent-hermes-policy-run', 'overlays/agent-stack/bin/agent-hermes-policy-stage1', 'overlays/agent-stack/bin/agent-task-worker', 'overlays/agent-stack/bin/agent_completion_evidence.py', 'overlays/agent-stack/bin/agent_durable_sandbox.py', 'overlays/agent-stack/bin/offline-case-host-entry', 'overlays/herdr/bootstrap_authority.py', 'overlays/herdr/bootstrap_self_observation.py', 'overlays/herdr/canonical_case_claim.py', 'overlays/herdr/canonical_case_effects.py', 'overlays/herdr/canonical_case_probe.py', 'overlays/herdr/canonical_case_recovery.py', 'overlays/herdr/canonical_case_runtime.py', 'overlays/herdr/canonical_startup_observation.py', 'overlays/herdr/case_roster.py', 'overlays/herdr/child_projection.py', 'overlays/herdr/credential_isolation.py', 'overlays/herdr/host_bootstrap.py', 'overlays/herdr/host_configuration.py', 'overlays/herdr/host_model_transport.py', 'overlays/herdr/host_reference_binding.py', 'overlays/herdr/launch_environment.py', 'overlays/herdr/launch_plan_issuer.py', 'overlays/herdr/metadata_provider.py', 'overlays/herdr/native_lifetime.py', 'overlays/herdr/native_preparation.py', 'overlays/herdr/native_preparation_transport.py', 'overlays/herdr/native_preparation_transport_v2.py', 'overlays/herdr/native_ticket_v2.py', 'overlays/herdr/observed_proc.py', 'overlays/herdr/observer_client.py', 'overlays/herdr/offline_case_host.py', 'overlays/herdr/ownership_release.py', 'overlays/herdr/policy_launch.py', 'overlays/herdr/prep_entry.py', 'overlays/herdr/preparation_contract.py', 'overlays/herdr/private_mount_plan.py', 'overlays/herdr/private_sdk_credentials.py', 'overlays/herdr/resolver_namespace.py', 'overlays/herdr/runtime.py', 'overlays/herdr/scheduler.py', 'overlays/herdr/sdk_phase.py', 'overlays/herdr/security.py', 'overlays/herdr/trusted_observer.py', 'overlays/herdr/unit_templates.py', 'overlays/herdr/work_authority.py', 'overlays/herdr/taskgraph.py', 'overlays/herdr/work_configuration.py', 'overlays/host-profile.apparmor', 'overlays/observer-profile.apparmor', 'overlays/operator-profile.apparmor', 'overlays/provenance/CANONICAL_SOURCE_MANIFEST.sha256', 'overlays/tests/herdr/test_native_namespace_contract.py', 'overlays/tests/herdr/test_claimed_child_contracts.py', 'overlays/tests/herdr/test_taskgraph.py', 'overlays/tests/herdr/test_clean_envelope.py', 'overlays/tests/herdr/test_compact_policy_evidence.py', 'overlays/tests/herdr/test_external_knowledge_sandbox.py', 'overlays/tests/herdr/test_file_authority.py', 'overlays/tests/herdr/test_hermes_guard.py', 'overlays/tests/herdr/test_host_policy_launch.py', 'overlays/tests/herdr/test_launch_environment.py', 'overlays/tests/herdr/test_launch_plan_handoff.py', 'overlays/tests/herdr/test_native_cli_bootstrap_wiring.py', 'overlays/tests/herdr/test_offline_provider.py', 'overlays/tests/herdr/test_p0_launch_regressions.py', 'overlays/tests/herdr/test_policy_bootstrap.py', 'overlays/tests/herdr/test_private_host_composition.py', 'overlays/tests/herdr/test_private_mount_plan.py', 'overlays/tests/herdr/test_private_profile_fd_bridge.py', 'overlays/tests/herdr/test_private_profile_namespace.py', 'overlays/tests/herdr/test_private_profile_sdk_initialization.py', 'overlays/tests/herdr/test_security.py', 'overlays/tests/herdr/test_trusted_profile_handoff.py', 'overlays/tests/herdr/test_work_cycle.py', 'overlays/tests/physical/clean_envelope.py', 'overlays/tests/physical/offline_case_inputs.json', 'overlays/tests/physical/offline_pilot.py', 'overlays/tests/physical/offline_provider.py', 'overlays/trusted-preparation.apparmor', 'overlays/worker-profile.apparmor', 'prep_entry.py', 'runtime-binding.json', 'trusted_prepare.py', 'units/herdr-offline-03414499dd0d1986.service', 'units/herdr-offline-cleanup-03414499dd0d1986.service', 'units/herdr-offline-cleanup-03414499dd0d1986.timer', 'units/herdr-offline-expire-03414499dd0d1986.service', 'units/herdr-offline-host-03414499dd0d1986.service', 'units/herdr-offline-operator-03414499dd0d1986.service'}, "build inventory mismatch")
    installations = {}
    for name in files:
        if name.startswith("units/"):
            target = "/etc/systemd/system/" + name.removeprefix("units/")
        elif name.startswith("overlays/herdr/"):
            target = COMPOSED_CORE + "/herdr/" + name.removeprefix("overlays/herdr/")
        elif name.startswith("overlays/agent-stack/bin/"):
            target = COMPOSED_CORE + "/agent-stack/bin/" + name.removeprefix("overlays/agent-stack/bin/")
        elif name.startswith("overlays/tests/"):
            target = COMPOSED_CORE + "/tests/" + name.removeprefix("overlays/tests/")
        elif name == "overlays/provenance/CANONICAL_SOURCE_MANIFEST.sha256":
            target = COMPOSED_CORE + "/provenance/CANONICAL_SOURCE_MANIFEST.sha256"
        elif name == "overlays/worker-profile.apparmor":
            target = "/etc/herdr/worker-profile.apparmor"
        elif name == "overlays/observer-profile.apparmor":
            target = "/etc/herdr/observer-profile.apparmor"
        elif name == "overlays/trusted-preparation.apparmor":
            target = "/etc/herdr/trusted-preparation.apparmor"
        elif name == "overlays/operator-profile.apparmor":
            target = "/etc/herdr/operator-profile.apparmor"
        elif name == "overlays/host-profile.apparmor":
            target = "/etc/herdr/host-profile.apparmor"
        else:
            target = INSTALL_ROOT + "/" + name
        installations[name] = target
    require(build["install_targets"] == installations and
            len(set(installations.values())) == len(installations),
            "closed deterministic installation map required")
    for name, digest in files.items():
        require(hex64(digest) and sha(pinned_bytes(root / name, root_owned=root_owned)) == digest,
                "changed build file: " + name)
    core_index_raw = pinned_bytes(root / "canonical-core-index.json", root_owned=root_owned)
    require(sha(core_index_raw) == CORE_BASE_INDEX, "canonical core base index changed")
    core_index = parse(core_index_raw, 262144)
    require(set(core_index) == {"schema", "kind", "files"} and
            core_index["schema"] == 1 and
            core_index["kind"] == "PINNED_CANONICAL_CORE_BASE" and
            type(core_index["files"]) is dict and len(core_index["files"]) == 448,
            "canonical core base inventory invalid")
    expected_core = dict(core_index["files"])
    for target, source in build["overlay_targets"].items():
        require(target.startswith("composed-core/") and source in files,
                "foreign canonical overlay")
        expected_core[target.removeprefix("composed-core/")] = files[source]
    require(build["core_files"] == expected_core and
            len(build["core_files"]) == 476, "composed canonical core inventory changed")
    from .publisher import expected_modes
    require(build["installed_modes"] == expected_modes(build),
            "installed executable or data modes changed")
    core_root = root / "composed-core"
    require({str(path.relative_to(core_root)) for path in core_root.rglob("*")
             if path.is_file() or path.is_symlink()} == set(expected_core),
            "composed canonical core contains extra or missing files")
    for name, digest in expected_core.items():
        require(hex64(digest) and
                sha(pinned_bytes(core_root / name, root_owned=root_owned)) == digest,
                "composed canonical core member changed: " + name)
    # The original 1471-member inventory remains hash-bound metadata. Runtime
    # verifies only the explicit retained closure. SOURCE construction checks
    # the entire original separately before selecting these bytes.
    require(baseline_index is None or Path(baseline_index) == root / "accepted-source-index.json",
            "external origin index forbidden")
    from .runtime_inputs import validate_retained
    runtime_index = validate_retained(root, baseline, root_owned=root_owned)
    from .runtime_inputs import validate_package_inventory
    validate_package_inventory(root, build, runtime_index, installed=installed)
    require(sha(pinned_bytes(baseline / "proposed/offline.apparmor", root_owned=root_owned)) == ACCEPTED_PROFILE_SOURCE,
            "baseline profile changed")
    require(sha(pinned_bytes(root / "overlays/worker-profile.apparmor", root_owned=root_owned)) == PROFILE_SOURCE,
            "candidate worker profile changed")
    require(sha(pinned_bytes(root / "overlays/observer-profile.apparmor", root_owned=root_owned)) == OBSERVER_SOURCE,
            "candidate observer profile changed")
    require(sha(pinned_bytes(root / "overlays/trusted-preparation.apparmor", root_owned=root_owned)) == PREP_SOURCE,
            "candidate preparation profile changed")
    require(sha(pinned_bytes(root / "overlays/host-profile.apparmor", root_owned=root_owned)) ==
            build["host_source"], "candidate host profile changed")
    pinned_core = {
        "proposed/core/herdr/policy_launch.py": "cffc9922d2483aa5779de5590a587a5159c68d14b5fdd94be78309b1aba48ec4",
        "proposed/core/herdr/credential_ingress_filter.py": "2176af7076107fd7f6888339ceb2c0611f2cc193e251db974d4f7ab540d742c8",
        "proposed/runtime-composition.json": "f812f242c52deca4c6b9586881faec68d7b631f5d66a73b05ec3114662cb5d53",
    }
    for name, digest in pinned_core.items():
        require(sha(pinned_bytes(baseline / name, root_owned=root_owned)) == digest,
                "baseline core changed: " + name)


def plan(build: dict) -> dict:
    return {"status": "DATA_ONLY_UNISSUED", "nonce": NONCE, "case_unit": CASE,
            "cleanup_unit": CLEANUP, "cleanup_timer": TIMER, "deadline": DEADLINE,
            "required_free_bytes": REQUIRED_FREE, "budget": BUDGET,
            "build_sha256": sha(canonical(build)), "authority": "NOT_PRESENT"}


class CaseDriver:
    """One attempt; host effect interface is root only and must return exact observations.

    Journal is subordinate evidence. Host.admit is the accepted fenced Herdr
    admission, never a new issuer. A crash after consume is retirement only.
    """
    def __init__(self, custody, host, clock=time.time):
        self.custody, self.host, self.clock = custody, host, clock

    def start(self, build: dict, *, root: Path, baseline: Path,
              baseline_index: Path | None = None, root_owned=False):
        validate_build(build, root, baseline=baseline, baseline_index=baseline_index,
                       root_owned=root_owned, installed=root_owned)
        a = self.custody.authority()
        now = int(self.clock())
        validate_authority(a, build, now=now, free=self.host.capacity(),
                           boot=self.host.boot_id())
        inputs = self.host.root_inputs()
        require(type(inputs) is dict and set(inputs) == {"profile_source", "observer_source", "prep_source", "host_profile_source", "operator_source", "config",
                "projection", "runtime", "host_selector"} and all(type(x) is bytes and x for x in inputs.values()),
                "root inputs missing")
        for name, raw in inputs.items():
            digest_key = ("profile_source_sha256" if name == "profile_source" else
                          "observer_source_sha256" if name == "observer_source" else
                          "prep_source_sha256" if name == "prep_source" else
                          "host_profile_source_sha256" if name == "host_profile_source" else
                          name + "_sha256")
            require(sha(raw) == a[digest_key], "root input hash mismatch")
        if hasattr(self.host, "preflight"):
            self.host.preflight(a, build, root)
        require(self.custody.state() is None and not self.custody.consumed(a["challenge"]),
                "attempt already consumed or uncertain")
        binding = {"nonce": NONCE, "challenge": a["challenge"],
                   "boot_id": a["boot_id"], "authority_sha256": sha(canonical(a)),
                   "build_sha256": a["build_sha256"]}
        self.custody.consume(a["challenge"], binding)
        try:
            self.custody.save({"phase": "CONSUMED", "binding": binding})
            # Cleanup must be independently armed before any admission or
            # trusted preparation can allocate a holder. The fixed nonce
            # marker also lets the cleanup entrypoint recover this binding
            # if the driver dies before publishing another state.
            self.host.arm_cleanup(CLEANUP, TIMER, DEADLINE, binding)
            require(self.host.cleanup_armed(TIMER, binding) is True,
                    "independent cleanup not armed")
            self.custody.save({"phase": "ARMED", "binding": binding})
            admission = self.host.admit(a, binding)  # existing Herdr fence/reservation
            require(type(admission) is dict and
                    set(admission) == {"binding", "kind", "task_id", "run_token",
                                       "fencing_token", "task_sha256", "work_catalogue_sha256"} and
                    admission["binding"] == binding and
                    admission["kind"] == "CANONICAL_RUNNING_ROOT_CLAIM" and
                    type(admission["task_id"]) is str and admission["task_id"] and
                    type(admission["run_token"]) is str and admission["run_token"] and
                    type(admission["fencing_token"]) is int and admission["fencing_token"] > 0 and
                    all(hex64(admission[key]) for key in
                        ("task_sha256", "work_catalogue_sha256")),
                    "original Herdr root claim receipt mismatch")
            self.custody.save({"phase": "ADMITTED", "binding": binding})
            prep = self.host.prepare(a, binding)
            require(prep == {"binding": binding, "sdk_imported": False,
                            "setup_fds_closed": True, "setup_paths_hidden": True},
                    "trusted preparation unproven")
            self.custody.save({"phase": "PREPARED", "binding": binding})
            kernel = self.host.verify_kernel(a, binding)
            require(kernel == {"binding": binding, "profile": PROFILE,
                               "loaded_sha256": a["compiled_profile_sha256"],
                               "observer": OBSERVER,
                               "observer_loaded_sha256": a["observer_compiled_sha256"],
                               "preparer": PREP,
                               "prep_loaded_sha256": a["prep_compiled_sha256"],
                               "host_profile": HOST_PROFILE,
                               "host_loaded_sha256": a["host_compiled_sha256"],
                               "enforce": True, "observed": True},
                    "loaded kernel policy unproven")
            require(int(self.clock()) < DEADLINE, "case deadline reached")
            self.custody.save({"phase": "START_INTENT", "binding": binding})
            if hasattr(self.custody, "suspend"):
                self.custody.suspend()
                try:
                    result = self.host.start_case(CASE, binding, BUDGET)
                finally:
                    self.custody.resume()
            else:
                result = self.host.start_case(CASE, binding, BUDGET)
            require(self.custody.state() == {"phase": "START_INTENT", "binding": binding},
                    "independent cleanup raced worker completion")
            require(result == {"binding": binding, "completed": True,
                               "root": True, "managed_children": 1,
                               "outcome": "SDK_GUARDED_FIXTURE_INGRESS_ONLY",
                               "semantic_child_acceptance": "NOT_ESTABLISHED",
                               "parent_dependency": "NOT_ESTABLISHED", "E2E184": "NOT_ESTABLISHED"},
                    "case guarded-ingress result unknown")
            self.custody.save({"phase": "FINISHED", "binding": binding})
            return result
        finally:
            self.cleanup()

    def cleanup(self):
        state = self.custody.state()
        require(type(state) is dict and set(state) == {"phase", "binding"},
                "unknown attempt state")
        binding = state["binding"]
        require(state["phase"] in {"CONSUMED", "ADMITTED", "ARMED", "PREPARED",
                "START_INTENT", "FINISHED", "FENCE_INTENT", "STOP_INTENT",
                "RETIRE_INTENT", "RETAINED_UNKNOWN", "RETIRED"} and
                type(binding) is dict and set(binding) == {"nonce", "challenge", "boot_id",
                "authority_sha256", "build_sha256"} and
                binding["nonce"] == NONCE and
                self.custody.consumed(binding["challenge"]) and
                binding["boot_id"] == self.host.boot_id(),
                "foreign or stale boot attempt")
        if state["phase"] == "RETIRED":
            if hasattr(self.host, "stop_host_if_retired"):
                require(self.host.stop_host_if_retired() is True,
                        "owned host stop incomplete")
            return {"phase": "RETIRED", "binding": binding}
        try:
            self.custody.save({"phase": "FENCE_INTENT", "binding": binding})
            require(self.host.fence(binding) is True, "birth/attachment fence unknown")
            self.custody.save({"phase": "STOP_INTENT", "binding": binding})
            require(self.host.stop_owned(CASE, binding) is True, "owned stop unknown")
            observation = self.host.observe_all(binding)
            require(type(observation) is dict and observation == {
                "fenced": True, "case_cgroup_empty": True,
                "descendants": [], "fds": [], "maps": [], "profile_holders": [],
                "complete": True, "boot_id": binding["boot_id"]},
                "holders or observation unknown")
            self.custody.save({"phase": "RETIRE_INTENT", "binding": binding})
            require(self.host.retire_owned(binding, observation) is True,
                    "owned policy/mount retirement unknown")
            self.custody.save({"phase": "RETIRED", "binding": binding})
        except BaseException:
            # A failed attachment fence cannot authorize retirement. Still
            # try to stop the exact owned unit, then retain every policy and
            # mount for independent reconciliation.
            try:
                self.host.stop_owned(CASE, binding)
                if hasattr(self.host, "observe_historical"):
                    self.host.observe_historical(binding)
            except BaseException:
                pass
            self.custody.save({"phase": "RETAINED_UNKNOWN", "binding": binding})
            raise
        if hasattr(self.host, "stop_host_if_retired"):
            require(self.host.stop_host_if_retired() is True,
                    "owned host stop incomplete")
        return {"phase": "RETIRED", "binding": binding}
