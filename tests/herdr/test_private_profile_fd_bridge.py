"""Production FD-launcher extension is tested without any model invocation."""
import hashlib
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import pytest
from herdr.private_profile_namespace import PrivateProfileSnapshot

BIN = Path(__file__).resolve().parents[2] / "agent-stack" / "bin" / "agent_durable_sandbox.py"


def bridge_module():
    loader = importlib.machinery.SourceFileLoader("test_profile_fd_launcher", str(BIN))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[loader.name] = module
    loader.exec_module(module)
    return module


def fixture_snapshot(tmp_path):
    profile = tmp_path / "approved"
    profile.mkdir()
    data = {
        "config.yaml": b"approved: fixture\n",
        ".env": b"DUMMY_TOKEN=non-secret-fixture\n",
    }
    for name, contents in data.items():
        (profile / name).write_bytes(contents)
    digests = {name: hashlib.sha256(raw).hexdigest() for name, raw in data.items()}
    return profile, data, PrivateProfileSnapshot.from_approved(
        profile, name="quantlab", approved_sha256=digests,
    )


def command_for(sandbox, snapshot, *, descriptors=None, opts=None):
    entries = descriptors if descriptors is not None else snapshot.fd_descriptors()
    flags = opts if opts is not None else snapshot.mount_arguments()
    return [
        "/usr/bin/python3", "-I", "-S", "-c", sandbox._POLICY_FD_LAUNCHER,
        json.dumps(entries, separators=(",", ":")),
        "/usr/bin/bwrap", "--ro-bind", "/", "/", "--dev", "/dev",
        "--proc", "/proc", "--unshare-pid",
        *flags, "--", "/bin/sleep", "4",
    ]


