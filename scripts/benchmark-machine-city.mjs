import { spawn, execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { createServer } from 'node:http';
import { existsSync } from 'node:fs';
import { mkdtemp, mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import os from 'node:os';
import { basename, dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const STATIC = join(ROOT, 'agent_platform_dashboard', 'static');
const DEFAULT_OUTPUT = join(ROOT, 'dist', 'issue-7-dashboard-performance.json');
const DEFAULT_SCREENSHOT = join(ROOT, 'dist', 'issue-7-dashboard-performance.png');
const THRESHOLDS = Object.freeze({ interactiveMs: 2500, updateMs: 500, fps12: 60, fps30: 45 });
const progress = message => process.stderr.write(`[machine-city-benchmark] ${message}\n`);

function parseArguments(argv) {
  const result = { output: DEFAULT_OUTPUT, screenshot: DEFAULT_SCREENSHOT, chrome: process.env.CHROME_PATH || '', headed: false };
  for (let index = 0; index < argv.length; index += 1) {
    const value = argv[index];
    if (value === '--output') result.output = resolve(argv[++index]);
    else if (value === '--screenshot') result.screenshot = resolve(argv[++index]);
    else if (value === '--chrome') result.chrome = resolve(argv[++index]);
    else if (value === '--headed') result.headed = true;
    else throw new Error(`unknown argument: ${value}`);
  }
  return result;
}

function findChrome(explicit) {
  const candidates = [
    explicit,
    process.platform === 'win32' ? 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe' : '',
    process.platform === 'win32' ? 'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe' : '',
    process.platform === 'darwin' ? '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' : '',
    process.platform === 'linux' ? '/usr/bin/google-chrome' : '',
    process.platform === 'linux' ? '/usr/bin/google-chrome-stable' : '',
  ].filter(Boolean);
  for (const candidate of candidates) {
    if (existsSync(candidate)) return candidate;
  }
  throw new Error('Google Chrome was not found; pass --chrome PATH or set CHROME_PATH');
}

function git(args) {
  return execFileSync('git', args, { cwd: ROOT, encoding: 'utf8' }).trim();
}

function makeSnapshot(agentCount) {
  const now = Math.floor(Date.now() / 1000);
  const tasks = Array.from({ length: agentCount }, (_, index) => {
    const number = index + 1;
    return {
      task_id: `benchmark-${String(number).padStart(2, '0')}`,
      parent_task_id: null,
      parent_agent_id: null,
      agent_id: `benchmark-agent-${String(number).padStart(2, '0')}`,
      state: 'running',
      role: index % 3 === 0 ? 'planner' : index % 3 === 1 ? 'coding' : 'reviewer',
      model: 'benchmark-model',
      fallback_model: 'benchmark-fallback',
      attempt: 1,
      max_attempts: 3,
      blocker: null,
      fencing_token: number,
      dependencies: [],
      result_sha: null,
    };
  });
  const agents = tasks.map(task => ({
    agent_id: task.agent_id,
    task_id: task.task_id,
    state: 'running',
    parent_task_id: null,
    parent_agent_id: null,
    fencing_token: task.fencing_token,
  }));
  const sources = ['majak', 'quantlab'].flatMap(profile => [
    {
      profile,
      kind: 'herdr',
      status: 'available',
      reason: 'benchmark',
      observed_at: now,
      rows: [
        { agent: `${profile}-hermes`, status: 'idle' },
        { agent: `${profile}-codex`, status: 'idle' },
      ],
    },
    {
      profile,
      kind: 'router',
      status: 'available',
      reason: 'benchmark',
      observed_at: now,
      data_at: now,
      rows: [{
        task_id: 'benchmark-router', requests: 1, input_tokens: 100, output_tokens: 50,
        cost_microusd: 0, actual_model: 'benchmark-model', provider: 'benchmark-provider',
        fallback_count: 0, successful_requests: 1, duration_ms: 100, last_used_at: now,
      }],
    },
    {
      profile,
      kind: 'search',
      status: 'available',
      reason: 'benchmark',
      observed_at: now,
      data_at: now,
      rows: [],
    },
    {
      profile,
      kind: 'queue',
      status: 'available',
      reason: 'benchmark',
      observed_at: now,
      data_at: now,
      rows: [],
    },
  ]);
  sources.push({
    profile: 'quantlab',
    kind: 'swarm',
    status: 'available',
    reason: 'benchmark',
    observed_at: now,
    data_at: now,
    rows: [{
      version: 1,
      repo: 'Bbambaaamm/herdr',
      issue: '7',
      issue_state: 'open',
      paper_only: false,
      policy_profiles: ['benchmark'],
      agents,
      tasks,
      edges: [],
    }],
  });
  sources.push({
    profile: 'quantlab',
    kind: 'release',
    status: 'available',
    reason: 'benchmark',
    observed_at: now,
    data_at: now,
    rows: [{
      tag: 'v0.3.0-rc.15',
      commit: 'e822d7243373939d7f229ca693a6b65936c98517',
      config_sha256: '3c7660874e437dd49dcbff83db20761fd595743c15ce3969a457d6f1de199ba9',
      deployed_at: now,
    }],
  });
  return { generated_at: now, sources };
}

function benchmarkBootstrap() {
  return `<script>
    window.__machineCityBenchmark = { startedAt: performance.now() };
    window.__machineCityLongTasks = [];
    if ('PerformanceObserver' in window) {
      try {
        const observer = new PerformanceObserver(list => {
          for (const entry of list.getEntries()) window.__machineCityLongTasks.push({ start: entry.startTime, duration: entry.duration });
        });
        observer.observe({ type: 'longtask', buffered: true });
      } catch (_) {}
    }
  </script>`;
}

async function createBenchmarkServer() {
  let scenario = 12;
  const htmlTemplate = await readFile(join(STATIC, 'machine-city.html'), 'utf8');
  const html = htmlTemplate.replace('</head>', `${benchmarkBootstrap()}\n</head>`);
  const assets = new Map([
    ['/agent-platform/machine-city.css', ['machine-city.css', 'text/css; charset=utf-8']],
    ['/agent-platform/machine-city.js', ['machine-city.js', 'text/javascript; charset=utf-8']],
    ['/agent-platform/machine-city-background.webp', ['machine-city-background.webp', 'image/webp']],
  ]);
  const server = createServer(async (request, response) => {
    try {
      const url = new URL(request.url, 'http://127.0.0.1');
      response.setHeader('Cache-Control', 'no-store');
      response.setHeader('Cross-Origin-Opener-Policy', 'same-origin');
      if (url.pathname === '/benchmark/' || url.pathname === '/agent-platform/' || url.pathname === '/agent-platform') {
        response.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
        response.end(html);
        return;
      }
      if (url.pathname === '/benchmark/scenario') {
        const next = Number(url.searchParams.get('agents'));
        if (![12, 30].includes(next)) throw new Error('scenario must be 12 or 30');
        scenario = next;
        response.writeHead(200, { 'Content-Type': 'application/json' });
        response.end(JSON.stringify({ agents: scenario }));
        return;
      }
      if (url.pathname === '/agent-platform/api/v1/overview') {
        response.writeHead(200, { 'Content-Type': 'application/json' });
        response.end(JSON.stringify(makeSnapshot(scenario)));
        return;
      }
      const asset = assets.get(url.pathname);
      if (asset) {
        const [name, contentType] = asset;
        response.writeHead(200, { 'Content-Type': contentType });
        response.end(await readFile(join(STATIC, name)));
        return;
      }
      response.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
      response.end('not found');
    } catch (error) {
      response.writeHead(500, { 'Content-Type': 'text/plain; charset=utf-8' });
      response.end(error.message);
    }
  });
  await new Promise((resolvePromise, rejectPromise) => {
    server.once('error', rejectPromise);
    server.listen(0, '127.0.0.1', resolvePromise);
  });
  return {
    server,
    url: `http://127.0.0.1:${server.address().port}/benchmark/`,
    close: () => new Promise((resolvePromise, rejectPromise) => server.close(error => error ? rejectPromise(error) : resolvePromise())),
  };
}

async function waitForFile(path, timeoutMs = 15000) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    try { return await readFile(path, 'utf8'); } catch (_) {}
    await new Promise(resolvePromise => setTimeout(resolvePromise, 50));
  }
  throw new Error(`timed out waiting for ${basename(path)}`);
}

class CdpClient {
  constructor(url) {
    this.socket = new WebSocket(url);
    this.sequence = 0;
    this.pending = new Map();
    this.events = new Map();
  }
  async open() {
    await new Promise((resolvePromise, rejectPromise) => {
      this.socket.addEventListener('open', resolvePromise, { once: true });
      this.socket.addEventListener('error', rejectPromise, { once: true });
    });
    this.socket.addEventListener('message', async event => {
      const raw = typeof event.data === 'string' ? event.data
        : event.data instanceof ArrayBuffer ? new TextDecoder().decode(event.data)
          : typeof event.data?.text === 'function' ? await event.data.text()
            : String(event.data);
      const message = JSON.parse(raw);
      if (message.id) {
        const pending = this.pending.get(message.id);
        if (!pending) return;
        this.pending.delete(message.id);
        if (message.error) pending.reject(new Error(`${pending.method}: ${message.error.message}`));
        else pending.resolve(message.result);
        return;
      }
      for (const callback of this.events.get(message.method) || []) callback(message.params);
    });
    this.socket.addEventListener('close', event => progress(`CDP socket closed code=${event.code}`));
    this.socket.addEventListener('error', () => progress('CDP socket error'));
  }
  send(method, params = {}) {
    const id = ++this.sequence;
    return new Promise((resolvePromise, rejectPromise) => {
      this.pending.set(id, { resolve: resolvePromise, reject: rejectPromise, method });
      this.socket.send(JSON.stringify({ id, method, params }));
    });
  }
  once(method, timeoutMs = 15000) {
    return new Promise((resolvePromise, rejectPromise) => {
      const timeout = setTimeout(() => rejectPromise(new Error(`timed out waiting for ${method}`)), timeoutMs);
      const callback = params => {
        clearTimeout(timeout);
        this.events.set(method, (this.events.get(method) || []).filter(item => item !== callback));
        resolvePromise(params);
      };
      this.events.set(method, [...(this.events.get(method) || []), callback]);
    });
  }
  close() { this.socket.close(); }
}

async function evaluate(client, expression, { awaitPromise = true, returnByValue = true } = {}) {
  const result = await client.send('Runtime.evaluate', { expression, awaitPromise, returnByValue, userGesture: true });
  if (result.exceptionDetails) throw new Error(result.exceptionDetails.exception?.description || result.exceptionDetails.text);
  return result.result.value;
}

async function waitFor(client, expression, timeoutMs = 15000) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    if (await evaluate(client, expression)) return;
    await new Promise(resolvePromise => setTimeout(resolvePromise, 25));
  }
  throw new Error(`browser condition timed out: ${expression}`);
}

