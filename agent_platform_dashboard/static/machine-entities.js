import * as THREE from 'three';

// All visible machinery is geometry: no image plates, billboards or sprite agents.
// Static pieces are baked into a handful of material batches. Articulated arms
// remain individually addressable through instanced transforms.
const UP = new THREE.Vector3(0, 1, 0);
const TAU = Math.PI * 2;

function randomSource(seed) {
  let value = (seed | 0) || 1;
  return () => {
    value ^= value << 13;
    value ^= value >>> 17;
    value ^= value << 5;
    return (value >>> 0) / 4294967296;
  };
}

function materialSet() {
  return {
    armor: new THREE.MeshStandardMaterial({color: 0x292d2f, metalness: 0.88, roughness: 0.39}),
    edge: new THREE.MeshStandardMaterial({color: 0x777569, metalness: 0.92, roughness: 0.3}),
    black: new THREE.MeshStandardMaterial({color: 0x080c0e, metalness: 0.6, roughness: 0.48}),
    bronze: new THREE.MeshStandardMaterial({color: 0x5c4930, metalness: 0.91, roughness: 0.39}),
    cable: new THREE.MeshStandardMaterial({color: 0x1a1f22, metalness: 0.7, roughness: 0.44}),
    light: new THREE.MeshStandardMaterial({color: 0xffb04b, emissive: 0xff9a31, emissiveIntensity: 1.2, metalness: 0.35, roughness: 0.27}),
    lens: new THREE.MeshStandardMaterial({color: 0xffdf99, emissive: 0xffa133, emissiveIntensity: 2.5, metalness: 0.3, roughness: 0.16}),
  };
}

class GeometryBatch {
  constructor(materials) {
    this.materials = materials;
    this.buckets = {};
    this.count = 0;
    this.matrix = new THREE.Matrix4();
    this.normalMatrix = new THREE.Matrix3();
    this.position = new THREE.Vector3();
    this.normal = new THREE.Vector3();
    this.rotation = new THREE.Quaternion();
  }

  add(key, geometry, position = [0, 0, 0], scale = [1, 1, 1], rotation = null) {
    const source = geometry.index ? geometry.toNonIndexed() : geometry;
    const bucket = this.buckets[key] || (this.buckets[key] = {position: [], normal: []});
    this.rotation.identity();
    if (rotation instanceof THREE.Quaternion) this.rotation.copy(rotation);
    else if (rotation) this.rotation.setFromEuler(new THREE.Euler(...rotation));
    this.matrix.compose(new THREE.Vector3(...position), this.rotation, new THREE.Vector3(...scale));
    this.normalMatrix.getNormalMatrix(this.matrix);
    const vertices = source.getAttribute('position');
    const normals = source.getAttribute('normal');
    for (let i = 0; i < vertices.count; i++) {
      this.position.fromBufferAttribute(vertices, i).applyMatrix4(this.matrix);
      this.normal.fromBufferAttribute(normals, i).applyNormalMatrix(this.normalMatrix);
      bucket.position.push(this.position.x, this.position.y, this.position.z);
      bucket.normal.push(this.normal.x, this.normal.y, this.normal.z);
    }
    this.count++;
    if (source !== geometry) source.dispose();
    geometry.dispose();
  }

  box(key, position, scale, rotation = null) {
    this.add(key, new THREE.BoxGeometry(1, 1, 1), position, scale, rotation);
  }

  strut(key, from, to, radius = 0.015, sides = 6, endRadius = radius) {
    const a = new THREE.Vector3(...from);
    const b = new THREE.Vector3(...to);
    const direction = b.clone().sub(a);
    const length = direction.length();
    if (length < 0.0001) return;
    this.add(key, new THREE.CylinderGeometry(endRadius, radius, length, sides),
      a.add(b).multiplyScalar(0.5).toArray(), [1, 1, 1],
      new THREE.Quaternion().setFromUnitVectors(UP, direction.normalize()));
  }

  cable(key, points, radius = 0.015, segments = 18) {
    const curve = new THREE.CatmullRomCurve3(points.map(point => new THREE.Vector3(...point)));
    this.add(key, new THREE.TubeGeometry(curve, segments, radius, 5, false));
  }

