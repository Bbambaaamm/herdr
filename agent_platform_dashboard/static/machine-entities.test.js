import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {createMachineDrone, createMachineCity} from './machine-entities.js';

function meshes(root) {
  const result = [];
  root.traverse(object => {
    if (object.isMesh) result.push(object);
  });
  return result;
}

function materials(root) {
  return [...new Set(meshes(root).flatMap(mesh => Array.isArray(mesh.material) ? mesh.material : [mesh.material]))];
}

function assertRealFiniteGeometry(root) {
  let vertices = 0;
  root.traverse(object => {
    assert.equal(Boolean(object.isSprite), false, `${object.name}: sprites are not machine geometry`);
    if (!object.isMesh) return;
    const position = object.geometry.getAttribute('position');
    assert.ok(position, `${object.name}: geometry contains position data`);
    assert.ok(position.count >= 3);
    vertices += position.count;
    for (const value of position.array) assert.ok(Number.isFinite(value), 'geometry cannot contain NaN/Infinity');
    if (object.isInstancedMesh) {
      for (const value of object.instanceMatrix.array) assert.ok(Number.isFinite(value));
    }
  });
  assert.ok(vertices > 10000, `expected detailed meshes, got ${vertices} vertices`);
  for (const material of materials(root)) {
    for (const value of Object.values(material)) {
      assert.equal(Boolean(value?.isTexture), false, 'machines must not be image-textured impostors');
    }
  }
}

function matrices(drone, name = 'articulated-cables') {
  return Array.from(drone.group.getObjectByName(name).instanceMatrix.array);
}

function dispose(root) {
  for (const mesh of meshes(root)) mesh.geometry.dispose();
  for (const material of materials(root)) material.dispose();
}

