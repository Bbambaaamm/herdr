/* Contract tests, not a visual/browser acceptance test. Run: node --test dashboard-ui.test.js */
const test = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { join } = require('node:path');

const STATES = ['idle', 'receiving', 'working', 'tool', 'delegating', 'waiting_result', 'waiting_user', 'speaking', 'complete', 'error', 'offline'];
const source = readFileSync(join(__dirname, 'dashboard-ui.js'), 'utf8');
const modulePromise = import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);

function fixture() {
  const now = Math.floor(Date.now() / 1000);
  const sources = ['majak', 'quantlab'].flatMap(profile => [
    { profile, kind: 'herdr', status: 'available', reason: 'ok', observed_at: now,
      rows: [{ agent: `${profile}-hermes`, status: 'done' }, { agent: `${profile}-codex`, status: 'idle' }] },
    { profile, kind: 'router', status: 'available', reason: 'ok', data_at: now,
      rows: [{ task_id: null, requests: 1, input_tokens: null, output_tokens: 12, cost_microusd: null,
        actual_model: '<img src=x onerror=alert(1)>', provider: 'openai-codex',
        fallback_count: 0, successful_requests: 1, duration_ms: 100 }] },
  ]);
  sources.push(
    { profile: 'majak', kind: 'search', status: 'available', reason: 'ok', observed_at: now, data_at: now,
      rows: [{ route_mode: 'fast', provider: 'exa-keyless', fallback_provider: 'exa-keyless', searches: 2,
        successful_searches: 2, duration_ms: 200, max_duration_ms: 120, fallback_count: 1,
        cost_microusd: 0, result_count: 10, extract_count: 0 }] },
    { profile: 'quantlab', kind: 'search', status: 'available', reason: 'ok', observed_at: now, data_at: now,
      rows: [{ route_mode: 'deep', provider: 'nous-managed', fallback_provider: null, searches: 1,
        successful_searches: 1, duration_ms: 300, max_duration_ms: 300, fallback_count: 0,
        cost_microusd: null, result_count: 8, extract_count: 3 }] },
  );
  sources.push({
    profile: 'quantlab', kind: 'queue', status: 'available', reason: 'ok', observed_at: now, data_at: now,
    rows: [{ task_id: 'issue190-prepare-20260926', issue: 190, status: 'pending', attempts: 0,
      not_before: now + 3600, updated_at: now, agent: 'quantlab-hermes',
      kind: 'scheduled_acceptance', blocker: null }],
  });
  sources.push({
    profile: 'majak', kind: 'codex', status: 'available', reason: 'ok', observed_at: now, data_at: now,
    rows: [{
      used_percent: 82, window_minutes: 10080, resets_at: now + 3600, ordinary_usage_allowed: true,
      has_credits: false, credits_unlimited: false, credits_balance: '0', reset_credits_available: 0,
      lifetime_tokens: 123456789, peak_daily_tokens: 9000000, longest_running_turn_sec: 1200,
      current_streak_days: 7, longest_streak_days: 9,
      daily: [{ day: '2026-09-24', tokens: 1000 }, { day: '2026-09-25', tokens: 2000 }],
      limit_history: [{ at: now - 300, used_percent: 80 }, { at: now, used_percent: 82 }],
    }],
  });
  return { generated_at: now, sources };
}

