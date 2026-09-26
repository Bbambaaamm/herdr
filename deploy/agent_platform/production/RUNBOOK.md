# Phase9 quantadmin activation runbook — NOT executed by agentops

Q1/Q2/Q3 are approved. Actual privileged activation remains ACTIVATION_BLOCKED
until quantadmin runs these steps on the intended host. No production password
exists in this repository. Phase8 refusal templates are unchanged; this directory
is the separately reviewed production configuration. Do not install demo.py.

## 1. Confirm host, release, topology and collision inventory

Use Bash in a private, non-recorded admin terminal; disable shell tracing (`set +x`). Never
paste password, complete Nginx config, source rows or logs into chat. No terminal
session recording during credential generation. Commands below are quantadmin
commands; `sudo` here is documentation, not authorization for agentops to run it.

```sh
set -euo pipefail
set +x
umask 077
RELEASE_SOURCE=/home/agentops/workspaces/majak/agent-platform-impl
printf 'Confirm source release path: '; read -r confirmed
[ "$confirmed" = "$RELEASE_SOURCE" ] || exit 1
git -C "$RELEASE_SOURCE" status --porcelain
git -C "$RELEASE_SOURCE" rev-parse HEAD
printf 'Type exact reviewed commit hash: '; read -r RELEASE_COMMIT
[ "$(git -C "$RELEASE_SOURCE" rev-parse HEAD)" = "$RELEASE_COMMIT" ] || exit 1
[ -z "$(git -C "$RELEASE_SOURCE" status --porcelain)" ] || exit 1
printf 'Type absolute existing HTTPS vhost file path: '; read -r VHOST
case "$VHOST" in /etc/nginx/sites-available/*) ;; *) exit 1;; esac
[ -f "$VHOST" ] && [ ! -L "$VHOST" ] || exit 1
printf 'Confirm target /opt/agent-platform/release and /etc/agent-platform: '; read -r confirmed
[ "$confirmed" = '/opt/agent-platform/release /etc/agent-platform' ] || exit 1
sudo nginx -t
sudo ss -ltnp 'sport = :3010'
curl --fail --silent --output /dev/null http://127.0.0.1:3000/
printf 'Type HTTPS origin (no path), e.g. https://approved-host: '; read -r ORIGIN
case "$ORIGIN" in https://*) ;; *) exit 1;; esac
[ "$(curl --silent --output /dev/null --write-out '%{http_code}' "$ORIGIN/")" = 200 ] || exit 1
```

STOP if 3010 is occupied, unit names/accounts/paths belong to another application,
or root/3000 does not work. Do not kill anything or alter QuantLab. Privately inspect
`sudo nginx -T` including recursive includes (do not log/copy its output). Require
exactly the intended TLS server, unchanged root location, no existing /agent-platform
exact/nested/prefix routes, no @agent_platform_auth_required/@agent_platform_failed,
no rate zone agent_platform_rate, no server-level rewrites/auth/error routing that
bypasses these paths. Named-location duplication is NOT reliably rejected by -t.
Check for shared-vhost inheritance, regex/nested prefixes and normalized URI routes.

On a repeated invocation recognize only your exact prior manifest/hashes; verify,
do not overwrite drift. Save a root-only baseline hash and reviewed one-line include
change outside Git. A repeat after successful installation should skip installation,
credential generation and route insertion; run validation/smoke instead. Existing
unexpected state is a STOP, never automatic repair/overwrite.

## 2. Install immutable reviewed release and provision separate principals

Precondition: `/opt/agent-platform/release` absent, or already the exact reviewed
release (then skip this block). No shared QuantLab release symlink. Prepare an
archive of ONLY the reviewed production package and launch/templates from the clean
commit. Do not copy workspace secrets, `.git`, venv, fixtures or user config.

