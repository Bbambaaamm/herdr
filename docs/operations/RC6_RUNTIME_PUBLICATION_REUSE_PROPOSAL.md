# #132 RC6 immutable runtime publication — non-authoritative proposal

This is a **proposal**, not a privileged publication request. The legacy
`p0-5035d92-test` and `p0-8e34c6f-test` records are reviewed as historical
evidence only. Do not copy their manifest hashes into an approval without
independent source and exact-head verification. No credentials, live profile,
operator grant, or reusable publication authority is stored in Git.

## Findings from staging inventory (2026-11-10)

- `p0-5035d92-test`: root-owned `code`, `hermes`, `python` directories exist;
  the old request digest and manifests match its old retained record.
- `p0-8e34c6f-test`: only `code` remains; `hermes` and `python` are absent.
- Both retained records use the historical `herdr-runtime-publication-1`
  **without** `record_sha256`. The current `validate_publication_record()`
  requires `herdr-runtime-publication-record-1` and rejects both.
- Historical Hermes (24,188 approved files) and Python (3,856 approved files)
  inventories can help the operator compare proposed new manifests; they do
  **not** prove byte-identical current runtime or authorize reusing inodes.
- Current `/etc/herdr/host-policy.json` still uses schema 1 and references
  other immutable releases; its issuer SHA pin does not match.

## Exact proposed operator sequence (separate approval required)

1. Verify installed immutable RC6 release and its exact payload SHA.
2. Obtain independently reviewed **current** code inventory, not the old
   `p0-5035d92-helper` code tree. Validate all directly executed shims.
3. Independently verify unchanged Hermes/Python contents, file modes,
   executable lists, pins and approved source ancestry against the historical
   inventories. A manifest equality check is not physical byte attestation.
4. Prepare a **new** root-owned publisher request with a unique version,
   three reviewed current trees, and the original `herdr-runtime-publication-1`
   request format. Run the existing `publish-herdr-runtime.py --configuration`
   *without* `--publish` for preflight from trusted immutable code only.
5. After independent review and explicit operator authorization, use the
   existing immutable privileged publisher; it copies into fresh immutable
   root-owned inodes and emits a valid new `record_sha256`. **Do not fabricate
   a record for historical paths, adopt old inodes, or mutate old records.**
6. Verify published record and file manifests with current native validators.
   Only then propose schema-2 host-policy and issuer SHA pin updates as a
   separate operator authorization. Do not enable worker/model dispatch.

The existing publisher deliberately performs a **fresh copy**. Zero-copy
migration has *not* been proven safe; do not optimize this away in this PR.

## Offline check

From a reviewed Git checkout for development only:

`python3 -I -B scripts/audit-herdr-runtime-reuse.py`

The checker reads only the two fixed historical root-owned record/request pairs
using the existing protected root reader. It reports a potential reuse of
*evidence*, not authorization and not verified source bytes. Root-level execution
must use only a subsequently published immutable reviewed entrypoint.

**Acceptance:** unit tests, repository/source manifest and exact-head CI,
independent security review; draft PR only. No root publish, schema migration,
release cutover, credentials, provider calls, scheduler admission or queue edit.
