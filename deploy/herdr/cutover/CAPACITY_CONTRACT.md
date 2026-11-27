# Filesystem capacity admission v2 — #269 / step 4E

RC10 `310f9429b3da50a4e23d24c2a5329a0af2ebc80d` imposed the complete
13,590,480,494-byte disk requirement on every path, including a separate
4,061,155,328-byte `/tmp` tmpfs. Even empty tmpfs failed. The exact baseline
function is retained in a hash-bound test fixture, so shallow CI can reproduce
red-before-green without fetching or executing mutable historical code.

`transaction_contract.capacity()` remains the public shared admission entry;
`filesystem_capacity.plan()` is its implementation, not a second policy.
Both normal and historical recovery controller paths use it. There is no
maintenance, cleanup, policy modification, new service or provider call.

## Allocations and lifetimes

All sizes below are **allocated** budgets (rounded to the destination block),
not just logical bytes. Objects already present reduce measured free space;
they are not silently counted again as new writes. Existing incident evidence,
immutable releases, controller, original artifact and rollback material remain.

| Object / operation | Actual path/domain | Bound / inodes | Lifetime and overlap / failure |
|---|---|---|---|
| Official transport ZIP | operator download location | official verified size; existing | outside controller; retained verification material; no future allocation claim |
| Original archive | approved input stage / incoming | <=64 MiB; 1 | existing, hash/closed payload validation; never a cleanup candidate |
| Immutable controller | approved incoming child | bounded payload; <=8194 objects | existing before preflight; retained; operator bootstrap needs its own pre-write admission |
| Archive/manifest verification | fixed `/tmp` | <=256 MiB data +8194 destination blocks | private TemporaryDirectory; verified sequentially, no overlap with next verification; bounded extractor owns cleanup |
| Comparison extraction | fixed `/tmp` | same bound; <=8194 objects | follows archive verification; actual 4-KiB allocation checked against bound; removed before final report |
| Pinned archive | incoming | archive size rounded; 1 | preparation through activation/rollback; source survives failed copying |
| Candidate installation | releases / `.staging-*` | measured 4-KiB metric <=320 MiB, adjusted per object for larger blocks | staging promoted by rename; failed staging cleanup; valid existing candidate verified, never deleted by admission |
| Candidate safety | releases | two additional candidate allocations | explicit prior approved conservative margin; not a claim three copies are always created |
| Existing RC6 / legacy | verified previous path | measured blocks, bounded <=8194 objects | retained; already charged to free space; one additional tree-sized margin preserves prior conservative plan |
| Authority backup / systemd authority | deployment state | backup3238168; six-unit authority262144 inside it | retained v2 root-only document; hash and restore plan checked on readback |
| Journal v2 | deployment state | <=3246360; 1 | created before quiescence; removed only after successful closure; retained on incomplete rollback |
| Atomic backup/journal/evidence siblings | deployment state | unchanged13558880 aggregate reserve, 64-object accounting | includes two document pairs, evidence524288 and65536 block slack; larger blocks get extra per-object overhead |
| Bridge, dashboard snapshot, marker | their actual mutable parents | snapshots131072 each, marker4096 | bounded publishers and atomic restore; separate runtime domains receive full conservative restore reserve |
| Consumers / units / Nginx / fence | their actual parents | exactly17 captured paths; per-file131072 except marker | writes/rollback after journal; same root reservation deduped per domain; no orphan controls removed by planner |
| Success / failed archive evidence | deployment state | archive-size bound; 1 | incoming/state rename when shared; otherwise bounded copy, source stability, digest readback, mode preservation, fsync and publication before source removal |
| Hermes local backup | `/home/agentops/backups/hermes` | peak policy below; bounded4096 inventory | independent maintenance may run concurrently; planner observes, never starts backup |
| Offsite plain + encrypted backup | `/home/agentops/backups/hermes-offsite` | same full peak on separate domain conservatively | both coexist during encryption, plaintext then removed by existing maintenance; admission does not change retention |
| Recovery temporary files / evidence | same fixed temp, incoming, release and state roles | same archive and transaction bounds | exact RC8-to-RC12 authorization remains; no new replay/recovery authority |

## Policy and phase arithmetic

Host root keeps the complete existing policy:

`peak = 3*max(512MiB,newest_backup_size)+1GiB`

`host_policy = max(12GiB,10GiB+128MiB+peak)`.

Even with backup directories on another filesystem, root keeps this policy
because installed #126 maintenance observes `/`. A separate backup/offsite
domain ALSO reserves the full preparation peak; shared backup/offsite paths
reserve it once. The factor3 and1-GiB safety allowance are unchanged.

