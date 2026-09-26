import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import { createMachineHead } from './machine-head.js';

const step = (head, state, options = {}) => {
  for (let i = 0; i < 90; i++) head.update({ time: i / 60, delta: 1 / 60, state, ...options });
  head.group.updateMatrixWorld(true);
};

for (const low of [false, true]) {
  test(`anatomical head ${low ? 'low' : 'high'}: finite 3D geometry, openings and batching`, () => {
    const head = createMachineHead({ low });
    try {
      const info = head.diagnostics();
      assert.equal(info.vertices, 468);
      assert.equal(info.faceTriangles, 852, 'closed canonical eye/mouth triangles are removed');
      assert.equal(info.usesFaceBitmap, false);
      assert.equal(info.independentOcularGimbals, 2);
      assert.ok(info.componentInstances >= (low ? 4500 : 9000));
      assert.ok(info.estimatedDrawCalls <= (low ? 45 : 65), JSON.stringify(info));
      assert.ok(info.localBounds.max.every(Number.isFinite));
      assert.ok(info.localBounds.min.every(Number.isFinite));
      const bounds = new THREE.Box3().setFromObject(head.group);
      const size = bounds.getSize(new THREE.Vector3());
      assert.ok(size.z > 3, 'real skull/nose depth, not a flat image');
      assert.ok(size.x > 4 && size.y > 5);
      head.group.traverse(object => {
        if (!object.isMesh) return;
        const values = object.geometry.getAttribute('position').array;
        for (const value of values) assert.ok(Number.isFinite(value));
        assert.equal(object.material.map, null, 'no photographic face map');
      });
    } finally { head.dispose(); }
  });

  test(`anatomical head ${low ? 'low' : 'high'}: real mandibular bone and ocular gaze`, () => {
    const head = createMachineHead({ low });
    try {
      step(head, 'idle');
      const idle = head.diagnostics();
      step(head, 'speaking', { gazeX: .8, gazeY: .4 });
      const speaking = head.diagnostics();
      const jaw = head.group.getObjectByName('Articulated mechanical mandible');
      const skin = head.group.getObjectByName('Skinned canonical anatomical facial shell');
      assert.ok(speaking.jawAngleRadians > idle.jawAngleRadians + .04);
      assert.ok(Math.abs(jaw.rotation.x - skin.skeleton.bones[1].rotation.x) < 1e-10);
      assert.ok(speaking.ocularYawRadians > .15);
      assert.ok(head.group.getObjectByName('Right ocular gimbal'));
      const jawSkin = skin.geometry.getAttribute('skinWeight');
      assert.equal(jawSkin.getY(14), 1, 'inner lower lip follows mandible');
      assert.equal(jawSkin.getY(13), 0, 'inner upper lip stays attached to cranium');
      assert.ok(jawSkin.getY(152) > .99, 'chin has true jaw deformation');
    } finally { head.dispose(); }
  });

  test(`anatomical head ${low ? 'low' : 'high'}: reduced motion and all state values`, () => {
    const head = createMachineHead({ low });
    try {
      const states = ['idle', 'receiving', 'working', 'tool', 'delegating', 'waiting_result', 'waiting_user', 'speaking', 'complete', 'error', 'offline'];
      for (const state of states) {
        step(head, state, { reduced: true });
        const info = head.diagnostics();
        assert.equal(info.state, state);
        assert.ok(info.jawAngleRadians <= .0041, `reduced motion disables lip motion for ${state}`);
        assert.ok(info.gaze.every(Number.isFinite));
      }
      const shell = head.group.getObjectByName('Head rotation rig');
      assert.equal(shell.rotation.z, 0);
      assert.equal(shell.position.y, 0);
      const eye = head.group.getObjectByName('Left ocular gimbal');
      const light = eye.getObjectByName('Independent gaze pivot').children.find(child => child.material?.emissive?.getHex() === 0xffbb58);
      assert.ok(light.material.emissiveIntensity < .1, 'offline is visibly dimmed');
    } finally { head.dispose(); }
  });

  test(`anatomical head ${low ? 'low' : 'high'}: one reduced-motion render settles active rig`, () => {
    const head = createMachineHead({ low });
    try {
      step(head, 'working', { gazeX: 1, gazeY: .6 });
      step(head, 'speaking', { gazeX: 1, gazeY: .6 });
      assert.ok(head.diagnostics().jawAngleRadians > .04);
      assert.ok(head.diagnostics().ocularYawRadians > .2);
      head.update({ time: 8, delta: 1 / 60, state: 'offline', reduced: true });
      const info = head.diagnostics();
      assert.equal(info.jawAngleRadians, .004);
      assert.deepEqual(info.gaze, [0, 0]);
      assert.equal(info.ocularYawRadians, 0);
      const shell = head.group.getObjectByName('Head rotation rig');
      assert.ok(Math.abs(shell.rotation.y) < 1e-10);
      assert.ok(Math.abs(shell.rotation.x - .01) < 1e-10);
      const eye = head.group.getObjectByName('Left ocular gimbal');
      const lens = eye.getObjectByName('Independent gaze pivot').children.find(child => child.material?.emissive?.getHex() === 0xffbb58);
      assert.equal(lens.material.emissiveIntensity, .04);
      const amberMaterials = new Set();
      head.group.traverse(object => {
        if (object.isMesh && object.material.emissive?.getHex() === 0xffb653) amberMaterials.add(object.material);
      });
      for (const mat of amberMaterials) assert.equal(mat.emissiveIntensity, .018);
      head.update({ time: 9, state: 'complete', reduced: true });
      for (const mat of amberMaterials) assert.ok(Math.abs(mat.emissiveIntensity - .555) < 1e-10, 'no frozen completion flash');
    } finally { head.dispose(); }
  });
}