async function harness(t, options = {}) {
  const globals = ['document', 'matchMedia', 'CSS', 'setInterval', 'fetch'];
  const saved = Object.fromEntries(globals.map(key => [key, Object.getOwnPropertyDescriptor(globalThis, key)]));
  t.after(() => {
    for (const key of globals) {
      if (saved[key]) Object.defineProperty(globalThis, key, saved[key]); else delete globalThis[key];
    }
  });
  const elements = new Map(), documentEvents = new Map(), intervals = [], mediaEvents = new Map(), overflowNodes = new Map();
  let activeElement = null, nodeSequence = 0;
  class Element {
    constructor(selector) {
      this.selector = selector; this.dataset = {}; this.style = {}; this.attrs = {}; this.events = new Map();
      this.children = []; this.hidden = ['#agent-detail', '#demo-panel', '#drawer-backdrop', '#webgl-fallback'].includes(selector);
      this.isConnected = true; this.textContent = ''; this.innerHTML = '';
      this.classList = { toggle() {} };
    }
    setAttribute(key, value) { this.attrs[key] = String(value); }
    getAttribute(key) { return this.attrs[key]; }
    removeAttribute(key) { delete this.attrs[key]; }
    addEventListener(type, callback) {
      this.events.set(type, [...(this.events.get(type) || []), callback]);
    }
    emit(type, details = {}) {
      const event = { currentTarget: this, target: this, preventDefault() { this.defaultPrevented = true; }, ...details };
      for (const callback of this.events.get(type) || []) callback(event);
      return event;
    }
    querySelectorAll(selector) {
      if (selector === 'button' && this.selector === '#demo-states') return this.children.filter(child => child instanceof Element);
      if (selector.startsWith('button:not(') && this.selector === '#agent-detail') return [get('#detail-close')];
      if (selector === '[data-overflow-profile]' && this.selector === '#film-view') {
        return ['majak', 'quantlab'].flatMap(profile => {
          if (!get(`#${profile}-agents`).innerHTML.includes(`data-overflow-profile="${profile}"`)) return [];
          if (!overflowNodes.has(profile)) {
            const button = new Element(`#overflow-${profile}`); button.dataset.overflowProfile = profile; overflowNodes.set(profile, button);
          }
          return [overflowNodes.get(profile)];
        });
      }
      return [];
    }
    querySelector(selector) { return get(selector); }
    closest(selector) { return selector === '.project' ? this.project : null; }
    replaceChildren(...children) { this.children = children; }
    append(...children) { this.children.push(...children); }
    focus() { activeElement = this; }
  }
  function get(selector) {
    if (!elements.has(selector)) elements.set(selector, new Element(selector));
    return elements.get(selector);
  }
  const viewButtons = ['film', 'work'].map(view => { const node = get(`#view-${view}`); node.dataset.view = view; return node; });
  const projectButtons = ['majak', 'quantlab'].map(profile => {
    const node = get(`#${profile}-title`); node.dataset.projectToggle = profile; node.attrs['aria-expanded'] = 'true';
    node.project = { querySelector: () => get(`#${profile}-agents`) }; return node;
  });
  globalThis.document = {
    hidden: false, body: { style: {} }, documentElement: { dataset: {} },
    get activeElement() { return activeElement; }, querySelector: get,
    querySelectorAll(selector) { return selector === '[data-view]' ? viewButtons : selector === '[data-project-toggle]' ? projectButtons : []; },
    createElement(type) { return new Element(`${type}-${++nodeSequence}`); },
    addEventListener(type, callback) { documentEvents.set(type, callback); },
  };
  globalThis.matchMedia = () => ({ matches: Boolean(options.reduced), addEventListener: (type, callback) => mediaEvents.set(type, callback) });
  globalThis.CSS = { escape: value => value };
  globalThis.setInterval = callback => { intervals.push(callback); return intervals.length; };
  let snapshot = fixture(), httpStatus = 200;
  globalThis.fetch = async () => ({ ok: httpStatus === 200, status: httpStatus, json: async () => structuredClone(snapshot) });
  const calls = { states: [], agents: [], demo: [], reduced: [], active: [], focused: [], activity: [] };
  const scene = {
    setState: value => calls.states.push(value), setDemo: value => calls.demo.push(value),
    setAgents: value => calls.agents.push(value), setReduced: value => calls.reduced.push(value), setActivity: value => calls.activity.push(value),
    setActive: value => calls.active.push(value), focusAgent: value => calls.focused.push(value),
    onSelect: callback => { calls.select = callback; },
  };
  const { mountDashboard } = await modulePromise;
  const ui = mountDashboard(options.factory || (() => scene));
  await new Promise(resolve => setImmediate(resolve));
  return {
    ui, get, calls, viewButtons, projectButtons, mediaEvents,
    snapshot: () => snapshot, setSnapshot: value => { snapshot = value; }, setHTTP: value => { httpStatus = value; },
    refresh: () => intervals[0](), tickAge: () => intervals[1](),
    click: selector => get(selector).emit('click'), documentEvents,
  };
}

test('partial telemetry stays explicit, Codex allowance is live, and snapshot values cannot inject HTML', async t => {
  const h = await harness(t);
  assert.equal(h.ui.diagnostics().freshSnapshot, true);
  assert.equal(h.get('#cost-total').textContent, '18 %');
  assert.match(h.get('#project-grid').innerHTML, /0 \/ 12 · 0 % req/);
  assert.match(h.get('#project-grid').innerHTML, /0 USD známé \+ 1 bez ceny/);
  assert.match(h.get('#observability-kpis').innerHTML, /123,5|123\.5|123/);
  assert.match(h.get('#observability-grid').innerHTML, /Codex tokeny po dnech/);
  assert.match(h.get('#observability-grid').innerHTML, /Fallback pressure/);
  assert.match(h.get('#project-grid').innerHTML, /&lt;img src=x onerror=alert\(1\)&gt;/);
  assert.doesNotMatch(h.get('#project-grid').innerHTML, /<img src=x/);
  assert.equal(h.calls.agents.at(-1).length, 4);
  assert.equal(h.get('#link-layer').children.length, 0, 'live status must not fabricate communication links');
});

