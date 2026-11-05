"""Inert native mount receipt and finalizer handoff checks; no namespace operations."""
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
NATIVE = ROOT / 'native'
spec = importlib.util.spec_from_file_location('native_trusted_prepare_under_test', NATIVE / 'trusted_prepare.py')
prep = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = prep
spec.loader.exec_module(prep)


class FakeOS:
    O_RDONLY=os.O_RDONLY;O_DIRECTORY=os.O_DIRECTORY;O_NOFOLLOW=os.O_NOFOLLOW
    O_CLOEXEC=os.O_CLOEXEC;O_WRONLY=os.O_WRONLY;O_CREAT=os.O_CREAT;O_EXCL=os.O_EXCL
    def __init__(self):self.writes=[];self.opens=[]
    def readlink(self,path):return {'/proc/self/ns/mnt':'mnt:[777]','/proc/self/ns/pid':'pid:[888]'}[path]
    def getpid(self):return 700
    def open(self,path,flags,mode=0,**kwargs):
        self.opens.append((str(path),flags,kwargs));return 10 if str(path).endswith('.mount.json') else 9
    def fstat(self,fd):return types.SimpleNamespace(st_uid=0,st_mode=stat.S_IFDIR|0o750)
    def write(self,fd,data):self.writes.append(bytes(data));return len(data)
    def fchown(self,*args):pass
    def fchmod(self,*args):pass
    def fsync(self,*args):pass
    def close(self,*args):pass


class NativeMountReceipt(unittest.TestCase):
    def test_real_native_preparer_publishes_exact_mount_identity_exclusively(self):
        ops=object.__new__(prep.LinuxOps)
        ops.runtime_binding={'role':'root','roster_sha256':'a'*64,
            'context_sha256':'b'*64,'unit':'owned-root.service'}
        root='/run/herdr-offline-private-root-'+'a'*16
        stat_bytes=b'700 (native child) '+b' '.join([b'S',b'1']+[b'0']*17+[b'321',b'0'])
        ops._read=lambda path,limit: (b'51 1 0:10 / '+root.encode()+b' rw - tmpfs tmpfs rw\n'+
                                      b'52 51 0:11 / '+root.encode()+b'/dev rw - tmpfs tmpfs rw\n'
                                      if path.endswith('mountinfo') else stat_bytes)
        fake=FakeOS()
        roster=types.ModuleType('case_roster');roster.CONTEXT_ROOT=Path('/synthetic/context')
        roster.canonical=lambda value:json.dumps(value,sort_keys=True,separators=(',',':')).encode()
        with patch.dict(sys.modules,{'case_roster':roster}),patch.object(prep,'os',fake):
            ops.publish_private_mount(root)
            row=json.loads(fake.writes[0])
            self.assertEqual((row['private_root'],row['mount_id'],row['mount_namespace'],row['pid_namespace']),
                             (root,51,'mnt:[777]','pid:[888]'))
            self.assertEqual(row['mount_ids'],[51,52])
            self.assertEqual((row['pid'],row['start_ticks']),(700,321))
            self.assertEqual(fake.opens[1][0],'root.mount.json')
            self.assertTrue(fake.opens[1][1]&os.O_EXCL)
            self.assertTrue(fake.opens[1][1]&os.O_NOFOLLOW)
        with patch.dict(sys.modules,{'case_roster':roster}),patch.object(prep,'os',fake):
            ops._read=lambda path,limit:b'52 1 0:10 / /wrong rw - tmpfs tmpfs rw\n' if path.endswith('mountinfo') else stat_bytes
            with self.assertRaises(prep.Denied):ops.publish_private_mount(root)

    def test_receipt_is_before_pivot_and_worker_exec(self):
        import ast
        tree=ast.parse((NATIVE/'trusted_prepare.py').read_text())
        body=next(node.body for node in tree.body if isinstance(node,ast.FunctionDef)
                  and node.name=='prepare_and_exec')
        source=ast.unparse(body)
        self.assertLess(source.index('ops.publish_private_mount(root)'),source.index('ops.pivot_to(root)'))
        self.assertLess(source.index('ops.pivot_to(root)'),source.index('ops.execve('))


if __name__=='__main__':unittest.main()