for (const kind of ['hermes', 'codex']) {
  for (const low of [false, true]) {
    const label = `${kind}/${low ? 'low' : 'high'}`;

    test(`${label}: true 3D bounded geometry, independent hierarchy, draw-call budget`, () => {
      const drone = createMachineDrone({kind, low, seed: 71});
      try {
        assert.ok(drone.group.isGroup);
        assert.ok(drone.group.getObjectByName('hovering-articulated-body')?.isGroup);
        assertRealFiniteGeometry(drone.group);
        const bounds = new THREE.Box3().setFromObject(drone.group);
        const extent = bounds.getSize(new THREE.Vector3());
        assert.ok(extent.x > 1 && extent.x < 4.5, `span x ${extent.x}`);
        assert.ok(extent.y > 1 && extent.y < 4, `span y ${extent.y}`);
        assert.ok(extent.z > 0.65 && extent.z < 2.8, `volume z ${extent.z}`);
        const diagnostics = drone.diagnostics();
        assert.equal(diagnostics.geometryOnly, true);
        assert.equal(diagnostics.kind, kind);
        assert.ok(diagnostics.staticPieces > 100);
        assert.ok(diagnostics.drawCalls <= 12);
        assert.equal(diagnostics.segmentsPerArm, low ? 11 : 17);
        assert.ok(diagnostics.articulatedArms >= 6);
        assert.equal(meshes(drone.group).filter(mesh => mesh.isInstancedMesh).length, 4);
      } finally { dispose(drone.group); }
    });

    for (const state of ['working', 'idle']) {
      test(`${label}: ${state} moves articulated geometry, not just the root`, () => {
        const drone = createMachineDrone({kind, low, seed: 73});
        try {
          drone.group.position.set(8, 9, 10);
          drone.update({time: 1, state, delta: 0.05});
          const first = matrices(drone);
          // Low quality intentionally updates its arm matrices every second frame.
          drone.update({time: 4, state, delta: 0.05});
          drone.update({time: 4, state, delta: 0.05});
          const second = matrices(drone);
          assert.notDeepEqual(first, second);
          assert.deepEqual(drone.group.position.toArray(), [8, 9, 10], 'caller owns root placement');
          const segments = drone.diagnostics().segmentsPerArm;
          const firstArmStart = 16 * 3;
          const secondArmStart = 16 * (segments + 3);
          const firstChange = second.slice(firstArmStart, firstArmStart + 16)
            .map((value, index) => value - first[firstArmStart + index]);
          const secondChange = second.slice(secondArmStart, secondArmStart + 16)
            .map((value, index) => value - first[secondArmStart + index]);
          assert.ok(firstChange.some(value => Math.abs(value) > 0.00001));
          assert.ok(secondChange.some(value => Math.abs(value) > 0.00001));
          assert.notDeepEqual(firstChange, secondChange, 'each arm must articulate independently');
        } finally { dispose(drone.group); }
      });
    }

    test(`${label}: reduced motion fixes arms and body regardless of clock`, () => {
      const drone = createMachineDrone({kind, low, seed: 75});
      try {
        drone.update({time: 1, state: 'working', reduced: true});
        const first = matrices(drone);
        const body = drone.group.getObjectByName('hovering-articulated-body');
        const initialPose = [...body.position.toArray(), ...body.quaternion.toArray()].map(value => value || 0);
        drone.update({time: 100, state: 'working', reduced: true});
        assert.deepEqual(matrices(drone), first);
        assert.deepEqual([...body.position.toArray(), ...body.quaternion.toArray()].map(value => value || 0), initialPose);
      } finally { dispose(drone.group); }
    });

    test(`${label}: offline dims emissive sensors and stops internal activity`, () => {
      const drone = createMachineDrone({kind, low, seed: 76});
      try {
        drone.update({time: 1, state: 'working', delta: 1});
        const lights = materials(drone.group).filter(material => material.emissive?.getHex() > 0);
        assert.ok(lights.length >= 2);
        const working = lights.map(material => material.emissiveIntensity);
        drone.update({time: 2, state: 'offline', delta: 1});
        drone.update({time: 2, state: 'offline', delta: 1});
        const offlinePose = matrices(drone);
        for (const [index, material] of lights.entries()) {
          assert.ok(material.emissiveIntensity < working[index] * 0.2, 'offline light must be substantially dimmed');
        }
        drone.update({time: 200, state: 'offline', delta: 1});
        drone.update({time: 200, state: 'offline', delta: 1});
        assert.deepEqual(matrices(drone), offlinePose);
      } finally { dispose(drone.group); }
    });

    test(`${label}: reduced offline applies final sensor state in one render`, () => {
      const busyDrone = createMachineDrone({kind, low, seed: 77});
      const freshDrone = createMachineDrone({kind, low, seed: 77});
      try {
        busyDrone.update({time: 1, state: 'working', reduced: true, delta: 1 / 60});
        const lights = materials(busyDrone.group).filter(material => material.emissive?.getHex() > 0);
        const working = lights.map(material => material.emissiveIntensity);
        busyDrone.update({time: 2, state: 'offline', reduced: true, delta: 1 / 60});
        freshDrone.update({time: 0, state: 'offline', reduced: true, delta: 1 / 60});
        const freshLights = materials(freshDrone.group).filter(material => material.emissive?.getHex() > 0);
        assert.deepEqual(lights.map(material => material.emissiveIntensity),
          freshLights.map(material => material.emissiveIntensity));
        for (const [index, material] of lights.entries()) {
          assert.ok(material.emissiveIntensity < working[index] * 0.2,
            'one reduced-motion render must completely dim an offline machine');
        }
      } finally {
        dispose(busyDrone.group);
        dispose(freshDrone.group);
      }
    });
  }
}

for (const low of [false, true]) {
  test(`city/${low ? 'low' : 'high'}: quiet server-room volume, central clearance and static geometry`, () => {
    const city = createMachineCity({low});
    try {
      assertRealFiniteGeometry(city.group);
      const diagnostics = city.diagnostics();
      assert.equal(diagnostics.towers, low ? 18 : 30);
      assert.equal(diagnostics.visualMode, 'quiet-server-room');
      assert.ok(diagnostics.centerClearance >= 8);
      assert.ok(diagnostics.drawCalls <= 7);
      const bounds = new THREE.Box3().setFromObject(city.group);
      const extent = bounds.getSize(new THREE.Vector3());
      assert.ok(extent.x > 30);
      assert.ok(extent.y > 15);
      assert.ok(extent.z > 10);
      assert.ok(bounds.max.z < -5, 'architecture belongs behind the agents');
      for (const mesh of meshes(city.group)) {
        const position = mesh.geometry.getAttribute('position');
        for (let i = 0; i < position.count; i++) {
          assert.ok(Math.abs(position.getX(i)) > 5, 'architecture must not fill the central head silhouette');
        }
      }
      const initial = meshes(city.group).map(mesh => Array.from(mesh.geometry.getAttribute('position').array));
      city.update({time: 1, reduced: false});
      city.update({time: 1000, reduced: true});
      for (const [index, mesh] of meshes(city.group).entries()) {
        assert.deepEqual(Array.from(mesh.geometry.getAttribute('position').array), initial[index]);
      }
      assert.ok(diagnostics.drawCalls + 4 * 11 < 60, 'budget for shared city plus four drones');
    } finally { dispose(city.group); }
  });
}