  finish(group) {
    for (const [name, bucket] of Object.entries(this.buckets)) {
      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute('position', new THREE.Float32BufferAttribute(bucket.position, 3));
      geometry.setAttribute('normal', new THREE.Float32BufferAttribute(bucket.normal, 3));
      geometry.computeBoundingSphere();
      const mesh = new THREE.Mesh(geometry, this.materials[name]);
      mesh.name = `machine-batch-${name}`;
      group.add(mesh);
    }
    return Object.keys(this.buckets).length;
  }
}

function lensAssembly(batch, x, y, z, radius = 0.075) {
  batch.add('black', new THREE.CylinderGeometry(radius * 1.4, radius * 1.3, 0.105, 12),
    [x, y, z - 0.025], [1, 1, 1], [Math.PI / 2, 0, 0]);
  batch.add('edge', new THREE.TorusGeometry(radius * 1.15, 0.015, 5, 16), [x, y, z + 0.028]);
  batch.add('bronze', new THREE.TorusGeometry(radius * 0.82, 0.007, 4, 14), [x, y, z + 0.039]);
  batch.add('lens', new THREE.SphereGeometry(radius * 0.69, 12, 8), [x, y, z + 0.025], [1, 1, 0.35]);
  batch.add('black', new THREE.SphereGeometry(radius * 0.19, 8, 6), [x, y, z + 0.053], [1, 1, 0.2]);
}

function sentinelBody(batch, random, low) {
  batch.add('black', new THREE.SphereGeometry(0.48, 20, 12), [0, 0, 0], [1, 0.9, 0.91]);
  // Independent meridian armor ribs expose the dark reactor through their gaps.
  const ribs = low ? 12 : 18;
  for (let i = 0; i < ribs; i++) {
    const theta = i / ribs * TAU;
    const points = [];
    for (let j = 0; j < 7; j++) {
      const latitude = -1.23 + j * 2.46 / 6;
      points.push([Math.cos(theta) * Math.cos(latitude) * 0.53,
        Math.sin(latitude) * 0.5, Math.sin(theta) * Math.cos(latitude) * 0.46]);
    }
    for (let j = 0; j < points.length - 1; j++) {
      batch.strut(i % 4 === 0 ? 'bronze' : 'armor', points[j], points[j + 1], 0.034, 6);
      batch.add('edge', new THREE.SphereGeometry(0.028, 6, 4), points[j]);
    }
    const a = theta + 0.1;
    const panel = [Math.cos(a) * 0.48, 0.15 * Math.sin(theta * 2), Math.sin(a) * 0.43];
    batch.box('armor', panel, [0.12, 0.19 + random() * 0.13, 0.06], [0, -a + Math.PI / 2, 0.12]);
    batch.strut('edge', [Math.cos(theta) * 0.32, 0.43, Math.sin(theta) * 0.3],
      [Math.cos(theta) * 0.18, 0.62 + random() * 0.12, Math.sin(theta) * 0.17], 0.012);
  }
  for (const y of [-0.27, 0.02, 0.29]) {
    const radius = Math.sqrt(1 - (y / 0.52) ** 2) * 0.51;
    batch.add('edge', new THREE.TorusGeometry(radius, 0.014, 5, 40), [0, y, 0], [1, 0.85, 1], [Math.PI / 2, 0, 0]);
  }
  // Multi-lens optical head, protruding rather than painted onto a sphere.
  batch.box('armor', [0, 0.045, 0.43], [0.37, 0.28, 0.14], [0.05, 0, 0]);
  lensAssembly(batch, 0, 0.07, 0.53, 0.092);
  lensAssembly(batch, -0.16, -0.025, 0.486, 0.048);
  lensAssembly(batch, 0.16, -0.025, 0.486, 0.048);
  lensAssembly(batch, -0.095, 0.205, 0.46, 0.035);
  lensAssembly(batch, 0.095, 0.205, 0.46, 0.035);
  for (let i = 0; i < 4; i++) {
    const x = (i - 1.5) * 0.095;
    batch.box('black', [x, -0.35, 0.26], [0.068, 0.16, 0.11]);
    batch.box('bronze', [x, -0.44, 0.26], [0.075, 0.025, 0.12]);
    batch.box('light', [x, -0.41, 0.321], [0.031, 0.018, 0.008]);
  }
  for (let i = 0; i < 95; i++) {
    const angle = random() * TAU;
    const y = (random() - 0.5) * 0.8;
    const r = Math.sqrt(1 - y * y / 0.25) * 0.51;
    batch.box(i % 8 === 0 ? 'bronze' : 'edge', [Math.cos(angle) * r, y, Math.sin(angle) * r * 0.9],
      [0.015, 0.027, 0.013], [random(), angle, random()]);
  }
  // Crown antennae and cable tangles give the head a readable machine silhouette.
  for (let i = 0; i < 5; i++) {
    const x = (i - 2) * 0.12;
    const top = 0.68 + random() * 0.35;
    batch.strut('armor', [x, 0.38, -0.05], [x * 1.12, top, -0.08], 0.022, 6, 0.007);
    batch.box('edge', [x, 0.54, -0.05], [0.035, 0.07, 0.04]);
    if (i % 2 === 0) batch.add('light', new THREE.SphereGeometry(0.012, 6, 4), [x * 1.12, top, -0.08]);
  }
}

