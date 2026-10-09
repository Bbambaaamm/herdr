"""Production FD-launcher extension is tested without any model invocation."""
import errno
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
            mount_lines = Path(f"/proc/{child}/mountinfo").read_text().splitlines()
            def mounted_flags(target):
                rows = [line for line in mount_lines
                        if line.split(" - ", 1)[0].split()[4] == target]
                assert len(rows) == 1
                return rows[0].split(" - ", 1)[0].split()[5].split(",")
            assert "ro" in mounted_flags("/home/agentops")
            assert "rw" in mounted_flags("/home/agentops/.hermes/profiles/quantlab/logs")
            readonly_profile = inside / "home/agentops/.hermes/profiles/quantlab"
            attacker_target = inside / "home/agentops/.hermes/profiles/attacker"
            with pytest.raises(OSError) as denied_rename:
                readonly_profile.rename(attacker_target)
            assert denied_rename.value.errno == errno.EROFS
            with pytest.raises(OSError) as denied_chmod:
                readonly_profile.chmod(0o777)
            assert denied_chmod.value.errno == errno.EROFS
            private_log = readonly_profile / "logs/runtime-fixture.txt"
            private_log.write_bytes(b"private runtime allowed")
            assert private_log.read_bytes() == b"private runtime allowed"
            with pytest.raises(OSError) as denied_config:
                (readonly_profile / "config.yaml").write_bytes(b"forbidden")
            assert denied_config.value.errno == errno.EROFS
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
    ("parent_bind_home", "policy_fd_private_home_shadowed"),
    ("parent_bind_root", "policy_fd_private_home_shadowed"),
    ("parent_tmpfs_home", "policy_fd_private_home_shadowed"),
    ("missing_ro_remount", "policy_fd_private_home_not_readonly"),
    ("early_ro_remount", "policy_fd_private_home_not_readonly"),
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
            assert flags[index - 1] == "--tmpfs"
            del flags[index - 1:index + 1]
        elif mutation == "wrong_target":
            descriptions[0]["target"] = (
                "/home/agentops/.hermes/profiles/quantlab/../logs/secret"
            )
            index = flags.index("--ro-bind-data")
            flags[index + 2] = descriptions[0]["target"]
        elif mutation == "profile_override":
            flags[-2:-2] = ["--ro-bind", str(source), str(snapshot.destination)]
        elif mutation == "nested_tmpfs":
            flags[-2:-2] = ["--tmpfs", str(snapshot.destination)]
        elif mutation == "parent_bind_home":
            flags[-2:-2] = ["--bind", str(source), "/home"]
        elif mutation == "parent_bind_root":
            flags[-2:-2] = ["--ro-bind", "/", "/"]
        elif mutation == "parent_tmpfs_home":
            flags[-2:-2] = ["--tmpfs", "/home"]
        elif mutation == "missing_ro_remount":
            del flags[-2:]
        elif mutation == "early_ro_remount":
            readonly = flags[-2:]
            del flags[-2:]
            flags[:0] = readonly
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

@pytest.mark.parametrize("attack,expected", [
    ("recursive_args", "policy_fd_private_option_denied"),
    ("relative_bind", "policy_fd_private_mount_path_invalid"),
    ("dotdot_bind", "policy_fd_private_mount_path_invalid"),
    ("repeat_slash_bind", "policy_fd_private_mount_path_invalid"),
    ("cap_sys_admin", "policy_fd_private_option_denied"),
    ("fail_open", "policy_fd_private_option_denied"),
    ("pidns", "policy_fd_private_option_denied"),
    ("unset_home", "policy_fd_private_home_env_invalid"),
    ("redirect_home", "policy_fd_private_home_env_invalid"),
    ("untrusted_profile_env", "policy_fd_private_home_env_invalid"),
    ("clearenv", "policy_fd_private_option_denied"),
    ("omit_pid_unshare", "policy_fd_private_proc_missing"),
    ("omit_proc_mount", "policy_fd_private_proc_missing"),
    ("shadow_proc", "policy_fd_private_proc_shadowed"),
    ("missing_explicit_home", "policy_fd_private_home_env_invalid"),
    ("missing_hermes_unset", "policy_fd_private_home_env_invalid"),
    ("duplicate_xdg_unset", "policy_fd_private_home_env_invalid"),
])
def test_private_home_rejects_bubblewrap_grammar_and_environment_bypasses(
    tmp_path, attack, expected,
):
    sandbox = bridge_module()
    source, _, snapshot = fixture_snapshot(tmp_path)
    with snapshot:
        opts = snapshot.mount_arguments()
        injected = {
            "recursive_args": ["--args", "0"],
            "relative_bind": ["--bind", str(source), "home/agentops/.hermes/profiles/quantlab"],
            "dotdot_bind": ["--bind", str(source),
                            "/home/agentops/../agentops/.hermes/profiles/quantlab"],
            "repeat_slash_bind": ["--ro-bind", str(source), "/home//agentops/.hermes"],
            "cap_sys_admin": ["--cap-add", "CAP_SYS_ADMIN"],
            "fail_open": ["--not-a-security-boundary"],
            "pidns": ["--pidns", "0"],
            "unset_home": ["--unsetenv", "HOME"],
            "redirect_home": ["--setenv", "HOME", "/tmp/untrusted"],
            "untrusted_profile_env": ["--setenv", "HERMES_HOME", "/tmp/untrusted"],
            "clearenv": ["--clearenv"],
            "shadow_proc": ["--ro-bind", str(source), "/proc"],
        }
        if attack in injected:
            opts[-2:-2] = injected[attack]
        elif attack == "missing_explicit_home":
            index = opts.index("HOME")
            assert opts[index - 1] == "--setenv"
            del opts[index - 1:index + 2]
        elif attack == "missing_hermes_unset":
            index = opts.index("HERMES_HOME")
            assert opts[index - 1] == "--unsetenv"
            del opts[index - 1:index + 1]
        elif attack == "duplicate_xdg_unset":
            opts[-2:-2] = ["--unsetenv", "XDG_DATA_HOME"]
        command = command_for(sandbox, snapshot, opts=opts)
        if attack == "omit_pid_unshare":
            command.remove("--unshare-pid")
        elif attack == "omit_proc_mount":
            index = command.index("--proc")
            del command[index:index + 2]
        result = subprocess.run(command, capture_output=True, timeout=8)
        assert result.returncode != 0
        assert expected.encode() in result.stderr
