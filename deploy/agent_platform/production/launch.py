"""Root-owned release entrypoint, invoked by admin-installed isolated units only."""
from pathlib import Path
import sys


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ('web', 'export', 'herdr', 'credentials'):
        return 78
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    mode = sys.argv[1]
    if mode == 'web':
        from agent_platform_dashboard.production_web import main as run
    elif mode == 'export':
        from agent_platform_dashboard.production_export import main as run
    elif mode == 'herdr':
        from agent_platform_dashboard.production_herdr import main as run
    else:
        from agent_platform_dashboard.production_credentials import main as run
    return run(sys.argv[2:])


if __name__ == '__main__':
    raise SystemExit(main())