function citadelBody(batch, random, low) {
  batch.box('black', [0, 0, 0], [0.63, 0.72, 0.56]);
  const sections = low ? 34 : 56;
  for (let i = 0; i < sections; i++) {
    const side = i % 4;
    const angle = side * Math.PI / 2;
    const width = 0.065 + random() * 0.12;
    const height = 0.19 + random() * 0.48;
    const tangent = (random() - 0.5) * 0.63;
    const radial = 0.29 + random() * 0.11;
    const x = Math.sin(angle) * radial + Math.cos(angle) * tangent;
    const z = Math.cos(angle) * radial - Math.sin(angle) * tangent;
    const y = (random() - 0.5) * 0.36;
    batch.box(i % 5 === 0 ? 'bronze' : 'armor', [x, y, z], [width, height, 0.11], [0, angle, 0]);
    batch.box('edge', [x, y + height * 0.45, z], [width * 1.09, 0.018, 0.13], [0, angle, 0]);
    batch.box('black', [x, y - height * 0.25, z], [width * 1.1, 0.03, 0.13], [0, angle, 0]);
    const normal = new THREE.Vector3(Math.sin(angle), 0, Math.cos(angle));
    for (let j = 0; j < 3; j++) {
      batch.box(j % 3 === 0 ? 'light' : 'edge', [x + normal.x * 0.061, y + j * 0.042, z + normal.z * 0.061],
        [0.012, 0.023, 0.008], [0, angle, 0]);
    }
  }
  // Cantilevered platters / radiators, not a generic plain cube.
  for (let side = -1; side <= 1; side += 2) {
    for (let i = 0; i < 4; i++) {
      const y = (i - 1.5) * 0.16;
      batch.box('armor', [side * 0.44, y, -0.07], [0.34, 0.038, 0.55], [0, 0, side * 0.07]);
      batch.strut('edge', [side * 0.29, y - 0.09, 0.15], [side * 0.6, y, 0.15], 0.009);
      batch.box('bronze', [side * 0.59, y, -0.08], [0.015, 0.045, 0.56]);
    }
  }
  lensAssembly(batch, 0, 0.04, 0.435, 0.063);
  lensAssembly(batch, -0.14, 0.09, 0.41, 0.028);
  lensAssembly(batch, 0.14, 0.09, 0.41, 0.028);
  for (let i = 0; i < 9; i++) {
    const x = (random() - 0.5) * 0.54;
    const z = (random() - 0.5) * 0.45;
    const height = 0.22 + random() * 0.45;
    batch.box('armor', [x, 0.35 + height / 2, z], [0.043, height, 0.05]);
    batch.strut('edge', [x, 0.35 + height, z], [x, 0.54 + height, z], 0.007, 5, 0.002);
    batch.box('bronze', [x, 0.46, z], [0.067, 0.016, 0.075]);
  }
  for (let i = 0; i < 12; i++) {
    const x = (i % 4 - 1.5) * 0.145;
    const z = (Math.floor(i / 4) - 1) * 0.14;
    const length = 0.14 + random() * 0.22;
    batch.strut('armor', [x, -0.33, z], [x, -0.33 - length, z], 0.03, 6, 0.014);
    batch.add('bronze', new THREE.TorusGeometry(0.025, 0.007, 4, 8), [x, -0.36 - length / 2, z], [1, 1, 1], [Math.PI / 2, 0, 0]);
  }
}

