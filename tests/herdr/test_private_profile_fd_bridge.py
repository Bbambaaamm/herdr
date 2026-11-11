"""Production FD-launcher extension is tested without any model invocation."""
import errno
import hashlib
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
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
        "config.yaml": b'{"model":"fixture","api_key":null}\n',
        ".env": b"",
        "auth.json": b'{"fixture_token":"non-secret-fixture"}\n',
    }
    for name, contents in data.items():
        (profile / name).write_bytes(contents)
    digests = {name: hashlib.sha256(raw).hexdigest() for name, raw in data.items()}
    return profile, data, PrivateProfileSnapshot.from_approved(
        profile, name="quantlab", approved_sha256=digests,
    )


def fixture_mount_arguments(snapshot):
    """Model the protected /home parent in portable grammar tests."""
    from herdr import private_profile_namespace as namespace
    original = namespace.os
    class FixtureOS:
        def __getattr__(self, name): return getattr(original, name)
        def lstat(self, path, *args, **kwargs):
            info = original.lstat(path, *args, **kwargs)
            if str(path) == "/home":
                fields = list(info); fields[4] = 0
                return os.stat_result(fields)
            return info
    namespace.os = FixtureOS()
    try:
        return snapshot.mount_arguments()
    finally:
        namespace.os = original


def test_credential_snapshot_is_host_bound_and_never_projected(tmp_path):
    from herdr.private_profile_namespace import PrivateProfileError
    _, values, snapshot = fixture_snapshot(tmp_path)
    with snapshot:
        assert {row.relative for row in snapshot.sdk_files} == {"config.yaml", ".env"}
        assert "auth.json" not in {row["target"].rsplit("/", 1)[-1]
                                   for row in snapshot.fd_descriptors()}
        assert values["auth.json"] not in json.dumps(snapshot.fd_descriptors()).encode()
        auth = next(row for row in snapshot.files if row.relative == "auth.json")
        original = snapshot.files
        try:
            snapshot.files = tuple(row for row in original if row is not auth)
            with pytest.raises(PrivateProfileError, match="host_credential_snapshot_required"):
                snapshot.fd_descriptors()
        finally:
            snapshot.files = original


def command_for(sandbox, snapshot, *, descriptors=None, opts=None):
    from herdr.credential_isolation import SYSTEM_RUNTIME_FILES
    entries = descriptors if descriptors is not None else snapshot.fd_descriptors()
    flags = opts if opts is not None else fixture_mount_arguments(snapshot)
    home_remount = ["--remount-ro", str(snapshot.home)]
    profile_flags, final_home = (flags[:-2], flags[-2:]) if flags[-2:] == home_remount else (flags, [])
    return [
        "/usr/bin/python3", "-I", "-S", "-c", sandbox._POLICY_FD_LAUNCHER,
        json.dumps(entries, separators=(",", ":")),
        "/usr/bin/bwrap", "--tmpfs", "/",
        *(part for name in sorted(SYSTEM_RUNTIME_FILES)
          for part in ("--ro-bind", name, name)),
        "--dev", "/dev", "--proc", "/proc", "--unshare-user", "--unshare-pid",
        "--unshare-net", "--disable-userns", "--cap-drop", "ALL", "--tmpfs", "/tmp",
        *profile_flags, "--tmpfs", "/run", "--tmpfs", "/home/agentops/.config/herdr",
        "--tmpfs", "/opt/agent-platform",
        "--setenv", "PATH", "/run/herdr/policy-code/agent-stack/policy-bin:/usr/bin:/bin",
        "--setenv", "HERDR_DURABLE_SANDBOX", "1",
        *final_home, "--remount-ro", "/",
        "--", "/bin/sleep", "4",
    ]