```sh
# Before accepting existing identities, confirm they belong only to this deployment.
getent group agent-platform-read >/dev/null || sudo groupadd --system agent-platform-read
getent group agent-platform-auth >/dev/null || sudo groupadd --system agent-platform-auth
if ! id agent-platform-web >/dev/null 2>&1; then
  sudo useradd --system --no-create-home --home-dir /nonexistent --shell /usr/sbin/nologin \
    --gid agent-platform-read agent-platform-web
fi
[ "$(id -u agent-platform-web)" != 0 ] || exit 1
sudo usermod -a -G agent-platform-auth agent-platform-web
# Verify the actual unprivileged Nginx worker identity first (Ubuntu normally www-data).
printf 'Confirm actual nginx worker account www-data: '; read -r confirmed
[ "$confirmed" = www-data ] || exit 1
sudo usermod -a -G agent-platform-auth www-data
sudo install -d -o root -g root -m 0755 /opt/agent-platform/release
sudo install -d -o root -g agent-platform-read -m 0755 /etc/agent-platform
sudo install -d -o agentops -g agent-platform-read -m 0750 /var/lib/agent-platform /var/lib/agent-platform-herdr
```

Existing credentials directory is NEVER overwritten by a repeat. Exporter output
directories must be owned by agentops, not group-writable; their primary group is
agent-platform-read. Files publish mode0640. Source DB permissions are not changed.

Install the reviewed package exactly once (skip this block ONLY after verifying an
existing installed release against its saved SHA256 manifest and commit):

```sh
STAGING=$(mktemp -d)
chmod 0700 "$STAGING"
git -C "$RELEASE_SOURCE" archive "$RELEASE_COMMIT" agent_platform_dashboard deploy/agent_platform/production | tar -x -C "$STAGING"
python3 - "$STAGING" <<'PYINSTALL'
from pathlib import Path
import sys
root = Path(sys.argv[1])
assert not any(p.is_symlink() for p in root.rglob('*'))
for p in (root/'agent_platform_dashboard').iterdir():
    if p.name == '__init__.py':
        p.write_text('')
    elif not (p.name.startswith('production_') and p.suffix == '.py'):
        assert p.is_file()
        p.unlink()
PYINSTALL
# Only into an EMPTY new private release path; never merge over an existing release.
[ -z "$(sudo find /opt/agent-platform/release -mindepth 1 -maxdepth 1 -print -quit)" ] || exit 1
sudo cp -a "$STAGING/." /opt/agent-platform/release/
sudo chown -R root:root /opt/agent-platform/release
sudo chmod -R u=rwX,go=rX /opt/agent-platform/release
sudo find /opt/agent-platform/release -type f -exec sha256sum {} +
# Save this manifest and RELEASE_COMMIT privately for repeat/drift validation.
```

No workspace secrets, .git, venv or fixture modules are installed. STAGING contains
only public reviewed code; remove that specific scratch directory after validation.
Release files are root-owned and not writable by service users. Future upgrades
require a separate reviewed release/rollback procedure; no in-place active updates.

## 3. Configure explicit sources and grants; do not guess Kanban

Install examples only when destination is absent; editing them requires admin review:

```sh
BUNDLE=/opt/agent-platform/release/deploy/agent_platform/production
for name in web sources herdr; do
  if sudo test -e "/etc/agent-platform/$name.json"; then
    printf 'Confirm reuse of reviewed config %s: ' "$name"; read -r confirmed
    [ "$confirmed" = "$name" ] || exit 1
  else
    sudo install -o root -g agent-platform-read -m 0640 "$BUNDLE/$name.example.json" "/etc/agent-platform/$name.json"
  fi
done
sudoedit /etc/agent-platform/sources.json /etc/agent-platform/herdr.json
```

The examples are intentionally incomplete. Confirm BOTH profiles independently:
verified router files are beneath each profile's `model-router/router.db`. They
use WAL. If both regular no-follow -wal/-shm files exist they remain pinned through
the read. If neither exists, the exporter copies the bounded checkpointed main file
to its private temporary directory, verifies source identity/size/timestamps and that
sidecars remained absent, and queries only that copy. A partial sidecar pair, source
change, access/schema error or oversized DB is unavailable. NEVER use immutable=1,
chmod live DBs, recovery, journal changes, migrations or writer helper imports.
Queries expose last1000 requests grouped by task digest, maximum50 groups.
Overflow/time budget => unavailable; numbers are this bounded window, not all-time
totals. Cost null is unknown; zero is only a measured zero. Router sensitive columns
are not queried.

Create `/etc/systemd/system/agent-platform-export.service.d` with
`sudo install -d -o root -g root -m 0755 /etc/systemd/system/agent-platform-export.service.d`.
Create its sources.conf with `sudoedit` only after confirming each
real path (no symlink component). Exact example mapping for independently verified
router directories, read-only, not permissions changes:

```ini
# /etc/systemd/system/agent-platform-export.service.d/sources.conf
[Service]
BindReadOnlyPaths=/home/agentops/.hermes/profiles/majak/model-router:/sources/majak-router
BindReadOnlyPaths=/home/agentops/.hermes/profiles/quantlab/model-router:/sources/quantlab-router
```

Kanban: no live store discovered in audited roots. Leave `kanban:null` until admin
verifies actual DB/path/schema, immutable board_id and source_epoch, and profile ACL.
Then use `{"path":"/sources/PROFILE-kanban/kanban.db","board_id":"64 lowercase hex",
"source_epoch":"64 lowercase hex"}` with an exact read-only directory bind. The
adapter accepts tasks(id,status,current_run_id,created_at), no title/body/assignee.
Do not invent board identity or assign a shared board implicitly to both profiles.

Git: explicit per-profile repo path under /sources, bind only that reviewed repo
read-only. Linked worktrees additionally need their explicit common Git metadata
path read-only at the same resolved path (or leave source null). No arbitrary Git
config/env/remote/diff; fixed HEAD + status only, fsmonitor disabled. Repository
owners are trusted; never point this registry at untrusted repos or config includes.


Durable task queue: the QuantLab-only queue projection is an optional sanitized bridge
at `/var/lib/agent-platform-herdr/queue.json`. It is produced by the external
`agent-task-export` watchdog helper owned by `agentops`; the dashboard never reads the
original task directories, prompts, results or logs. The bridge contains only bounded
operational metadata: task_id, issue number, state, attempt count, schedule timestamps,
agent, kind and a sanitized blocker code. The exporter already has read-only access to
`/var/lib/agent-platform-herdr`, so no additional home-directory or broad source bind is
allowed. Missing/stale/invalid bridge data must publish the queue source as unavailable,
never fall back to task files. The fixed bridge is QuantLab-only and requires no
`sources.json` key. During the search-source migration, the exporter accepts the legacy
profile shape without `search` and normalizes it to `search:null`; this preserves the
currently deployed root-owned config until its separately reviewed search rollout.

Reports: explicit per-profile regular JSON file path (read-only bind). Format:
`{"version":1,"profile":"majak","observed_at":UNIX_SECONDS,"passed":COUNT,
"failed":COUNT,"artifact_digest":"SHA256"}`. Populate from actual verified test
results, not guessed parsing of Markdown/logs. Age>24h or wrong profile => unavailable.
No adapter for raw logs. Report provenance is the trusted producer/file permissions,
not the digest alone. Until producer configured, tests:null => unavailable.

Herdr: ONLY agentops status bridge gets an explicitly bound socket. From the intended
Herdr session, inspect `herdr agent list` privately; configure explicit name→profile
AND exact pane_id mapping in root-owned herdr.json. Do NOT infer scope just from
name. Copy the verified installed Herdr binary into a root-owned release path,
verify its hash and configure that exact binary. Bind the verified actual session
socket path in a herdr service drop-in (AF_UNIX only); no broad /run or home mount.
Create `/etc/systemd/system/agent-platform-herdr.service.d` with sudo install -d
(owner root, mode0755), then sudoedit sources.conf with the exact socket bind
`BindReadOnlyPaths=VERIFIED_HOST_SOCKET:/sources/herdr.sock` and set config.socket
to `/sources/herdr.sock`. VERIFIED_HOST_SOCKET must be explicitly confirmed; do not
copy that placeholder literally. Status bridge binary is the separately verified
root-owned copy in the release; never use an arbitrary executable from input.
Set config.socket to the sandbox-visible socket. Explicit binary installation
(admin confirms the already installed binary; no download):

```sh
printf 'Confirm absolute audited Herdr binary path: '; read -r HERDR_SOURCE
case "$HERDR_SOURCE" in /*) ;; *) exit 1;; esac
[ -f "$HERDR_SOURCE" ] && [ ! -L "$HERDR_SOURCE" ] || exit 1
sha256sum "$HERDR_SOURCE"  # compare with the audited installed binary
printf 'Type its SHA256: '; read -r HERDR_DIGEST
[ "$(sha256sum "$HERDR_SOURCE" | cut -d ' ' -f 1)" = "$HERDR_DIGEST" ] || exit 1
if sudo test -e /opt/agent-platform/release/herdr; then
  sudo cmp "$HERDR_SOURCE" /opt/agent-platform/release/herdr || exit 1
else
  sudo install -o root -g root -m 0755 "$HERDR_SOURCE" /opt/agent-platform/release/herdr
fi
# Set herdr.json binary=/opt/agent-platform/release/herdr after this verification.
```