function articulatedArms(body, materials, random, kind, low) {
  const armCount = kind === 'hermes' ? (low ? 7 : 10) : 6;
  const segments = low ? 11 : 17;
  const meshCount = armCount * segments;
  const links = new THREE.InstancedMesh(new THREE.CylinderGeometry(1, 1, 1, 6), materials.cable, meshCount);
  const cuffs = new THREE.InstancedMesh(new THREE.BoxGeometry(1, 1, 1), materials.armor, meshCount);
  const joints = new THREE.InstancedMesh(new THREE.SphereGeometry(1, 6, 4), materials.edge, meshCount);
  const claws = new THREE.InstancedMesh(new THREE.ConeGeometry(1, 1, 5), materials.bronze, armCount * 2);
  for (const mesh of [links, cuffs, joints, claws]) {
    mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
    mesh.frustumCulled = false;
    mesh.name = `articulated-${mesh === links ? 'cables' : mesh === cuffs ? 'armor' : mesh === joints ? 'joints' : 'claws'}`;
    body.add(mesh);
  }
  const specs = Array.from({length: armCount}, (_, i) => ({
    angle: (i / armCount) * TAU + (kind === 'hermes' ? 0 : 0.14),
    phase: random() * TAU,
    reach: (kind === 'hermes' ? 1.12 : 0.84) + random() * 0.35,
    depth: (random() - 0.5) * 0.9,
    curl: random() > 0.5 ? 1 : -1,
  }));
  const matrix = new THREE.Matrix4();
  const quaternion = new THREE.Quaternion();
  const a = new THREE.Vector3();
  const b = new THREE.Vector3();
  const midpoint = new THREE.Vector3();
  const vector = new THREE.Vector3();
  const size = new THREE.Vector3();
  function point(spec, u, time, motion, target) {
    const angle = spec.angle + Math.sin(time * 0.27 + spec.phase) * 0.065 * motion + spec.curl * u * u * 0.75;
    const radius = 0.43 + Math.sin(u * 1.37) * spec.reach;
    const wave = Math.sin(time * 0.48 + spec.phase - u * 3.9) * 0.085 * motion * u;
    target.set(Math.cos(angle) * radius, Math.sin(angle) * radius * 0.61 - u * u * 0.35 + wave,
      -0.1 + Math.sin(u * Math.PI) * spec.depth + Math.cos(time * 0.39 + spec.phase) * 0.07 * motion * u);
    return target;
  }
  function update(time, motion) {
    let index = 0;
    for (let arm = 0; arm < specs.length; arm++) {
      const spec = specs[arm];
      for (let j = 0; j < segments; j++, index++) {
        const u = j / segments;
        point(spec, u, time, motion, a);
        point(spec, (j + 1) / segments, time, motion, b);
        vector.copy(b).sub(a);
        const length = vector.length();
        quaternion.setFromUnitVectors(UP, vector.normalize());
        midpoint.copy(a).add(b).multiplyScalar(0.5);
        const width = (1 - u * 0.77) * 0.029;
        size.set(width, length, width);
        matrix.compose(midpoint, quaternion, size);
        links.setMatrixAt(index, matrix);
        size.set(width * 2.4, length * 0.58, width * 2.15);
        matrix.compose(midpoint, quaternion, size);
        cuffs.setMatrixAt(index, matrix);
        size.setScalar(width * 1.08);
        matrix.compose(a, quaternion, size);
        joints.setMatrixAt(index, matrix);
      }
      point(spec, 1, time, motion, a);
      for (let finger = 0; finger < 2; finger++) {
        point(spec, 0.96, time, motion, b);
        vector.copy(a).sub(b).normalize();
        vector.z += finger ? 0.4 : -0.4;
        vector.normalize();
        midpoint.copy(a).addScaledVector(vector, 0.047);
        quaternion.setFromUnitVectors(UP, vector);
        matrix.compose(midpoint, quaternion, size.set(0.015, 0.12, 0.015));
        claws.setMatrixAt(arm * 2 + finger, matrix);
      }
    }
    for (const mesh of [links, cuffs, joints, claws]) mesh.instanceMatrix.needsUpdate = true;
  }
  update(0, 0);
  return {update, armCount, segments};
}