const frameMeasureExpression = durationMs => `(async () => {
  const duration = ${durationMs};
  const timestamps = [];
  const longTaskStart = window.__machineCityLongTasks.length;
  await new Promise(resolve => {
    const start = performance.now();
    const step = timestamp => {
      timestamps.push(timestamp);
      if (timestamp - start >= duration) resolve(); else requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  });
  const deltas = timestamps.slice(1).map((value, index) => value - timestamps[index]).filter(value => value > 0);
  const sorted = [...deltas].sort((a, b) => a - b);
  const percentile = value => sorted[Math.min(sorted.length - 1, Math.max(0, Math.ceil(sorted.length * value) - 1))] || null;
  const elapsed = timestamps.at(-1) - timestamps[0];
  const averageFps = elapsed > 0 ? (timestamps.length - 1) * 1000 / elapsed : 0;
  return {
    frames: timestamps.length,
    duration_ms: Number(elapsed.toFixed(2)),
    average_fps: Number(averageFps.toFixed(2)),
    display_fps: Math.round(averageFps),
    median_frame_ms: Number((percentile(.5) || 0).toFixed(2)),
    p95_frame_ms: Number((percentile(.95) || 0).toFixed(2)),
    p99_frame_ms: Number((percentile(.99) || 0).toFixed(2)),
    long_tasks: window.__machineCityLongTasks.slice(longTaskStart),
  };
})()`;