Per domain, allocations are summed within each of verification, preparation,
activation and rollback, then the **maximum phase** plus named applicable
reserves determines required bytes. The two candidate safety copies remain
explicit reserves. Incoming archive and retained archive can coexist during
cross-filesystem publication. A shared device/fsid is budgeted once; minimum
available bytes/inodes across its views is used. Every domain requires at
least32768 free inodes; object needs are independently included. No current
free space can be made larger by ignoring a view with a smaller quota bound.

The fixed temporary requirement on4-KiB blocks is
`256MiB +8194*4096 +64MiB =369106944 B` (the extractor caps created objects,
including auto-created parent directories, at8193 plus its private directory).
Its maximum raw256MiB, inflated stream320MiB, compressed64MiB, single file64MiB
and8192 members remain unchanged. Verification copies are sequential, so they
are not added together. Cleanup failures leave usage visible in the next fresh
measurement; SIGKILL is not claimed to run Python context-manager cleanup.

Tmpfs memory admission combines all simultaneous planned pages across tmpfs
domains plus their applicable margins,64MiB maximum file read,64MiB parser /
inventory allowance, four transaction working copies and128MiB memory guard.
Disk floor and already-used rollback bytes are not falsely treated as new RAM
allocations. MemAvailable is capped by memory.max-minus-memory.current at every
visible enclosing cgroup-v2 ancestor. Hierarchy root has no memory.max interface;
its physical bound is MemAvailable. Hidden/unverified hierarchy, unreadable
nonroot limits or insufficient headroom reject. No swap is counted as RAM.

## Filesystem authority and drift

Directories are pinned via descriptor-based no-follow walks; a missing target
uses its nearest existing pinned ancestor. `/proc/self/mountinfo` is bounded,
decoded, matched by deepest mountpoint and corroborated against the descriptor's
device plus fstatvfs fsid. Mount table and named-directory identity are checked
again. Mount ID attests topology but does not establish independent free space.
Bind views sharing proven device/fsid are grouped; distinct views remain in the
topology report. Read-only mounts, overlay/btrfs/unknown storage, project quotas
and unverified capacity semantics fail closed. ext4/xfs/tmpfs are supported;
enabled user/group quotas require successful read-only quotactl_fd results with
valid block/inode fields, including root/agentops and relevant service groups.
Unreadable/unsupported quota queries are NO-GO, never assumed unlimited.

Preflight checks temporary admission before the verifier's first allocation,
then checks actual extraction allocation and the full transaction plan. Apply
performs fresh preflight under its existing deployment lock, compares topology
and recomputes free bytes, inodes, backup growth and memory before preparation,
pinning, candidate install, journal writing and initial runtime mutation.
Topology comparison excludes changing free-space values. Failure before journal
does not imply absence of prepared files; existing preparation evidence remains.
Rollback does not demand a new full host floor before restoring reserved authority.

Report `capacity.schema_version=2` has per-domain identity, type, paths/roles,
mount IDs, total/available bytes, inodes, allocation phases, named reserves,
requirements, headroom/deficit, physical feasibility and PASS/FAIL reasons.
Tmpfs rows also include observed and required memory. Legacy scalar
`required_bytes` and `observations` remain display-compatible but cannot prove
capacity across filesystems. Consumers must use each domain's requirement.

## Verification matrix and limits

C01–C27,C31,C32: `test_filesystem_capacity.py`, including exact original RC10
failure, modeled staging / separate paths / binds, drift, byte/inode boundaries,
backup growth, max envelope, memory/cgroup and real Linux descriptor observation.
C28,C29: `test_cutover_rehearsal.py::test_B29_complete_isolated_deployment`
promotion/rollback, now using distinct disk2049/tmpfs42 capacity observations.
C30: `test_B30_historical_recovery_real_preflight_and_apply`.
Original T/W/B and #126 tests remain required. Cross-device retention additionally
tests corruption refusal with source/evidence preserved and successful400-mode
publication. Original production capture/serialization/restore functions remain.

These are isolated tests using actual files/controller functions and safe OS,
systemd, HTTP, topology and memory adapters. A modeled bind or memory budget is
not a physical mount/cgroup acceptance. Physical split-mount/systemd staging
acceptance is NOT_RUN until separately authorized deployment. The recorded
staging disk/tmpfs figures are a model input, not a fresh protected preflight;
quota and current memory observations must pass on the actual approved host.
