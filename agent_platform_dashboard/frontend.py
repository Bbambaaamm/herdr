"""Static, server-rendered frontend. Values are escaped; no JavaScript or external assets."""
from html import escape

CSS = """
:root{color-scheme:dark;font:15px system-ui,sans-serif;background:#0b1220;color:#e4edf7}
*{box-sizing:border-box}body{max-width:1180px;margin:auto;padding:40px 24px}
header{border-bottom:1px solid #30415b;padding-bottom:24px;display:flex;justify-content:space-between;gap:24px}
h1{font-size:32px;margin:8px 0}h2{font-size:19px;margin:32px 0 12px}
p{line-height:1.6;color:#adc0d6}a{color:#85dcca}.label{color:#85dcca;font-size:12px;text-transform:uppercase;letter-spacing:2px}
.badge{display:inline-block;padding:6px 10px;background:#20334b;border:1px solid #466384;border-radius:5px}
.cards{display:grid;grid-template-columns:repeat(5,1fr);gap:14px;margin:28px 0}
.card{padding:20px;background:#131f32;border:1px solid #283c55;border-radius:9px}.count{font-size:30px;display:block;margin-top:10px}
.table-wrap{overflow:auto}table{width:100%;border-collapse:collapse;background:#101b2c}
th,td{padding:13px;text-align:left;border-bottom:1px solid #283c55;vertical-align:top}
th{color:#93aac5;font-size:12px;text-transform:uppercase}code{font-size:12px;color:#bccee3}
footer{margin-top:32px;border-top:1px solid #30415b;padding-top:16px;font-size:12px;color:#93aac5}
.empty{color:#93aac5;padding:16px}.muted{font-size:12px;color:#93aac5}
@media(max-width:720px){body{padding:20px 12px}.cards{grid-template-columns:repeat(2,1fr)}header{display:block}th,td{padding:9px}}
"""


def _text(value):
    return escape('unknown' if value is None else str(value), quote=True)


def _details(row):
    kind = row['kind']
    if kind == 'agent':
        return row['status']
    if kind == 'task':
        run = row['run_id'][:12] if row['run_id'] else 'unknown'
        return f"{row['status']} · run {run}"
    if kind == 'router':
        cost = row['cost_microusd']
        cost = 'unknown' if cost is None else f'{cost // 1000000}.{cost % 1000000:06d} USD'
        tokens = f"{_text(row['input_tokens'])} / {_text(row['output_tokens'])} tokens"
        return f"{row['provider']} · {row['model']} · {tokens} · cost {cost} · {row['reason']}"
    if kind == 'repo':
        return f"{row['commit'][:12]} · {'dirty' if row['dirty'] else 'clean'}"
    return f"{row['status']} · {_text(row['passed'])} passed / {_text(row['failed'])} failed"


def render(data):
    # Called only on a validated, scope-filtered project() result.
    sections = []
    cards = []
    for kind, label in (('agent', 'Agents'), ('task', 'Kanban tasks'), ('router', 'Router telemetry'),
                        ('repo', 'Git repositories'), ('report', 'Tests & reports')):
        rows = [row for row in data['rows'] if row['kind'] == kind]
        cards.append(f'<div class="card">{escape(label)}<strong class="count">{len(rows)}</strong></div>')
        content = []
        for row in rows:
            scope = row['scope']
            content.append('<tr><td><code title="' + _text(row['record_id']) + '">' + _text(row['record_id'][:12])
                           + '</code></td><td>' + _text(scope['board_name']) + '<br><code>' + _text(scope['profile_id'][:12])
                           + '</code></td><td>' + _text(_details(row)) + '</td></tr>')
        table = ('<div class="table-wrap"><table><thead><tr><th>ID</th><th>Board / profile</th><th>Metadata</th></tr></thead><tbody>'
                 + ''.join(content) + '</tbody></table></div>') if content else '<p class="empty">No visible fixture records.</p>'
        sections.append(f'<section><h2>{escape(label)}</h2>{table}</section>')
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Agent platform · Offline fixtures</title><link rel="stylesheet" href="style.css"></head><body>'
            '<header><div><span class="label">Read-only foundation</span><h1>Agent platform</h1>'
            '<p>Offline fixtures · Explicit profile scope · No live connections</p></div><div><span class="badge">'
            + _text(data['availability']) + '</span><p class="muted">Observed at ' + _text(data['observed_at']) + '</p></div></header>'
            '<main><div class="cards">' + ''.join(cards) + '</div>' + ''.join(sections) + '</main>'
            '<footer>Source version <code>' + _text(data['source_version'][:16]) + '</code>'
            ' · Unknown cost remains unknown. Automatic fallback disabled. Deployment pending.</footer></body></html>')
