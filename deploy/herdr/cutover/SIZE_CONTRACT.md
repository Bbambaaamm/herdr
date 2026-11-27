# Transaction size audit (#266 / step 4B)

RC9 `3b014011beac10944b9791c90455f6a5c2bbc7e8` accepted a 119,973-byte
dashboard snapshot but read its aggregate Base64 backup through the same
131,072-byte reader. Base64 alone adds 159,964 characters. The protected real
backup was 178,649 bytes, root:root 0600, one link, SHA-256
`508088706b14a3c920602020b9a7c38e9f2c28242ebe3c30806bd0373cee97c5`.
It failed before journal creation, quiescence, override reconciliation or service
changes. Candidate/pinned-archive preparation had already happened; unchanged
current never means that no files were written.

## Lifecycle and ceilings

| Object | Count / writer | Reader and restore contract | Failure |
|---|---|---|---|
| Dashboard snapshot | 1; production publisher <=131072 B | production decoder and individual capture <=131072 B | reject before journal |
| Bridge | 1; production publisher <=131072 B | individual capture <=131072 B; actual readiness additionally validates closed telemetry | reject before journal |
| Public marker | 1 | capture AND trusted-state reader <=4096 B; exact deployed identity | reject before journal |
| Units | exactly 6 | each <=131072 B; required, preserved bytes/mode/owner; installed/candidate hashes checked independently | reject before journal |
| Consumers | exactly 5 | each <=131072 B; required for versioned baseline; parse/permission/config digest checks remain | reject before journal |
| Nginx route | 1 required | <=131072 B; exact authenticated route hash | reject before journal |
| Capacity override / fence | 2 slots | each <=131072 B; override presence must match mode; initial fence must be absent | reject before journal |
| Systemd authority | 1; capture v1 | <=262144 B canonical; six closed unit records, seven named external entrypoints; bounded facts, commands, environments, drop-ins and dependency inventories | reject before write |
| Aggregate authority backup | 17 fixed paths, v2 | separate root:root 0600 reader; maximum 3238168 B | reject before write / fail closed on corrupt readback |
| Transaction journal | backup + path/hash binding, v2 | maximum 3246360 B; exact backup hash AND full document equality; same restore-plan validation | retain on failed validation; no replay |
| Deployment/preparation evidence | bounded metadata, no raw telemetry | 524288 B budget; metadata is distinct from a committed deployment marker | retain; never infer activation |
| Historical recovery | existing exact RC8-to-RC12 identity and evidence gates | its preflight uses the shared planner; existing special authorization remains mandatory | existing fail-closed behavior |
| Release archive | <=64 MiB compressed; <=8192 members, <=64 MiB/file, <=256 MiB total raw, <=320 MiB stream | bounded extractor; compressed-copy loop stops at initial size + one-byte growth probe; stable identity/mtime/ctime/link count | no unbounded copy; reject |

An ordinary capture has exactly 17 named paths, not an attacker-supplied path
list. Individual snapshot absence is role-specific: optional telemetry and
initial legacy overlays may be absent; six units and Nginx cannot. The marker
and five consumer files are required for a versioned baseline. The transaction
start fence cannot already exist. No restore helper follows arbitrary JSON
paths or automatically replays a journal.

## Derivation and resource admission

`BASE64_MAX = 16 * 4*ceil(131072/3) + 4*ceil(4096/3) = 2801688`.
This conservatively includes the optional slots, although the fence is absent.
Authority has an independent 256-KiB canonical budget. JSON envelope reserve is
`17*(6*1024+256)+65536 = 174336` bytes, covering worst-case escaped paths,
bounded numeric ownership/mode metadata, release identity, six service states
and envelope fields. Consequently backup maximum is 3,238,168 bytes; journal
adds 8,192 bytes for its root-owned backup path/hash reference.

