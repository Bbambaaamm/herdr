#!/bin/bash
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "Spust tento skript jako root."
  exit 1
fi

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)"
UNIT="$SCRIPT_DIR/systemd/agent-stack-watchdog.service"

test -f "$UNIT"

install -o root -g root -m 0644   "$UNIT"   /etc/systemd/system/agent-stack-watchdog.service

systemctl daemon-reload
systemctl enable agent-stack-watchdog.service
systemctl restart agent-stack-watchdog.service

sleep 3

systemctl is-enabled agent-stack-watchdog.service
systemctl is-active agent-stack-watchdog.service
systemctl --no-pager --full status agent-stack-watchdog.service
