"""Admin-only explicit TTY credential creation. Never used by runtime/exporter."""
from contextlib import contextmanager
import grp
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import tempfile

from . import production_contract as c
from .production_auth import ITERATIONS
from .production_io import directory


def material(password, salt):
    """Derive verifier only. No persistence or password logging."""
    c.need(type(password) is str and 32 <= len(password) <= 128 and password.isascii()
           and all(ch.isalnum() or ch in '-_' for ch in password))
    c.need(type(salt) is bytes and len(salt) == 16)
    return dict(version=1, username='michal', salt=salt.hex(),
                verifier=hashlib.pbkdf2_hmac('sha256', password.encode(), salt, ITERATIONS).hex(),
                profiles=['majak', 'quantlab'])


@contextmanager
def terminal(path='/dev/tty'):
    # Separate streams: buffered r+ requires seek and fails on a real terminal.
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOCTTY | os.O_CLOEXEC), 'r', encoding='utf-8') as reader, \
            os.fdopen(os.open(path, os.O_WRONLY | os.O_NOCTTY | os.O_CLOEXEC), 'w', encoding='utf-8') as writer:
        c.need(os.isatty(reader.fileno()) and os.isatty(writer.fileno()))
        yield reader, writer


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    destination = Path('/etc/agent-platform/credentials')
    try:
        c.need(args == ['--confirm', str(destination)] and os.geteuid() == 0)
        with directory(str(destination.parent)) as parent:
            info = os.fstat(parent)
            c.need(info.st_uid == 0 and not info.st_mode & 0o022)
        if destination.exists() or destination.is_symlink():
            print('credentials_already_exist_no_rotation', file=sys.stderr)
            return 78
        # Require a private, non-recorded admin terminal. Never stdout/stderr/argv/env.
        with terminal() as (reader, tty):
            tty.write('Type CREATE michal to generate once (no terminal recording): '); tty.flush()
            c.need(reader.readline(80).strip() == 'CREATE michal')
            password = secrets.token_urlsafe(36)
            auth = material(password, secrets.token_bytes(16))
            hashed = subprocess.run(['/usr/bin/openssl', 'passwd', '-6', '-stdin'],
                                    input=(password + '\n').encode(), stdout=subprocess.PIPE,
                                    stderr=subprocess.DEVNULL, timeout=5, check=True,
                                    env={'PATH': '/usr/bin:/bin', 'LANG': 'C'}, close_fds=True).stdout
            c.need(len(hashed) < 256 and hashed.startswith(b'$6$') and hashed.count(b'\n') == 1)
            group = grp.getgrnam('agent-platform-auth').gr_gid
            temporary = Path(tempfile.mkdtemp(prefix='.credentials-', dir=destination.parent))
            try:
                for name, content in (('htpasswd', b'michal:' + hashed), ('auth.json', json.dumps(auth).encode())):
                    path = temporary / name
                    with path.open('xb') as stream:
                        stream.write(content); stream.flush()
                        os.fchmod(stream.fileno(), 0o640); os.fchown(stream.fileno(), 0, group); os.fsync(stream.fileno())
                os.chown(temporary, 0, group); temporary.chmod(0o750)
                # parent is root-only writable; no other administrator may race setup.
                c.need(not destination.exists() and not destination.is_symlink())
                os.rename(temporary, destination)
                with directory(str(destination.parent)) as parent:
                    os.fsync(parent)
            finally:
                if temporary.exists():
                    shutil.rmtree(temporary)
            tty.write('\nStore in your password manager now. Shown once:\nmichal: ' + password + '\n')
            tty.flush()
            password = None
        return 0
    except Exception:
        print('credential_setup_failed_no_secret_output', file=sys.stderr)
        return 78


if __name__ == '__main__':
    raise SystemExit(main())