def approved_invocation(tmp_path, command, entries, *, execute_bwrap=False):
    """Exercise the actual isolated launcher with an explicit root-record double.

    The child substitutes only ownership and bytes of the one fixed /etc
    authority file. It never executes bwrap; an accepted command prints a
    marker after the full grammar and FD checks have passed.
    """
    from herdr.private_mount_plan import request_for, VERSION
    from herdr.policy_launch import IDENTITY_ENV
    from herdr.security import canonical_json_bytes
    from tests.herdr.test_security import identity
    invocation = identity()
    args = command[6:]
    plan = request_for(invocation, entries, args)
    record = tmp_path / "approved-private-mount-plan.json"
    record.write_bytes(canonical_json_bytes(plan)); record.chmod(0o400)
    authority = ("/etc/herdr/launch-plans/" +
                 hashlib.sha256(canonical_json_bytes(invocation.to_json())).hexdigest() + ".json")
    envelope = {"schema_version": VERSION, "authority": authority,
                "authority_sha256": hashlib.sha256(record.read_bytes()).hexdigest(),
                "entries": entries}
    wrapper = r'''
import os, stat, sys
source, envelope, record, authority, execute_bwrap = sys.argv[1:6]
args = sys.argv[6:]
original_lstat, original_open, original_fstat, original_close = os.lstat, os.open, os.fstat, os.close
authority_fds = set()
def owned(info, kind):
    fields = list(info)
    fields[0] = kind | (0o400 if kind == stat.S_IFREG else 0o755)
    fields[4] = 0
    return os.stat_result(fields)
def named(path, *a, **kw):
    name = str(path)
    if name == authority: return owned(original_lstat(record), stat.S_IFREG)
    if name in ('/', '/etc', '/etc/herdr', '/etc/herdr/launch-plans', '/home'):
        return owned(original_lstat(os.path.dirname(record)), stat.S_IFDIR)
    return original_lstat(path, *a, **kw)
def opened(path, *a, **kw):
    approved = str(path) == authority
    fd = original_open(record if approved else path, *a, **kw)
    if approved: authority_fds.add(fd)
    return fd
def held(fd):
    info = original_fstat(fd)
    return owned(info, stat.S_IFREG) if fd in authority_fds else info
def closed(fd):
    authority_fds.discard(fd)
    return original_close(fd)
os.lstat, os.open, os.fstat, os.close = named, opened, held, closed
def reached_exec(file, argv):
    os.write(1, b'APPROVED_GRAMMAR_REACHED_EXEC\n')
    os._exit(0)
if execute_bwrap != '1':
    os.execv = reached_exec
sys.argv = ['launcher', envelope, *args]
exec(source, {'__name__': '__main__'})
'''
    env = {**os.environ, **{key: str(getattr(invocation, field))
                            for field, key in IDENTITY_ENV.items()}}
    invocation = [sys.executable, "-I", "-S", "-c", wrapper,
                  command[4], json.dumps(envelope, separators=(",", ":")),
                  str(record), authority, '1' if execute_bwrap else '0', *args]
    return invocation, env, tuple(row["fd"] for row in entries)


def run_approved_command(tmp_path, command, entries):
    invocation, env, fds = approved_invocation(tmp_path, command, entries)
    try:
        return subprocess.run(invocation, pass_fds=fds, env=env,
                              capture_output=True, timeout=8)
    except subprocess.TimeoutExpired as exc:
        raise AssertionError(f"isolated launcher timed out: stdout={exc.stdout!r} stderr={exc.stderr!r}") from None


def test_isolated_private_home_baseline_reaches_exec(tmp_path):
    sandbox = bridge_module()
    _, _, snapshot = fixture_snapshot(tmp_path)
    with snapshot:
        entries = snapshot.fd_descriptors()
        result = run_approved_command(tmp_path, command_for(sandbox, snapshot,
                                      descriptors=entries), entries)
        assert result.returncode == 0, result.stderr
        assert b"APPROVED_GRAMMAR_REACHED_EXEC" in result.stdout


