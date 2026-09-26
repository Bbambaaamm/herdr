import * as THREE from 'three';

const STATE = {
  idle: { energy: .34, speed: .16, cyan: 0x7edcff, amber: 0xe7a24b },
  receiving: { energy: .72, speed: .55, cyan: 0x8be9ff, amber: 0xffb45b },
  working: { energy: 1, speed: .92, cyan: 0x9af2ff, amber: 0xffbd62 },
  tool: { energy: .92, speed: 1.12, cyan: 0x7fffdc, amber: 0xffc15f },
  delegating: { energy: .88, speed: .82, cyan: 0x72ffd0, amber: 0xffb04f },
  waiting_result: { energy: .48, speed: .28, cyan: 0x79d8ff, amber: 0xd69b4a },
  waiting_user: { energy: .76, speed: .34, cyan: 0xff8f75, amber: 0xff684f },
  speaking: { energy: .7, speed: .74, cyan: 0x8cf8df, amber: 0xffc56a },
  complete: { energy: .56, speed: .32, cyan: 0x89f5bf, amber: 0xffc76d },
  error: { energy: .74, speed: .2, cyan: 0xff806c, amber: 0xff5f48 },
  offline: { energy: .12, speed: .04, cyan: 0x59666b, amber: 0x665444 },
};

const clamp = THREE.MathUtils.clamp;

