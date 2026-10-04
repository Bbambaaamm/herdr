# Portable Agent Skills registry v1

Issue #72 consumes the accepted #69 Capability Registry. It supplies a host-side,
provider-independent resolver for #73's context compiler; live embedding and
cross-provider E2E evidence remain #76/#78. A skill is versioned context data.
Tool declarations never grant authority or execute a script.

## Package contract

A package directory has the skill name, a strict manifest.json, SKILL.md and
optional scripts/, references/ or assets/. Names follow Agent Skills' lowercase
hyphenated form, at most 64 characters. Versions use SemVer, including prerelease
and build identifiers. Manifest schema_version is 1.0.0.

The manifest records name/version/description, publisher, credential-free HTTPS
source_uri and authoring_base_revision. The latter identifies the authoring
baseline, not a claim that new package bytes already exist in that commit.
A separate host SkillApproval pins the package hash, name/version, publisher,
source URI, actual approved immutable Git revision and reviewed trust tier.
Approval must come from the host review/release authority; package self-claims
and successful lint do not approve anything. The repository deliberately ships
no automatically activated approval catalog.

Every declared file binds its POSIX relative path, exact byte size, SHA256,
media type and data class. The canonical package hash covers the entire manifest,
including all file hashes. Paths cannot escape the package. Limits: 64 files,
2 MB aggregate,256 KB per resource,64 KB body,32 KB manifest. Resources not declared
in the approved manifest cannot be loaded. Text is UTF-8; binary assets use
base64 only when explicitly requested.

This implementation accepts a documented subset of Agent Skills YAML frontmatter:
name and description plus optional license, compatibility and allowed-tools,
with JSON-quoted scalar values, one per line. Nested YAML, tags, aliases, duplicate
fields and implicit coercion are rejected. Name/description must match the
manifest. allowed-tools is informative and cannot alter an admitted scope.
This is an explicit supported subset of the upstream YAML specification.

## Resolution and child context

Construct SkillNodeContext from the host's exact consumer/task/run/attempt/fence,
SpecPolicy hash, frozen CapabilityScope and RegistrySnapshot. The node grant
must be a subset of both parent and consumer grants. Compatibility checks chosen
executor/provider/capability, tools, permissions, features, platform, text input
and the common region/data policy intersection. This is static context
compatibility; it does not claim provider availability or grant execution.

ConsumerSkillPolicy pins allowed package hashes and trust tiers, records disabled
optional skills, and separately pins mandatory project security skills.
The consumer must match the node. A missing, disabled, incompatible or oversized
mandatory skill fails closed. Optional skills may be omitted with an explicit
reason code; turning off optional skills never removes mandatory instructions.

SkillRegistry holds each accepted package directory open. Manifest-only discovery
produces a bounded 16 KB index with name, short description, version and hash.
It opens no body, script or resource. resolve takes explicit SkillRequests with
bounded selection reasons and exact needed resource paths. Only those bodies and
resources are loaded. File components are opened relative to the held directory
with no-follow flags; only regular bounded files with the approved digest pass.
Replacing the original directory name cannot redirect the held package.
Tampered selected content fails; unneeded content never enters the model request.

The output is an immutable SkillBundle. Its provider-independent envelope carries:
- exact node/platform/registry/grant binding and consumer skill policy hash;
- host-supplied policy layers in stable Herdr → consumer → node order;
- selected bodies/resources explicitly marked context_data;
- exact package version/hash and external approval provenance.

A project's instructions, including a request to enable tools or delegate, remain
context data. Neither skill text nor declaration rewrites the policy layer or
scope. Physical invocation enforcement belongs to #76. Providers receive the same
envelope; #73 owns token measurement, redaction, task artifacts and provider
serialization. The resolver enforces a byte budget, up to256 KB, and never silently
drops mandatory content to fit it.

Telemetry excludes loaded body/resource bytes and reports the exact binding,
selected versions/hashes/provenance, reasons and rejected/not-needed reason codes.
Consumers must retain this trace with the frozen context plan. A changed package,
approval, policy, task/run/fence or RegistrySnapshot changes the frozen binding.

## Authoring and review lifecycle

1. Author a small SKILL.md focused on relevant context, verification and conventions.
   Put infrequently used templates/examples in references/, scripts in scripts/
   and binary resources in assets/. Avoid copied global policy and all secrets.
2. Record tool/permission/capability/feature requirements and supported platforms.
   Declarations describe needs; they cannot activate tools.
3. Hash exact resource bytes and create the strict manifest. Increment SemVer for
   changes and record the exact authoring baseline.
4. Run scripts/lint-skills.py on the package. Lint validates all declared content,
   including unused resources, but never executes scripts or grants trust.
5. Review source, provenance, prompt injection and data classification. Approve
   the exact immutable released revision plus canonical package hash through
   host-owned SkillApproval. Do not take approval from a worker-writable catalog.
6. Pin that hash in the consumer policy; add mandatory project security pins where
   required. Select optional skills/resources for the current node only.
7. Store the resolution trace and bundle hash in #73's immutable context plan.
   Runtime activation is accepted only after #76/#78 evidence.

Initial migrated packages are repo-research, coding-handoff and review-evidence,
all 1.0.0. They contain generic source inspection/handoff/evidence workflows and
small lazy templates; no consumer credentials, direct production actuation or
provider-specific SDK logic. The coding handoff validator is inert package data.

The package reader currently requires a POSIX host with openat/no-follow directory
semantics. Skill content/rendering is provider-neutral and its declared target
platforms are independent of the host reader. Unsupported host primitives must
not be emulated by unsafe path-following reads.

Reference: [Agent Skills specification](https://agentskills.io/specification).

Authoring lint decodes every declared textual resource, including application/json, before approval. The source manifest hashes exact skill bytes and declared media independently of filename extension, including PNG/JPEG/octet-stream assets and text line endings. Undeclared or changed skill source files cannot be included by the source-manifest generator. Legacy tools feature spelling normalizes to tool_use before compatibility and hashing, matching the shared registry.

## Exhaustive lint and bounded resolution

CI discovers every direct package directory under skills and lints each package.
Source-manifest traversal rejects symlinks, FIFOs and other nonregular entries,
including broken links, before accepting a release payload. Declared capability
requirements must match the selected executor's capability, in addition to
remaining inside the grant.

Resolution accounts for exact serialized JSON bytes incrementally. It rejects
an over-budget resource from its declared size before reading or base64 expansion,
and checks text escaping before loading the next resource. Mandatory content
cannot bypass the same budget. Selected telemetry includes resource paths,
digests, sizes, media types and data classes; resource bytes remain excluded.
