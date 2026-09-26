import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import { createQuantumCore } from './machine-core.js';

const STATES = ['idle','receiving','working','tool','delegating','waiting_result','waiting_user','speaking','complete','error','offline'];

function step(core, state, activity = {}, reduced = false) {
  for (let i = 0; i < 90; i++) {
    core.update({ time: i / 60, delta: 1 / 60, state, activity, reduced });
  }
  core.group.updateMatrixWorld(true);
  return core.diagnostics();
}

for (const low of [false, true]) {
  test(`quantum core ${low ? 'low' : 'high'}: finite volumetric geometry`, () => {
    const core = createQuantumCore({ low });
    try {
      const info = step(core, 'working', { running: 1, pending: 3, workingAgents: 1 });
      assert.equal(info.type, 'reactive-quantum-core');
      assert.ok(info.rings >= (low ? 7 : 11));
      assert.ok(info.particles >= (low ? 600 : 1400));
      assert.ok(info.nodes >= (low ? 24 : 48));
      assert.ok(info.energy > .8);
      const bounds = new THREE.Box3().setFromObject(core.group);
      const size = bounds.getSize(new THREE.Vector3());
      assert.ok(size.x > 4 && size.y > 4 && size.z > 4);
      core.group.traverse(object => {
        if (!object.geometry?.getAttribute?.('position')) return;
        for (const value of object.geometry.getAttribute('position').array) assert.ok(Number.isFinite(value));
      });
    } finally { core.dispose(); }
  });
  test(`quantum core ${low ? 'low' : 'high'}: every state remains deterministic and reactive`, () => {
    const core = createQuantumCore({ low });
    try {
      for (const state of STATES) {
        const info = step(core, state, { running: state === 'working' ? 1 : 0, pending: 2 }, true);
        assert.equal(info.state, state);
        assert.ok(Number.isFinite(info.energy));
        assert.ok(info.energy >= .08 && info.energy <= 1.28);
      }
      const calm = step(core, 'idle', { running: 0, pending: 0, workingAgents: 0 });
      const busy = step(core, 'working', { running: 1, pending: 6, workingAgents: 2 });
      assert.ok(busy.energy > calm.energy, `${busy.energy} <= ${calm.energy}`);
      const blocked = step(core, 'waiting_user', { blocked: 1 });
      assert.equal(blocked.activity.blocked, 1);
    } finally { core.dispose(); }
  });

  test(`quantum core ${low ? 'low' : 'high'}: activity can be updated independently of state`, () => {
    const core = createQuantumCore({ low });
    try {
      core.setActivity({ running: 2, pending: 4, activeAgent: 'quantlab-hermes' });
      const info = step(core, 'working');
      assert.equal(info.activity.running, 2);
      assert.equal(info.activity.pending, 4);
      assert.equal(info.activity.activeAgent, 'quantlab-hermes');
    } finally { core.dispose(); }
  });
}