async function main() {
  const options = parseArguments(process.argv.slice(2));
  const chromePath = findChrome(options.chrome);
  await mkdir(dirname(options.output), { recursive: true });
  await mkdir(dirname(options.screenshot), { recursive: true });
  const profile = await mkdtemp(join(tmpdir(), 'herdr-machine-city-'));
  const benchmarkServer = await createBenchmarkServer();
  let chrome;
  let client;
  try {
    const chromeStarted = performance.now();
    progress('starting Chrome');
    const chromeArguments = [
      '--remote-debugging-port=0',
      '--remote-allow-origins=*',
      `--user-data-dir=${profile}`,
      '--window-size=1920,1080',
      '--force-device-scale-factor=1',
      '--no-first-run',
      '--disable-default-apps',
      '--disable-background-networking',
      '--disable-component-update',
      '--disable-sync',
      '--metrics-recording-only',
      'about:blank',
    ];
    if (!options.headed) chromeArguments.unshift('--headless=new');
    chrome = spawn(chromePath, chromeArguments, { stdio: ['ignore', 'ignore', 'pipe'] });
    chrome.once('exit', (code, signal) => progress(`Chrome exited code=${code} signal=${signal || 'none'}`));
    const chromeDiagnostics = [];
    chrome.stderr.setEncoding('utf8');
    chrome.stderr.on('data', value => {
      chromeDiagnostics.push(...value.trim().split(/\r?\n/).filter(Boolean));
      if (chromeDiagnostics.length > 20) chromeDiagnostics.splice(0, chromeDiagnostics.length - 20);
    });
    const activePort = (await waitForFile(join(profile, 'DevToolsActivePort'))).trim().split(/\r?\n/);
    const chromeReadyMs = performance.now() - chromeStarted;
    progress('Chrome debugging endpoint ready');
    const port = Number(activePort[0]);
    const version = await (await fetch(`http://127.0.0.1:${port}/json/version`)).json();
    const target = await (await fetch(`http://127.0.0.1:${port}/json/new?${encodeURIComponent('about:blank')}`, { method: 'PUT' })).json();
    client = new CdpClient(target.webSocketDebuggerUrl);
    await client.open();
    progress('connected to dashboard tab');
    await Promise.all([client.send('Page.enable'), client.send('Runtime.enable')]);
    progress('Page and Runtime domains enabled');
    await client.send('Emulation.setDeviceMetricsOverride', {
      width: 1920, height: 1080, deviceScaleFactor: 1, mobile: false,
      screenWidth: 1920, screenHeight: 1080,
    });
    progress('viewport configured');
    await client.send('Page.navigate', { url: benchmarkServer.url });
    progress('navigation command accepted');
    await waitFor(client, `document.readyState === 'complete'`);
    progress('dashboard loaded');
    await waitFor(client, `document.querySelector('#swarm-kpis .swarm-kpi:first-child b')?.textContent.trim() === '12'
      && document.querySelector('#film-view')?.hidden === false
      && document.querySelector('#webgl-fallback')?.hidden === true`);
    const interactiveMs = await evaluate(client, 'performance.now()');
    progress(`interactive in ${interactiveMs.toFixed(2)} ms`);
    await new Promise(resolvePromise => setTimeout(resolvePromise, 1000));
    const fps12 = await evaluate(client, frameMeasureExpression(5000));
    progress(`12-agent sample: ${fps12.average_fps.toFixed(2)} FPS`);
    const updateMs = await evaluate(client, `(async () => {
      await fetch('/benchmark/scenario?agents=30', { cache: 'no-store' });
      const button = document.querySelector('#demo-toggle');
      if (button.getAttribute('aria-pressed') !== 'false') button.click();
      button.click();
      await new Promise(requestAnimationFrame);
      const started = performance.now();
      button.click();
      while (document.querySelector('#swarm-kpis .swarm-kpi:first-child b')?.textContent.trim() !== '30') {
        if (performance.now() - started > 5000) throw new Error('telemetry update timeout');
        await new Promise(resolve => setTimeout(resolve, 5));
      }
      return performance.now() - started;
    })()`);
    progress(`telemetry visible in ${updateMs.toFixed(2)} ms`);
    await new Promise(resolvePromise => setTimeout(resolvePromise, 1000));
    const fps30 = await evaluate(client, frameMeasureExpression(5000));
    progress(`30-agent sample: ${fps30.average_fps.toFixed(2)} FPS`);
    const renderer = await evaluate(client, `(() => {
      const canvas = document.querySelector('#machine-scene');
      const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
      if (!gl) return { available: false };
      const extension = gl.getExtension('WEBGL_debug_renderer_info');
      return {
        available: true,
        vendor: extension ? gl.getParameter(extension.UNMASKED_VENDOR_WEBGL) : gl.getParameter(gl.VENDOR),
        renderer: extension ? gl.getParameter(extension.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER),
        version: gl.getParameter(gl.VERSION),
      };
    })()`);
    const screenshot = await client.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false });
    await writeFile(options.screenshot, Buffer.from(screenshot.data, 'base64'));
    const reducedMotion = await evaluate(client, `(async () => {
      const button = document.querySelector('#motion-toggle');
      if (document.documentElement.dataset.motion !== 'reduced') button.click();
      await new Promise(requestAnimationFrame);
      const card = document.querySelector('.coordinator-card');
      const style = getComputedStyle(card);
      return {
        data_motion: document.documentElement.dataset.motion,
        button_pressed: button.getAttribute('aria-pressed'),
        transition_duration: style.transitionDuration,
        animation_name: style.animationName,
        canvas_present: Boolean(document.querySelector('#machine-scene')),
        fallback_hidden: document.querySelector('#webgl-fallback').hidden,
      };
    })()`);

    const measuredAt = new Date().toISOString();
    const bundle = await readFile(join(STATIC, 'machine-city.js'));
    const report = {
      schema_version: 1,
      status: 'measured',
      measured_at_utc: measuredAt,
      source: {
        repository: 'https://github.com/Bbambaaamm/herdr.git',
        commit: git(['rev-parse', 'HEAD']),
        dirty: Boolean(git(['status', '--short'])),
        bundle: 'agent_platform_dashboard/static/machine-city.js',
        bundle_sha256: createHash('sha256').update(bundle).digest('hex'),
        bundle_last_commit: git(['log', '-1', '--format=%H', '--', 'agent_platform_dashboard/static/machine-city.js']),
      },
      operator_device: {
        platform: `${os.platform()} ${os.release()} ${os.arch()}`,
        cpu: os.cpus()[0]?.model || 'unknown',
        logical_cpus: os.cpus().length,
        memory_gib: Number((os.totalmem() / 1024 ** 3).toFixed(1)),
        browser: version.Browser,
        user_agent: version['User-Agent'],
        viewport: '1920x1080@1x',
        mode: options.headed ? 'headed' : 'headless-new',
        chrome_start_ms: Number(chromeReadyMs.toFixed(2)),
        webgl: renderer,
      },
      measurements: {
        initial_interactive_ms: Number(interactiveMs.toFixed(2)),
        telemetry_to_visible_ms: Number(updateMs.toFixed(2)),
        fps_12_active_agents: fps12,
        fps_30_active_agents: fps30,
        reduced_motion: reducedMotion,
      },
      thresholds: THRESHOLDS,
      acceptance: {
        initial_interactive: interactiveMs <= THRESHOLDS.interactiveMs,
        telemetry_to_visible: updateMs <= THRESHOLDS.updateMs,
        fps_12: fps12.display_fps >= THRESHOLDS.fps12,
        fps_30: fps30.average_fps >= THRESHOLDS.fps30,
        reduced_motion: reducedMotion.data_motion === 'reduced'
          && reducedMotion.button_pressed === 'true'
          && reducedMotion.transition_duration === '0s'
          && reducedMotion.animation_name === 'none'
          && reducedMotion.canvas_present
          && reducedMotion.fallback_hidden,
      },
      artifacts: { screenshot: options.screenshot },
    };
    report.acceptance.pass = Object.values(report.acceptance).every(Boolean);
    report.status = report.acceptance.pass ? 'pass' : 'fail';
    await writeFile(options.output, `${JSON.stringify(report, null, 2)}\n`);
    progress(`report written to ${options.output}`);
    process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
    if (!report.acceptance.pass) process.exitCode = 1;
  } finally {
    progress('cleaning up');
    client?.close();
    if (chrome && chrome.exitCode == null) {
      chrome.kill();
      await Promise.race([
        new Promise(resolvePromise => chrome.once('exit', resolvePromise)),
        new Promise(resolvePromise => setTimeout(resolvePromise, 3000)),
      ]);
    }
    benchmarkServer.server.closeAllConnections?.();
    await benchmarkServer.close();
    for (let attempt = 0; attempt < 5; attempt += 1) {
      try { await rm(profile, { recursive: true, force: true }); break; }
      catch (error) {
        if (attempt === 4 || error.code !== 'EBUSY') throw error;
        await new Promise(resolvePromise => setTimeout(resolvePromise, 250));
      }
    }
  }
}

await main();
