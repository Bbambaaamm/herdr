"""Real isolated interpreter/imports; root-policy/tree checks are explicit doubles.

This tests the host wrapper, not privileged native issuer acceptance.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


PROGRAM = r'''
import json, pathlib, runpy, sys
from types import SimpleNamespace
repository, fixture, directory, fault = sys.argv[1:]
sys.path.insert(0, repository)
from herdr import host_configuration, host_bootstrap, launch_plan_issuer
from herdr.policy_launch import RUNTIME_TARGETS
fixture = pathlib.Path(fixture)
root = fixture / "code"
sys.path.append(str(fixture / "default-site"))
target = root / directory / "probe.py"
python_target = str(host_bootstrap.PYTHON_TARGET)
hermes_target = next(str(x) for x in RUNTIME_TARGETS if str(x) != python_target)
host_bootstrap.PYTHON_EXECUTABLE = "bin/" + pathlib.Path(sys.executable).name
runtime = [{"target": python_target, "source": str(pathlib.Path(sys.executable).parent.parent)},
           {"target": hermes_target, "source": str(fixture / "hermes")}]
if fault == "missing": runtime.pop()
if fault == "duplicate": runtime[1] = dict(runtime[0])
if fault == "extra": runtime.append(dict(runtime[1]))
policy = {"code": {"source": str(root)}, "runtime": runtime, "storage": str(fixture)}
launch_plan_issuer._policy = lambda: ({"entrypoints": [directory + "/probe.py"]}, policy)
observed = []
def tree(definition, *, immutable):
    assert immutable
    def freeze(*args):
        assert "pinned_host_dependency" not in sys.modules and "hermes_cli" not in sys.modules
        observed.append(definition["source"])
        if fault == "withdrawal" and definition is runtime[-1]:
            raise RuntimeError("fixture runtime verification denied")
        return SimpleNamespace(close=lambda: None)
    return SimpleNamespace(freeze=freeze)
host_configuration._tree = tree
wrapper = root / launch_plan_issuer.HOST_ENTRYPOINT
sys.argv = [str(wrapper), directory + "/probe.py", "caller-argument"]
runpy.run_path(str(wrapper), run_name="__main__")
assert observed == [str(root), *[x["source"] for x in runtime]]
'''


def fixture(tmp_path):
    repository = Path(__file__).resolve().parents[2]
    root = tmp_path / "code"
    wrapper = root / "agent-stack/bin/agent-herdr-host-entrypoint"
    wrapper.parent.mkdir(parents=True)
    shutil.copyfile(repository / "agent-stack/bin/agent-herdr-host-entrypoint", wrapper)
    site = tmp_path / "hermes/venv/lib/python3.11/site-packages"
    site.mkdir(parents=True)
    (site / "pinned_host_dependency.py").write_text("value = 'approved-dependency'\n")
    sdk = tmp_path / "hermes/hermes_cli"; sdk.mkdir()
    (sdk / "__init__.py").write_text("value = 'approved-sdk-source'\n")
    # -I still retains interpreter-level site-packages. A duplicate there must
    # lose to the explicitly selected immutable Hermes dependency inventory.
    default_site = tmp_path / "default-site"; default_site.mkdir()
    (default_site / "pinned_host_dependency.py").write_text("raise RuntimeError('unapproved default dependency')\n")
    (default_site / "hermes_cli.py").write_text("raise RuntimeError('unapproved SDK source')\n")
    (site / "sibling_helper.py").write_text("raise RuntimeError('SDK shadowed approved sibling')\n")
    (site / "root_host_helper.py").write_text("raise RuntimeError('SDK shadowed approved code')\n")
    (root / "root_host_helper.py").write_text("value = 'approved-root'\n")
    marker = tmp_path / "startup-hook-executed"
    hook = "import pathlib; pathlib.Path(" + repr(str(marker)) + ").touch()\n"
    (site / "unsafe.pth").write_text(hook)
    (site / "sitecustomize.py").write_text(hook)
    for directory in ("agent-stack/bin", "scripts"):
        entry = root / directory / "probe.py"
        entry.parent.mkdir(parents=True, exist_ok=True)
        entry.write_text(
            "import json, sys, pinned_host_dependency, hermes_cli\n"
            "from sibling_helper import value\n"
            "from root_host_helper import value as root_value\n"
            "assert root_value == 'approved-root'\n"
            "print(json.dumps([pinned_host_dependency.value, hermes_cli.value, value, sys.argv]))\n")
        (entry.parent / "sibling_helper.py").write_text("value = 'approved-sibling'\n")
    return repository, root, site, marker


@pytest.mark.parametrize("directory", ["agent-stack/bin", "scripts"])
def test_isolated_host_imports_only_verified_runtime_dependencies(tmp_path, directory):
    repository, root, site, marker = fixture(tmp_path)
    poison = tmp_path / "poison"; poison.mkdir()
    (poison / "pinned_host_dependency.py").write_text("raise RuntimeError('untrusted PYTHONPATH')\n")
    result = subprocess.run([sys.executable, "-I", "-B", "-c", PROGRAM,
                             str(repository), str(tmp_path), directory, "none"],
                            capture_output=True, text=True, timeout=15,
                            env={**os.environ, "PYTHONPATH": str(poison)})
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == ["approved-dependency", "approved-sdk-source", "approved-sibling",
                                        [str(root / directory / "probe.py"), "caller-argument"]]
    assert not marker.exists(), ".pth/sitecustomize must not be executed"


@pytest.mark.parametrize("fault", ["missing", "duplicate", "extra", "withdrawal", "absent", "alias"])
def test_host_denies_runtime_drift_before_importing_entrypoint(tmp_path, fault):
    repository, root, site, marker = fixture(tmp_path)
    if fault == "absent":
        site.rename(site.with_name("old-site"))
    elif fault == "alias":
        old = site.with_name("old-site")
        site.rename(old); site.symlink_to(old, target_is_directory=True)
    result = subprocess.run([sys.executable, "-I", "-B", "-c", PROGRAM,
                             str(repository), str(tmp_path), "scripts", fault],
                            capture_output=True, text=True, timeout=15)
    assert result.returncode != 0
    assert result.stdout == ""
    assert not marker.exists()
    expected = ("fixture runtime verification denied" if fault == "withdrawal" else
                "approved host dependency directory required" if fault in {"absent", "alias"} else
                "exact approved host runtimes required")
    assert expected in result.stderr
