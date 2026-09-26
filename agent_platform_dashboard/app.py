"""Fixture-only WSGI surface. No source paths, DB helpers, command runner or Herdr socket."""
from base64 import b64encode
from dataclasses import dataclass, field
from hmac import compare_digest
import json

from . import contracts as c
from .frontend import CSS, render


@dataclass(frozen=True, slots=True)
class Login:
    username: str
    password: str = field(repr=False)
    grant: c.Grant

    def __post_init__(self):
        c.need(type(self.username) is str and self.username in ('majak', 'quantlab', 'agent-platform'))
        c.need(type(self.password) is str and 16 <= len(self.password) <= 128
               and self.password.isascii() and all(33 <= ord(ch) <= 126 and ch != ':' for ch in self.password))
        c.need(type(self.grant) is c.Grant)
        c.validate(self.grant)


class DashboardApp:
    def __init__(self, snapshot, logins=(), *, now, enabled=False):
        c.need(type(enabled) is bool and callable(now))
        c.need(type(snapshot) is c.Snapshot)
        c.validate(snapshot)
        c.need(type(logins) is tuple and len(logins) <= 3)
        for login in logins:
            c.need(type(login) is Login)
            login.__post_init__()
        c.need(len({v.username for v in logins}) == len(logins))
        self._snapshot, self._logins, self._now, self._enabled = snapshot, logins, now, enabled
        self._authority = '127.0.0.1'

    def __call__(self, environ, start_response):
        status, mime, body = self._response(environ)
        headers = [('Content-Type', mime), ('Content-Length', str(len(body))), ('Cache-Control', 'no-store'),
                   ('X-Content-Type-Options', 'nosniff'), ('X-Frame-Options', 'DENY'), ('Referrer-Policy', 'no-referrer'),
                   ('Content-Security-Policy', "default-src 'none'; style-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")]
        if status.startswith('401'):
            headers.append(('WWW-Authenticate', 'Basic realm="Offline fixtures", charset="UTF-8"'))
        start_response(status, headers)
        return [b'' if environ.get('REQUEST_METHOD') == 'HEAD' else body]

    def _response(self, env):
        def error(status):
            return status, 'application/json', b'{"error":"unavailable"}'
        if not self._enabled:
            return error('503 Service Unavailable')
        if env.get('HTTP_HOST') != self._authority:
            return error('403 Forbidden')
        header = env.get('HTTP_AUTHORIZATION', '')
        if type(header) is not str or not header.isascii() or len(header) > 1024:
            return error('401 Unauthorized')
        login = None
        for candidate in self._logins:
            expected = 'Basic ' + b64encode((candidate.username + ':' + candidate.password).encode()).decode()
            if compare_digest(header, expected):
                login = candidate
        if login is None:
            return error('401 Unauthorized')
        try:
            now = self._now()
        except Exception:
            return error('503 Service Unavailable')
        try:
            data = c.project(self._snapshot, login.grant, now=now)
        except c.Invalid:
            return error('403 Forbidden')
        if env.get('REQUEST_METHOD') not in ('GET', 'HEAD'):
            return error('405 Method Not Allowed')
        if env.get('QUERY_STRING', ''):
            return error('404 Not Found')
        path = env.get('PATH_INFO')
        if path == '/agent-platform/':
            return '200 OK', 'text/html; charset=utf-8', render(data).encode()
        if path == '/agent-platform/style.css':
            return '200 OK', 'text/css; charset=utf-8', CSS.encode()
        if path == '/agent-platform/api/v1/overview':
            return '200 OK', 'application/json', json.dumps(data, sort_keys=True, separators=(',', ':')).encode()
        if path == '/agent-platform/health':
            return '200 OK', 'application/json', b'{"mode":"offline-fixtures"}'
        return error('404 Not Found')


def make_demo_server(application, *, enabled=False):
    """Explicit opt-in, loopback port 0 only; caller owns lifecycle. Never called on import."""
    c.need(enabled is True and type(application) is DashboardApp and application._enabled, 'disabled')
    from wsgiref.simple_server import WSGIRequestHandler, make_server

    class QuietHandler(WSGIRequestHandler):
        def log_message(self, format, *args):
            pass

    server = make_server('127.0.0.1', 0, application, handler_class=QuietHandler)
    application._authority = f'127.0.0.1:{server.server_port}'
    return server
