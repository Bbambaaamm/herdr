"""Q01–Q24: exercise the actual native call boundary and quota arithmetic."""
import ctypes
import errno
from types import SimpleNamespace

import pytest

from deploy.herdr.cutover import filesystem_capacity as f
from herdr.release import ReleaseError


class Query:
    def __init__(self, direct, values, failure=None):
        self.direct = direct
        self.values = values
        self.failure = failure
        self.calls = []

    def __call__(self, *args):
        if self.direct:
            number, *args = args
            assert number == 443 and self.restype is ctypes.c_long
        else:
            assert self.restype is ctypes.c_int
        fd, command, identity, pointer = args
        assert type(fd) is ctypes.c_int and fd.value == 7
        assert type(command) is type(identity) is ctypes.c_uint
        assert command.value in (0x80000700, 0x80000701)
        key = (command.value & 1, identity.value)
        self.calls.append(key)
        if self.failure and self.failure[:2] == key:
            ctypes.set_errno(self.failure[2])
            return -1
        data = pointer._obj
        assert ctypes.sizeof(data) == 72 and ctypes.alignment(data) == 8
        assert data.valid == 0
        for field, value in self.values.items():
            setattr(data, field, value)
        return 0


def run(monkeypatch, query, options='usrquota,grpquota'):
    lib = SimpleNamespace(**{'syscall' if query.direct else 'quotactl_fd': query})
    monkeypatch.setattr(ctypes, 'CDLL', lambda *a, **kw: lib)
    return f.quota_headroom(7, dict(options='rw', super_options=options), 5000, 100)


@pytest.mark.parametrize('direct', [False, True])
@pytest.mark.parametrize('fields,expected', [
    ({}, (5000, 100)), ({'bhard': 4, 'space': 96}, (4000, 100)),
    ({'bhard': 4, 'space': 4096}, (0, 100)),
    ({'bhard': 4, 'space': 4097}, (0, 100)),
    ({'bsoft': 2, 'space': 2050, 'btime': 1}, (0, 100)),
    ({'bsoft': 2, 'space': 2050, 'btime': 2**63}, (0, 100)),
    ({'isoft': 3, 'inodes': 4}, (5000, 0)),
    ({'ihard': 8, 'inodes': 2, 'bsoft': 1}, (1024, 6)),
    ({'bhard': 2**64-1}, (5000, 100)),
])
def test_limits_and_identity_coverage(monkeypatch, direct, fields, expected):
    query = Query(direct, dict(valid=63, **fields))
    assert run(monkeypatch, query) == (*expected, 'verified')
    assert query.calls == [(0, 0), (0, 1001), (1, 0), (1, 982), (1, 1001)]


@pytest.mark.parametrize('code', [errno.EPERM, errno.EACCES, errno.EBADF, errno.ENOSYS,
                                  errno.ESRCH, errno.EINVAL, errno.EOPNOTSUPP])
@pytest.mark.parametrize('kind,identity', [(0, 1001), (1, 982)])
@pytest.mark.parametrize('direct', [True, False])
def test_identity_failure_is_final(monkeypatch, code, kind, identity, direct):
    q = Query(direct, {'valid': 63}, (kind, identity, code))
    with pytest.raises(ReleaseError, match=errno.errorcode[code]):
        run(monkeypatch, q)
    assert q.calls[-1] == (kind, identity)


@pytest.mark.parametrize('valid', [0, 14, 13, 11, 7])
def test_incomplete_structure(monkeypatch, valid):
    with pytest.raises(ReleaseError, match='quota_fields_unverified'):
        run(monkeypatch, Query(True, {'valid': valid}))


def test_architecture_and_abi(monkeypatch):
    monkeypatch.setattr(f.os, 'uname', lambda: SimpleNamespace(machine='unknown'))
    with pytest.raises(ReleaseError, match='architecture_unsupported'):
        run(monkeypatch, Query(True, {}))
    monkeypatch.setattr(f.os, 'uname', lambda: SimpleNamespace(machine='x86_64'))
    monkeypatch.setattr(f.sys, 'byteorder', 'big')
    with pytest.raises(ReleaseError, match='abi_unsupported'):
        run(monkeypatch, Query(True, {}))


def test_no_query_interface(monkeypatch):
    monkeypatch.setattr(ctypes, 'CDLL', lambda *a, **kw: SimpleNamespace())
    with pytest.raises(ReleaseError, match='syscall_unavailable'):
        f._read_quota(7, 0, 0)


def test_disabled_and_unknown_project(monkeypatch):
    q = Query(True, {})
    assert run(monkeypatch, q, 'rw') == (5000, 100, 'not_enabled')
    with pytest.raises(ReleaseError, match='project_quota_unverified'):
        run(monkeypatch, q, 'prjquota')
    assert not q.calls


@pytest.mark.parametrize('opts', ['usrjquota=a,grpjquota=b,jqfmt=vfsv1',
                                  'uqnoenforce,gqnoenforce'])
def test_accounted_identities(monkeypatch, opts):
    q = Query(True, {'valid': 63})
    assert run(monkeypatch, q, opts)[-1] == 'verified'
    assert len(q.calls) == 5


@pytest.mark.parametrize('opts', ['pqnoenforce', 'jqfmt=vfsv1', 'unknownquota'])
def test_unknown_quota_authority(monkeypatch, opts):
    with pytest.raises(ReleaseError, match='quota_'):
        run(monkeypatch, Query(True, {}), opts)
