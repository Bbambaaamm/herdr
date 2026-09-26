#!/bin/bash
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "Spust tento skript jako root."
  exit 1
fi

install -o root -g root -m 0644 \
  /home/agentops/.local/share/agent-stack/agent-stack-watchdog.service \
  /etc/systemd/system/agent-stack-watchdog.service

pkill -u agentops -f '^/bin/bash /home/agentops/.local/bin/agent-stack-watchdog$' 2>/dev/null || true
systemctl daemon-reload
systemctl enable --now agent-stack-watchdog.service
sleep 3
systemctl is-enabled agent-stack-watchdog.service
systemctl is-active agent-stack-watchdog.service
systemctl --no-pager --full status agent-stack-watchdog.service