@pytest.mark.parametrize("mutation", ["duplicate-runtime", "reordered-runtime", "unknown-option"])
def test_approved_private_plan_still_requires_closed_runtime_grammar(tmp_path, mutation):
    from herdr.credential_isolation import SYSTEM_RUNTIME_FILES
    sandbox = bridge_module()
    _, _, snapshot = fixture_snapshot(tmp_path)
    with snapshot:
        entries = snapshot.fd_descriptors()
        command = command_for(sandbox, snapshot, descriptors=entries)
        first = sorted(SYSTEM_RUNTIME_FILES)[0]
        first_mount = command.index(first) - 1
        if mutation == "duplicate-runtime":
            command[first_mount:first_mount] = ["--ro-bind", first, first]
            expected = b"policy_fd_system_runtime_mounts_incomplete"
        elif mutation == "reordered-runtime":
            second_mount = first_mount + 3
            command[first_mount:first_mount + 6] = (
                command[second_mount:second_mount + 3]
                + command[first_mount:first_mount + 3])
            expected = b"policy_fd_system_runtime_mounts_incomplete"
        else:
            command[command.index("--"):command.index("--")] = ["--unknown", "value"]
            expected = b"policy_fd_private_option_denied"
        result = run_approved_command(tmp_path, command, entries)
        assert result.returncode != 0
        assert expected in result.stderr


def test_host_policy_fd_launcher_binds_sealed_profile_without_raw_secrets(tmp_path):
    if shutil.which("bwrap") is None:
        pytest.skip("bubblewrap unavailable")
    if not Path("/home/agentops").is_dir():
        pytest.skip("physical profile FD test requires the fixed staging home")
    sandbox = bridge_module()
    source, values, snapshot = fixture_snapshot(tmp_path)
    with snapshot:
        entries = snapshot.fd_descriptors()
        command = command_for(sandbox, snapshot, descriptors=entries)
        command[command.index("--"):] = ["--", "/bin/bash", "-c", "read -t 4"]
        assert "DUMMY_TOKEN" not in " ".join(command)
        invocation, env, fds = approved_invocation(tmp_path, command, entries,
                                                  execute_bwrap=True)
        proc = subprocess.Popen(
            invocation, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE, env=env, pass_fds=fds,
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
            proc.stdin.close()
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
    ("parent_bind_root", "policy_fd_private_source_exposes_host"),
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
        flags = fixture_mount_arguments(snapshot)
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
        completed = run_approved_command(tmp_path, cmd, descriptions)
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
            mounts = fixture_mount_arguments(snapshot)
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
    ("omit_user_unshare", "policy_fd_private_lifetime_boundary_missing"),
    ("duplicate_user_unshare", "policy_fd_private_lifetime_boundary_missing"),
    ("omit_userns_disable", "policy_fd_private_lifetime_boundary_missing"),
    ("omit_pid_unshare", "policy_fd_private_proc_missing"),
    ("omit_proc_mount", "policy_fd_private_proc_missing"),
    ("shadow_proc", "policy_fd_private_proc_shadowed"),
    ("missing_explicit_home", "policy_fd_private_home_env_invalid"),
    ("missing_hermes_unset", "policy_fd_private_home_env_invalid"),
    ("duplicate_xdg_unset", "policy_fd_private_home_env_invalid"),
    ("bind_host_home_alias", "policy_fd_private_source_exposes_host"),
    ("bind_host_proc_alias", "policy_fd_private_source_exposes_host"),
    ("bind_host_root_alias", "policy_fd_private_source_exposes_host"),
    ("bind_host_home_parent", "policy_fd_private_source_exposes_host"),
    ("bind_host_profile", "policy_fd_private_source_exposes_host"),
    ("bind_other_home_worktree", "policy_fd_private_source_exposes_host"),
    ("symlink_source_alias", "policy_fd_private_source_exposes_host"),
])
def test_private_home_rejects_bubblewrap_grammar_and_environment_bypasses(
    tmp_path, attack, expected,
):
    sandbox = bridge_module()
    source, _, snapshot = fixture_snapshot(tmp_path)
    with snapshot:
        opts = fixture_mount_arguments(snapshot)
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
            "bind_host_home_alias": ["--bind", "/home/agentops", "/mnt/host-home"],
            "bind_host_proc_alias": ["--ro-bind", "/proc", "/mnt/host-proc"],
            "bind_host_root_alias": ["--ro-bind", "/", "/mnt/host-root"],
            "bind_host_home_parent": ["--ro-bind", "/home", "/mnt/host-parent"],
            "bind_host_profile": ["--ro-bind", "/home/agentops/.hermes", "/mnt/host-profile"],
            "bind_other_home_worktree": ["--bind", "/home/agentops/workspaces", "/mnt/other-worktree"],
        }
        if attack == "symlink_source_alias":
            alias = tmp_path / "host-home-alias"
            alias.symlink_to("/home/agentops", target_is_directory=True)
            opts[-2:-2] = ["--bind", str(alias), "/mnt/alias"]
        elif attack in injected:
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
        if attack == "omit_user_unshare":
            command.remove("--unshare-user")
        elif attack == "duplicate_user_unshare":
            command.insert(command.index("--unshare-user"), "--unshare-user")
        elif attack == "omit_userns_disable":
            command.remove("--disable-userns")
        elif attack == "omit_pid_unshare":
            command.remove("--unshare-pid")
        elif attack == "omit_proc_mount":
            index = command.index("--proc")
            del command[index:index + 2]
        result = run_approved_command(tmp_path, command, snapshot.fd_descriptors())
        assert result.returncode != 0
        assert expected.encode() in result.stderr