Example bindings value:
`{"majak-hermes":{"profile":"majak","pane_id":"EXPLICIT_LIVE_PANE"}}`.
All configured bindings must match; missing/renamed/moved panes fail closed.
The bridge publishes explicit covered profiles; a profile without binding is
unavailable/not_configured, never a measured zero. Refresh
registry by explicit admin review. Other agents' titles/cwd/raw data are discarded.
The Herdr socket itself is control-capable; the trusted one-shot bridge contains only
`agent list`. This is process/code isolation, NOT a server-enforced read-only token.
Web/export service never receives the socket. Export service also denies the
network-io syscall group, so even AF_UNIX socket access is blocked there. A missing bridge means unavailable.

## 4. Generate password exactly once, outside Git/logs

```sh
if sudo test -e /etc/agent-platform/credentials; then
  printf 'Credentials already present: validate existing pair; no generation or redisplay.\n'
else
  sudo /usr/bin/python3 -I -B "$BUNDLE/launch.py" credentials \
    --confirm /etc/agent-platform/credentials
fi
```

The helper requires root + `/dev/tty` and another typed confirmation. New random
password (288 bits before encoding), only michal; hash pipe to OpenSSL, no argv/env
password. Saves salted SHA512-crypt for Nginx and independently salted PBKDF2-SHA256
600000 verifier with explicit majak/quantlab grants for backend. File mode0640,
root:agent-platform-auth; directory0750. Displays plaintext once to the admin TTY
only; immediately store in an approved password manager. Never tee/script/record,
copy to shell variable or pass password in curl argv. Existing credentials refuse
without rotation or redisplay. If terminal fails after files publish, plaintext
cannot be recovered: keep route denied and perform a separately authorized rotation.
Rotation/revocation: deny route first, stop web, archive/remove old credential bundle
in a root-only area under a separately approved admin operation, generate a fresh
pair, validate, restart web, smoke; never mix old Nginx and new backend verifiers.

## 5. Install inactive units, verify, then explicit source and web start

```sh
for name in agent-platform-web.service agent-platform-export.service agent-platform-herdr.service \
            agent-platform-export.timer agent-platform-herdr.timer; do
  # Destination MUST be absent or byte-identical; stop on unexpected drift.
  if sudo test -e "/etc/systemd/system/$name"; then
    sudo cmp "$BUNDLE/$name.in" "/etc/systemd/system/$name" || exit 1
  else
    sudo install -o root -g root -m 0644 "$BUNDLE/$name.in" "/etc/systemd/system/$name"
  fi
done
sudo systemd-analyze verify /etc/systemd/system/agent-platform-{web,export,herdr}.service \
  /etc/systemd/system/agent-platform-{export,herdr}.timer
sudo systemctl daemon-reload
sudo systemctl start agent-platform-herdr.service  # configure bridge first, otherwise STOP
sudo systemctl start agent-platform-export.service
# Confirm snapshot source status/profile/timestamps privately; unavailable is not zero.
# Mandatory launch gate: BOTH router profiles and BOTH Herdr profiles available.
# Any intended Git/report/Kanban source must also be available; explicitly null
# sources require a recorded admin acknowledgement of partial source coverage.
sudo -u agent-platform-web /usr/bin/python3 -I -B "$BUNDLE/launch.py" web --config /etc/agent-platform/web.json --check
sudo systemctl start agent-platform-web.service
[ "$(curl --silent --output /dev/null --write-out '%{http_code}' http://127.0.0.1:3010/agent-platform/health)" = 401 ] || exit 1
# curl prompts privately. Password is not a CLI argument or environment variable.
curl --user michal --fail --silent http://127.0.0.1:3010/agent-platform/health
sudo systemctl enable --now agent-platform-herdr.timer agent-platform-export.timer
sudo systemctl enable agent-platform-web.service
```