export function createQuantumCore({ low = false } = {}) {
  const group = new THREE.Group();
  group.name = 'Reactive orchestration quantum core';
  const resources = new Set();
  const keep = value => { resources.add(value); return value; };
  const additive = { transparent: true, depthWrite: false, blending: THREE.AdditiveBlending };

  const coreMat = keep(new THREE.MeshStandardMaterial({
    color: 0xffd089, emissive: 0xffa63d, emissiveIntensity: 3.2,
    roughness: .28, metalness: .15, transparent: true, opacity: .9,
  }));
  const core = new THREE.Mesh(keep(new THREE.IcosahedronGeometry(.48, low ? 2 : 4)), coreMat);
  core.name = 'Energy nucleus';
  group.add(core);

  const cageMat = keep(new THREE.MeshBasicMaterial({ color: 0x9beaff, wireframe: true, opacity: .35, ...additive }));
  const cage = new THREE.Mesh(keep(new THREE.IcosahedronGeometry(.76, low ? 2 : 3)), cageMat);
  cage.name = 'Nucleus field cage';
  group.add(cage);
  const ringRoot = new THREE.Group();
  ringRoot.name = 'Concentric computation rings';
  group.add(ringRoot);
  const ringMaterials = [];
  const rings = [];
  const ringCount = low ? 7 : 11;
  for (let i = 0; i < ringCount; i++) {
    const radius = 1.05 + i * .19;
    const material = keep(new THREE.MeshBasicMaterial({
      color: i % 2 ? 0x84e8ff : 0xf0ad55,
      opacity: .16 + (i % 3) * .035, ...additive,
    }));
    ringMaterials.push(material);
    const mesh = new THREE.Mesh(
      keep(new THREE.TorusGeometry(radius, .009 + (i % 3) * .004, low ? 5 : 7, low ? 72 : 128)),
      material,
    );
    mesh.rotation.set(
      (i % 3) * Math.PI / 3 + .16,
      ((i * 2) % 5) * Math.PI / 5,
      (i % 4) * .19,
    );
    mesh.userData.phase = i * .71;
    ringRoot.add(mesh);
    rings.push(mesh);
  }

  const orbitRoot = new THREE.Group();
  orbitRoot.name = 'Data orbit filaments';
  group.add(orbitRoot);
  const orbitMaterials = [];
  for (let i = 0; i < (low ? 7 : 12); i++) {
    const points = [];
    const segments = low ? 90 : 150;
    const radius = 1.32 + (i % 5) * .29;
    const squash = .56 + (i % 4) * .11;
    for (let j = 0; j <= segments; j++) {
      const a = j / segments * Math.PI * 2;
      points.push(new THREE.Vector3(Math.cos(a) * radius, Math.sin(a) * radius * squash, Math.sin(a * 2 + i) * .16));
    }
    const geometry = keep(new THREE.BufferGeometry().setFromPoints(points));
    const material = keep(new THREE.LineBasicMaterial({
      color: i % 3 ? 0x8beaff : 0xffb75d,
      opacity: i % 3 ? .2 : .28, ...additive,
    }));
    orbitMaterials.push(material);
    const line = new THREE.LineLoop(geometry, material);
    line.rotation.set(i * .39, i * .51, i * .23);
    line.userData.phase = i * .64;
    orbitRoot.add(line);
  }
  let seed = 0x51a7c0de;
  const random = () => { seed = (1664525 * seed + 1013904223) >>> 0; return seed / 4294967296; };
  const makeParticles = (count, inner, outer, color, size) => {
    const positions = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const z = random() * 2 - 1;
      const theta = random() * Math.PI * 2;
      const radius = inner + (outer - inner) * Math.pow(random(), .62);
      const planar = Math.sqrt(Math.max(0, 1 - z * z));
      positions[i * 3] = Math.cos(theta) * planar * radius;
      positions[i * 3 + 1] = z * radius;
      positions[i * 3 + 2] = Math.sin(theta) * planar * radius;
    }
    const geometry = keep(new THREE.BufferGeometry());
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const material = keep(new THREE.PointsMaterial({ color, size, sizeAttenuation: true, opacity: .72, ...additive }));
    const points = new THREE.Points(geometry, material);
    group.add(points);
    return { points, material };
  };
  const cyanParticles = makeParticles(low ? 430 : 1050, .86, 2.86, 0x9beeff, low ? .025 : .021);
  const amberParticles = makeParticles(low ? 180 : 430, .72, 2.5, 0xffb452, low ? .031 : .027);

  const beamMaterial = keep(new THREE.MeshBasicMaterial({ color: 0xa6efff, opacity: .12, ...additive }));
  const vertical = new THREE.Mesh(keep(new THREE.CylinderGeometry(.018, .055, 7.5, 10, 1, true)), beamMaterial);
  const horizontal = vertical.clone();
  horizontal.geometry = keep(vertical.geometry.clone());
  horizontal.rotation.z = Math.PI / 2;
  group.add(vertical, horizontal);

  const nodeGeometry = keep(new THREE.SphereGeometry(.035, low ? 5 : 7, low ? 4 : 6));
  const nodeMaterial = keep(new THREE.MeshBasicMaterial({ color: 0xe8faff, ...additive }));
  const nodes = new THREE.InstancedMesh(nodeGeometry, nodeMaterial, low ? 24 : 48);
  const nodeMatrix = new THREE.Matrix4(), nodeScale = new THREE.Vector3(1, 1, 1), nodeQ = new THREE.Quaternion();
  for (let i = 0; i < nodes.count; i++) {
    const a = i / nodes.count * Math.PI * 2;
    const r = 1.52 + (i % 6) * .23;
    const y = Math.sin(a * 3) * .9;
    nodeMatrix.compose(new THREE.Vector3(Math.cos(a) * r, y, Math.sin(a) * r), nodeQ, nodeScale);
    nodes.setMatrixAt(i, nodeMatrix);
  }
  nodes.instanceMatrix.needsUpdate = true;
  group.add(nodes);

  const light = new THREE.PointLight(0x9aefff, 11, 11, 1.5);
  group.add(light);
  let energy = .28;
  let state = 'offline';
  let activity = { running: 0, pending: 0, blocked: 0, userBlocked: 0, workingAgents: 0 };
  function update({ time = 0, delta = 1 / 60, state: next = state, reduced = false, activity: nextActivity = activity } = {}) {
    state = STATE[next] ? next : 'offline';
    activity = { ...activity, ...nextActivity };
    const profile = STATE[state];
    const load = clamp((activity.running || 0) * .26 + (activity.workingAgents || 0) * .16 + Math.min(activity.pending || 0, 6) * .035, 0, .58);
    const target = clamp(profile.energy + load, .08, 1.28);
    const ease = reduced ? 1 : 1 - Math.exp(-Math.max(delta, 0) * 4.2);
    energy = THREE.MathUtils.lerp(energy, target, ease);
    const blocked = state === 'waiting_user' || state === 'error' || (activity.userBlocked || 0) > 0;
    const cyan = blocked ? 0xff7864 : profile.cyan;
    const amber = blocked ? 0xff5e48 : profile.amber;
    const speed = reduced ? 0 : profile.speed * (.72 + energy * .72);
    const pulse = reduced ? 1 : 1 + Math.sin(time * (1.8 + speed * 3.2)) * .055 * energy;

    core.scale.setScalar(pulse * (.92 + energy * .11));
    cage.scale.setScalar(1 + (reduced ? 0 : Math.sin(time * 1.13) * .025 * energy));
    coreMat.emissive.setHex(amber);
    coreMat.emissiveIntensity = .2 + energy * 3.7;
    coreMat.opacity = .32 + energy * .55;
    cageMat.color.setHex(cyan);
    cageMat.opacity = .08 + energy * .34;

    ringRoot.rotation.y = reduced ? 0 : time * speed * .19;
    ringRoot.rotation.x = reduced ? .11 : .11 + Math.sin(time * .17) * .08;
    rings.forEach((ring, i) => {
      if (!reduced) ring.rotation.z += delta * speed * (.12 + (i % 5) * .035) * (i % 2 ? 1 : -1);
      ring.material.color.setHex(i % 2 ? cyan : amber);
      ring.material.opacity = .05 + energy * (.11 + (i % 3) * .025);
    });
    orbitRoot.rotation.z = reduced ? 0 : -time * speed * .08;
    orbitRoot.rotation.y = reduced ? 0 : time * speed * .06;
    orbitMaterials.forEach((material, i) => {
      material.color.setHex(i % 3 ? cyan : amber);
      material.opacity = .045 + energy * (i % 3 ? .18 : .25);
    });
    cyanParticles.points.rotation.y = reduced ? 0 : time * speed * .09;
    cyanParticles.points.rotation.z = reduced ? 0 : time * speed * .035;
    amberParticles.points.rotation.y = reduced ? 0 : -time * speed * .14;
    amberParticles.points.rotation.x = reduced ? 0 : time * speed * .028;
    cyanParticles.material.color.setHex(cyan);
    cyanParticles.material.opacity = .16 + energy * .68;
    amberParticles.material.color.setHex(amber);
    amberParticles.material.opacity = .1 + energy * .64;
    beamMaterial.color.setHex(cyan);
    beamMaterial.opacity = state === 'offline' ? .02 : .035 + energy * .14;
    vertical.scale.set(1, .75 + energy * .32, 1);
    horizontal.scale.set(.72 + energy * .34, 1, 1);
    nodeMaterial.color.setHex(blocked ? 0xffa07f : 0xe6fbff);
    nodes.rotation.y = reduced ? 0 : time * speed * .12;
    nodes.rotation.x = reduced ? 0 : Math.sin(time * .11) * .14;
    light.color.setHex(cyan);
    light.intensity = .45 + energy * 12.5;
  }

  return {
    group,
    update,
    setActivity(value) { activity = { ...activity, ...value }; },
    diagnostics() {
      return {
        type: 'reactive-quantum-core',
        state,
        energy,
        rings: rings.length,
        particles: cyanParticles.points.geometry.attributes.position.count + amberParticles.points.geometry.attributes.position.count,
        nodes: nodes.count,
        activity: { ...activity },
      };
    },
    dispose() { for (const resource of resources) resource.dispose?.(); },
  };
}