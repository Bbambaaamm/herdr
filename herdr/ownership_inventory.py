"""Conservative host migration gate over protected canonical child ledgers.

This is inventory, never a queue. Unknown legacy writers retain a global
quarantine even if a model submitted DONE or an observed pane disappeared.
Only an exact registry claim with host-verified release can retire ownership.
"""
from __future__ import annotations

import json
import os
import re
import stat
from pathlib import Path

from .child_ownership import ChildOwnership, OwnershipError, require
from .security import InvocationIdentity
from .scheduler import AuditLog, DynamicChildScheduler


class _InventoryAudit(AuditLog):
    def __init__(self, events):
        self.events = events

    def replay(self):
        return self.events


class LegacyOwnershipInventory:
    MAX_DIRECTORIES = 1024
    MAX_LEDGER = 8*1024*1024
    MAX_TOTAL = 32*1024*1024
    MAX_EVENTS = 16384

    def __init__(self, root):
        self.root = Path(root).absolute()
        require(self.root.resolve(strict=True) == self.root, "ownership_inventory_root")
        info = self.root.lstat()
        require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid()
                and not info.st_mode & 0o022, "ownership_inventory_root")
        self.root_identity = (info.st_dev, info.st_ino)

    @staticmethod
    def _directory(fd, *, private=True):
        info = os.fstat(fd)
        require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid()
                and (stat.S_IMODE(info.st_mode) == 0o700 if private else not info.st_mode & 0o022),
                "ownership_inventory_private_directory")
        return info

    def _events(self, directory):
        flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK
        try:
            fd = os.open("scheduler.jsonl", flags, dir_fd=directory)
        except FileNotFoundError:
            # A genuinely empty/pending initialization has no child economic
            # claim. A required-but-missing ledger is corrupt and blocks writes.
            names = set(os.listdir(directory))
            require("scheduler.required" not in names, "ownership_inventory_missing_ledger")
            return [], 0
        try:
            info = os.fstat(fd)
            require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid()
                    and not info.st_mode & 0o022 and info.st_nlink == 1
                    and info.st_size <= self.MAX_LEDGER, "ownership_inventory_private_ledger")
            raw = bytearray()
            while len(raw) <= self.MAX_LEDGER:
                chunk = os.read(fd, min(65536, self.MAX_LEDGER+1-len(raw)))
                if not chunk:
                    break
                raw.extend(chunk)
            require(len(raw) <= self.MAX_LEDGER, "ownership_inventory_ledger_bound")
            after = os.fstat(fd)
            named = os.stat("scheduler.jsonl", dir_fd=directory, follow_symlinks=False)
            require((after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) ==
                    (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)
                    and (named.st_dev, named.st_ino, named.st_size, named.st_mtime_ns) ==
                    (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns),
                    "ownership_inventory_ledger_changed")
            def unique(pairs):
                value = {}
                for key, item in pairs:
                    require(key not in value, "ownership_inventory_duplicate_key")
                    value[key] = item
                return value
            lines = raw.splitlines()
            require(len(lines) <= self.MAX_EVENTS, "ownership_inventory_event_bound")
            events = [json.loads(line, object_pairs_hook=unique,
                      parse_constant=lambda _: require(False, "ownership_inventory_nonfinite"))
                      for line in lines if line.strip()]
            require(all(isinstance(x, dict) for x in events), "ownership_inventory_event_schema")
            return events, len(raw)
        finally:
            os.close(fd)

    def _known_claim(self, rec, data):
        row = data["reservations"].get(rec.ownership_reservation)
        if row is None and rec.ownership_reservation:
            from .child_ownership import OwnershipRegistry
            row = OwnershipRegistry(self.root).retired_reservation(rec.ownership_reservation)
        if row is None or rec.ownership is None or row["ownership"] is None or ChildOwnership.from_json(row["ownership"]) != rec.ownership:
            return False
        actual = InvocationIdentity("github:"+rec.repo, rec.agent_id,
            rec.parent_agent_id, rec.parent_task_id, rec.id, rec.run_token, rec.fencing_token)
        return row["identity"] == actual.to_json() and row["task_id"] == rec.id

    def __call__(self, data):
        from .ownership_epoch import legacy_admission_guard
        with legacy_admission_guard(self.root):
            self._require_current_parents()
            return self._scan(data)

    def _require_current_parents(self):
        """An old bridge can have no children yet; inspect its canonical parent."""
        total = 0
        for state in ("running", "blocked", "pending"):
            directory = self.root / state
            try:
                fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
            except FileNotFoundError:
                continue
            try:
                self._directory(fd, private=False)
                names = os.listdir(fd)
                require(len(names) <= self.MAX_DIRECTORIES, "ownership_parent_inventory_bound")
                for name in names:
                    require(name.endswith(".json") and "/" not in name,
                            "ownership_parent_inventory_name")
                    task_fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK |
                                      os.O_CLOEXEC, dir_fd=fd)
                    try:
                        before = os.fstat(task_fd)
                        require(stat.S_ISREG(before.st_mode) and before.st_uid == os.getuid()
                                and not before.st_mode & 0o022 and before.st_nlink == 1
                                and before.st_size <= 131072, "ownership_parent_inventory_file")
                        raw = os.read(task_fd, 131073)
                        require(len(raw) <= 131072, "ownership_parent_inventory_bound")
                        total += len(raw)
                        require(total <= self.MAX_TOTAL, "ownership_parent_inventory_bound")
                        def unique(pairs):
                            value = {}
                            for key, item in pairs:
                                require(key not in value, "ownership_parent_inventory_duplicate")
                                value[key] = item
                            return value
                        task = json.loads(raw, object_pairs_hook=unique)
                        after = os.fstat(task_fd)
                        named = os.stat(name, dir_fd=fd, follow_symlinks=False)
                        fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
                        require(tuple(getattr(before, k) for k in fields) ==
                                tuple(getattr(after, k) for k in fields) ==
                                tuple(getattr(named, k) for k in fields),
                                "ownership_parent_inventory_changed")
                        require(isinstance(task, dict), "ownership_parent_inventory_schema")
                        if task.get("run_token") and task.get("attempt_state") in {
                            "dispatching", "accepted", "delivery_uncertain", "result_ready", "verifying"
                        }:
                            epoch = task.get("ownership_epoch")
                            require(isinstance(epoch, dict) and
                                    set(epoch) == {"version", "run_token", "fencing_token"} and
                                    type(epoch["version"]) is int and epoch["version"] == 1 and
                                    epoch["run_token"] == task["run_token"] and
                                    type(epoch["fencing_token"]) is int and
                                    epoch["fencing_token"] == task.get("fencing_token"),
                                    "ownership_legacy_parent_active")
                    finally:
                        os.close(task_fd)
            finally:
                os.close(fd)

    def _scan(self, data):
        root_fd = container = None
        total = 0
        try:
            root_fd = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
            info = self._directory(root_fd, private=False)
            require((info.st_dev, info.st_ino) == self.root_identity, "ownership_inventory_root_changed")
            try:
                container = os.open("durable-children", os.O_RDONLY | os.O_DIRECTORY |
                                    os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=root_fd)
            except FileNotFoundError:
                return True
            self._directory(container)
            names = os.listdir(container)
            require(len(names) <= self.MAX_DIRECTORIES and all(re.fullmatch("[0-9a-f]{64}", x)
                    for x in names), "ownership_inventory_directory_bound")
            for name in sorted(names):
                fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW |
                             os.O_CLOEXEC, dir_fd=container)
                try:
                    before = self._directory(fd)
                    events, size = self._events(fd)
                    total += size
                    require(total <= self.MAX_TOTAL, "ownership_inventory_total_bound")
                    scheduler = DynamicChildScheduler(audit_log=_InventoryAudit(events))
                    scheduler.replay()
                    for rec in scheduler._tasks.values():
                        if rec.parent_task_id is None or scheduler._ownership_read_only(rec):
                            continue
                        # Old pending writers can still be claimed by an older
                        # bridge without the registry. Quarantine them as well.
                        if rec.ownership is None:
                            return False
                        if rec.run_token is None:
                            continue
                        if not self._known_claim(rec, data):
                            return False
                    named = os.stat(name, dir_fd=container, follow_symlinks=False)
                    require((named.st_dev, named.st_ino) == (before.st_dev, before.st_ino),
                            "ownership_inventory_directory_changed")
                finally:
                    os.close(fd)
            require(set(os.listdir(container)) == set(names), "ownership_inventory_changed")
            return True
        except OwnershipError:
            raise
        except (OSError, ValueError, TypeError, KeyError, RuntimeError, RecursionError):
            raise OwnershipError("ownership_inventory_unavailable") from None
        finally:
            if container is not None:
                os.close(container)
            if root_fd is not None:
                os.close(root_fd)