export function createMachineDrone({kind = 'hermes', seed = 1, low = false} = {}) {
  const group = new THREE.Group();
  group.name = `flying-${kind}-machine`;
  const body = new THREE.Group();
  body.name = 'hovering-articulated-body';
  group.add(body);
  const random = randomSource(seed);
  const materials = materialSet();
  const batch = new GeometryBatch(materials);
  if (kind === 'codex') citadelBody(batch, random, low);
  else sentinelBody(batch, random, low);
  const staticDrawCalls = batch.finish(body);
  const arms = articulatedArms(body, materials, random, kind, low);
  const phase = random() * TAU;
  let lightLevel = 1;
  let lastState = '';
  let frame = 0;
  return {
    group,
    update({time = 0, state = 'idle', reduced = false, delta = 1 / 60} = {}) {
      const disconnected = ['offline', 'unavailable', 'unknown', 'disconnected'].includes(state);
      const busy = ['working', 'tool', 'delegating', 'receiving', 'speaking'].includes(state);
      const problem = ['error', 'blocked', 'waiting_user'].includes(state);
      const target = disconnected ? 0.09 : problem ? 0.75 : busy ? 1.4 : 0.72;
      // Reduced-motion rendering can stop after this frame. Commit the full
      // semantic state now rather than leaving a stale half-lit transition.
      lightLevel = reduced ? target : lightLevel + (target - lightLevel) * Math.min(1, delta * 4);
      materials.lens.emissiveIntensity = lightLevel * 2;
      materials.light.emissiveIntensity = lightLevel * 0.62;
      if (state !== lastState) {
        materials.lens.emissive.setHex(problem ? 0xfb6234 : 0xffa63b);
        materials.light.emissive.setHex(problem ? 0xf27132 : 0xffa437);
        lastState = state;
      }
      const motion = reduced || disconnected ? 0 : busy ? 1 : 0.46;
      body.position.y = Math.sin(time * 0.53 + phase) * 0.045 * motion;
      body.rotation.y = Math.sin(time * 0.24 + phase) * 0.1 * motion;
      body.rotation.z = Math.sin(time * 0.31 + phase) * 0.025 * motion;
      body.rotation.x = Math.sin(time * 0.29 + phase * 0.3) * 0.024 * motion;
      if (!low || frame++ % 2 === 0 || reduced) arms.update(reduced ? 0 : time, motion);
    },
    diagnostics() {
      return {kind, geometryOnly: true, staticPieces: batch.count, articulatedArms: arms.armCount,
        segmentsPerArm: arms.segments, drawCalls: staticDrawCalls + 4, nominalCoreDiameter: 1.2,
        fullSpan: kind === 'hermes' ? 3.65 : 3.15};
    },
  };
}

