"""In-memory WSGI smoke, no listener and no live data sources."""
from concurrent.futures import ThreadPoolExecutor
from contextvars import ContextVar, copy_context
from dataclasses import replace
import base64
import builtins
import json
import socket
import subprocess
from html.parser import HTMLParser

import pytest

from agent_platform_dashboard import app as web, contracts as c
from tests.agent_platform_dashboard.test_contracts import snapshot, scope


def authorization(user='majak', password='fixture-password-1234'):
    return 'Basic ' + base64.b64encode(f'{user}:{password}'.encode()).decode()


def app(enabled=True):
    s = snapshot()
    s = replace(s, rows=s.rows + (replace(s.rows[0], scope=scope('c')),))
    grants = (web.Login('majak', 'fixture-password-1234', c.Grant('d'*64, (scope(),), 200)),
              web.Login('quantlab', 'different-fixture-1234', c.Grant('e'*64, (scope('c'),), 200)))
    return web.DashboardApp(s, grants, now=lambda: 110, enabled=enabled)


def request(application, path='/agent-platform/', *, auth=True, method='GET', host='127.0.0.1', query=''):
    result = []
    env = {'PATH_INFO': path, 'QUERY_STRING': query, 'REQUEST_METHOD': method,
           'HTTP_HOST': host, 'HTTP_AUTHORIZATION': authorization() if auth is True else auth or ''}
    body = b''.join(application(env, lambda status, headers: result.append((status, dict(headers)))))
    return result[0][0], result[0][1], body


def test_disabled_and_anonymous_deny():
    assert request(app(False))[0].startswith('503')
    assert request(app(), auth=False)[0].startswith('401')
    assert request(app(), path='/agent-platform/style.css', auth=False)[0].startswith('401')


def test_html_and_api_smoke_security_headers():
    application = app()
    status, headers, body = request(application)
    assert status == '200 OK'
    parser = HTMLParser()
    parser.feed(body.decode())
    assert b'Agent platform' in body and b'Offline fixtures' in body
    assert b'unknown' in body and b'working' in body
    assert b'<script' not in body and b'fixture-password' not in body
    assert headers['Cache-Control'] == 'no-store'
    assert "default-src 'none'" in headers['Content-Security-Policy']
    assert headers['X-Frame-Options'] == 'DENY'
    status, _, body = request(application, '/agent-platform/api/v1/overview')
    data = json.loads(body)
    assert len(data['rows']) == 5
    assert data['rows'][2]['cost_microusd'] is None
    assert request(application, method='HEAD')[2] == b''


@pytest.mark.parametrize('path,query', [('/etc/passwd',''), ('/agent-platform/../x',''),
    ('/agent-platform/%2e%2e/x',''), ('/agent-platform/','path=/home/live'),
    ('/agent-platform/','profile=quantlab'), ('/agent-platform/api/v1/overview','sql=DROP')])
def test_fixed_routes_no_path_or_query_source(path, query):
    assert request(app(), path, query=query)[0].startswith('404')


