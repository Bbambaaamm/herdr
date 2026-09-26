import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { FACE_VERTICES, FACE_TRIANGLES } from './face-anatomy.js';

/**
 * An anatomical machine, not a billboard. The front is the MediaPipe canonical
 * face, skinned to a head and a hinged mandible. All detailing is real geometry.
 * Scene lighting, camera and lifecycle are owned by the caller.
 */
export function createMachineHead({ low = false } = {}) {
  const group = new THREE.Group();
  group.name = 'Anatomical machine intelligence';
  const shell = new THREE.Group();
  shell.name = 'Head rotation rig';
  group.add(shell);
  const scale = .3;
  const point = i => new THREE.Vector3(
    FACE_VERTICES[i * 3] * scale,
    FACE_VERTICES[i * 3 + 1] * scale,
    (FACE_VERTICES[i * 3 + 2] - 3) * scale,
  );
  const vertices = Array.from({ length: FACE_VERTICES.length / 3 }, (_, i) => point(i));
  const resources = new Set();
  const keep = value => { resources.add(value); return value; };
  const material = (color, metalness, roughness, extra = {}) => keep(new THREE.MeshStandardMaterial({ color, metalness, roughness, ...extra }));
  const metal = material(0x65645b, .84, .46);
  const dark = material(0x242b2b, .89, .4);
  const steel = material(0x8b8b7e, .91, .35);
  const bronze = material(0x735432, .87, .46);
  const cavity = material(0x010203, .05, 1);
  const rubber = material(0x101515, .3, .72);
  const ember = material(0x42250a, .65, .46, { emissive: 0xffb653, emissiveIntensity: .9 });
  const core = material(0xffd387, .3, .33, { emissive: 0xffbb58, emissiveIntensity: 2.1 });
  let seed = 407;
  const random = () => { seed = (1664525 * seed + 1013904223) >>> 0; return seed / 4294967296; };
  const smooth = (a, b, x) => { const t = THREE.MathUtils.clamp((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); };
  const mouthY = (point(13).y + point(14).y) / 2;
  const hingePosition = new THREE.Vector3(0, -.5, -1.14);
  const jawWeight = p => {
    // Upper/lower lip edges must not be averaged together: the oral aperture is
    // a real opening, while the outer cheek transition remains smoothly skinned.
    const rigidLip = Math.abs(p.x) < .67 && p.y < mouthY + .3 && p.y > mouthY - .45;
    return rigidLip ? (p.y < mouthY ? 1 : 0) : smooth(mouthY + .15, mouthY - .44, p.y);
  };
  const jaw = new THREE.Group();
  jaw.name = 'Articulated mechanical mandible';
  jaw.position.copy(hingePosition);
  shell.add(jaw);
  const put = (object, position, moving = false) => {
    object.position.copy(position);
    if (moving) object.position.sub(hingePosition);
    (moving ? jaw : shell).add(object);
    return object;
  };

  // Anatomical base: every vertex below the mouth is physically skinned to the
  // mandibular hinge. This also moves the silhouette in three-quarter views.
  const faceGeometry = keep(new THREE.BufferGeometry());
  faceGeometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices.flatMap(v => v.toArray()), 3));
  const openings = [
    [33,7,163,144,145,153,154,155,133,173,157,158,159,160,161,246],
    [263,249,390,373,374,380,381,382,362,398,384,385,386,387,388,466],
    [78,95,88,178,87,14,317,402,318,324,308,415,310,311,312,13,82,81,80,191],
  ].map(ids => new Set(ids));
  // The canonical OBJ closes its eyes and mouth with triangles. Remove those
  // cap faces so the independent optics and oral cavity are genuinely recessed.
  const indices = [];
  for (let i = 0; i < FACE_TRIANGLES.length; i += 3) {
    const tri = FACE_TRIANGLES.slice(i, i + 3);
    if (!openings.some(ring => tri.every(id => ring.has(id)))) indices.push(...tri);
  }
  let outward = 0;
  for (let i = 0; i < indices.length; i += 3) {
    const a = vertices[indices[i]], b = vertices[indices[i + 1]], c = vertices[indices[i + 2]];
    outward += new THREE.Vector3().subVectors(b, a).cross(new THREE.Vector3().subVectors(c, a)).z;
  }
  if (outward < 0) for (let i = 0; i < indices.length; i += 3) [indices[i + 1], indices[i + 2]] = [indices[i + 2], indices[i + 1]];
  faceGeometry.setIndex(indices);
  faceGeometry.computeVertexNormals();
  const skinIndices = [], skinWeights = [];
  for (const v of vertices) { const w = jawWeight(v); skinIndices.push(0, 1, 0, 0); skinWeights.push(1 - w, w, 0, 0); }
  faceGeometry.setAttribute('skinIndex', new THREE.Uint16BufferAttribute(skinIndices, 4));
  faceGeometry.setAttribute('skinWeight', new THREE.Float32BufferAttribute(skinWeights, 4));
  const surface = new THREE.SkinnedMesh(faceGeometry, metal);
  surface.name = 'Skinned canonical anatomical facial shell';
  const headBone = new THREE.Bone(), jawBone = new THREE.Bone();
  headBone.name = 'cranium'; jawBone.name = 'mandible';
  jawBone.position.copy(hingePosition);
  headBone.add(jawBone); surface.add(headBone);
  surface.bind(new THREE.Skeleton([headBone, jawBone]));
  surface.castShadow = false; surface.receiveShadow = true;
  shell.add(surface);

  const normalAttribute = faceGeometry.getAttribute('normal');
  const normals = vertices.map((_, i) => new THREE.Vector3().fromBufferAttribute(normalAttribute, i));
  const triangles = [];
  let totalArea = 0;
  for (let i = 0; i < indices.length; i += 3) {
    const ids = indices.slice(i, i + 3);
    const [a, b, c] = ids.map(n => vertices[n]);
    const area = new THREE.Vector3().subVectors(b, a).cross(new THREE.Vector3().subVectors(c, a)).length() / 2;
    totalArea += area;
    triangles.push({ ids, accumulated: totalArea });
  }
  const sample = () => {
    const area = random() * totalArea;
    let lo = 0, hi = triangles.length - 1;
    while (lo < hi) { const mid = (lo + hi) >>> 1; if (triangles[mid].accumulated < area) lo = mid + 1; else hi = mid; }
    const ids = triangles[lo].ids;
    let u = random(), v = random(); if (u + v > 1) { u = 1 - u; v = 1 - v; }
    const p = vertices[ids[0]].clone().multiplyScalar(1 - u - v).addScaledVector(vertices[ids[1]], u).addScaledVector(vertices[ids[2]], v);
    const n = normals[ids[0]].clone().multiplyScalar(1 - u - v).addScaledVector(normals[ids[1]], u).addScaledVector(normals[ids[2]], v).normalize();
    return { p, n };
  };

  // Irregular, bevelled hexagonal armour. Flat top surfaces follow the facial
  // normal; reflected edges are smaller than the panels, keeping anatomy clear.
  const panelShape = new THREE.Shape();
  panelShape.moveTo(-.43, -.5); panelShape.lineTo(.27, -.5); panelShape.lineTo(.5, -.29);
  panelShape.lineTo(.5, .28); panelShape.lineTo(.23, .5); panelShape.lineTo(-.5, .37); panelShape.closePath();
  const panelGeometry = keep(new THREE.ExtrudeGeometry(panelShape, { depth: .2, bevelEnabled: true, bevelSegments: 1, steps: 1, bevelSize: .065, bevelThickness: .06 }));
  panelGeometry.translate(0, 0, -.03);
  const deviceGeometry = keep(new THREE.BoxGeometry(.48, 1, .45));
  const boltGeometry = keep(new THREE.CylinderGeometry(.34, .4, .3, 6));
  boltGeometry.rotateX(Math.PI / 2);
  const pinGeometry = keep(new THREE.SphereGeometry(1, 5, 4));
  const matrix = new THREE.Matrix4(), quaternion = new THREE.Quaternion(), twist = new THREE.Quaternion(), unitZ = new THREE.Vector3(0, 0, 1);
  const scratchScale = new THREE.Vector3(), color = new THREE.Color();
  const batches = new Map();
  const collect = (kind, p, n, size, colorHex, moving = false) => {
    const key = kind + (moving ? '-jaw' : '-head');
    if (!batches.has(key)) batches.set(key, []);
    quaternion.setFromUnitVectors(unitZ, n);
    twist.setFromAxisAngle(unitZ, (random() - .5) * 2.8);
    quaternion.multiply(twist);
    scratchScale.copy(size);
    const position = p.clone(); if (moving) position.sub(hingePosition);
    matrix.compose(position, quaternion, scratchScale);
    batches.get(key).push({ matrix: matrix.clone(), color: colorHex });
  };
  const palette = [0x444942, 0x616155, 0x2f3736, 0x767367, 0x393f3e, 0x4b4a3e, 0x8c8267];
  const panelCount = low ? 2700 : 5100;
  for (let i = 0; i < panelCount; i++) {
    const { p, n } = sample();
    // Fine plating at the nose/lips; larger fractured sections at temples.
    const central = Math.abs(p.x) < .68 && p.y < .55 && p.y > -1.8;
    const s = (central ? .038 : .048) + random() * (central ? .058 : .1);
    p.addScaledVector(n, .017 + random() * .018);
    const moving = jawWeight(p) > .5;
    collect('panel', p, n, new THREE.Vector3(s * (.75 + random() * .8), s * (.8 + random() * 1.1), s * (.6 + random() * .7)), palette[Math.floor(random() * palette.length)], moving);
    if (i % 3 === 0) {
      const dp = p.clone().addScaledVector(n, s * .24);
      collect('device', dp, n, new THREE.Vector3(s * .29, s * (.8 + random()), s * .45), i % 9 ? 0x283131 : 0xa39374, moving);
    }
    if (i % 4 === 0) collect('bolt', p.clone().addScaledVector(n, s * .22), n, new THREE.Vector3(s * .3, s * .3, s * .3), 0x9a917b, moving);
    if (i % 17 === 0) collect('ember', p.clone().addScaledVector(n, s * .3), n, new THREE.Vector3(.011, .006, .009), 0xf4be69, moving);
  }

  const faceOval = [10,338,297,332,284,251,389,356,454,323,361,288,397,365,379,378,400,377,152,148,176,149,150,136,172,58,132,93,234,127,162,21,54,103,67,109];
  const skullPositions = [], skullIndices = [];
  const rings = 9;
  for (let ring = 0; ring <= rings; ring++) {
    const t = ring / rings;
    for (const id of faceOval) {
      const p = point(id), radial = Math.cos(t * Math.PI * .49);
      skullPositions.push(p.x * radial, p.y * radial + .25 * t, p.z * (1 - t) - 2.13 * Math.sin(t * Math.PI / 2));
    }
  }
  for (let ring = 0; ring < rings; ring++) for (let i = 0; i < faceOval.length; i++) {
    const a = ring * faceOval.length + i, b = ring * faceOval.length + (i + 1) % faceOval.length, c = a + faceOval.length, d = b + faceOval.length;
    skullIndices.push(a, c, b, b, c, d);
  }
  const skullGeometry = keep(new THREE.BufferGeometry());
  skullGeometry.setAttribute('position', new THREE.Float32BufferAttribute(skullPositions, 3));
  skullGeometry.setIndex(skullIndices); skullGeometry.computeVertexNormals();
  const skull = new THREE.Mesh(skullGeometry, dark); skull.name = 'Volumetric occipital cranium'; shell.add(skull);
  for (let i = 0; i < (low ? 550 : 1200); i++) {
    const theta = random() * Math.PI * 2, depth = random();
    const xx = Math.sin(theta) * (1.8 + random() * .4), yy = Math.cos(theta) * (2.2 + random() * .4);
    const p = new THREE.Vector3(xx * (1 - depth * .48), yy * (1 - depth * .48) + .2, -1.3 - depth * .75);
    const n = new THREE.Vector3(xx, yy * .6, -1.7).normalize();
    const s = .05 + random() * .14;
    collect('panel', p, n, new THREE.Vector3(s, s * 1.8, s * 1.7), palette[Math.floor(random() * palette.length)]);
  }
  const instanced = [];
  for (const [key, entries] of batches) {
    const kind = key.split('-')[0];
    const geometry = { panel: panelGeometry, device: deviceGeometry, bolt: boltGeometry, ember: pinGeometry }[kind];
    const mesh = new THREE.InstancedMesh(geometry, kind === 'ember' ? ember : metal, entries.length);
    mesh.name = `${key} / ${entries.length} mechanical parts`;
    for (let i = 0; i < entries.length; i++) { mesh.setMatrixAt(i, entries[i].matrix); mesh.setColorAt(i, color.setHex(entries[i].color)); }
    mesh.instanceMatrix.needsUpdate = true; mesh.instanceColor.needsUpdate = true;
    mesh.computeBoundingSphere();
    (key.endsWith('jaw') ? jaw : shell).add(mesh);
    instanced.push(mesh);
  }

  function tube(points, radius, mat, moving = false, segments = 36) {
    const curve = new THREE.CatmullRomCurve3(points);
    const geometry = keep(new THREE.TubeGeometry(curve, segments, radius, low ? 4 : 6, false));
    const mesh = new THREE.Mesh(geometry, mat);
    if (moving) mesh.position.copy(hingePosition).negate();
    (moving ? jaw : shell).add(mesh);
    return mesh;
  }
  function landmarkTube(ids, radius, mat, moving = false, offset = .045) {
    return tube(ids.map(i => point(i).addScaledVector(normals[i], offset)), radius, mat, moving, ids.length * 5);
  }
  // Metal lip rims remain physically attached to their respective jaws.
  landmarkTube([61,40,37,0,267,270,291], .024, bronze);
  landmarkTube([61,91,84,17,314,321,291], .028, bronze, true);
  landmarkTube([78,81,13,311,308], .013, dark);
  landmarkTube([78,178,14,402,308], .017, steel, true);
  const throatGeometry = keep(new THREE.SphereGeometry(1, 24, 16));
  const throat = new THREE.Mesh(throatGeometry, cavity);
  throat.name = 'Recessed three-dimensional oral cavity';
  throat.userData.keepSeparate = true;
  throat.position.set(0, mouthY - .055, .38); throat.scale.set(.62, .21, .24); shell.add(throat);
  // Individually segmented upper/lower labial plates, not bright cartoon teeth.
  const lipCurveUpper = new THREE.CatmullRomCurve3([61,40,37,0,267,270,291].map(i => point(i)));
  const lipCurveLower = new THREE.CatmullRomCurve3([61,91,84,17,314,321,291].map(i => point(i)));
  const labialGeometry = keep(new THREE.BoxGeometry(.027, .056, .03));
  for (let i = 1; i < 31; i++) for (const moving of [false, true]) {
    const curve = moving ? lipCurveLower : lipCurveUpper, p = curve.getPoint(i / 31), tangent = curve.getTangent(i / 31);
    const lip = new THREE.Mesh(labialGeometry, i % 5 === 0 ? steel : bronze);
    p.z += .032; put(lip, p, moving); lip.rotation.z = Math.atan2(tangent.y, tangent.x);
  }

  const eyes = [], eyelids = [], brows = [];
  const globeGeometry = keep(new THREE.SphereGeometry(1, 28, 20));
  const irisGeometry = keep(new THREE.CylinderGeometry(.097, .104, .035, 24)); irisGeometry.rotateX(Math.PI / 2);
  const irisRingGeometry = keep(new THREE.TorusGeometry(.105, .009, 6, 28));
  const irisDetailGeometry = keep(new THREE.BoxGeometry(.004, .029, .006));
  const lensGeometry = keep(new THREE.SphereGeometry(.041, 16, 12));
  for (const [index, cornerIds, upperIds, lowerIds, browIds] of [
    [0,[33,133],[33,160,158,133],[33,144,153,133],[70,63,105,66,107]],
    [1,[362,263],[362,385,387,263],[362,380,373,263],[336,296,334,293,300]],
  ]) {
    const center = point(cornerIds[0]).add(point(cornerIds[1])).multiplyScalar(.5);
    center.z -= .1;
    const eye = new THREE.Group(); eye.name = index ? 'Right ocular gimbal' : 'Left ocular gimbal'; put(eye, center);
    const globe = new THREE.Mesh(globeGeometry, dark); globe.scale.set(.355, .175, .22); globe.userData.keepSeparate = true; eye.add(globe);
    const ocular = new THREE.Group(); ocular.name = 'Independent gaze pivot'; eye.add(ocular);
    const iris = new THREE.Mesh(irisGeometry, bronze); iris.position.z = .211; ocular.add(iris);
    const ring = new THREE.Mesh(irisRingGeometry, steel); ring.position.z = .232; ocular.add(ring);
    const lens = new THREE.Mesh(lensGeometry, core); lens.position.z = .24; lens.scale.set(1, .95, .6); lens.userData.keepSeparate = true; ocular.add(lens);
    for (let i = 0; i < 18; i++) {
      const a = i * Math.PI / 9, detail = new THREE.Mesh(irisDetailGeometry, i % 3 === 0 ? ember : steel);
      detail.position.set(Math.sin(a) * .072, Math.cos(a) * .072, .234); detail.rotation.z = -a; ocular.add(detail);
    }
    const lidTop = landmarkTube(upperIds, .032, dark, false, .024);
    const lidBottom = landmarkTube(lowerIds, .025, steel, false, .018);
    lidTop.name = 'Upper mechanical eyelid'; lidBottom.name = 'Lower mechanical eyelid';
    lidTop.userData.keepSeparate = true; lidBottom.userData.keepSeparate = true;
    eyelids.push({ top: lidTop, bottom: lidBottom, center, globe });
    landmarkTube(upperIds, .009, bronze, false, .065);
    const brow = new THREE.Group(); brow.name = 'Expressive segmented brow';
    const browCenter = point(browIds[2]); put(brow, browCenter);
    const curve = new THREE.CatmullRomCurve3(browIds.map(i => point(i).addScaledVector(normals[i], .05)));
    for (let i = 0; i < 17; i++) {
      const p = curve.getPoint(i / 16), tangent = curve.getTangent(i / 16);
      const plate = new THREE.Mesh(panelGeometry, i % 4 === 0 ? steel : dark);
      plate.position.copy(p).sub(browCenter); plate.scale.set(.085, .066, .08); plate.rotation.z = Math.atan2(tangent.y, tangent.x); brow.add(plate);
    }
    brows.push(brow); eyes.push({ eye, ocular, lens });
  }

  // Nose has real volume from anatomy. Tiny separate nostril sleeves add shadow
  // instead of replacing the nose with a stylised tube or luminous triangle.
  for (const side of [-1, 1]) {
    const nostril = new THREE.Mesh(keep(new THREE.SphereGeometry(1, 14, 10)), cavity);
    nostril.position.set(side * .18, -.49, .998); nostril.scale.set(.105, .063, .047); nostril.rotation.z = side * .21; shell.add(nostril);
  }

  // Small mechanical actuator pairs at the mandible, visibly connected to both
  // moving and fixed anatomy. Their endpoint updates preserve physical joints.
  const actuators = [];
  const rodGeometry = keep(new THREE.CylinderGeometry(.023, .023, 1, 8));
  const sleeveGeometry = keep(new THREE.CylinderGeometry(.057, .057, .4, 8));
  const hingeGeometry = keep(new THREE.CylinderGeometry(.15, .15, .13, 12)); hingeGeometry.rotateZ(Math.PI / 2);
  for (const side of [-1, 1]) {
    const hinge = new THREE.Mesh(hingeGeometry, bronze); hinge.position.set(side * 1.8, -.55, -.7); shell.add(hinge);
    for (let j = 0; j < (low ? 1 : 3); j++) {
      const anchor = new THREE.Vector3(side * (1.7 - j * .08), -.75 - j * .1, -.38 + j * .09);
      const end = new THREE.Vector3(side * (1.36 - j * .1), -2.07 - j * .04, -.08 + j * .12);
      const rod = new THREE.Mesh(rodGeometry, steel), sleeve = new THREE.Mesh(sleeveGeometry, dark);
      rod.userData.keepSeparate = true; sleeve.userData.keepSeparate = true;
      shell.add(rod, sleeve); actuators.push({ rod, sleeve, anchor, end });
    }
  }

  // Crown and cheek wiring extend the silhouette in real depth. Sparse amber
  // couplings illuminate dark metal; no animated traffic is invented here.
  const cableCount = low ? 52 : 94;
  const crown = new THREE.Group(); crown.name = 'Volumetric machine swarm crown'; shell.add(crown);
  const sparkGeometry = keep(new THREE.SphereGeometry(.02, 5, 4));
  for (let i = 0; i < cableCount; i++) {
    const a = random() * Math.PI * 2;
    const source = new THREE.Vector3(Math.sin(a) * (1.5 + random() * .35), Math.cos(a) * 2.1 + .3, -.75 - random() * .65);
    // Most crown mass rises above and behind, never covers the eyes or lips.
    const rise = Math.max(.2, Math.cos(a) + .45);
    const reach = .3 + random() * .85;
    const target = source.clone().add(new THREE.Vector3(Math.sin(a) * reach, rise * reach, -.2 - random() * .75));
    const p1 = source.clone().lerp(target, .3).add(new THREE.Vector3((random() - .5) * .32, .15, .2));
    const p2 = source.clone().lerp(target, .72).add(new THREE.Vector3((random() - .5) * .5, .18, -.2));
    const cable = tube([source, p1, p2, target], .011 + random() * .021, i % 8 === 0 ? bronze : rubber, false, low ? 12 : 20);
    const housing = new THREE.Mesh(panelGeometry, i % 5 === 0 ? steel : dark);
    housing.position.copy(target); housing.scale.set(.08 + random() * .13, .08 + random() * .11, .15 + random() * .16); housing.rotation.set(random() * 6, random() * 6, random() * 6); crown.add(housing);
    if (i % 4 === 0) {
      const lamp = new THREE.Mesh(sparkGeometry, ember); lamp.position.copy(target).add(new THREE.Vector3(0, 0, .07)); crown.add(lamp);
    }
    cable.name = 'Fixed anatomical loom';
  }
  // Raised trace bundles follow cheeks and temples. Paths are tied to anatomy.
  for (const ids of [[234,127,162,21,54,103,67,109,10],[454,356,389,251,284,332,297,338,10],[132,58,172,136,150,149,176,148,152],[361,288,397,365,379,378,400,377,152]]) {
    landmarkTube(ids, .016, steel, ids.includes(152), .064);
    landmarkTube(ids, .008, bronze, ids.includes(152), .1);
  }

  // Draw-call budget: bake only STATIC siblings with an identical material.
  // Every animated pivot remains intact, and skinning/instancing are untouched.
  // Non-indexed temporary clones let boxes, bevels and tubes share one batch.
  function batchStaticSiblings(parent) {
    for (const child of [...parent.children]) if (child.isGroup) batchStaticSiblings(child);
    const candidates = new Map();
    for (const child of parent.children) {
      if (!child.isMesh || child.isSkinnedMesh || child.isInstancedMesh || child.userData.keepSeparate || Array.isArray(child.material)) continue;
      if (!candidates.has(child.material)) candidates.set(child.material, []);
      candidates.get(child.material).push(child);
    }
    for (const [mat, meshes] of candidates) {
      if (meshes.length < 2) continue;
      const temporary = meshes.map(mesh => {
        mesh.updateMatrix();
        const geo = mesh.geometry.index ? mesh.geometry.toNonIndexed() : mesh.geometry.clone();
        // Primitive geometries carry UVs but the custom cranium intentionally
        // does not. These are untextured materials: merge a uniform attribute
        // layout instead of depending on optional attributes of each source.
        for (const name of Object.keys(geo.attributes)) {
          if (name !== 'position' && name !== 'normal') geo.deleteAttribute(name);
        }
        if (!geo.getAttribute('normal')) geo.computeVertexNormals();
        geo.applyMatrix4(mesh.matrix);
        return geo;
      });
      const merged = mergeGeometries(temporary, false);
      for (const geo of temporary) geo.dispose();
      if (!merged) throw new Error(`Cannot batch static head geometry for ${parent.name}`);
      keep(merged); merged.computeBoundingSphere();
      const mesh = new THREE.Mesh(merged, mat);
      mesh.name = `${parent.name || 'Head'} / static ${meshes.length}-part batch`;
      mesh.userData.batchedParts = meshes.length;
      mesh.receiveShadow = true;
      for (const old of meshes) parent.remove(old);
      parent.add(mesh);
    }
  }
  batchStaticSiblings(shell);
  const liveGeometry = new Set();
  group.traverse(object => { if (object.geometry) liveGeometry.add(object.geometry); });
  for (const resource of [...resources]) {
    if (resource.isBufferGeometry && !liveGeometry.has(resource)) {
      resource.dispose(); resources.delete(resource);
    }
  }

  let jawAngle = 0, gazeHorizontal = 0, gazeVertical = 0, stateWeight = 0;
  let lastState = 'idle', stateChangedAt = 0;
  const vecA = new THREE.Vector3(), vecB = new THREE.Vector3(), direction = new THREE.Vector3(), unitY = new THREE.Vector3(0, 1, 0), unitX = new THREE.Vector3(1, 0, 0);
  const initialBounds = new THREE.Box3().setFromObject(group);
  let drawCalls = 0, geometricalTriangles = 0;
  group.traverse(object => {
    if (!object.isMesh) return;
    drawCalls++;
    const triangleCount = (object.geometry.index?.count ?? object.geometry.attributes.position.count) / 3;
    geometricalTriangles += triangleCount * (object.isInstancedMesh ? object.count : 1);
  });
  const diagnostics = () => ({
    kind: 'anatomical-skinned-3d-mechanical-head',
    vertices: vertices.length, faceTriangles: indices.length / 3,
    componentInstances: instanced.reduce((sum, mesh) => sum + mesh.count, 0),
    estimatedDrawCalls: drawCalls, geometricalTriangles,
    articulatedJaw: true, independentOcularGimbals: eyes.length,
    jawAngleRadians: Number(jawAngle.toFixed(5)),
    ocularYawRadians: Number(eyes[0].ocular.rotation.y.toFixed(5)),
    gaze: [Number(gazeHorizontal.toFixed(4)), Number(gazeVertical.toFixed(4))],
    state: lastState, usesFaceBitmap: false,
    localBounds: { min: initialBounds.min.toArray(), max: initialBounds.max.toArray() },
  });

  function update({ time = 0, state = 'idle', gazeX = 0, gazeY = 0, reduced = false, delta = 1 / 60 } = {}) {
    if (state !== lastState) { lastState = state; stateChangedAt = time; }
    const age = time - stateChangedAt;
    const dt = Math.min(.12, Math.max(.001, delta));
    // A reduced-motion scene may render exactly once for a state transition.
    // Snap targets immediately: easing here would leave a frozen half-state.
    const damping = reduced ? 1 : 1 - Math.exp(-dt * 5);
    const offline = state === 'offline', working = state === 'working', speaking = state === 'speaking';
    const targetWeight = offline ? 0 : state === 'receiving' || speaking ? 1 : working ? .75 : ['tool', 'delegating'].includes(state) ? .65 : .3;
    stateWeight += (targetWeight - stateWeight) * damping;
    const drift = reduced || offline ? 0 : Math.sin(time * .27) * .027 + Math.sin(time * .69) * .012;
    gazeHorizontal += (THREE.MathUtils.clamp(gazeX, -1, 1) * .42 + drift - gazeHorizontal) * damping;
    gazeVertical += (THREE.MathUtils.clamp(gazeY, -1, 1) * .2 - (working ? .035 : 0) - gazeVertical) * damping;
    // Head accompanies the eyes with lower amplitude and inertia.
    shell.rotation.y += (gazeHorizontal * .58 + (reduced || offline ? 0 : Math.sin(time * .17) * .025) - shell.rotation.y) * (reduced ? 1 : damping * .45);
    shell.rotation.x += (-gazeVertical * .5 + (state === 'receiving' ? -.035 : .01) - shell.rotation.x) * (reduced ? 1 : damping * .5);
    shell.rotation.z = reduced || offline ? 0 : Math.sin(time * .19) * .009;
    shell.position.y = reduced || offline ? 0 : Math.sin(time * .62) * .011;
    const syllable = .32 + .68 * Math.pow(Math.max(0, Math.sin(time * 12.1) * .65 + Math.sin(time * 19.4 + .6) * .35), .65);
    const targetJaw = speaking && !reduced ? .035 + .19 * syllable : .004;
    jawAngle += (targetJaw - jawAngle) * (reduced ? 1 : 1 - Math.exp(-dt * 16));
    jaw.rotation.x = jawAngle; jawBone.rotation.x = jawAngle;
    throat.scale.y = .21 + jawAngle * .56;
    throat.position.y = mouthY - .055 - jawAngle * .45;
    const blinkPhase = ((time + 2.7) % 6.8), blink = !reduced && !offline && blinkPhase < .19 ? Math.sin(blinkPhase / .19 * Math.PI) : 0;
    for (let i = 0; i < eyes.length; i++) {
      eyes[i].ocular.rotation.y = gazeHorizontal * .83;
      eyes[i].ocular.rotation.x = -gazeVertical;
      // The actual mechanical globe contracts behind the upper shutter.
      eyelids[i].globe.scale.y = .175 * (1 - .82 * blink);
      eyelids[i].top.position.y = -.072 * blink;
      eyelids[i].bottom.position.y = .022 * blink;
      eyes[i].lens.scale.y = .95 * (1 - .88 * blink);
      const browRoll = (i ? -1 : 1) * (working ? .045 : state === 'receiving' ? -.025 : 0);
      const browHeight = point(i ? 334 : 105).y + (state === 'receiving' ? .027 : working ? -.018 : 0);
      brows[i].rotation.z += (browRoll - brows[i].rotation.z) * damping;
      brows[i].position.y += (browHeight - brows[i].position.y) * damping;
    }
    core.emissiveIntensity = offline ? .04 : .9 + stateWeight * 1.7 + (reduced ? 0 : Math.sin(time * 1.5) * .08);
    const completion = state === 'complete' && !reduced ? Math.max(0, 1 - age / 1.8) * .65 : 0;
    ember.emissiveIntensity = offline ? .018 : .36 + stateWeight * .65 + completion;
    ember.emissive.setHex(state === 'error' ? 0xef652f : 0xffb653);
    for (const actuator of actuators) {
      vecA.copy(actuator.anchor);
      vecB.copy(actuator.end).sub(hingePosition).applyAxisAngle(unitX, jawAngle).add(hingePosition);
      direction.subVectors(vecB, vecA);
      actuator.rod.position.copy(vecA).add(vecB).multiplyScalar(.5);
      actuator.rod.scale.y = direction.length(); actuator.rod.quaternion.setFromUnitVectors(unitY, direction.normalize());
      actuator.sleeve.position.copy(vecA).lerp(vecB, .25); actuator.sleeve.quaternion.copy(actuator.rod.quaternion);
    }
    group.userData.diagnostics = diagnostics();
  }
  update();
  return { group, update, diagnostics, dispose() { for (const item of resources) item.dispose(); } };
}
