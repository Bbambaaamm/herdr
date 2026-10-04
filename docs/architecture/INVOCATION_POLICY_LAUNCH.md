# Host invocation policy launch

Herdr owns physical launch and derives no permission from a prompt, TaskGraph field, environment variable or remote metadata. The host supplies a HostPolicyLaunchFactory backed by accepted consumer/provider authorization and exact approved code/runtime source manifests. Root and managed-child launch deny before pane creation when that host authority is unavailable. The embedding/configuration and live activation remain issue #78 work; this change does not install or deploy a runtime or modify credentials.

## Frozen execution bytes

ApprovedTree freezes a copied immutable manifest at construction. FrozenTree walks source components through held no-follow directory descriptors, admits bounded regular files only, checks every raw SHA-256 while copying, and creates a private independent storage tree outside worker writable roots. Explicit executable files are selected by the host manifest. A source checkout edit, rename or updater cannot change copied bytes. Complete inventory checks reject missing, extra, symlink, FIFO and changed entries; files and total bytes are bounded.

The independently copied roots are mounted by retained descriptors at the fixed policy code, Hermes and Python locations. No read-only alias of a writable runtime installation is used. Mount verification requires exact device/inode, read-only roots, no writable descendant mounts and non-host mount/PID namespaces. The host storage and copies remain outside the worker write surface for the lifetime of its owned pane. Host storage is part of the trusted host boundary, never a directory selected by the task.

The launch helper reopens each held host descriptor before bwrap creates namespaces, rechecks type/device/inode and admits exactly the declared descriptor/target pairs. Missing, duplicate, unused or changed descriptors deny. Managed workspaces also use their held original inode. Policy launches mask /run, make Hermes session/cache/log state ephemeral and pin PATH to the copied policy shim.

## Same-inode sealing order

1. Accept node identity, tools, permissions, workspace and host grant.
2. Create independent code/runtime copies and an empty exclusive 0600 grant inode in protected host storage.
3. Create the owned pane with exact consumer/agent/parent/task/run/fence environment.
4. Start bwrap with read-only descriptor binds and verify physical mount/PID identity.
5. Observe the actual runtime assurance and sign through the retained grant O_RDWR descriptor.
6. Fsync/read back/signature-verify the same inode and recheck its mounted read-only inode and digest.
7. Publish protected host policy evidence before recording agent-start intent and invoking Hermes.

The private signing key stays in the host object and is discarded after sealing. Only the signed public bundle is exposed to the worker. Version 2 evidence records grant/bundle/code/runtime hashes, every mounted tree inode, bundle inode, process start ticks, exact identity and sandbox attestation digest. Restart verification reopens those exact mounts and the signed bundle, checks namespace/environment/runtime assurance and rejects replaced processes or writable descendants. Historical completion may validate the grant at the protected launch timestamp; this never extends live invocation authorization. The protected scheduler attestation persists the bounded proof and revalidates exact consumer/parent/task/run/fence and every digest during replay; malformed or cross-attempt records fail closed. A legacy namespace-only record remains distinct from sealed invocation policy and cannot supply semantic acceptance.

Network assurance is measured: the retained host namespace is GLOBAL; an isolated namespace is NONE. This implementation never claims provider-only network enforcement or credential isolation. Enabled process grants therefore deny. Native file tools can operate within admitted scope; privileged operations and an approval broker require their separately proven host embedding.

## Delegation and lifecycle

prepare_child requires an accepted typed parent grant. Consumer/parent identity, lifetime, tools/arguments/paths, provider/privacy/credential and process ceilings must remain a mathematical subset; legitimate child workspaces must already be covered by host authorization. No automatic parent filesystem expansion occurs.

Root fencing increases for a new semantic attempt and is retained during ambiguous-delivery reconciliation. Scheduler identity remains authoritative for children. A protected queue field or browser status never substitutes for a policy mount or semantic acceptance evidence.

Prepared host objects and copies remain retained across ambiguous prompt outcomes. Cleanup of only factory-owned objects is allowed after closure of the exact owned pane has been proven; an unknown outcome retains resources for reconciliation. Recovery after host-process loss must reopen and prove retained objects from protected host evidence, without manufacturing a new grant, prompt, attempt or budget. Issue #85 owns semantic acceptance, #86 owns execution plans and #87 owns cumulative retry/budget accounting.

Every unexpected descendant mount beneath a frozen policy/runtime root is rejected, including read-only shadows. A read-only visible shadow can still refer to mutable external backing bytes and never proves the approved FrozenTree inventory. The real bwrap regression attempts a separate RO bind over approved module.py and denies sealing before agent start.