@pytest.mark.parametrize('method', ['POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
def test_no_mutation_routes(method):
    assert request(app(), method=method)[0].startswith('405')


@pytest.mark.parametrize('auth', ['Bearer PRIVATE', 'Basic invalid!', authorization(password='wrong'),
                                  'Basic ' + 'a' * 5000])
def test_bad_auth_never_echoed(auth):
    status, _, body = request(app(), auth=auth)
    assert status.startswith('401') and b'PRIVATE' not in body


def test_host_and_expired_grant_fail_closed():
    assert request(app(), host='attacker.test')[0].startswith('403')
    application = web.DashboardApp(snapshot(), (web.Login('majak', 'fixture-password-1234',
        c.Grant('d'*64, (scope(),), 100)),), now=lambda: 110, enabled=True)
    assert request(application)[0].startswith('403')


def test_concurrent_copy_context_profile_isolation():
    application = app()
    ambient = ContextVar('profile', default='irrelevant')
    ambient.set('quantlab')
    def read(auth):
        _, _, body = request(application, '/agent-platform/api/v1/overview', auth=auth)
        return json.loads(body)['rows']
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(copy_context().run, read, authorization())
        second = pool.submit(copy_context().run, read, authorization('quantlab', 'different-fixture-1234'))
        assert len(first.result(timeout=5)) == 5
        assert len(second.result(timeout=5)) == 1
    assert len(read(authorization())) == 5


def test_no_implicit_io_or_control_imports(monkeypatch):
    application = app()
    def forbidden(*args, **kwargs):
        pytest.fail('unexpected I/O')
    for owner, attr in ((builtins, 'open'), (socket, 'socket'), (subprocess, 'Popen')):
        monkeypatch.setattr(owner, attr, forbidden)
    assert request(application)[0] == '200 OK'
    assert request(application, '/agent-platform/api/v1/overview')[0] == '200 OK'


def test_clock_error_sanitized_and_baseexception_preserved():
    credentials = (web.Login('majak', 'fixture-password-1234', c.Grant('d'*64, (scope(),), 200)),)
    for error in (RuntimeError, KeyboardInterrupt, SystemExit):
        def broken():
            raise error('PRIVATE')
        application = web.DashboardApp(snapshot(), credentials, now=broken, enabled=True)
        if error is RuntimeError:
            status, _, body = request(application)
            assert status.startswith('503') and b'PRIVATE' not in body
        else:
            with pytest.raises(error):
                request(application)


def test_renderer_escapes_defensive_untrusted_strings():
    from agent_platform_dashboard.frontend import render
    data = c.project(snapshot(), c.Grant('d'*64, (scope(),), 200), now=110)
    data['rows'][0]['status'] = '<script>alert("PRIVATE")</script>'
    data['rows'][0]['record_id'] = '\"><img src=x onerror=alert(1)>'
    output = render(data)
    assert '<script>' not in output and '<img' not in output
    assert '&lt;script&gt;' in output


def test_server_factory_is_opt_in_loopback_ephemeral_without_start(monkeypatch):
    from wsgiref import simple_server
    calls = []
    class Server:
        server_port = 45678
    def factory(host, port, application, handler_class):
        calls.append((host, port))
        return Server()
    monkeypatch.setattr(simple_server, 'make_server', factory)
    with pytest.raises(c.Invalid):
        web.make_demo_server(app())
    with pytest.raises(c.Invalid):
        web.make_demo_server(app(False), enabled=True)
    assert calls == []
    application = app()
    server = web.make_demo_server(application, enabled=True)
    assert server.server_port == 45678 and calls == [('127.0.0.1', 0)]
    assert request(application, host='127.0.0.1:45678')[0] == '200 OK'
    assert request(application, host='127.0.0.1:3010')[0].startswith('403')


def test_assets_health_and_empty_scope_are_bounded_and_authenticated():
    application = app()
    for path in ('/agent-platform/style.css', '/agent-platform/health'):
        assert request(application, path, auth=False)[0].startswith('401')
        assert request(application, path)[0] == '200 OK'
    unrelated = c.Grant('d'*64, (scope(board='f'),), 200)
    application = web.DashboardApp(snapshot(), (web.Login('majak', 'fixture-password-1234', unrelated),),
                                   now=lambda: 110, enabled=True)
    _, _, body = request(application, '/agent-platform/api/v1/overview')
    assert json.loads(body)['rows'] == []


def test_no_path_reader_or_environment_profile_fallback(monkeypatch):
    monkeypatch.setenv('HERMES_HOME', '/not-a-fixture')
    monkeypatch.setenv('HERDR_SOCKET', '/not-a-socket')
    application = app()
    before = request(application, '/agent-platform/api/v1/overview')[2]
    monkeypatch.setenv('HERMES_HOME', '/different-profile')
    assert request(application, '/agent-platform/api/v1/overview')[2] == before
