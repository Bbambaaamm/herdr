#!/usr/bin/env python3
"""Read-only Herdr 0.9.1 schema and live parent-chain probe."""
from __future__ import annotations
import json
import subprocess
from pathlib import Path


def main() -> int:
    binary = '/home/agentops/.local/bin/herdr'
    version = subprocess.check_output([binary, '--version'], text=True).strip()
    if version != 'herdr 0.9.1':
        raise SystemExit(f'unaudited Herdr version: {version}')
    schema = json.loads(subprocess.check_output([binary, 'api', 'schema', '--json'], text=True))
    defs = schema['schemas']['request']['$defs']
    agent_fields = set(defs['AgentStartParams']['properties'])
    pane_fields = set(defs['PaneSplitParams']['properties'])
    assert agent_fields == {'name', 'kind', 'pane_id', 'args', 'timeout_ms'}
    assert 'env' in pane_fields
    rows = subprocess.check_output(['ps', '-eo', 'pid=,ppid=,args='], text=True).splitlines()
    processes = {}
    for row in rows:
        parts = row.strip().split(None, 2)
        if len(parts) == 3:
            processes[int(parts[0])] = (int(parts[1]), parts[2])
    servers = {pid for pid, (_, command) in processes.items()
               if command.startswith(binary + ' server')}
    hermes = [pid for pid, (_, command) in processes.items()
              if '/home/agentops/.hermes/hermes-agent/hermes' in command
              and '/venv/bin/python' in command]
    chains = []
    for pid in hermes:
        parent = processes[pid][0]
        grandparent = processes.get(parent, (0, ''))[0]
        if grandparent in servers:
            chains.append([pid, parent, grandparent])
    status = 'PASS' if chains else 'INCONCLUSIVE_PROCESS_NAMESPACE'
    print(json.dumps({'status': status, 'herdr_version': version,
                      'agent_start_fields': sorted(agent_fields),
                      'pane_split_has_env': True, 'daemon_shell_hermes_chains': chains}, sort_keys=True))
    return 0 if chains else 2


if __name__ == '__main__':
    raise SystemExit(main())