The shared serializer validates before write, then exercises the same strict
JSON parser and restore validator as the reader. Duplicate keys, non-finite
numbers, invalid/noncanonical Base64, changed document types, foreign paths,
over-limit inputs and collections fail closed. JSON has depth <=64 and at most
65,536 structural delimiters outside strings, bounding node allocation before
JSON parsing. Aggregate reads validate all ancestor types/ownership, no-follow
walks, one link, exact 0600/root ownership, bounded actual bytes, stable FD and
reopened named identity; access-time updates do not invalidate a snapshot.

Transaction reserve is
`2*(BACKUP_MAX+JOURNAL_MAX)+524288+65536 = 13558880 B`.
This covers retained documents plus atomic siblings, evidence and filesystem
block slack. The previous 8-MiB allowance does **not** cover the new worst case.
Existing retained artifacts are already reflected in measured free space; none
is deleted to pass admission. The single filesystem-aware planner assigns
archive, candidate, transaction and runtime reservations to their actual
capacity domains. The host root retains `max(12GiB,10GiB+128MiB+backup_peak)`;
backup peak remains `3*max(512MiB,newest ZIP size)+1GiB`. Separate backup and
offsite domains additionally retain their physical preparation peak. Bind
mounts sharing proven device/fsid space are not counted as independent disks.
The previously approved two-archive / three-candidate conservative envelope
and additional rollback-tree-sized safety margin remain explicit. Existing
source/controller/rollback artifacts are already in measured usage; safety
margins are distinguished from future writes. See [CAPACITY_CONTRACT.md](CAPACITY_CONTRACT.md).

Temporary admission precedes even archive verification's extraction, using
the bounded extractor's 256-MiB raw and 8194-object ceilings plus destination
block overhead and 64-MiB safety margin. Tmpfs additionally needs verified
physical/cgroup memory headroom. Live candidate allocation is measured from
bounded temporary extraction with 4-KiB rounding and directory overhead;
larger destination blocks receive a per-object adjustment. The maximum
admitted 4-KiB candidate metric remains 320 MiB. Apply repeats shared preflight
under the deployment lock before pinning
or candidate installation, then checks fresh capture, serialization, reserve
and readback before runtime mutation. Telemetry growth between preflight and
apply is not grandfathered in.

## Preparation and reconciliation

Each apply retains a separate root-owned `*-preparation.json`, identifying source
digest, pinned path, candidate path and preparation phase. These files are not
successful deployment state. Candidate installation validates an existing tree
before reuse; each pinned copy has a unique name. Failure evidence and prior
immutable candidates remain; there is no automatic deletion of unknown data.

For operator reconciliation, use `transaction_contract.Contract(controller_globals)`
from the approved immutable controller. `read(transaction_path, journal=True)`
verifies both bounded v2 documents and their hash/content binding;
`validate(document, journal=True)` yields only the closed, bounded restore plan.
These functions do not write or start services. Operator reconciliation still
requires explicit host authorization, quiescence and the existing fence/permit
protocol. Never edit a retained document to make it pass. Previously retained
RC9 v2 backups retain their original bytes/hash; schema stays version 2.

## Verification levels

The new size suite covers byte boundaries, valid large v2 documents, metadata,
links, growth, corruption, serializer/readback/restore validation, capacity and
preflight/apply drift. B09 tests the exact aggregate reader ceiling and separately
proves that a byte-valid but schema-invalid document is rejected: the conservative
envelope budget is not a promise that every byte length admits a valid schema.
B23 maps to the real fork/SIGKILL transaction test; B30 includes preserved
historical recovery gate tests. B29 is a distinct Linux deployment simulation:
real archive/manifest, immutable controller, pinning/install, full preflight,
actual authority capture, real v2 documents/readback, readiness and rollback.
Ownership/privileged filesystem permission, systemd-manager and HTTP operations
are isolated adapters; production telemetry contracts validate synthetic data
with the observed 119,973-byte snapshot size. This is not privileged live-systemd
acceptance or live staging deployment. Those remain NOT_RUN in step 4B.
