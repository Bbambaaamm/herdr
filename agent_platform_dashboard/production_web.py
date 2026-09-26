"""Production HTTP reads only a sanitized snapshot and independent auth verifier."""
from html import escape
import json
import os
from pathlib import Path
import sys
import time

from . import production_contract as c
from .production_auth import authenticate, verifier
from .production_io import read


STATIC_ROOT = Path(__file__).resolve().with_name('static')
ASSETS = {
    '/agent-platform/machine-city.css': ('machine-city.css', 'text/css; charset=utf-8', 131072),
    '/agent-platform/machine-city.js': ('machine-city.js', 'text/javascript; charset=utf-8', 2 * 1024 * 1024),
    '/agent-platform/machine-city-background.webp': ('machine-city-background.webp', 'image/webp', 1024 * 1024),
}
CSP = ("default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; "
       "img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")


class Application:
    def __init__(self, snapshot_path, auth, *, now=time.time):
        self.snapshot_path = snapshot_path
        self.auth = verifier(auth)
        self.now = now
        self.highwater = 0

    def __call__(self, env, start_response):
        status, mime, body = self.response(env)
        headers = [('Content-Type', mime), ('Content-Length', str(len(body))), ('Cache-Control', 'no-store'),
                   ('X-Content-Type-Options', 'nosniff'), ('Referrer-Policy', 'no-referrer'),
                   ('Content-Security-Policy', CSP), ('X-Frame-Options', 'DENY')]
        if status.startswith('401'):
            headers.append(('WWW-Authenticate', 'Basic realm="Agent Platform", charset="UTF-8"'))
        start_response(status, headers)
        return [b'' if env.get('REQUEST_METHOD') == 'HEAD' else body]

    def response(self, env):
        def error(status):
            return status, 'application/json', b'{"error":"unavailable"}'
        if env.get('HTTP_HOST') != '127.0.0.1:3010':
            return error('403 Forbidden')
        if not authenticate(env.get('HTTP_AUTHORIZATION'), self.auth):
            return error('401 Unauthorized')
        if env.get('REQUEST_METHOD') not in ('GET', 'HEAD'):
            return error('405 Method Not Allowed')
        path = env.get('PATH_INFO')
        allowed = {'/agent-platform', '/agent-platform/', '/agent-platform/api/v1/overview',
                   '/agent-platform/health', *ASSETS}
        if env.get('QUERY_STRING', '') or path not in allowed:
            return error('404 Not Found')
        if path in ASSETS:
            filename, mime, limit = ASSETS[path]
            try:
                return '200 OK', mime, read(str(STATIC_ROOT / filename), limit)
            except Exception:
                return error('503 Service Unavailable')
        try:
            now = int(self.now())
            data = c.project(c.decode(read(self.snapshot_path, c.MAX_BYTES)), tuple(self.auth['profiles']), now)
            c.need(self.highwater <= data['generated_at'] and 0 <= now - data['generated_at'] <= 90)
            self.highwater = data['generated_at']
        except Exception:
            return error('503 Service Unavailable')
        if path == '/agent-platform/health':
            body = json.dumps({'mode': 'production-read-only', 'generated_at': data['generated_at'],
                               'unavailable_sources': sum(s['status'] != 'available' for s in data['sources'])}).encode()
        elif path == '/agent-platform/api/v1/overview':
            body = json.dumps(data, sort_keys=True, separators=(',', ':')).encode()
        else:
            try:
                template = read(str(STATIC_ROOT / 'machine-city.html'), 65536).decode('utf-8')
            except (OSError, UnicodeError, ValueError):
                return error('503 Service Unavailable')
            sections = []
            for source in data['sources']:
                count = str(len(source['rows'])) if source['status'] == 'available' else 'unavailable'
                sections.append('<section><h3>' + escape(source['profile'] + ' / ' + source['kind']) + '</h3><p>'
                                + escape(source['status'] + ' · ' + source['reason'] + ' · records ' + count)
                                + '</p><pre>' + escape(json.dumps(source, sort_keys=True, indent=2)) + '</pre></section>')
            marker = '<!--SERVER_FALLBACK-->'
            c.need(template.count(marker) == 1)
            html = template.replace(marker, '<div class="server-fallback">' + ''.join(sections) + '</div>')
            return '200 OK', 'text/html; charset=utf-8', html.encode()
        return '200 OK', 'application/json', body


def load(filename):
    config = c.parse(read(filename, 4096, owner=0), 4096)
    c.keys(config, 'version snapshot auth')
    c.need(type(config['version']) is int and config['version'] == 1)
    for name in ('snapshot', 'auth'):
        c.need(type(config[name]) is str and config[name].startswith('/'))
    auth = verifier(c.parse(read(config['auth'], 4096, private=True, owner=0), 4096))
    snapshot = c.decode(read(config['snapshot'], c.MAX_BYTES))
    now = int(time.time())
    c.need(0 <= now - snapshot['generated_at'] <= 90)
    for source in snapshot['sources']:
        if source['profile'] in auth['profiles'] and source['kind'] in ('router', 'herdr'):
            c.need(source['status'] == 'available' and 0 <= now - source['observed_at'] <= 90)
            if source['kind'] == 'herdr':
                c.need(bool(source['rows']))
    return Application(config['snapshot'], auth)


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    try:
        c.need(len(args) in (2, 3) and args[:1] == ['--config'] and os.geteuid() != 0)
        c.need(len(args) == 2 or args[2] == '--check')
        application = load(args[1])
        if len(args) == 3:
            return 0
        from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server
        class QuietHandler(WSGIRequestHandler):
            def log_message(self, format, *args):
                pass
        class Server(WSGIServer):
            def get_request(self):
                connection, address = super().get_request()
                connection.settimeout(5)
                return connection, address
            def handle_error(self, request, address):
                pass
        with make_server('127.0.0.1', 3010, application, server_class=Server, handler_class=QuietHandler) as server:
            server.serve_forever()
        return 0
    except Exception:
        print('runtime_unavailable', file=sys.stderr)
        return 78


if __name__ == '__main__':
    raise SystemExit(main())