test('search layer shows bounded real telemetry without query text', async t => {
  const h = await harness(t);
  assert.equal(h.get('#search-count').textContent, '3');
  assert.equal(h.get('#search-latency').textContent, '167 ms');
  const html = h.get('#search-grid').innerHTML;
  assert.match(html, /MAJÁK|MAJAK/);
  assert.match(html, /exa-keyless/);
  assert.match(html, /nous-managed/);
  assert.match(html, /FAST/);
  assert.match(html, /DEEP/);
  assert.match(html, /1 fallback|Fallbacky/);
  assert.doesNotMatch(html, /query_hash|official OpenAI|prompt/i);
});

test('durable QuantLab queue renders safe metadata and drives coordinator state', async t => {
  const h = await harness(t);
  assert.equal(h.get('#queue-count').textContent, '1');
  assert.equal(h.ui.diagnostics().queueActive, 1);
  assert.match(h.get('#queue-list').innerHTML, /issue190-prepare-20260926/);
  assert.match(h.get('#queue-list').innerHTML, /#190/);
  assert.match(h.get('#queue-list').innerHTML, /scheduled_acceptance/);
  assert.match(h.get('#coordinator-next').textContent, /issue190-prepare-20260926/);
  assert.equal(h.get('#coordinator-current').textContent, 'Žádná');
  assert.doesNotMatch(h.get('#queue-list').innerHTML, /prompt|PRIVATE|tool_args|log/i);

  const queue = h.snapshot().sources.find(item => item.kind === 'queue');
  queue.rows[0].status = 'running';
  queue.rows[0].attempts = 1;
  await h.refresh();
  assert.equal(h.ui.diagnostics().state, 'working');
  assert.equal(h.get('#queue-count').textContent, '1');
  assert.match(h.get('#face-task').textContent, /#190/);
  assert.match(h.get('#face-task').textContent, /issue190-prepare-20260926/);
  assert.match(h.get('#coordinator-current').textContent, /issue190-prepare-20260926/);
  assert.equal(h.get('#coordinator-next').textContent, 'Žádná');
  assert.equal(h.calls.activity.at(-1).activeAgent, 'quantlab-hermes');
  assert.equal(h.calls.activity.at(-1).running, 1);
  assert.equal(h.get('#quantlab-project-state').textContent, 'pracuje');

  h.calls.select('quantlab-hermes');
  assert.match(h.get('#detail-metrics').innerHTML, /issue190-prepare-20260926/);
  assert.match(h.get('#detail-events').innerHTML, /Durable queue/);
  assert.doesNotMatch(h.get('#detail-events').innerHTML, /PRIVATE|tool_args|secret payload|raw log/i);
});

test('blocked queue task raises attention with sanitized blocker only', async t => {
  const h = await harness(t);
  const queue = h.snapshot().sources.find(item => item.kind === 'queue');
  queue.rows[0].status = 'blocked';
  queue.rows[0].blocker = 'github_write_auth_required';
  await h.refresh();
  assert.equal(h.ui.diagnostics().state, 'waiting_user');
  assert.match(h.get('#attention-summary').textContent, /issue190-prepare-20260926/);
  assert.match(h.get('#queue-list').innerHTML, /github_write_auth_required/);
  assert.doesNotMatch(h.get('#queue-list').innerHTML, /PRIVATE|secret|prompt/i);
});

test('queue source is QuantLab-only in browser validation', async t => {
  const h = await harness(t);
  const queue = h.snapshot().sources.find(item => item.kind === 'queue');
  queue.profile = 'majak';
  await h.refresh();
  assert.equal(h.ui.diagnostics().freshSnapshot, false);
  assert.equal(h.ui.diagnostics().state, 'offline');
});

test('both views preserve selected agent and detail follows new live status', async t => {
  const h = await harness(t);
  h.calls.select('majak-codex');
  assert.equal(h.get('#agent-detail').hidden, false);
  assert.equal(h.ui.diagnostics().selectedAgent, 'majak-codex');
  h.viewButtons[1].emit('click');
  assert.equal(h.ui.diagnostics().view, 'work');
  assert.equal(h.get('#film-view').hidden, true);
  assert.equal(h.get('#work-view').hidden, false);
  h.viewButtons[0].emit('click');
  assert.equal(h.ui.diagnostics().view, 'film');
  assert.equal(h.ui.diagnostics().selectedAgent, 'majak-codex');
  h.snapshot().sources[0].rows[1].status = 'blocked';
  await h.refresh();
  assert.equal(h.ui.diagnostics().state, 'waiting_user');
  assert.match(h.get('#detail-status').textContent, /Blokováno/);
  assert.equal(h.get('#attention-action').hidden, false);
  assert.equal(h.calls.focused.at(-1), 'majak-codex');
});

test('all eleven demo states are explicit and target a valid machine without changing live data', async t => {
  const h = await harness(t);
  const original = structuredClone(h.snapshot());
  h.click('#demo-toggle');
  assert.equal(h.ui.diagnostics().mode, 'demo');
  assert.match(h.get('#header-status').textContent, /DEMO/);
  const buttons = h.get('#demo-states').children;
  assert.deepEqual(buttons.map(button => button.dataset.demoState), STATES);
  for (const button of buttons) {
    button.emit('click');
    assert.equal(h.ui.diagnostics().state, button.dataset.demoState);
    assert.equal(h.calls.demo.at(-1).enabled, true);
    assert.equal(h.calls.demo.at(-1).target, 'majak-codex');
    assert.match(h.get('#face-task').textContent, /^DEMO/);
    assert.match(h.get('#majak-agents').innerHTML, /Ukázkový stroj · syntetický/);
    assert.match(h.get('#majak-agents').innerHTML, /DEMO · Čeká/);
    assert(h.get('#majak-agents').innerHTML.includes(`data-agent="majak-codex" data-state="${button.dataset.demoState}"`));
    assert.doesNotMatch(h.get('#project-grid').innerHTML, /DEMO/);
  }
  assert.deepEqual(h.snapshot(), original);
  assert.equal(h.get('#request-count').textContent, '2');
  h.click('#demo-toggle');
  assert.equal(h.ui.diagnostics().mode, 'live');
  assert.equal(h.calls.demo.at(-1).enabled, false);
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(h.ui.diagnostics().state, 'complete');
  assert.doesNotMatch(h.get('#majak-agents').innerHTML, /DEMO/);
});

test('demo focus changes synthetic film target without changing actual detail or work states', async t => {
  const h = await harness(t);
  const original = structuredClone(h.snapshot());
  h.click('#demo-toggle');
  h.get('#demo-states').children.find(button => button.dataset.demoState === 'working').emit('click');
  h.calls.select('quantlab-codex');
  assert.equal(h.calls.demo.at(-1).target, 'quantlab-codex');
  assert.match(h.get('#quantlab-agents').innerHTML, /data-agent="quantlab-codex" data-state="working"/);
  assert.match(h.get('#quantlab-agents').innerHTML, /DEMO · Zpracovává úlohu/);
  assert.match(h.get('#majak-agents').innerHTML, /data-agent="majak-codex" data-state="idle"/);
  assert.match(h.get('#detail-status').textContent, /Živý stav: Čeká/);
  assert.doesNotMatch(h.get('#project-grid').innerHTML, /DEMO/);
  assert.deepEqual(h.snapshot(), original);
});

test('completion effect is emitted once per state transition rather than on every poll', async t => {
  const h = await harness(t);
  assert.equal(h.calls.states.filter(state => state === 'complete').length, 1);
  await h.refresh(); await h.refresh();
  assert.equal(h.calls.states.filter(state => state === 'complete').length, 1);
});

test('stale or failed live data clears metrics and drawer instead of looking active', async t => {
  const h = await harness(t);
  h.calls.select('majak-codex');
  h.snapshot().generated_at = Math.floor(Date.now() / 1000) - 100;
  await h.refresh();
  assert.equal(h.ui.diagnostics().freshSnapshot, false);
  assert.equal(h.ui.diagnostics().state, 'offline');
  assert.equal(h.get('#agent-count').textContent, 'Neznámé');
  assert.equal(h.get('#cost-total').textContent, 'Nedostupné');
  assert.match(h.get('#work-freshness').textContent, /90 s/);
  assert.match(h.get('#detail-status').textContent, /Odpojeno/);
  assert.equal(h.get('#attention-action').textContent, 'Obnovit data');
  h.setHTTP(503); await h.refresh();
  assert.equal(h.ui.diagnostics().state, 'offline');
  assert.match(h.get('#work-freshness').textContent, /připojení/);
});

test('snapshot freshness expires between fetches', async t => {
  const h = await harness(t);
  const originalNow = Date.now;
  t.after(() => { Date.now = originalNow; });
  Date.now = () => originalNow() + 91000;
  h.tickAge();
  assert.equal(h.ui.diagnostics().state, 'offline');
  assert.equal(h.ui.diagnostics().freshSnapshot, false);
});

test('WebGL initialization failure leaves live working/text view usable', async t => {
  const h = await harness(t, { factory: () => { throw new Error('WebGL unavailable'); } });
  assert.equal(h.ui.diagnostics().sceneAvailable, false);
  assert.equal(h.ui.diagnostics().view, 'work');
  assert.equal(h.get('#work-view').hidden, false);
  assert.equal(h.get('#webgl-fallback').hidden, false);
  assert.equal(h.ui.diagnostics().freshSnapshot, true);
  assert.match(h.get('#project-grid').innerHTML, /majak-codex/);
});

for (const eventName of ['webglcontextlost', 'scene-unavailable']) {
  test(`${eventName} switches to usable text view without losing selection`, async t => {
    const h = await harness(t);
    h.calls.select('quantlab-codex');
    h.get('#machine-scene').emit(eventName);
    assert.equal(h.ui.diagnostics().sceneAvailable, false);
    assert.equal(h.ui.diagnostics().view, 'work');
    assert.equal(h.ui.diagnostics().selectedAgent, 'quantlab-codex');
    assert.equal(h.get('#work-view').hidden, false);
    assert.equal(h.get('#webgl-fallback').hidden, false);
    assert.equal(h.ui.diagnostics().freshSnapshot, true);
  });
}

test('reduced motion and inactive tab are forwarded explicitly to the renderer', async t => {
  const h = await harness(t, { reduced: true });
  assert.equal(h.ui.diagnostics().reduced, true);
  assert.equal(h.calls.reduced.at(-1), true);
  assert.equal(h.get('#motion-toggle').attrs['aria-pressed'], 'true');
  assert.equal(h.get('#face-signal').style.boxShadow, 'none');
  h.click('#motion-toggle');
  assert.equal(h.calls.reduced.at(-1), false);
  globalThis.document.hidden = true;
  h.documentEvents.get('visibilitychange')();
  assert.equal(h.calls.active.at(-1), false);
});

test('project collapsing preserves identities while marking corresponding scene machines hidden', async t => {
  const h = await harness(t);
  h.projectButtons[0].emit('click');
  assert.equal(h.get('#majak-agents').hidden, true);
  const rows = h.calls.agents.at(-1);
  assert.deepEqual(rows.filter(row => row.profile === 'majak').map(row => row.visible), [false, false]);
  assert.deepEqual(rows.filter(row => row.profile === 'quantlab').map(row => row.visible), [true, true]);
  assert.equal(rows.length, 4);
});

test('additional agents remain accessible without unprojected film labels or invented machine slots', async t => {
  const h = await harness(t);
  h.snapshot().sources[0].rows.push(
    { agent: 'majak-research-worker', status: 'working' },
    { agent: 'majak-review-worker', status: 'idle' },
  );
  h.snapshot().sources[2].rows.push({ agent: 'quantlab-test-worker', status: 'working' });
  await h.refresh();
  const majak = h.get('#majak-agents').innerHTML, quantlab = h.get('#quantlab-agents').innerHTML;
  assert.match(majak, /\+2 dalších agentů — pracovní přehled/);
  assert.match(quantlab, /\+1 dalších agentů — pracovní přehled/);
  assert.doesNotMatch(majak, /data-agent="majak-research-worker"/);
  assert.doesNotMatch(majak, /data-agent="majak-review-worker"/);
  assert.doesNotMatch(quantlab, /data-agent="quantlab-test-worker"/);
  assert.match(h.get('#project-grid').innerHTML, /data-agent="majak-research-worker"/);
  assert.match(h.get('#project-grid').innerHTML, /data-agent="quantlab-test-worker"/);
  assert.equal(h.get('#agent-count').textContent, '7');
  assert.equal(h.calls.agents.at(-1).length, 4);
  assert.match(h.get('#data-caveat').textContent, /Dalších 3 agentů/);
  const overflow = h.get('#film-view').querySelectorAll('[data-overflow-profile]');
  assert.equal(overflow.length, 2); overflow[0].emit('click');
  assert.equal(h.ui.diagnostics().view, 'work');
  h.calls.select('majak-research-worker');
  assert.equal(h.ui.diagnostics().selectedAgent, 'majak-research-worker');
  assert.match(h.get('#detail-status').textContent, /Pracuje/);
});
