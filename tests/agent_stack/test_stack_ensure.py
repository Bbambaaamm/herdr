import importlib.machinery
import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "agent-stack" / "bin" / "agent-stack-ensure"


def load_module():
    loader = importlib.machinery.SourceFileLoader("herdr_stack_ensure_test", str(SCRIPT))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def test_herdr_origin_allowlist_is_exact_and_host_bound():
    ensure = load_module()
    repo = "Bbambaaamm/herdr"
    configured = "https://github.com/Bbambaaamm/herdr.git"

    assert ensure._origin_allowed(configured, repo, configured)
    assert ensure._origin_allowed("https://github.com/Bbambaaamm/herdr", repo, configured)
    assert ensure._origin_allowed("git@github.com:Bbambaaamm/herdr.git", repo, configured)
    assert ensure._origin_allowed("ssh://git@github.com/Bbambaaamm/herdr.git", repo, configured)

    assert not ensure._origin_allowed(
        "https://attacker.example/Bbambaaamm/herdr.git", repo, configured
    )
    assert not ensure._origin_allowed(
        "https://github.com.evil.example/Bbambaaamm/herdr.git", repo, configured
    )
    assert not ensure._origin_allowed(
        "https://github.com/Bbambaaamm/herdr-evil.git", repo, configured
    )


def test_clone_timeout_stays_below_systemd_start_timeout():
    ensure = load_module()
    assert 0 < ensure.CHECKOUT_CLONE_TIMEOUT_SECONDS < 120


def test_checkout_rejects_malicious_push_url(monkeypatch, tmp_path):
    ensure = load_module()
    calls = []

    def completed(args, stdout="", returncode=0):
        return ensure.subprocess.CompletedProcess(args, returncode, stdout=stdout, stderr="")

    def fake_run(args, timeout=30):
        calls.append(list(args))
        if args[-2:] == ["rev-parse", "--is-inside-work-tree"]:
            return completed(args, "true\n")
        if args[-4:] == ["remote", "get-url", "--all", "origin"]:
            return completed(args, "https://github.com/Bbambaaamm/herdr.git\n")
        if args[-5:] == ["remote", "get-url", "--push", "--all", "origin"]:
            return completed(args, "https://attacker.example/Bbambaaamm/herdr.git\n")
        if args[-3:] == ["rev-parse", "--verify", "HEAD"]:
            return completed(args, "a" * 40 + "\n")
        raise AssertionError(args)

    monkeypatch.setattr(ensure, "run", fake_run)
    with __import__("pytest").raises(RuntimeError, match="origin mismatch"):
        ensure._verify_repo_checkout(
            tmp_path,
            "Bbambaaamm/herdr",
            "https://github.com/Bbambaaamm/herdr.git",
        )
    assert any("--push" in call for call in calls)
    assert any("--all" in call for call in calls)


def test_full_cold_start_budget_fits_systemd_timeout():
    ensure = load_module()
    source = (
        Path(__file__).resolve().parents[2]
        / "agent-stack"
        / "systemd"
        / "agent-stack-watchdog.service"
    ).read_text(encoding="utf-8")
    template = (
        Path(__file__).resolve().parents[2]
        / "deploy"
        / "agent_platform"
        / "production"
        / "agent-stack-watchdog.service.in"
    ).read_text(encoding="utf-8")
    assert source == template
    assert "TimeoutStartSec=300" in source
    assert (
        ensure.CHECKOUT_CLONE_TIMEOUT_SECONDS
        + 2 * ensure.AGENT_START_TIMEOUT_SECONDS
        < 300
    )

def test_terminal_server_spawn_rejects_inherited_loader_controls(monkeypatch, tmp_path):
    from herdr.launch_environment import require_clean_environment
    ensure = load_module()
    ensure.ENV.update(LD_PRELOAD="/unapproved/lib.so", LD_FUTURE_CONTROL="", BASH_ENV="/unapproved/startup")
    states = iter((False, True))
    calls = []
    monkeypatch.setattr(ensure, "herdr_ready", lambda: next(states))
    monkeypatch.setattr(ensure, "HERDR_BOOT_LOG", tmp_path / "server.log")
    monkeypatch.setattr(ensure.time, "sleep", lambda _: None)
    monkeypatch.setattr(ensure, "log", lambda _: None)

    def spawn(args, **kwargs):
        require_clean_environment(kwargs["env"])
        calls.append((args, kwargs["env"]))

    monkeypatch.setattr(ensure.subprocess, "Popen", spawn)
    ensure.ensure_herdr_server()
    assert len(calls) == 1
    assert calls[0][0] == [str(ensure.HERDR), "server"]
    assert calls[0][1]["HOME"] == str(ensure.HOME)
    assert "LD_LIBRARY_PATH" in ensure.ENV  # Legacy browser helpers keep their own environment.


def test_watchdog_units_start_with_clean_native_loader_environment():
    import shlex
    from herdr.launch_environment import require_clean_environment
    root = Path(__file__).resolve().parents[2]
    paths = (
        root / "agent-stack/systemd/agent-stack-watchdog.service",
        root / "deploy/agent_platform/production/agent-stack-watchdog.service.in",
    )
    for path in paths:
        environment = {}
        for line in path.read_text().splitlines():
            if line.startswith("Environment="):
                for assignment in shlex.split(line.removeprefix("Environment=")):
                    key, value = assignment.split("=", 1)
                    environment[key] = value
        require_clean_environment(environment)