Web startup/--check enforces fresh available router and nonempty Herdr coverage
for every granted profile. Runtime later source failures remain explicit unavailable;
a stale whole snapshot returns503. Service has no auto-restart or API retry. Timers invoke bounded one-shot exports,
not retry loops; a failure cannot present an old snapshot as fresh. Web is a normal
long-lived HTTP service with bounded socket read timeout; no background source loop.
Check sandbox effective mounts/cgroup enforcement (`systemctl show`), source mounts
read-only, absence of socket in web/export, DB hashes and unchanged profiles. Do not
activate public proxy until this passes. Unavailable optional Kanban/Git/reports must
be explicitly acknowledged; they do not claim production source completeness.

## 6. Auth-gated Nginx activation with exact include-only change

```sh
install_exact() {
  if sudo test -e "$2"; then
    sudo cmp "$1" "$2" || return 1
  else
    sudo install -o root -g root -m 0644 "$1" "$2"
  fi
}
install_exact "$BUNDLE/nginx-location-common.conf.in" /etc/agent-platform/nginx-location-common.conf
install_exact "$BUNDLE/nginx-server.conf.in" /etc/agent-platform/nginx-server.conf
# Confirm /etc/nginx/conf.d/*.conf is included in http context, not server/location.
install_exact "$BUNDLE/nginx-http.conf.in" /etc/nginx/conf.d/agent-platform-rate.conf
sudo sha256sum "$VHOST"  # record privately for compare-and-swap/drift gate
sudoedit "$VHOST"
```

Insert exactly one line **inside the already confirmed HTTPS server**:
`include /etc/agent-platform/nginx-server.conf;`
Do not replace the whole vhost or edit QuantLab root/3000/listeners/TLS. On repeat,
require exactly this one include; do not insert twice. Inspect a private diff against
admin baseline: only that line may change. STOP if shared config changed concurrently.
Verify full route inventory again; native -t does not prove correct server placement.

```sh
sudo nginx -t
sudo systemctl reload nginx
for suffix in /agent-platform /agent-platform/ /agent-platform/health /agent-platform/api/v1/overview /agent-platform/style.css; do
  sleep 7  # pace the independent smoke checks; not a retry
  [ "$(curl --silent --output /dev/null --write-out '%{http_code}' "$ORIGIN$suffix")" = 401 ] || exit 1
done
sleep 7
curl --user michal --fail --silent --output /dev/null "$ORIGIN/agent-platform/"
sleep 7
curl --user michal --fail --silent "$ORIGIN/agent-platform/health"
sleep 7
curl --user michal --fail --silent "$ORIGIN/agent-platform/api/v1/overview"
[ "$(curl --silent --output /dev/null --write-out '%{http_code}' "$ORIGIN/")" = 200 ] || exit 1
[ "$(curl --silent --output /dev/null --write-out '%{http_code}' http://127.0.0.1:3000/)" = 200 ] || exit 1
```

Respect 10 requests/minute per IP (+burst5); do not blindly repeat smoke on429/503.
Use curl without -v/--trace; JSON response is allowlisted but keep admin output
private. Check expected selected profiles, unavailable vs zero, timestamps and
cost null. Confirm no changes to QuantLab service/source/config and no external
3010 listener. Public TLS/certificate correctness and same-origin QuantLab trust are
host gates, not proven by unit tests.

## 7. Rollback — preserve path reservation, never fall through to QuantLab

On any auth/source/isolation/root regression: FIRST atomically install the reviewed
`nginx-maintenance.conf.in` content over **our**
`/etc/agent-platform/nginx-server.conf` (preserve the one-line shared include).
Keep its exact/prefix/named503 handling together; never construct a partial fragment
at the terminal.

Inherited error handlers MUST also be neutralized: use the full maintenance fragment
with its own internal @agent_platform_unavailable and fixed JSON503 response. Check
no collision for that named location. Validate `sudo nginx -t`, then separately
`sudo systemctl reload nginx`, confirm both paths denied and QuantLab root200.
Only then `sudo systemctl disable --now agent-platform-web.service
agent-platform-export.timer agent-platform-herdr.timer`; stop any running export/
herdr oneshot separately. No changes to QuantLab units. Keep credentials private;
revoke/rotate only through an explicit admin operation. Do not delete databases or
restore an entire shared vhost over concurrent operator changes. Keep the 503
reservation until an explicit user decision to unreserve; never proxy to3000 as
fallback. Failure before activation only discards our scratch/staged artifacts.