export function createMachineCity({low = false} = {}) {
  const group = new THREE.Group();
  group.name = 'machine-city-architecture';
  const random = randomSource(691309);
  const materials = materialSet();
  materials.armor.color.setHex(0x353837);
  materials.edge.color.setHex(0x666053);
  materials.light.emissiveIntensity = 0.95;
  const batch = new GeometryBatch(materials);
  const towers = [];
  const count = low ? 36 : 68;
  for (let i = 0; i < count; i++) {
    const side = i % 2 ? 1 : -1;
    const distance = 8 + random() * 16;
    const x = side * (6.8 + random() * 21);
    const z = -distance;
    const width = 0.3 + random() * 1.2;
    const height = 7 + random() * 18;
    const y = -8 + height / 2;
    towers.push({x, z, width, height});
    batch.box('black', [x, y, z], [width, height, width * 0.79]);
    const buttresses = low ? 3 : 5;
    for (let j = 0; j < buttresses; j++) {
      const bx = x + (j / (buttresses - 1) - 0.5) * width * 1.27;
      const depth = width * (0.7 + random() * 0.35);
      batch.box('armor', [bx, y, z + depth * 0.23], [width * 0.11, height * (0.88 + random() * 0.21), depth]);
      batch.box('edge', [bx, y, z + depth * 0.77], [0.022, height * 0.96, 0.025]);
    }
    const floors = Math.floor(height / 0.65);
    for (let floor = 0; floor < floors; floor++) {
      const fy = -7.8 + floor * 0.65;
      batch.box('armor', [x, fy, z + width * 0.15], [width * 1.27, 0.055, width * 1.07]);
      if (floor % 3 === 0) batch.box('bronze', [x, fy, z + width * 0.74], [width * 0.96, 0.015, 0.022]);
      const windows = low ? 2 : 4;
      for (let w = 0; w < windows; w++) {
        if (random() < 0.4) continue;
        batch.box('light', [x + ((w + 0.5) / windows - 0.5) * width,
          fy + 0.12 + random() * 0.14, z + width * 0.704],
        [0.022 + random() * 0.04, 0.055 + random() * 0.14, 0.015]);
      }
    }
    for (let spire = 0; spire < 3; spire++) {
      const sx = x + (spire - 1) * width * 0.34;
      const heightAbove = 0.6 + random() * 2;
      batch.strut('armor', [sx, height - 8, z], [sx, height - 8 + heightAbove, z], width * 0.055, 5, 0.01);
    }
  }
  // Distant gantries give parallax and scale without drawing a graphical "network".
  for (let i = 0; i < (low ? 6 : 11); i++) {
    const side = i % 2 ? 1 : -1;
    const x1 = side * (7 + random() * 2);
    const x2 = side * (20 + random() * 10);
    const y = -5 + random() * 15;
    const z = -12 - random() * 10;
    const span = Math.abs(x2 - x1);
    const center = (x1 + x2) / 2;
    batch.box('armor', [center, y, z], [span, 0.16, 0.5]);
    batch.box('edge', [center, y + 0.47, z + 0.22], [span, 0.035, 0.035]);
    batch.box('black', [center, y - 0.35, z - 0.1], [span, 0.15, 0.3]);
    for (let j = 0; j < span; j++) {
      const x = Math.min(x1, x2) + j;
      batch.strut('edge', [x, y - 0.35, z + 0.27], [x + 0.65, y + 0.48, z + 0.27], 0.021);
      if (j % 2 === 0) batch.box('light', [x, y + 0.18, z + 0.32], [0.045, 0.055, 0.015]);
    }
    batch.cable('cable', [[x1, y + 0.4, z + 0.2], [center, y - 1.4, z], [x2, y + 0.4, z + 0.2]], 0.028, 26);
  }
  // Hanging power conduits frame the composition; they do not imply agent traffic.
  for (const side of [-1, 1]) {
    for (let i = 0; i < (low ? 6 : 12); i++) {
      const x = side * (7.5 + random() * 6);
      const z = -7 - random() * 9;
      batch.cable('cable', [[x, 15, z], [x + side * 0.6, 6, z + 0.5],
        [x + side * 1.1, -1, z], [x + side * 1.9, -9, z - 1]], 0.017 + random() * 0.04, 24);
    }
  }
  const drawCalls = batch.finish(group);
  return {
    group,
    update() {}, // Buildings and window lights remain still; they are not status lamps.
    diagnostics() { return {geometryOnly: true, towers: towers.length, staticPieces: batch.count, drawCalls,
      centerClearance: 6.8, depthRange: [-24, -7]}; },
  };
}
