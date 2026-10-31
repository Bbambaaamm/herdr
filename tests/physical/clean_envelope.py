"""Clean, explicitly approved Linux offline envelope; never a production authority.

The outer half imports only stdlib. The inner half composes the existing host
factory, automatic issuer, ordinary worker and original recovery. Local handoff
is distinct from GitHub acceptance. No historical Work is an input.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import time

EXECUTABLE_SOURCE_READY = True  # Source composition only; separate root approval and physical gates remain mandatory.
MAIN = '5fbabd5864d2f74f5c4658aa6e5f577967e88ffa'
BASE_MAIN_MANIFEST = '4af7aaff0d8fb847c5c33f5e806ddf60d78da4e7dc49d7a60e7b4f54b380ffc8'
CORE_PATCH = {
    "agent-stack/bin/agent-task-worker": "b72a9ab8b236520758d1a91fedefdf01cce7c80e5ffe28e813dacf1e1eb165b2",
    "agent-stack/bin/agent_durable_sandbox.py": "36dbde3941fb97e29010faa518fbe44806c3fa6c9c41b5ec1beaf2601f7514d9",
    "herdr/check_runner.py": "58284f4cf0a3eec00c7ee58a0a1a68a8a350d464975a1c92282abd0a39d2dcaf",
    "herdr/hermes_guard.py": "8b08c151420d2dd804473e1dd49809116cb9fbb77b9781e34fcf15cff9d92347",
    "herdr/policy_launch.py": "72234402db3c7ae86923dfb5ca4fa66ba6259ff60df7cd0d3d36dd6ea813453a",
    "herdr/security.py": "5ffe3d7e95ed0606c8915b7af340a1e52e754611ebc21ee7fa6f97bc04df4b6c",
    "herdr/work_configuration.py": "6d49c2200921a3dcea115964cf128243f8adb6005d982ee53ca04388333f26cd",
    "herdr/work_cycle.py": "758e350b0990ae6ed6a26e47f6a9bd8917c3bd6e15bc2cec74d3de917336c799"
}
PATCH_MANIFEST = '5e32152515590c319ad22eea81614d463b76795890765d4f772448ca68c9f513'
MAIN_MANIFEST = 'fd98b1d33c301643e77a307589bcbb7fc0246440056e163cc457b0b604b0a596'
CASE = '18755d84fa0db150adeb5bbe3fcaacd724316ebe75e03af54af8e39c6f6d6d59'
SDK_MANIFEST = 'b9770ab7ad312b382f9d7d470f8f2471ca4b71ce197db3004eed6ee8a4cc2b14'
PYTHON_MANIFEST = 'd35e6083e474e8d049bad69c46bd84d97c8d4cfc650bcf32fce44e2e6299f0ef'
SDK = '/opt/herdr/releases/p0-5035d92-test/hermes'
PYTHON = '/opt/herdr/releases/p0-5035d92-test/python'
PY = PYTHON + '/bin/python3.11'
CONSUMER = 'github:Bbambaaamm/herdr'
MODEL = 'meituan/longcat-2.0:free'
URL = 'https://inference-api.nousresearch.com/v1'
ROOT = Path('/run/clean')
HOME = Path('/home/agentops')
QUEUE = HOME / '.local/state/agent-stack/tasks'
POLICY = Path('/etc/herdr/host-policy.json')
SHA = re.compile(r'[0-9a-f]{64}')
NONCE = re.compile(r'[0-9a-f]{32}')
HARNESSES = ('offline_pilot.py', 'offline_provider.py', 'clean_envelope.py')
GRANT_TTL = 1500
CREDENTIAL_REF = 'pool:nous:ab19ef'
_BOUNDARY_VERIFIED = False
CAPS = dict(external_model_calls=0, external_auth_calls=0, external_github_calls=0,
            local_requests=16, work_seconds=900, envelope_seconds=1800,
            memory_bytes=2147483648, tmpfs_bytes=536870912, persistent_bytes=134217728,
            process_count=192, floor_bytes=10737418240, margin_bytes=268435456)


class Denied(RuntimeError):
    pass


def need(ok, reason):
    if not ok:
        raise Denied(reason)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def closed(value, keys):
    need(isinstance(value, dict) and set(value) == set(keys), 'closed schema required')
    return value


def pairs(items):
    result = {}
    for key, value in items:
        need(key not in result, 'duplicate JSON key')
        result[key] = value
    return result


def relative(name):
    need(isinstance(name, str) and name and not any(x in name for x in ('\\', ':', '\x00')),
         'relative manifest member required')
    p = PurePosixPath(name)
    need(not p.is_absolute() and str(p) == name and not set(p.parts) & {'.', '..'},
         'canonical relative member required')
    return p


def stamp(s):
    return (s.st_dev, s.st_ino, s.st_mode, s.st_uid, s.st_gid, s.st_nlink,
            s.st_size, s.st_mtime_ns, s.st_ctime_ns)


def read_pin(path, sha, *, owner, limit=4194304):
    """Stable exclusive FD, including no-follow ancestry and named substitution."""
    p = Path(path)
    need(SHA.fullmatch(sha or '') and p.is_absolute() and p.resolve(strict=True) == p,
         'absolute pinned input required')
    if os.name == 'posix':
        fd = os.open('/', os.O_PATH | os.O_DIRECTORY | os.O_CLOEXEC)
        try:
            for index, part in enumerate(p.parts[1:]):
                flags = os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK
                flags |= os.O_RDONLY if index == len(p.parts) - 2 else os.O_PATH | os.O_DIRECTORY
                child = os.open(part, flags, dir_fd=fd)
                os.close(fd); fd = child
                if index != len(p.parts) - 2:
                    s = os.fstat(fd)
                    need(s.st_uid in {0, owner} and not s.st_mode & 0o022, 'untrusted input ancestry')
        except BaseException:
            os.close(fd); raise
    else:  # Portable source tests; never an execution platform.
        fd = os.open(p, os.O_RDONLY | getattr(os, 'O_BINARY', 0))
    try:
        s = os.fstat(fd)
        need(stat.S_ISREG(s.st_mode) and s.st_nlink == 1 and s.st_uid == owner
             and (os.name != 'posix' or not s.st_mode & 0o022) and 0 < s.st_size <= limit, 'unsafe pinned input')
        data = bytearray()
        while len(data) <= limit:
            part = os.read(fd, min(65536, limit + 1 - len(data)))
            if not part:
                break
            data.extend(part)
        t, named = os.fstat(fd), p.lstat()
        # Windows ctime from separate APIs is not comparable; each API remains stable.
        cross = lambda row: stamp(row)[:-1] if os.name == 'nt' else stamp(row)
        need(stamp(s) == stamp(t) and cross(s) == cross(named)
             and len(data) == s.st_size and hashlib.sha256(data).hexdigest() == sha,
             'pinned input changed')
        return bytes(data)
    finally:
        os.close(fd)


def load_pin(path, sha, *, owner=0):
    return json.loads(read_pin(path, sha, owner=owner), object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(Denied('nonfinite JSON')))


def validate_bundle(value):
    closed(value, ('version', 'source_main', 'case_sha256', 'nonce', 'runtime',
                   'harness', 'system', 'check_runtime', 'caps', 'shared_before', 'core_patch'))
    need(value['version'] == 1 and value['source_main'] == MAIN and value['case_sha256'] == CASE
         and NONCE.fullmatch(value['nonce'] or '') and value['caps'] == CAPS, 'envelope binding changed')
    patch = closed(value['core_patch'], ('baseline_main', 'baseline_manifest_sha256', 'files', 'manifest_sha256', 'source_sha'))
    need(patch['baseline_main'] == MAIN and patch['baseline_manifest_sha256'] == BASE_MAIN_MANIFEST
         and patch['files'] == CORE_PATCH and patch['manifest_sha256'] == PATCH_MANIFEST
         and digest(patch['files']) == PATCH_MANIFEST and isinstance(patch['source_sha'], str)
         and re.fullmatch(r'[0-9a-f]{40}', patch['source_sha']), 'reviewed core patch binding changed')
    runtime = closed(value['runtime'], ('code', 'sdk', 'python', 'native'))
    for name in ('code', 'sdk', 'python'):
        row = closed(runtime[name], ('source', 'files', 'executable_files', 'max_bytes', 'max_file_bytes'))
        need(isinstance(row['files'], dict) and 1 <= len(row['files']) <= 30000,
             'bounded immutable manifest required')
        need(isinstance(row['max_bytes'], int) and 0 < row['max_bytes'] <= 600000000
             and isinstance(row['max_file_bytes'], int) and 0 < row['max_file_bytes'] <= 268435456,
             'immutable tree size ceiling required')
        for path, sha in row['files'].items():
            relative(path); need(SHA.fullmatch(sha or ''), 'manifest digest required')
        need(isinstance(row['executable_files'], list) and set(row['executable_files']) <= set(row['files']),
             'executable inventory changed')
    need(digest(runtime['code']['files']) == MAIN_MANIFEST
         and all(runtime['code']['files'].get(p) == sha for p, sha in CORE_PATCH.items()),
         'composed runtime manifest changed')
    need(digest(runtime['sdk']['files']) == SDK_MANIFEST
         and digest(runtime['python']['files']) == PYTHON_MANIFEST,
         'shared runtime manifest changed')
    need(runtime['sdk']['source'] == SDK and runtime['python']['source'] == PYTHON,
         'runtime source changed')
    # No historical release/work/task path may become the new code source.
    need(runtime['code']['source'] == '/run/clean/code', 'private main source required')
    native = closed(runtime['native'], ('source', 'sha256', 'bytes'))
    need(native['source'] == '/home/agentops/.local/bin/herdr'
         and SHA.fullmatch(native['sha256'] or '') and 0 < native['bytes'] <= 33554432,
         'native executable pin required')
    harness = closed(value['harness'], (*HARNESSES, 'offline_case_inputs.json'))
    need(all(SHA.fullmatch(sha or '') for sha in harness.values())
         and harness['offline_case_inputs.json'] == CASE, 'harness/case pin changed')
    system = value['system']
    need(isinstance(system, dict) and 1 <= len(system) <= 8192, 'system manifest required')
    for path, sha in system.items():
        need(isinstance(path, str) and path.startswith(('/usr/', '/lib/', '/lib64/'))
             and str(PurePosixPath(path)) == path and '..' not in PurePosixPath(path).parts
             and SHA.fullmatch(sha or ''), 'system source outside allowlist')
    need({'/usr/bin/bwrap', '/usr/bin/git', '/usr/bin/openssl', '/usr/sbin/ip', '/usr/bin/unshare'} <= set(system),
         'required system pins missing')
    check = closed(value['check_runtime'], ('files', 'executables', 'runtime_aliases', 'bytes'))
    need(isinstance(check['files'], dict) and 1 <= len(check['files']) <= 8192
         and 0 < check['bytes'] <= 134217728, 'bounded check runtime required')
    need(set(check['executables']) <= set(check['files']) and PY in check['executables']
         and '/usr/bin/git' in check['executables'], 'check executable inventory required')
    for path, sha in check['files'].items():
        need(isinstance(path, str) and path.startswith(('/usr/', '/lib/', '/lib64/', PYTHON + '/'))
             and '..' not in PurePosixPath(path).parts and SHA.fullmatch(sha or ''), 'check file outside allowlist')
    need(isinstance(value['shared_before'], dict) and len(value['shared_before']) <= 16,
         'shared-state observations required')
    # Shared-state inputs are hashes supplied by a separate authorized observer,
    # never mounted/read as fixture data (especially #185).
    for key, sha in value['shared_before'].items():
        need(re.fullmatch(r'[a-z][a-z0-9_-]{0,63}', key) and SHA.fullmatch(sha or ''),
             'opaque shared-state pin required')
    return value


def bind_proposal(bundle, proposal):
    validate_bundle(bundle)
    need(proposal['status'] == 'PROPOSAL_ONLY_NOT_ADMITTED' and proposal['source_main'] == MAIN
         and proposal['case_sha256'] == CASE and proposal['task_seed']['run_token'] == bundle['nonce'],
         'fresh case/proposal mismatch')
    task = proposal['task_seed']
    need(task['id'] == 'offline188-' + bundle['nonce'] and task['fencing_token'] == 1
         and task['attempts'] == task['attempt_id'] == 0
         and task['workspace'] == '/home/agentops/worktrees/' + task['id'] + '/workspace',
         'historical or substituted task rejected')
    return task


def write(path, data, *, owner=0, mode=0o600):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    raw = data if isinstance(data, bytes) else canonical(data)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
    try:
        os.fchown(fd, owner, owner)
        with os.fdopen(os.dup(fd), 'wb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    finally:
        os.close(fd)


def deadline_check(admission, *, now=None):
    closed(admission, ('version', 'nonce', 'bundle_sha256', 'started_epoch', 'deadline_epoch'))
    need(admission['version'] == 1 and NONCE.fullmatch(admission['nonce'] or '')
         and admission['deadline_epoch'] - admission['started_epoch'] == CAPS['envelope_seconds'],
         'original admission deadline changed')
    current = time.time() if now is None else now
    need(admission['started_epoch'] <= current < admission['deadline_epoch'], 'original deadline exhausted')
    return admission['deadline_epoch'] - current


def environment():
    return {'PATH': '/home/agentops/.local/bin:/usr/bin:/bin:/usr/sbin', 'HOME': str(HOME),
            'LANG': 'C.UTF-8', 'SHELL': '/bin/bash', 'XDG_RUNTIME_DIR': '/run/user/1001',
            'SSL_CERT_FILE': '/etc/ssl/certs/ca-certificates.crt',
            'REQUESTS_CA_BUNDLE': '/etc/ssl/certs/ca-certificates.crt',
            'HERMES_HOME': str(HOME / '.hermes/profiles/quantlab')}


def sealed(data, name):
    import fcntl
    fd = os.memfd_create(name, os.MFD_ALLOW_SEALING)
    try:
        view = memoryview(data)
        while view:
            view = view[os.write(fd, view):]
        os.fchmod(fd, 0o555)
        fcntl.fcntl(fd, fcntl.F_ADD_SEALS, fcntl.F_SEAL_WRITE | fcntl.F_SEAL_GROW
                    | fcntl.F_SEAL_SHRINK | fcntl.F_SEAL_SEAL)
        return fd
    except BaseException:
        os.close(fd); raise


def verify_unit(bundle):
    expected = '/system.slice/herdr-clean-' + bundle['nonce'] + '.service'
    groups = Path('/proc/self/cgroup').read_text().splitlines()
    need(groups == ['0::' + expected], 'dedicated bounded unit required')
    group = Path('/sys/fs/cgroup' + expected)
    for name, ceiling in (('memory.max', CAPS['memory_bytes']), ('pids.max', CAPS['process_count']),
                          ('memory.swap.max', 0)):
        raw = (group / name).read_text().strip()
        need(raw.isdecimal() and int(raw) <= ceiling, 'unit resource cap missing')
    timeout = run(['/usr/bin/systemctl', 'show', expected.rsplit('/', 1)[1],
                   '--property=RuntimeMaxUSec', '--value'], timeout=10, env={'PATH': '/usr/bin:/bin'}).decode().strip()
    need(timeout == '30min', 'hard unit deadline missing')


def inventory(root, expected):
    root = Path(root)
    need(root.resolve(strict=True) == root, 'immutable root alias')
    found = set()
    stack = [root]
    while stack:
        directory = stack.pop(); info = directory.lstat()
        need(stat.S_ISDIR(info.st_mode) and info.st_uid == 0 and not info.st_mode & 0o022,
             'immutable directory is writable or aliased')
        for item in directory.iterdir():
            info = item.lstat()
            if stat.S_ISDIR(info.st_mode):
                stack.append(item)
            else:
                need(stat.S_ISREG(info.st_mode) and info.st_uid == 0 and info.st_nlink == 1
                     and not info.st_mode & 0o022, 'immutable asset has link/special/writable member')
                found.add(item.relative_to(root).as_posix())
                need(len(found) <= len(expected), 'unlisted runtime input')
    need(found == set(expected), 'runtime inventory differs from approved manifest')


def outer(bundle_path, bundle_sha, source, harness, evidence):
    need(EXECUTABLE_SOURCE_READY, 'pinned core lacks a safe admitted child snapshot/write partition; do not run this draft')
    need(sys.platform == 'linux' and os.geteuid() == 0, 'separately approved Linux administrator run required')
    bundle = validate_bundle(load_pin(bundle_path, bundle_sha))
    need(digest(bundle) == bundle_sha, 'canonical approved bundle bytes required')
    verify_unit(bundle)
    evidence = Path(evidence)
    need(evidence.parent == Path('/var/lib') and evidence.name == 'herdr-clean-' + bundle['nonce']
         and not os.path.lexists(evidence), 'fresh evidence directory required')
    available = os.statvfs('/').f_bavail * os.statvfs('/').f_frsize
    need(available >= CAPS['floor_bytes'] + CAPS['persistent_bytes'] + CAPS['margin_bytes'],
         'capacity gate failed; no materialization')
    source, harness = Path(source), Path(harness)
    need(source.is_absolute() and harness.is_absolute() and source != harness, 'separate runtime/harness roots required')
    memory = dict(line.split(':', 1) for line in Path('/proc/meminfo').read_text().splitlines() if ':' in line)
    need(int(memory['MemAvailable'].split()[0]) * 1024 >= 2684354560, 'host RAM headroom gate failed')
    files, handles = [], []
    def data_bind(data, target, mode=0o444):
        fd = sealed(data, 'herdr-clean-input'); handles.append(fd)
        files.extend(['--perms', format(mode, 'o'), '--ro-bind-data', str(fd), str(target)])
    # Snapshot every runtime-code and harness byte into sealed FDs; a later path
    # swap cannot change the executed source. No SDK import occurs here.
    try:
        for relative_name, sha in bundle['runtime']['code']['files'].items():
            data_bind(read_pin(source / relative_name, sha, owner=0), ROOT / 'code' / relative_name,
                      0o555 if relative_name in bundle['runtime']['code']['executable_files'] else 0o444)
        for name, sha in bundle['harness'].items():
            data_bind(read_pin(harness / name, sha, owner=0), ROOT / 'harness' / name)
        native = bundle['runtime']['native']
        data_bind(read_pin(native['source'], native['sha256'], owner=1001, limit=native['bytes']), ROOT / 'native', 0o555)
        for path, sha in {**bundle['system'], **bundle['check_runtime']['files']}.items():
            read_pin(Path(path).resolve(), sha, owner=0, limit=268435456)
        for name in ('sdk', 'python'):
            row = bundle['runtime'][name]
            inventory(row['source'], row['files'])
            total = 0
            for member, sha in row['files'].items():
                total += len(read_pin(Path(row['source']) / member, sha, owner=0, limit=row['max_file_bytes']))
            need(total <= row['max_bytes'], 'immutable runtime exceeds allowance')
            fd = os.open(row['source'], os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW)
            handles.append(fd)
            files.extend(['--ro-bind', '/proc/self/fd/' + str(fd), row['source']])
        data_bind(canonical(bundle), ROOT / 'bundle.json')
        started = time.time()
        admission = dict(version=1, nonce=bundle['nonce'], bundle_sha256=bundle_sha,
                         started_epoch=started, deadline_epoch=started + CAPS['envelope_seconds'])
        data_bind(canonical(admission), ROOT / 'admission.json')
        evidence.mkdir(mode=0o700)
        write(evidence / 'admission.json', admission)
        # All executable writes are under ONE size-limited private tmpfs. Only
        # the bounded supervisor exports nonsecret evidence afterward.
        command = ['/usr/bin/unshare', '--user', '--map-users=0:0:65536', '--map-groups=0:0:65536',
                   '--setgroups=allow', '--', '/usr/bin/bwrap', '--die-with-parent', '--new-session', '--unshare-pid',
            '--unshare-net', '--unshare-ipc', '--unshare-uts', '--cap-add', 'ALL',
            '--clearenv', '--ro-bind', '/usr', '/usr', '--proc', '/proc', '--dev', '/dev']
        for directory in ('/lib', '/lib64', '/bin'):
            if Path(directory).is_symlink():
                command += ['--symlink', os.readlink(directory), directory]
            elif Path(directory).is_dir():
                command += ['--ro-bind', directory, directory]
        command += ['--size', str(CAPS['tmpfs_bytes']), '--tmpfs', '/private',
                    '--dir', '/private/home', '--bind', '/private/home', '/home',
                    '--dir', '/private/etc', '--bind', '/private/etc', '/etc',
                    '--dir', '/private/run', '--bind', '/private/run', '/run',
                    '--dir', '/private/var', '--bind', '/private/var', '/var',
                    '--symlink', '/private/tmp', '/tmp', '--dir', '/sys/fs',
                    '--ro-bind', '/sys/fs/cgroup', '/sys/fs/cgroup', *files, '--remount-ro', '/',
                    '--setenv', 'HOME', '/private/root', '--setenv', 'LANG', 'C.UTF-8',
                    '--setenv', 'PATH', '/usr/bin:/bin:/usr/sbin',
                    PY, '-I', '-B', str(ROOT / 'harness/clean_envelope.py'), '--inner']
        log = evidence / 'unit.log'
        import resource
        def child_limits():
            resource.setrlimit(resource.RLIMIT_FSIZE, (67108864, 67108864))
        with log.open('xb') as stream:
            process = subprocess.Popen(command, pass_fds=handles, env={'PATH': '/usr/bin:/bin'},
                                       stdout=stream, stderr=subprocess.STDOUT, preexec_fn=child_limits)
            try:
                code = process.wait(timeout=max(1, deadline_check(admission)))
            except subprocess.TimeoutExpired:
                process.kill(); process.wait(timeout=10)
                raise Denied('original envelope timeout; never retry')
        need(log.stat().st_size <= 67108864, 'evidence cap exceeded')
        need(code == 0, 'isolated envelope failed; retain original evidence')
    finally:
        for fd in handles:
            os.close(fd)


def run(command, *, cwd=None, user=False, timeout=30, env=None):
    credentials = {}
    if user:
        if os.geteuid() == 0:
            credentials = {'user': 1001, 'group': 1001, 'extra_groups': ()}
        else:
            need(os.geteuid() == os.getegid() == 1001 and not os.getgroups(), 'private host credentials changed')
    result = subprocess.run(list(map(str, command)), cwd=cwd, env=environment() if env is None else env,
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=timeout, **credentials)
    need(result.returncode == 0, 'fixed operation failed: ' + str(command[0]))
    return result.stdout


def private_boundary(bundle):
    import socket
    import resource
    need(os.geteuid() == 0 and Path('/private').is_mount(), 'private root boundary required')
    names = [name for _, name in socket.if_nameindex()]
    need(names == ['lo'], 'nonlocal network interface present')
    for path in ('/root', '/home/agentops/.config/gh', '/etc/herdr/host-policy.json'):
        need(not os.path.lexists(path), 'host credentials/config exposed before materialization')
    rows = [line.split(' - ', 1)[0].split() for line in Path('/proc/self/mountinfo').read_text().splitlines()]
    mounts = {row[4]: set(row[5].split(',')) for row in rows}
    need('ro' in mounts.get('/', set()) and 'rw' in mounts.get('/private', set()), 'root mount contract changed')
    for kind in ('code', 'harness'):
        need(all('ro' in mounts.get(str(ROOT / kind / member), set())
                 for member in (bundle['runtime']['code']['files'] if kind == 'code' else bundle['harness'])),
             'source is not a sealed read-only view')
    # Exact unit/cgroup is checked outside; namespace identities are retained for
    # later comparison with the actual worker's protected bootstrap proof.
    return {kind: os.readlink('/proc/self/ns/' + kind) for kind in ('mnt', 'pid', 'net', 'ipc')}


def configure_profile(bundle, admission):
    # This is the FIRST SDK import and happens only after private_boundary.
    import base64
    sys.path[:0] = [SDK, SDK + '/venv/lib/python3.11/site-packages']
    from hermes_cli.auth import NOUS_INFERENCE_INVOKE_SCOPE
    scope = NOUS_INFERENCE_INVOKE_SCOPE
    encode = lambda x: base64.urlsafe_b64encode(canonical(x)).decode().rstrip('=')
    token = encode({'alg': 'none', 'typ': 'JWT'}) + '.' + encode({
        'sub': 'herdr-offline-fixture', 'exp': int(admission['deadline_epoch']) + 1800, 'scope': scope}) + '.Zml4dHVyZQ'
    spec = importlib.util.spec_from_file_location('clean_credential_shape', ROOT / 'code/deploy/herdr/existing_credential_snapshot.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    auth = module.minimal_store({'id': 'ab19ef', 'source': 'device_code', 'credential_type': 'oauth',
                                'agent_key': token, 'access_token': token, 'scope': scope}, token)
    profile = ROOT / 'profile/quantlab'
    content = {'auth.json': canonical(auth), '.env': b'', 'config.yaml': canonical({
        'model': {'default': MODEL, 'provider': 'nous'}, 'fallback_providers': [], 'fallback_model': []}),
        'herdr-sdk-policy.json': canonical({'schema_version': 1, 'managed_scope': 'none', 'fallback_chain': 'empty'})}
    for name, body in content.items():
        write(profile / name, body, mode=0o444)
        write(HOME / '.hermes/profiles/quantlab' / name, body, owner=1001)
    write(HOME / '.hermes/auth.json', canonical(auth), owner=1001)
    profile.chmod(0o555); profile.parent.chmod(0o555)
    from herdr.policy_launch import ApprovedProfile
    files = {name: hashlib.sha256(body).hexdigest() for name, body in content.items()}
    approved = ApprovedProfile('quantlab', profile, files)
    return {'profile': {'name': 'quantlab', 'source': str(profile), 'files': files},
            'credential_approval': {'schema_version': 'herdr-profile-credential-approval-1',
                'profile_sha256': approved.identity['manifest_sha256'], 'minimum_ttl_seconds': 60,
                'valid_until': iso(admission['deadline_epoch'] + 1800)},
            'plan_handoff': {'proposal_directory': str(HOME / '.local/state/herdr-clean/proposals'),
                             'timeout_seconds': 60, 'automatic_issuer': True}}


def iso(epoch):
    from datetime import datetime, timezone
    return datetime.fromtimestamp(epoch, timezone.utc).isoformat()


def fresh_repository(proposal):
    root = Path(proposal['task_seed']['workspace'])
    root.mkdir(parents=True)
    for name, body in proposal['workspace_files'].items():
        write(root / name, body.encode(), owner=1001)
    # New independent object database, not an imported historic task/workspace.
    def git(*args):
        return run(['/usr/bin/git', '-C', root, *args], user=True,
            env={**environment(), 'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null'}).decode().strip()
    for parent in (root.parent.parent, root.parent, root):
        os.chown(parent, 1001, 1001); parent.chmod(0o700)
    git('init', '-q', '--template=', '-b', 'herdr/root')
    git('config', 'user.name', 'Herdr offline fixture'); git('config', 'user.email', 'offline@example.invalid')
    git('remote', 'add', 'origin', 'https://github.com/Bbambaaamm/herdr.git')
    git('add', '--', *proposal['workspace_files']); git('commit', '-qm', 'Fresh arithmetic fixture baseline')
    base = git('rev-parse', 'HEAD'); git('update-ref', 'refs/remotes/origin/main', base)
    (root / '.git/hooks').mkdir(exist_ok=True)
    write(root / '.git/info/exclude', b'.managed-child/\n', owner=1001)
    child = root / '.managed-child/workspace'
    child.parent.mkdir(mode=0o700); os.chown(child.parent, 1001, 1001)
    git('clone', '--no-hardlinks', '--template=', str(root), str(child))
    run(['/usr/bin/git', '-C', child, 'branch', '-m', 'herdr/child'], user=True)
    for key, value in (('user.name', 'Herdr offline child'), ('user.email', 'offline@example.invalid')):
        run(['/usr/bin/git', '-C', child, 'config', key, value], user=True)
    run(['/usr/bin/git', '-C', child, 'remote', 'set-url', 'origin', 'https://github.com/Bbambaaamm/herdr.git'], user=True)
    (child / '.git/hooks').mkdir(exist_ok=True)
    return root, child, base


def check_environment(bundle):
    from herdr.check_runner import CheckEnvironment
    check = bundle['check_runtime']
    return CheckEnvironment(version='offline-clean-1', system_files=tuple(sorted(check['files'].items())),
        executables=tuple(check['executables']), runtime_aliases=tuple(map(tuple, check['runtime_aliases'])),
        runtime_executables=tuple(path for path in check['files'] if Path(path).name.startswith('ld-linux')))


def root_grant(bundle, proposal, admission, private, task):
    from herdr.security import (SecurityGrant, InvocationIdentity, ToolRule, RiskClass,
                               ProcessPolicy, RuntimeAssurance, ProviderRoute, NetworkAccess)
    from herdr.capability import CapabilityScope, DataClass, Egress, Retention, Training
    from agent_durable_children import attempt_directory
    tools = sorted(proposal['tools'] + ['herdr_delegate_child'])
    workspace = proposal['task_seed']['workspace']
    rules = [ToolRule('read_file', RiskClass.READ, allowed_arg_keys=('path', 'offset', 'limit'),
                     path_fields=('path',), allowed_roots=(workspace,)),
             ToolRule('write_file', RiskClass.WORKSPACE_WRITE, allowed_arg_keys=('path', 'content'),
                     path_fields=('path',), allowed_roots=(workspace,)),
             ToolRule('herdr_verify_work', RiskClass.READ, allowed_arg_keys=('request_id', 'handoff'), requires_sandbox=True),
             ToolRule('herdr_submit_result', RiskClass.RESULT_SUBMISSION,
                      allowed_arg_keys=('status', 'evidence', 'summary'), requires_sandbox=True,
                      allowed_roots=(str(QUEUE / 'results' / (task['id'] + '.json')),
                          str(attempt_directory(QUEUE, task['id'], task['run_token']) / 'results')))]
    from herdr.delegation_tool import ARGUMENTS
    rules.append(ToolRule('herdr_delegate_child', RiskClass.DELEGATION, allowed_arg_keys=ARGUMENTS,
                          requires_sandbox=True))
    scope = CapabilityScope(providers=('nous',), capabilities=('reasoning',), executors=('hermes-runtime',),
        tools=tuple(tools), permissions=tuple(proposal['permissions']), regions=('global',),
        data_classes=(DataClass.INTERNAL,), input_modalities=('text',), output_modalities=('text',),
        max_cost_microusd=0, max_context_tokens=1048576, max_egress=Egress.GLOBAL,
        max_retention=Retention.INDEFINITE, training=Training.ALLOWED)
    route = ProviderRoute('nous', URL, 'chat_completions', ('global',), (DataClass.INTERNAL,),
                          Egress.GLOBAL, Retention.INDEFINITE, Training.ALLOWED, (CREDENTIAL_REF,))
    identity = InvocationIdentity(CONSUMER, 'fixture-supervisor', 'offline', 'offline',
                                  task['id'], task['run_token'], task['fencing_token'])
    # Unverified initial assurance is intentional. Only the actual core sealer
    # may replace it after observing physical worker bootstrap.
    return SecurityGrant('offline-' + bundle['nonce'], workspace, identity, scope, tuple(rules),
        ProcessPolicy(False, (), NetworkAccess.NONE), RuntimeAssurance(False, None, NetworkAccess.NONE, (), False),
        (route,), (CREDENTIAL_REF,), (), (), iso(admission['started_epoch']), iso(admission['deadline_epoch'])).to_json()


def work_definition(proposal, task, base, workspace, tools, environment, budget):
    from dataclasses import asdict
    from herdr.work_hygiene import LocalCommitPolicy
    from herdr.work_budget import BudgetAllocation
    reference = BudgetAllocation(**{**budget['allocation'], 'limits': __import__(
        'herdr.work_budget', fromlist=['BudgetLimits']).BudgetLimits(**budget['allocation']['limits'])}).hash
    check = proposal['check']
    files = proposal['write_files']
    planning = {'goal': task['prompt'], 'allowed_files': files, 'tools': tools,
        'permissions': proposal['permissions'], 'constraints': ['No external effects', 'Stop after local handoff'],
        'assumptions': [], 'uncertainties': [], 'acceptance': ['arithmetic'],
        'verification': {'dimensions': [{'id': 'correctness', 'hard': True, 'check_ids': ['arithmetic']}],
                         'prebuild_review_required': False, 'accepted_review_ref': None},
        'expected_artifact': 'Exact host-verified local arithmetic commit; no GitHub acceptance',
        'stop_condition': 'Stop implementation after host oracle PASS',
        'team': {'topology': 'SINGLE', 'nodes': [{'id': 'worker', 'role_ref': None, 'write_files': files,
            'decision_scope': ['arithmetic'], 'tools': tools, 'permissions': proposal['permissions']}],
            'edges': [], 'integration_owner': 'worker', 'concurrency': 1, 'budget_reference': reference},
        'runbook': None, 'orientation': None, 'prompt_plan': None,
        'clarification': {'status': 'resolved', 'reason': 'Exact frozen arithmetic case', 'material': False},
        'decomposition': None}
    hygiene = LocalCommitPolicy('offline-clean-1', environment,
        hashlib.sha256((workspace / '.git/config').read_bytes()).hexdigest(), str(workspace / '.git/hooks'), ())
    hygiene = asdict(hygiene); hygiene.pop('environment')
    return {'spec_version': 'offline-arithmetic-1', 'policy_version': 'offline-clean-1',
        'base_sha': base, 'files': [{'path': name, 'subtree': False, 'symbols': []} for name in files],
        'criteria': ['arithmetic'], 'checks': [{'id': 'arithmetic', 'command': [PY, '-I', '-B', check['script']],
            'criterion_ids': ['arithmetic'], 'expected_baseline_failure': True, 'timeout_seconds': 20,
            'output_bytes': 4096, 'expected_baseline_output_sha256': hashlib.sha256(
                check['expected_baseline_stdout'].encode()).hexdigest(), 'protected_inputs': []}],
        'budget_reference': reference, 'mode': 'repair', 'baseline_omission_reason': None,
        'phases': ['work', 'verify', 'handoff'], 'prerequisite_commits': [], 'purpose': planning['goal'],
        'baseline_policy': 'required', 'discovery_files': list(proposal['workspace_files']),
        'planning': planning, 'hygiene': hygiene, 'budget': budget}


def budgets(bundle):
    from dataclasses import asdict, replace
    from herdr.work_budget import BudgetAllocation, BudgetLimits
    key = lambda tag: digest({'bundle': digest(bundle), 'tag': tag})
    limits = BudgetLimits(900000, 900000, 16, 1056768, 0, 2, 0, 1, 1,
                         max_implementation_attempts=1, attempt_override_reference=key('one-attempt'))
    parent = BudgetAllocation(key('parent'), CONSUMER, key('work'), key('lineage'), key('authorization'), limits)
    child = BudgetAllocation(key('child'), CONSUMER, key('child-work'), parent.lineage_key,
        parent.authorization_reference, replace(limits, max_model_calls=8), parent.allocation_id)
    quote = {'provider': 'nous', 'model': MODEL, 'api_mode': 'chat_completions', 'base_url': URL,
             'max_request_bytes': 524288, 'max_output_tokens': 512, 'max_tokens': 66048,
             'max_cost_microusd': 0, 'max_work_ms': 30000}
    return ({'version': 1, 'allocation': asdict(parent), 'ancestors': [], 'model_quotes': [quote]},
            {'version': 1, 'allocation': asdict(child), 'ancestors': [asdict(parent)], 'model_quotes': [quote]})


def configure_work(bundle, proposal, admission):
    from dataclasses import asdict
    from herdr.security import SecurityGrant
    from herdr.taskgraph import TaskGraph
    from agent_completion_evidence import (spec_digest, typed_policy, store_for, binding,
                                          advertise_plan, validate_plan)
    workspace, child, base = fresh_repository(proposal)
    task = dict(bind_proposal(bundle, proposal))
    tools = sorted(proposal['tools'] + ['herdr_delegate_child'])
    task.update(issue=0, safety_profile='herdr-core', agent='quantlab-hermes',
        routing={'selected_agent': 'quantlab-hermes', 'model': MODEL, 'fallback_model': None},
        hermes_profile='quantlab', parent_role='writer', parent_tools=tools,
        parent_permissions=proposal['permissions'], worktree_root=str(HOME / 'worktrees'),
        spec_hash='sha256:' + proposal['case_sha256'], completion_plan={'base_sha': base},
        dispatch_claimed_at=iso(admission['started_epoch']), attempt_started_at=iso(admission['started_epoch']))
    # Allocate the fresh attempt through the EXISTING worker exactly once.
    worker = worker_module(); worker.prepare_attempt(task)
    task['completion_plan_pending'] = True
    task['max_attempts'] = 1
    env = check_environment(bundle)
    parent_budget, child_budget = budgets(bundle)
    definition = work_definition(proposal, task, base, workspace, tools, env, parent_budget)
    child_tools = sorted(proposal['tools'])
    child_definition = work_definition(proposal, task, base, child, child_tools, env, child_budget)
    ownership = {'write_scope': [{'kind': 'file', 'key': name} for name in proposal['write_files']],
        'decision_scope': [], 'hard_dependencies': [], 'shared_dependencies': [],
        'integration_owner': task['id'], 'handoff_ref': 'arithmetic-child'}
    criteria = {'version': 1, 'files': [{'path': name, 'subtree': False} for name in proposal['write_files']],
                'acceptance_ids': ['arithmetic'], 'shared_contract_keys': []}
    child_template = {'key': 'arithmetic-child', 'objective': 'Repair frozen arithmetic in managed child',
        'role': 'writer', 'tools': child_tools, 'permissions': proposal['permissions'],
        'worktree_identity': str(child) + f'|{child.stat().st_dev}:{child.stat().st_ino}',
        'ownership': ownership, 'completion': {'kind': 'coding', 'criteria': criteria,
            'work_contract_version': 1, 'work_budget_version': 1}, 'work_definition': child_definition}
    definition['managed_children'] = {'version': 1, 'children': [child_template]}
    node = {'type': 'task', 'id': task['id'], 'parent_id': None, 'role': task['parent_role'],
        'dependencies': [], 'priority': 0, 'resource_class': 'standard', 'permissions': proposal['permissions'],
        'timeout_seconds': 900, 'max_attempts': 1, 'objective': task['prompt'], 'inputs': [],
        'expected_outputs': [{'kind': 'candidate_commit'}], 'model_policy': {'model': MODEL, 'fallback_model': None},
        'tools': tools}
    graph = {'envelope': {'issue': task['repo'] + '#0', 'spec_hash': task['spec_hash'],
        'graph_version': '1.1.0', 'created_at': iso(admission['started_epoch']), 'planner': 'offline-clean',
        'max_nodes': 2, 'max_depth': 2, 'max_fanout': 1, 'policy_profile': 'herdr-core'}, 'nodes': [node]}
    definition['reviewed_graph'] = {'version': 1, 'graph': graph,
                                    'graph_sha256': TaskGraph.parse_planner_output(graph).graph_hash()}
    private = json.loads((ROOT / 'private-launch.json').read_bytes())
    grant = root_grant(bundle, proposal, admission, private, task)
    code = dict(bundle['runtime']['code'], target='/run/herdr/policy-code')
    runtime = [dict(bundle['runtime'][name], target=target) for name, target in (
        ('sdk', '/home/agentops/.hermes/hermes-agent'),
        ('python', '/home/agentops/.local/share/uv/python/cpython-3.11.16-linux-x86_64-gnu'))]
    policy = {'schema_version': 2, 'host_uid': 1001, 'code': code, 'runtime': runtime,
        'storage': str(HOME / '.local/state/herdr-clean'), 'templates': {CONSUMER: grant},
        'grant_ttl_seconds': GRANT_TTL, 'task_store_root': str(QUEUE), 'private_launch': private,
        'work_contracts': {'version': 1, 'environment': asdict(env),
            'plans': {spec_digest(task): definition}, 'review_records': {}}}
    # A NEW protected completion plan is configuration, with no invented checks,
    # PR, success receipt or historical SDK evidence. Offline acceptance stops at
    # verified_local_artifact; any GitHub completion attempt still fails closed.
    kind_policy = typed_policy('coding')
    workflow = ROOT / 'code/.github/workflows/ci.yml'
    workflow_blob = hashlib.sha1(b'blob ' + str(workflow.stat().st_size).encode() + b'\0' + workflow.read_bytes()).hexdigest()
    completion = {'version': 1, 'identity': binding(task), 'repo': task['repo'], 'kind': 'coding',
        'spec_hash': spec_digest(task), 'policy_hash': digest(kind_policy), 'base_sha': base,
        'workspace_root': str(HOME / 'worktrees'), 'required_checks': ['Herdr contract', 'GitGuardian Security Checks'],
        'reviewer': 'chatgpt-codex-connector[bot]', 'environment': {'collector': 'github-api-v1',
            'python': sys.version.split()[0], 'ci_workflow': kind_policy['workflow'],
            'github_actions_app_id': 15368, 'ci_workflow_id': kind_policy['workflow_id'],
            'ci_workflow_blob_sha': workflow_blob}, 'scope_policy': criteria}
    completion['plan_hash'] = digest(completion); completion['baseline'] = []
    validate_plan(completion)
    # Same existing EvidenceStore and immutable completion contract used by the
    # ordinary worker. This record asserts no external validation outcome.
    store_for(QUEUE, task).publish('plan', digest(binding(task)), completion)
    advertise_plan(task, completion)
    issuer = {'schema_version': 'herdr-automatic-launch-plan-1', 'host_policy_sha256': digest(policy),
        'host_cgroups': ['/system.slice/herdr-clean-' + bundle['nonce'] + '.service'],
        'entrypoints': ['agent-stack/bin/agent-task-worker', 'agent-stack/bin/agent-task-dispatcher',
                       'agent-stack/bin/agent-herdr-host-entrypoint', 'agent-stack/bin/agent-herdr-fd-launch', 'agent-stack/bin/agent-durable-bridge'], 'request_timeout_seconds': 60}
    write(HOME / '.local/state/clean-binding.json', {'proposal_sha256': proposal['proposal_sha256'],
        'policy_sha256': digest(policy), 'grant_template_sha256': SecurityGrant.from_dict(grant).hash,
        'profile_sha256': private['credential_approval']['profile_sha256'], 'case_sha256': CASE,
        'bundle_sha256': admission['bundle_sha256'], 'deadline_epoch': admission['deadline_epoch'], 'actual_task': binding(task)}, owner=1001, mode=0o444)
    delegation = {key: child_template[key] for key in ('key', 'objective', 'role', 'ownership')}
    delegation.update(prompt='Repair add in arithmetic.py only; verify the frozen check and submit local result.',
        tool=child_tools, permission=proposal['permissions'], cwd=str(child), model=MODEL, fallback_model=None)
    return task, delegation, policy, issuer


def import_harness(name):
    spec = importlib.util.spec_from_file_location('clean_' + name, ROOT / 'harness' / (name + '.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def setup_private_home():
    Path('/run/herdr-launch-authority').mkdir(parents=True, mode=0o755)
    for path in (HOME, HOME / '.local', HOME / '.local/bin', HOME / '.local/state',
        HOME / '.local/state/agent-stack', HOME / '.hermes', HOME / '.hermes/profiles', HOME / '.local/state/herdr',
        HOME / '.local/state/herdr-clean', HOME / '.config', HOME / '.cache',
        HOME / '.hermes/profiles/quantlab', HOME / 'worktrees', Path('/run/user/1001'),
        Path('/var/lib/agent-platform-herdr'), Path('/private/tmp')):
        path.mkdir(parents=True, exist_ok=True, mode=0o700); os.chown(path, 1001, 1001)
    for name in ('pending', 'running', 'blocked', 'failed', 'done', 'results', 'verification', 'logs'):
        path = QUEUE / name; path.mkdir(parents=True, mode=0o700); os.chown(path, 1001, 1001)
    os.chown(QUEUE, 1001, 1001); QUEUE.chmod(0o700)
    for name in ('logs', 'sessions', 'cron', 'cache', 'memories'):
        path = HOME / '.hermes/profiles/quantlab' / name
        path.mkdir(mode=0o700); os.chown(path, 1001, 1001)
    for path in ('/etc/herdr/launch-plans', '/etc/herdr/launch-plan-approvals'):
        Path(path).mkdir(parents=True, mode=0o755)
    write('/etc/passwd', b'root:x:0:0:root:/private/root:/bin/bash\nagentops:x:1001:1001:fixture:/home/agentops:/bin/bash\n', mode=0o444)
    write('/etc/group', b'root:x:0:\nagentops:x:1001:\n', mode=0o444)
    write('/etc/nsswitch.conf', b'passwd: files\ngroup: files\nhosts: files\n', mode=0o444)
    write('/etc/hosts', b'127.0.0.1 localhost inference-api.nousresearch.com\n', mode=0o444)
    # Native source is already a sealed FD. All mutable runtime state is new.
    write(HOME / '.local/bin/herdr', (ROOT / 'native').read_bytes(), owner=1001, mode=0o555)
    wrapper = '#!/bin/sh\nexec ' + PY + ' -I -B /run/clean/harness/clean_envelope.py --sdk "$@"\n'
    write(HOME / '.local/bin/hermes', wrapper.encode(), owner=1001, mode=0o555)


def current_scope_claim(role):
    from agent_completion_evidence import store_for, binding, digest
    task = json.loads((ROOT / 'prepared.json').read_bytes())['task']
    _, task = observe_task(task['id'])
    if role == 'child':
        from agent_durable_children import attempt_directory, replay_host_scheduler
        from herdr.child_evidence import child_task
        directory = attempt_directory(QUEUE, task['id'], task['run_token'])
        scheduler = replay_host_scheduler(QUEUE, directory / 'scheduler.jsonl')
        children = [rec for rec in scheduler._tasks.values() if rec.parent_task_id == task['id']]
        need(len(children) == 1, 'original child scope unavailable')
        task = child_task(children[0])
    plan = store_for(QUEUE, task).read('plan', digest(binding(task)))
    policy = plan.get('scope_policy')
    if policy is None:
        return None
    return {'version': 1, 'changed_groups': [{'files': [row['path'] for row in policy['files']],
        'symbols': ['add'], 'resources': [], 'acceptance_ids': policy['acceptance_ids'],
        'justification': 'Frozen arithmetic transport fixture declaration, subject to host verification.'}],
        'unrelated_changes': [], 'unexpected_side_effects': [], 'followups_not_implemented': [],
        'shared_contract_changes': [], 'verdict': 'IN_SCOPE'}


def local_transport(proposal, delegation, admission):
    import base64
    import http.server
    import socket
    import ssl
    import threading
    need(all(row.split()[1] != '00000000' for row in Path('/proc/net/route').read_text().splitlines()[1:]),
         'external route detected')
    cert = Path('/etc/ssl/certs/ca-certificates.crt'); cert.parent.mkdir(parents=True)
    key = ROOT / 'tls.key'
    run(['/usr/bin/openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '1',
        '-subj', '/CN=inference-api.nousresearch.com', '-addext', 'subjectAltName=DNS:inference-api.nousresearch.com',
        '-keyout', key, '-out', cert])
    fixture = import_harness('offline_provider').TeamFixture.for_proposal(proposal, delegation)
    observed = {'requests': 0, 'errors': [], 'external_http_calls': 0}
    class Handler(http.server.BaseHTTPRequestHandler):
        protocol_version = 'HTTP/1.0'
        def log_message(self, *args):
            pass
        def reply(self, status, value):
            raw = canonical(value); self.send_response(status)
            self.send_header('Content-Length', str(len(raw))); self.send_header('Content-Type', 'application/json')
            self.end_headers(); self.wfile.write(raw)
        def bounded(self):
            deadline_check(admission); observed['requests'] += 1
            need(observed['requests'] <= CAPS['local_requests'], 'local fixture request cap')
            self.connection.settimeout(10)
        def do_GET(self):
            try:
                self.bounded(); need(self.path == '/v1/models', 'only local model catalogue allowed')
                self.reply(200, {'data': [{'id': MODEL, 'pricing': {'prompt': '0', 'completion': '0',
                    'input_cache_read': '0'}, 'context_length': 1048576,
                    'top_provider': {'max_completion_tokens': 512}, 'supported_parameters': ['tools', 'max_tokens']}]})
            except Exception as error:
                observed['errors'].append(type(error).__name__); self.reply(400, {'error': 'local fixture stopped'})
        def do_POST(self):
            try:
                self.bounded(); need(self.path == '/v1/chat/completions', 'auth/GitHub endpoint forbidden')
                need(self.headers.get('Transfer-Encoding') is None, 'chunked request forbidden')
                length = int(self.headers.get('Content-Length', '0'))
                need(0 < length <= 524288, 'bounded fixture request required')
                bearer = self.headers.get('Authorization', '')
                need(bearer.startswith('Bearer '), 'synthetic bearer required')
                claim = bearer[7:].split('.')[1]
                value = json.loads(base64.urlsafe_b64decode(claim + '=' * (-len(claim) % 4)))
                need(value.get('sub') == 'herdr-offline-fixture', 'real credential rejected')
                payload = json.loads(self.rfile.read(length), object_pairs_hook=pairs)
                need(payload.get('model') == MODEL, 'model substitution denied')
                names = {item['function']['name'] for item in payload.get('tools', [])}
                role = 'root' if 'herdr_delegate_child' in names else 'child'
                selected = getattr(fixture, role)
                if selected.turn == 2:
                    selected.scope_claim = json.loads(run([PY, '-I', '-B',
                        str(ROOT / 'harness/clean_envelope.py'), '--scope', role], user=True, timeout=20))
                self.reply(200, fixture.answer(payload))
            except Exception as error:
                observed['errors'].append(type(error).__name__); self.reply(400, {'error': 'local fixture stopped'})
    server = http.server.HTTPServer(('127.0.0.1', 443), Handler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); context.load_cert_chain(cert, key)
    server.socket = context.wrap_socket(server.socket, server_side=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    return server, fixture, observed


def worker_module():
    from importlib.machinery import SourceFileLoader
    loader = SourceFileLoader('clean_original_worker', str(ROOT / 'code/agent-stack/bin/agent-task-worker'))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec); loader.exec_module(module)
    return module


def observe_task(task_id):
    from herdr.operation_readiness import observe_task as observe, SnapshotChanged
    from herdr.evidence import binding
    expected = binding(json.loads((ROOT / 'prepared.json').read_bytes())['task'])
    admission = json.loads((ROOT / 'admission.json').read_bytes())
    while deadline_check(admission) > 0:
        try:
            return observe(QUEUE, task_id, expected)
        except SnapshotChanged:
            time.sleep(.05)
    raise Denied('original observation deadline exhausted')


def wait_original_worker(admission):
    import fcntl
    fd = os.open(QUEUE / 'worker.loop.lock', os.O_RDWR | os.O_NOFOLLOW)
    try:
        while deadline_check(admission) > 20:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return
            except BlockingIOError:
                time.sleep(.05)
        raise Denied('original worker did not quiesce before deadline')
    finally:
        os.close(fd)


def recover_original(task):
    """Existing original-worker recovery, never main()/redispatch/new SDK."""
    import fcntl
    worker = worker_module()
    lock = os.open(QUEUE / 'worker.loop.lock', os.O_RDWR | os.O_NOFOLLOW)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        result = QUEUE / 'results' / (task['id'] + '.json')
        before = result.read_bytes()
        need(before and task.get('attempt_state') == 'result_ready'
             and task.get('watchdog_blocker') == 'active_durable_children', 'original quarantined local result required')
        need(worker._recover_root_local_result(task), 'original worker local replay denied')
        need(result.read_bytes() == before, 'original result changed on cold replay')
        factory, cycle = worker._recover_root_work_cycle(task)
        from herdr.work_result_receipt import WorkResultAuthority
        need(isinstance(factory.result_authority, WorkResultAuthority), 'original result authority required')
        # The receipt verifier rechecks exact artifacts, plan and launch identity.
        payload = json.loads(before)
        identity = cycle.plan.identity
        from agent_completion_evidence import store_for, binding, digest
        completion = store_for(QUEUE, task).read('plan', digest(binding(task)))
        factory.before_completion(identity, payload)
        receipt = factory.result_authority.verifier(task, payload, completion, work_plan_sha256=cycle.plan.hash)
        receipt(task)
        return {'result_sha256': hashlib.sha256(before).hexdigest(), 'work_plan_sha256': cycle.plan.hash,
                'identity': identity.to_json(), 'cold_recovery': True, 'semantic_done': False}
    finally:
        os.close(lock)


def recover_child(task):
    from agent_durable_children import attempt_directory
    from agent_completion_evidence import child_completion_for_replay, binding, digest
    from herdr.scheduler import DynamicChildScheduler, AuditLog
    from herdr.child_evidence import child_identity, child_task
    directory = attempt_directory(QUEUE, task['id'], task['run_token'])
    from agent_durable_children import replay_host_scheduler
    scheduler = replay_host_scheduler(QUEUE, directory / 'scheduler.jsonl')
    children = [rec for rec in scheduler._tasks.values() if rec.parent_task_id == task['id']]
    need(len(children) == 1, 'exactly one retained managed child required')
    rec = children[0]
    authority = child_completion_for_replay(QUEUE, scheduler)
    need(authority is not None, 'original derived child authority missing')
    result = directory / 'results' / (rec.id + '.result.json')
    before = result.read_bytes()
    need(before and authority.recover_local_result(rec, result), 'original child local replay denied')
    need(result.read_bytes() == before, 'child result changed during replay')
    completion = authority.store.read('plan', digest(binding(child_task(rec))))
    factory, work_task = authority.recover_work(rec, completion)
    cycle = factory.before_completion(child_identity(rec), json.loads(before))
    verify = factory.result_authority.verifier(work_task, json.loads(before), completion, work_plan_sha256=cycle.plan.hash)
    verify(work_task)
    return {'identity': child_identity(rec).to_json(), 'result_sha256': hashlib.sha256(before).hexdigest(),
            'cold_recovery': True, 'level': 'verified_local_artifact', 'semantic_done': False}


def economic_history():
    return {str(path.relative_to(HOME)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (HOME / '.local/state/herdr-clean/work-budget').glob('*/events.jsonl')}


def host_run(bundle, admission, prepared):
    """Observe/control only one native session; ordinary dispatcher owns the task."""
    import signal
    from herdr.launch_environment import process_environment
    native = HOME / '.local/bin/herdr'
    session = 'offline-' + bundle['nonce'][:20]
    task = prepared['task']; workspace = task['workspace']
    env = environment()
    def call(args, timeout=10):
        raw = run([native, '--session', session, *args], timeout=timeout, env=env)
        return json.loads(raw) if raw.strip() else None
    log = (HOME / '.local/state/native.log').open('xb')
    server = subprocess.Popen([str(native), '--session', session, 'server'], cwd=workspace,
                              env=env, stdout=log, stderr=log)
    try:
        until = time.monotonic() + 25
        while True:
            need(server.poll() is None and time.monotonic() < until, 'native server unavailable')
            try:
                call(['workspace', 'list']); break
            except (Denied, subprocess.TimeoutExpired):
                time.sleep(.1)
        marker = 'offline-coordinator-' + bundle['nonce'][:12]
        layout = call(['workspace', 'create', '--cwd', workspace, '--label', 'Clean arithmetic fixture',
                       '--env', 'HERDR_DURABLE_TASK_PANE=' + marker, '--no-focus'])['result']
        pane = layout['root_pane']['pane_id']
        from agent_durable_sandbox import pane_input_ready, verify_pane_prompt
        until = time.monotonic() + 15
        while True:
            info = call(['pane', 'process-info', '--pane', pane])['result']['process_info']
            if pane_input_ready(info, marker):
                break
            need(time.monotonic() < until, 'coordinator shell unavailable'); time.sleep(.05)
        verify_pane_prompt(call, pane, marker, timeout_seconds=10)
        call(['agent', 'start', 'quantlab-hermes', '--kind', 'hermes', '--pane', pane, '--timeout', '60000',
              '--', '-p', 'quantlab', 'chat', '--model', MODEL, '--continue', 'offline-coordinator',
              '--create-if-missing', '--in', workspace], timeout=75)
        # Use context from a fresh owned shell, never inherit a live host pane.
        control = call(['tab', 'create', '--workspace', layout['workspace']['workspace_id'], '--cwd', workspace,
            '--label', 'Offline host control', '--env', 'HERDR_DURABLE_TASK_PANE=offline-control', '--no-focus'])['result']['root_pane']['pane_id']
        context = call(['pane', 'process-info', '--pane', control])['result']['process_info']
        context = {k: v for k, v in process_environment(int(context['shell_pid'])).items() if k.startswith('HERDR_')}
        need(context.get('HERDR_ENV') == '1', 'fresh native context required')
        dispatch = [PY, '-I', '-B', str(ROOT / 'code/agent-stack/bin/agent-herdr-host-entrypoint'),
                    'agent-stack/bin/agent-task-dispatcher']
        # Only this once: there is no retry, watchdog, intake poll or second queue.
        run(dispatch, env={**env, **context}, timeout=min(300, deadline_check(admission)))
        while deadline_check(admission) > 30:
            path, current = observe_task(task['id'])
            need(current['run_token'] == task['run_token'] and current['fencing_token'] == task['fencing_token'],
                 'original task identity changed')
            if current.get('attempt_state') == 'result_ready' and current.get('watchdog_blocker') == 'active_durable_children':
                # This separate process is a cold reconstruction of existing ports.
                wait_original_worker(admission)
                raw = run([PY, '-I', '-B', str(ROOT / 'harness/clean_envelope.py'), '--recover'], timeout=120)
                return json.loads(raw)
            need(path.parent.name not in ('failed', 'done') and not (
                path.parent.name == 'blocked' and current.get('attempt_state') not in ('verification_pending', 'result_ready')),
                'ordinary worker stopped before local handoff')
            time.sleep(.2)
        raise Denied('original work deadline; no redispatch')
    finally:
        if server.poll() is None:
            try:
                call(['server', 'stop'])
            except Exception:
                server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill(); server.wait(timeout=5)
        log.close()


def drop_setup_authority():
    import ctypes
    libc = ctypes.CDLL(None, use_errno=True)
    # root issuer needs proc/FD observation and UID transitions, never remount.
    keep = {0, 1, 2, 3, 5, 6, 7, 10, 19}
    for capability in range(41):
        if capability not in keep:
            result = libc.prctl(24, capability, 0, 0, 0)  # PR_CAPBSET_DROP
            need(result == 0 or ctypes.get_errno() == 22, 'capability bounding drop failed')
    class Header(ctypes.Structure):
        _fields_ = [('version', ctypes.c_uint32), ('pid', ctypes.c_int)]
    class Data(ctypes.Structure):
        _fields_ = [('effective', ctypes.c_uint32), ('permitted', ctypes.c_uint32), ('inheritable', ctypes.c_uint32)]
    need(libc.prctl(28, 3, 0, 0, 0) == 0, 'locked no-root-exec privilege policy unavailable')
    header = Header(0x20080522, 0); data = (Data * 2)()
    mask = sum(1 << x for x in keep)
    data[0].effective = data[0].permitted = data[0].inheritable = mask
    need(libc.capset(ctypes.byref(header), ctypes.byref(data)) == 0, 'setup capability drop failed')
    for capability in keep:
        need(libc.prctl(47, 2, capability, 0, 0) == 0, 'minimal ambient capability unavailable')
    need(libc.prctl(38, 1, 0, 0, 0) == 0, 'no-new-privileges unavailable')
    # No raw source-directory FD may bypass a readonly bind.
    for name in os.listdir('/proc/self/fd'):
        if name.isdecimal() and int(name) > 2:
            try:
                os.close(int(name))
            except OSError:
                pass
    status = dict(line.split(':', 1) for line in Path('/proc/self/status').read_text().splitlines() if ':' in line)
    need(not int(status['CapBnd'].strip(), 16) & (1 << 21), 'remount capability retained')


def retained_evidence():
    """Export original nonsecret fixture records, not invented success receipts.

    No profile/auth/credential files, host paths or large runtime copies enter
    this archive. All workspaces are the new two-file case and its own Git DB.
    """
    import base64
    import gzip
    import io
    import tarfile
    chosen = [path for path in (POLICY, POLICY.with_name('launch-plan-issuer.json'), ROOT / 'binding.json',
        ROOT / 'admission.json', ROOT / 'issuer.log', HOME / '.local/state/native.log') if path.is_file()]
    for root in (QUEUE, HOME / '.local/state/herdr-clean'):
        chosen.extend(p for p in root.rglob('*') if p.is_file() and p.suffix in ('.json', '.jsonl', '.log'))
    chosen.extend(p for p in (HOME / 'worktrees').rglob('*') if p.is_file())
    output = io.BytesIO(); index = {}; total = 0
    with tarfile.open(fileobj=output, mode='w:gz') as archive:
        for path in sorted(set(chosen)):
            info = path.lstat()
            need(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, 'evidence alias/special file rejected')
            data = path.read_bytes(); total += len(data)
            need(total <= 67108864, 'retained original evidence bound')
            name = str(path).lstrip('/')
            index[name] = hashlib.sha256(data).hexdigest()
            member = tarfile.TarInfo(name); member.size = len(data); member.mode = 0o400
            archive.addfile(member, io.BytesIO(data))
    payload = output.getvalue(); need(len(payload) <= 33554432, 'compressed evidence bound')
    return {'format': 'tar+gzip+base64', 'sha256': hashlib.sha256(payload).hexdigest(),
            'members': index, 'bytes': len(payload), 'data': base64.b64encode(payload).decode()}


def binding_record(policy, bundle, admission):
    template = policy['templates'][CONSUMER]
    return {'policy_sha256': digest(policy), 'grant_sha256': digest(template),
            'profile_sha256': digest(policy['private_launch']), 'source_sha256': digest(policy['code']),
            'bundle_sha256': admission['bundle_sha256'], 'deadline_epoch': admission['deadline_epoch']}


def require_binding(record, policy, bundle, admission):
    need(record == binding_record(policy, bundle, admission), 'source/policy/grant/profile binding changed')
    need(policy['code']['files'] == bundle['runtime']['code']['files']
         and policy['code']['source'] == '/run/clean/code', 'runtime code differs from main')
    need(policy['templates'][CONSUMER]['expires_at'] == iso(admission['deadline_epoch']),
         'grant deadline changed after admission')


def inner():
    global _BOUNDARY_VERIFIED
    bundle = validate_bundle(json.loads((ROOT / 'bundle.json').read_bytes()))
    admission = json.loads((ROOT / 'admission.json').read_bytes())
    need(digest(bundle) == admission['bundle_sha256'], 'bundle/admission changed')
    deadline_check(admission); namespaces = private_boundary(bundle)
    _BOUNDARY_VERIFIED = True
    run(['/usr/sbin/ip', 'link', 'set', 'dev', 'lo', 'up'])
    drop_setup_authority()
    setup_private_home()
    sys.path[:0] = [str(ROOT / 'code'), str(ROOT / 'code/agent-stack/bin')]
    private = configure_profile(bundle, admission)
    write(ROOT / 'private-launch.json', private, mode=0o444)
    raw = run([PY, '-I', '-B', str(ROOT / 'harness/clean_envelope.py'), '--prepare-user'], user=True, timeout=120)
    prepared = json.loads(raw); policy = prepared.pop('policy'); issuer = prepared.pop('issuer')
    binding = binding_record(policy, bundle, admission)
    require_binding(binding, policy, bundle, admission)
    write(ROOT / 'binding.json', binding, mode=0o444)
    write(POLICY, policy, mode=0o644); write(POLICY.with_name('launch-plan-issuer.json'), issuer, mode=0o644)
    write(ROOT / 'prepared.json', prepared, mode=0o444)
    proposal = import_harness('offline_pilot').prepare_clean_inputs(ROOT / 'harness/offline_case_inputs.json', CASE, bundle['nonce'])
    server, fixture, observed = local_transport(proposal, prepared['delegation'], admission)
    issuer_log = (ROOT / 'issuer.log').open('xb')
    process = subprocess.Popen([PY, '-I', '-B', str(ROOT / 'code/scripts/serve-herdr-launch-plan-issuer.py')],
                               env=environment(), stdout=issuer_log, stderr=issuer_log)
    try:
        until = time.monotonic() + 30
        while not Path('/run/herdr-launch-authority/issuer.sock').exists():
            need(process.poll() is None and time.monotonic() < until, 'real issuer unavailable'); time.sleep(.1)
        require_binding(binding, load_pin(POLICY, binding['policy_sha256']), bundle, admission)
        raw = run([PY, '-I', '-B', str(ROOT / 'harness/clean_envelope.py'), '--host'], user=True,
                  timeout=max(1, deadline_check(admission) - 20))
        result = json.loads(raw)
        need(fixture.complete and not observed['errors'], 'root/child local fixture incomplete')
        # This observation is NOT a semantic coding DONE or accepted child handoff.
        print(canonical({'schema_version': 'herdr-clean-local-envelope-1', 'local': result,
            'namespace_observation': namespaces, 'transport': observed, 'source_main': MAIN,
            'core_patch': bundle['core_patch'], 'composed_runtime_manifest_sha256': MAIN_MANIFEST,
            'original_evidence': retained_evidence(),
            'physical_local_handoff': True, 'semantic_child_acceptance': 'NOT_ESTABLISHED',
            'parent_dependency_released': False, 'quarantined_until_private_unit_teardown': True,
            'full_e2e': 'NOT_ESTABLISHED', 'usage_is_fixture_only': True, 'automatic_retry_allowed': False}).decode(), flush=True)
    finally:
        server.shutdown(); server.server_close()
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill(); process.wait(timeout=5)
        issuer_log.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--inspect', action='store_true')
    modes.add_argument('--execute-approved-clean-envelope', action='store_true')
    modes.add_argument('--scope', choices=('root', 'child'))
    for mode in ('inner', 'prepare-user', 'host', 'recover', 'sdk'):
        modes.add_argument('--' + mode, action='store_true')
    parser.add_argument('--bundle'); parser.add_argument('--sha256')
    parser.add_argument('--source'); parser.add_argument('--harness'); parser.add_argument('--evidence')
    args, rest = parser.parse_known_args()
    if args.inspect:
        need(not rest, 'unexpected inspection argument')
        print(canonical(validate_bundle(load_pin(args.bundle, args.sha256))).decode()); return
    if args.execute_approved_clean_envelope:
        need(not rest, 'unexpected execution argument')
        outer(args.bundle, args.sha256, args.source, args.harness, args.evidence); return
    need(not any((args.bundle, args.sha256, args.source, args.harness, args.evidence)), 'closed inner invocation required')
    need(Path(__file__) == ROOT / 'harness/clean_envelope.py', 'inner harness path required')
    if args.inner:
        need(not rest, 'unexpected inner argument'); inner(); return
    # These modes can exist only in the private namespace prepared by inner().
    bundle = validate_bundle(json.loads((ROOT / 'bundle.json').read_bytes()))
    admission = json.loads((ROOT / 'admission.json').read_bytes())
    deadline_check(admission)
    sys.path[:0] = [str(ROOT / 'code'), str(ROOT / 'code/agent-stack/bin')]
    if args.sdk:
        sys.path[:0] = [SDK, SDK + '/venv/lib/python3.11/site-packages']
        sys.argv = ['hermes', *rest]
        from hermes_cli.main import main as sdk_main
        raise SystemExit(sdk_main())
    need(not rest and os.geteuid() == 1001, 'private host UID required')
    if args.scope:
        print(canonical(current_scope_claim(args.scope)).decode())
    elif args.prepare_user:
        proposal = import_harness('offline_pilot').prepare_clean_inputs(ROOT / 'harness/offline_case_inputs.json', CASE, bundle['nonce'])
        task, delegation, policy, issuer = configure_work(bundle, proposal, admission)
        write(QUEUE / 'pending' / (task['id'] + '.json'), task, owner=1001)
        print(canonical(dict(task=task, delegation=delegation, policy=policy, issuer=issuer)).decode())
    elif args.host:
        print(canonical(host_run(bundle, admission, json.loads((ROOT / 'prepared.json').read_bytes()))).decode())
    elif args.recover:
        task = json.loads((ROOT / 'prepared.json').read_bytes())['task']
        _, task = observe_task(task['id'])
        before = economic_history()
        result = {'root': recover_original(task), 'child': recover_child(task)}
        need(before and economic_history() == before, 'cold replay changed economic history')
        print(canonical(result).decode())


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        if _BOUNDARY_VERIFIED and os.geteuid() == 0:
            try:
                print(canonical({'physical_pass': False, 'retained_failure_evidence': retained_evidence()}).decode(), flush=True)
            except Exception as archive_error:
                print(canonical({'physical_pass': False, 'evidence_export_error': type(archive_error).__name__}).decode(), flush=True)
        print(canonical({'error_type': type(error).__name__, 'reason': str(error),
                         'automatic_retry_allowed': False, 'physical_pass': False}).decode(), file=sys.stderr)
        raise SystemExit(1)