def test_sealed_profile_fd_mounts_after_delimiter_never_satisfy_policy(tmp_path):
    """After -- they are command arguments, NOT secure bwrap bindings."""
    sandbox = bridge_module()
    _, _, snapshot = fixture_snapshot(tmp_path)
    with snapshot:
        cmd = command_for(sandbox, snapshot)
        triples = []
        # The option stream starts after the embedded Python launcher metadata.
        options_start = cmd.index("/usr/bin/bwrap") + 1
        delimiter = cmd.index("--", options_start)
        for i in reversed(range(options_start, delimiter)):
            if cmd[i] == "--ro-bind-data":
                triples.insert(0, cmd[i:i + 3])
                del cmd[i:i + 3]
        assert len(triples) == len(snapshot.sdk_files)
        assert all("auth.json" not in row["target"] for row in snapshot.fd_descriptors())
        # An attacker may add fake FD tuples to a program's argv; they must
        # never be accepted as mounts by the policy launcher.
        for triple in triples:
            cmd.extend(triple)
        result = subprocess.run(cmd, capture_output=True, timeout=8)
        assert result.returncode != 0
        assert b"policy_fd_launch_invalid" in result.stderr



@pytest.mark.parametrize("origin,destination,expected", [
    ("/proc", "/mnt/host-proc", "policy_fd_private_fd_target_untrusted"),
    ("/", "/mnt/host-root", "policy_fd_private_fd_target_untrusted"),
    ("/home/agentops", "/run/herdr/policy-code", "policy_fd_private_fd_source_untrusted"),
    ("/proc", "/run/herdr/policy-code", "policy_fd_private_fd_source_untrusted"),
    ("/home/agentops/.hermes", "/run/herdr/policy-code",
     "policy_fd_private_fd_source_untrusted"),
    ("/tmp", "/mnt/other", "policy_fd_private_fd_target_untrusted"),
    ("/tmp", "/home/agentops/.ssh", "policy_fd_private_fd_target_untrusted"),
])
def test_private_home_rejects_protected_fd_sources_and_unauthorized_targets(
    tmp_path, origin, destination, expected,
):
    if not Path(origin).exists():
        pytest.skip("host-specific descriptor source unavailable")
    sandbox = bridge_module()
    _, _, snapshot = fixture_snapshot(tmp_path)
    with snapshot:
        fd = os.open(origin, os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            info = os.fstat(fd)
            entries = snapshot.fd_descriptors()
            entries.append({
                "source": f"/proc/{os.getpid()}/fd/{fd}",
                "fd": fd, "device": info.st_dev, "inode": info.st_ino,
                "kind": "directory", "target": destination,
            })
            opts = fixture_mount_arguments(snapshot)
            opts[-2:-2] = [
                "--chdir", str(tmp_path),
                "--ro-bind-fd", str(fd), destination,
            ]
            result = run_approved_command(
                tmp_path, command_for(sandbox, snapshot, descriptors=entries, opts=opts), entries)
            assert result.returncode != 0
            assert expected.encode() in result.stderr
        finally:
            os.close(fd)


@pytest.mark.parametrize("origin,destination", [
    ("/home/agentops/.ssh", "/home/agentops/.ssh"),
    ("/home/agentops/.aws", "/home/agentops/.aws"),
    ("/tmp", "/mnt/tree"),
    ("/tmp", "/mnt/tree/alias/config.yaml"),
])
def test_private_home_never_accepts_unaudited_literal_bind_target(
    tmp_path, origin, destination,
):
    sandbox = bridge_module()
    _, _, snapshot = fixture_snapshot(tmp_path)
    with snapshot:
        opts = fixture_mount_arguments(snapshot)
        opts[-2:-2] = ["--bind", origin, destination]
        entries = snapshot.fd_descriptors()
        result = run_approved_command(tmp_path, command_for(sandbox, snapshot, opts=opts), entries)
        assert result.returncode != 0
        assert b"policy_fd_private_literal_source_unpinned" in result.stderr


@pytest.mark.parametrize("source,destination", [("/usr/bin/bash", "/home/agentops/.local/bin/herdr"), ("/tmp", "/tmp")])
def test_private_home_rejects_unapproved_literal_even_when_root_owned(tmp_path, source, destination):
    sandbox = bridge_module()
    _, _, snapshot = fixture_snapshot(tmp_path)
    with snapshot:
        opts = fixture_mount_arguments(snapshot)
        opts[-2:-2] = ["--ro-bind", source, destination]
        result = subprocess.run(command_for(sandbox, snapshot, opts=opts), capture_output=True, timeout=8)
        assert result.returncode != 0
        assert b"policy_fd_private_plan_required" in result.stderr


def test_private_home_denies_host_user_mutable_cli_bytes(tmp_path):
    sandbox = bridge_module()
    mutable_shim = tmp_path / "mutable-policy-shim"
    mutable_shim.write_bytes(b"fake-reviewed-code")
    _, _, snapshot = fixture_snapshot(tmp_path)
    with snapshot:
        opts = fixture_mount_arguments(snapshot)
        opts[-2:-2] = [
            "--ro-bind", str(mutable_shim), "/home/agentops/.local/bin/herdr",
        ]
        entries = snapshot.fd_descriptors()
        result = run_approved_command(tmp_path, command_for(sandbox, snapshot, opts=opts), entries)
        assert result.returncode != 0
        assert b"policy_fd_private_literal_source_unpinned" in result.stderr

@pytest.mark.parametrize("mutation", ["missing-net", "duplicate-net"])
def test_private_launcher_rejects_missing_or_duplicate_network_namespace(tmp_path, mutation):
    sandbox = bridge_module()
    _, _, snapshot = fixture_snapshot(tmp_path)
    with snapshot:
        entries = snapshot.fd_descriptors()
        command = command_for(sandbox, snapshot, descriptors=entries)
        assert command.count("--unshare-net") == 1
        if mutation == "missing-net":
            command.remove("--unshare-net")
        else:
            command.insert(command.index("--unshare-net"), "--unshare-net")
        # The approval fixture is recomputed for the malicious command, so
        # failure is attributable to the closed kernel namespace grammar,
        # not just a stale plan digest.
        result = run_approved_command(tmp_path, command, entries)
        assert result.returncode != 0
        assert b"policy_fd_private_lifetime_boundary_missing" in result.stderr
