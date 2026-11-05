# VS Code + Hermes CVM Harness v2026.10.1

This bounded #149 source slice repairs the historical #150 audit. Its observations
are advisory. They cannot authorize scheduling, SDK/model use, hook execution,
retry, completion, skill approval, merge, release or deployment. Existing Herdr
TaskGraph, signed grants, budget, evidence/reviewer and recovery stay authoritative.

The textual harness convention is:

**Contract -> Plan -> Act -> Evidence -> Gate**

The audit checks that the marker and this rule occur in the actual rendered
stable prompt from both inspection samples. A disk heading, empty stable hash,
or a stable fallback prompt cannot substitute for that observation. Text presence
is not proof that an agent followed the rule or that effective policy enforces it.

## Read-only audit interface

On an independently authorized POSIX inspection host, the source entry point is:

~~~sh
python3 scripts/audit-agent-harness.py
~~~

It uses Hermes config/hooks-list/prompt-size inspection and the existing inspection
agent. This implementation was tested with mocked CLIs and private HOME fixtures;
no installed Hermes/SDK, host policy, model, LSP or real hook was run to validate
this source slice. A supported interpreter/CLI and fresh host evidence still need
separate verification. Non-POSIX command capture reports UNKNOWN.

The report schema is herdr-harness-observations-1. Individual observations retain
PASS, FAIL, UNKNOWN, NOT_CONFIGURED and UNSUPPORTED_KEY. Exit 1 means an observed
failure; exit 2 means incomplete/unknown conformance; exit 0 is reserved for complete
PASS. Unknowns never become PASS because the CLI exited successfully or failed
while reading an obsolete key. The audit never changes config to test a key.

Every installed profile directory is considered independently of its config or
SOUL.md presence. Required missing files fail. Unknown/aliased/oversized inventories
remain incomplete. At most 16 named profiles and 128 directory entries are inspected.
Reports label profiles by ordinal rather than exposing host names or private paths.

Runtime fingerprints require nonempty stable text, positive bounded byte counts,
valid SHA256 values and matching samples. Tool counts use integers (hard ceiling 100,
ideal 80); both tool-schema samples and unmapped-tool lists are checked. The only
allowed unmapped meta-tools remain tool_search, tool_describe and tool_call.
These observations do not assert provider cache hits or effective tool authority.

## Hook consent and behavior are different evidence

For each profile the audit matches the exact pre_verify event AND exact configured
command. A path suffix, another event, duplicate/contradictory entry, matcher or
unrecognized output grammar cannot approve that pair. The supported hooks-list
shape is an event heading and command row, for example:

~~~text
  [pre_verify]
    - <exact command> (timeout=10.0s, ✓ allowed)
~~~

It follows Hermes' public hermes_cli/hooks.py event/command rendering. A changed
format remains UNKNOWN instead of inheriting a previous event. This parser fixture
is not a claim that a particular installed SDK version was freshly verified.

An owner-only executable at the expected hook path proves only file metadata.
No reviewed external hook content/effective behavior was supplied with #150, so
hook.behavior_status remains UNKNOWN, including for a no-op executable. The audit
never executes the hook, accepts a self-declared hash as trust or changes allowlists.
Consequently the overall report currently cannot claim full conformance PASS.
The supported hard-stop and hooks_auto_accept settings are configuration observations,
not a replacement for InvocationGuard or the original acceptance oracle.

## Host verification workspace

When /tmp is a bounded tmpfs, use a private, task-owned test directory on the
approved host filesystem instead of relying on the default temporary location.
Set TMPDIR to that verified directory and pass a fresh, unused child directory
to pytest --basetemp, so unrelated temporary data is never reused or cleared.
Keep every existing disk admission floor and margin unchanged. Never delete
another task's temporary tree, move archives or alter foreign task files to make
room. This guidance grants no cleanup, reclaim or storage-change permission.

## Bounds and privacy

The POSIX command collector caps stdout and stderr at 65536 bytes each, uses a 30s
bound, kills its owned process group even after a successful leader, and reaps
that direct leader. The unreaped leader anchors the group identity until signaling;
unsupported waitid/WNOWAIT platforms or incomplete cleanup remain UNKNOWN. This
is not a physical proof of namespace closure or orphan reaping by init. Invalid UTF8 and
malformed/oversized JSON fail closed. SOUL reads are bounded to 65536 bytes; reports
are bounded to 65536 bytes, with a fixed UNKNOWN fallback if needed. These are byte
limits, not character or token counts.

No raw CLI errors, model/tool names, profile names, credential-bearing paths,
SOUL/profile contents or prompts are printed. Only fixed diagnostic codes,
validated numeric/hash observations and metadata are projected. .env is checked
by metadata only; its contents are never opened. No secret discovery or arbitrary
unknown-secret recognition is claimed.

Issue #149 stays open. Physical post-write LSP behavior, supported-key/effective-policy
proof, approved SDLC skill conformance, physical isolation and connected E2E/soak
remain outside this source slice and under their existing owners. Do not change
#185, held accounting, capacity thresholds or production policy to make this audit
PASS. Source tests and merges grant no operational activation.