def test_host_policy_fd_launcher_binds_sealed_profile_without_raw_secrets(tmp_path):
    if shutil.which("bwrap") is None:
        pytest.skip("bubblewrap unavailable")
    if not Path("/home/agentops").is_dir():
        pytest.skip("physical profile FD test requires the fixed staging home")
    sandbox = bridge_module()
    source, values, snapshot = fixture_snapshot(tmp_path)
    with snapshot:
        command = command_for(sandbox, snapshot)
        assert "DUMMY_TOKEN" not in " ".join(command)
        proc = subprocess.Popen(
            command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        try:
            time.sleep(.3)
            if proc.poll() is not None:
                error = (proc.stderr.read() or b"")[:500].decode(errors="replace")
                if "Operation not permitted" in error or "Creating new namespace failed" in error:
                    pytest.skip("unprivileged bwrap disabled by CI runner")
                pytest.fail("sealed profile FD launch failed: " + error)
            children = Path(f"/proc/{proc.pid}/task/{proc.pid}/children").read_text().split()
            assert len(children) == 1
            child = int(children[0])
            inside = Path(f"/proc/{child}/root")
            assert os.readlink(f"/proc/{child}/ns/mnt") != os.readlink("/proc/self/ns/mnt")
            assert (inside / "home/agentops/.hermes/profiles/quantlab/config.yaml").read_bytes() == values["config.yaml"]
            assert (inside / "home/agentops/.hermes/profiles/quantlab/.env").read_bytes() == values[".env"]
            source.rename(tmp_path / "approved-old")
            hostile = tmp_path / "hostile-source"
            hostile.mkdir()
            (hostile / "config.yaml").write_bytes(b"hostile: true\n")
            (hostile / ".env").write_bytes(b"HOSTILE_TOKEN=forbidden\n")
            source.symlink_to(hostile, target_is_directory=True)
            assert (inside / "home/agentops/.hermes/profiles/quantlab/config.yaml").read_bytes() == values["config.yaml"]
            assert (inside / "home/agentops/.hermes/profiles/quantlab/.env").read_bytes() == values[".env"]
        finally:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill()


@pytest.mark.parametrize("mutation,expected", [
    ("wrong_digest", "policy_fd_profile_digest_mismatch"),
    ("mixed_profiles", "policy_fd_profile_mismatch"),
    ("without_private_home", "policy_fd_profile_data_without_private_home"),
    ("missing_runtime_dir", "policy_fd_private_runtime_missing"),
    ("wrong_target", "policy_fd_profile_target_invalid"),
    ("profile_override", "policy_fd_private_home_shadowed"),
    ("nested_tmpfs", "policy_fd_private_home_shadowed"),
    ("data_before_home", "policy_fd_private_home_order_invalid"),
])
def test_sealed_fd_policy_launcher_fails_before_bwrap_on_invalid_metadata(
    tmp_path, mutation, expected,
):
    sandbox = bridge_module()
    source, values, snapshot = fixture_snapshot(tmp_path)
    with snapshot:
        descriptions = snapshot.fd_descriptors()
        flags = snapshot.mount_arguments()
        if mutation == "wrong_digest":
            descriptions[0]["sha256"] = "0" * 64
        elif mutation == "mixed_profiles":
            descriptions[0]["target"] = descriptions[0]["target"].replace(
                "/quantlab/", "/majak/",
            )
            index = flags.index("--ro-bind-data")
            flags[index + 2] = descriptions[0]["target"]
        elif mutation == "without_private_home":
            index = flags.index("--tmpfs")
            del flags[index:index + 2]
        elif mutation == "missing_runtime_dir":
            index = flags.index(str(snapshot.destination / "logs"))
            assert flags[index - 1] == "--dir"
            del flags[index - 1:index + 1]
        elif mutation == "wrong_target":
            descriptions[0]["target"] = (
                "/home/agentops/.hermes/profiles/quantlab/../logs/secret"
            )
            index = flags.index("--ro-bind-data")
            flags[index + 2] = descriptions[0]["target"]
        elif mutation == "profile_override":
            flags.extend(["--ro-bind", str(source), str(snapshot.destination)])
        elif mutation == "nested_tmpfs":
            flags.extend(["--tmpfs", str(snapshot.destination)])
        elif mutation == "data_before_home":
            index = flags.index("--ro-bind-data")
            item = flags[index:index + 3]
            del flags[index:index + 3]
            flags[0:0] = item
        cmd = command_for(sandbox, snapshot, descriptors=descriptions, opts=flags)
        completed = subprocess.run(cmd, capture_output=True, timeout=8)
        assert completed.returncode != 0
        assert expected.encode() in completed.stderr


def test_unsealed_regular_fd_cannot_impersonate_profile_memfd(tmp_path):
    sandbox = bridge_module()
    source, values, snapshot = fixture_snapshot(tmp_path)
    ordinary = tmp_path / "normal-file"
    ordinary.write_bytes(values["config.yaml"])
    with snapshot:
        with ordinary.open("rb") as input_file:
            desc = snapshot.fd_descriptors()
            record = desc[-1]
            fd = input_file.fileno()
            info = os.fstat(fd)
            record.update({
                "source": f"/proc/{os.getpid()}/fd/{fd}",
                "fd": fd,
                "device": info.st_dev,
                "inode": info.st_ino,
                "size": len(values["config.yaml"]),
                "sha256": hashlib.sha256(values["config.yaml"]).hexdigest(),
            })
            mounts = snapshot.mount_arguments()
            index = mounts.index("--ro-bind-data")
            # Since the sorted order is .env then config, the second bind has
            # the altered data descriptor. Adjust its FD argument.
            indices = [i for i in range(len(mounts)) if mounts[i] == "--ro-bind-data"]
            mounts[indices[-1] + 1] = str(fd)
            result = subprocess.run(
                command_for(sandbox, snapshot, descriptors=desc, opts=mounts),
                capture_output=True, timeout=8,
            )
            assert result.returncode != 0
            assert b"policy_fd_profile_not_sealed" in result.stderr or b"Invalid argument" in result.stderr
