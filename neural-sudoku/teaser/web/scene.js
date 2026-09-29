// Neural Sudoku teaser: three.js scene.
// Every visual state is a pure function of time: window.renderAt(t) draws the frame for t seconds,
// so render.mjs can capture frames deterministically in headless Chromium.
//
// Timeline (96 BPM, one bar = 2.5 s) -- keep in sync with post.py and music.py:
//   0.0 - 5.0   hook: glass board, 21 glowing clues
//   5.0 - 12.5  classic search: a tree of branches grows, most die red (backtracking)
//  12.5 - 15.0  darkness: the question
//  15.0 - 32.5  neural phase: 9 candidate orbs per cell, attention arcs, probabilities harden
//  32.5 - 37.5  verification: every row, column and box lights up
//  37.5 - 45.0  title

import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

const W = 1920, H = 1080;
const BEAT = 60 / 96;

// ---------------------------------------------------------------- helpers
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const smooth = (x) => { x = clamp(x); return x * x * (3 - 2 * x); };
const easeIO = (x) => { x = clamp(x); return 0.5 - 0.5 * Math.cos(Math.PI * x); };
const lerp = (a, b, s) => a + (b - a) * s;
const lerpV = (a, b, s) => new THREE.Vector3(lerp(a[0], b[0], s), lerp(a[1], b[1], s), lerp(a[2], b[2], s));
function mulberry32(a) {
  return function () {
    a |= 0; a = a + 0x6D2B79F5 | 0;
    let t = Math.imul(a ^ a >>> 15, 1 | a);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };
}
const rand = mulberry32(9);

// ---------------------------------------------------------------- data
const puzzle = await (await fetch('./puzzle.json')).json();
const givens = puzzle.givens, solution = puzzle.solution, order = puzzle.order;
const settleTime = new Array(81).fill(-1);
order.forEach((cell, j) => { settleTime[cell] = 18.5 + 12.5 * Math.pow(j / (order.length - 1), 0.85); });

const peers = [];
for (let i = 0; i < 81; i++) {
  const r = Math.floor(i / 9), c = i % 9, br = 3 * Math.floor(r / 3), bc = 3 * Math.floor(c / 3);
  const s = new Set();
  for (let k = 0; k < 9; k++) { s.add(r * 9 + k); s.add(k * 9 + c); }
  for (let a = 0; a < 3; a++) for (let b = 0; b < 3; b++) s.add((br + a) * 9 + bc + b);
  s.delete(i);
  peers.push([...s]);
}
// digits already ruled out by the clues (these orbs fade first: constraint propagation)
const excluded = [];
for (let i = 0; i < 81; i++) {
  const ex = new Set(peers[i].map(j => givens[j]).filter(v => v > 0));
  excluded.push(ex);
}
// one or two decoy digits per cell that rise before losing (the network "considering" options)
const decoys = [];
for (let i = 0; i < 81; i++) {
  const opts = [1, 2, 3, 4, 5, 6, 7, 8, 9].filter(d => !excluded[i].has(d) && d !== solution[i]);
  const n = Math.min(opts.length, 1 + Math.floor(rand() * 2));
  const pick = [];
  for (let k = 0; k < n; k++) pick.push(opts.splice(Math.floor(rand() * opts.length), 1)[0]);
  decoys.push(pick);
}

// ---------------------------------------------------------------- renderer
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1);
renderer.setSize(W, H);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.outputColorSpace = THREE.SRGBColorSpace;
document.body.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x020308);
scene.fog = new THREE.FogExp2(0x020308, 0.018);
const camera = new THREE.PerspectiveCamera(38, W / H, 0.1, 400);

const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, camera));
const bloom = new UnrealBloomPass(new THREE.Vector2(W / 2, H / 2), 1.05, 0.55, 0.18);  // half-res: cheaper, same look
composer.addPass(bloom);
composer.addPass(new OutputPass());

scene.add(new THREE.HemisphereLight(0x3060ff, 0x080010, 0.6));
const key = new THREE.PointLight(0x66ccff, 60, 40, 1.6);
const rim = new THREE.PointLight(0xff4fd8, 18, 40, 1.6);
scene.add(key, rim);

// ---------------------------------------------------------------- starfield
{
  const n = 2500, pos = new Float32Array(n * 3), col = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) {
    const r = 80 + rand() * 120, th = rand() * Math.PI * 2, ph = Math.acos(2 * rand() - 1);
    pos.set([r * Math.sin(ph) * Math.cos(th), r * Math.cos(ph), r * Math.sin(ph) * Math.sin(th)], i * 3);
    const b = 0.3 + rand() * 0.7;
    col.set([b * 0.8, b * 0.85, b], i * 3);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  g.setAttribute('color', new THREE.BufferAttribute(col, 3));
  scene.add(new THREE.Points(g, new THREE.PointsMaterial({ size: 0.5, vertexColors: true, fog: false })));
}

// ---------------------------------------------------------------- board
const board = new THREE.Group();
scene.add(board);
const cellPos = (i) => {
  const r = Math.floor(i / 9), c = i % 9;
  const gx = Math.floor(c / 3) * 0.12, gz = Math.floor(r / 3) * 0.12;
  return new THREE.Vector3((c - 4) * 1.02 + gx - 0.12, 0, (r - 4) * 1.02 + gz - 0.12);
};

const tileGeo = new THREE.BoxGeometry(0.94, 0.14, 0.94);
const edgeGeo = new THREE.EdgesGeometry(tileGeo);
const tiles = [], edges = [];
for (let i = 0; i < 81; i++) {
  const m = new THREE.MeshStandardMaterial({ color: 0x0a1226, roughness: 0.28, metalness: 0.75,
    emissive: new THREE.Color(0x000000) });
  const mesh = new THREE.Mesh(tileGeo, m);
  mesh.position.copy(cellPos(i));
  board.add(mesh);
  tiles.push(mesh);
  const e = new THREE.LineSegments(edgeGeo, new THREE.LineBasicMaterial({ color: 0x3a7bff, transparent: true,
    opacity: 0.5, toneMapped: false }));
  e.position.copy(mesh.position);
  board.add(e);
  edges.push(e);
}
// glowing 3x3 box frame
const frameMat = new THREE.MeshBasicMaterial({ color: new THREE.Color(0.18, 0.42, 0.85), toneMapped: false });
for (let k = 0; k <= 3; k++) {
  const off = -4.74 + k * 3.18;
  const a = new THREE.Mesh(new THREE.BoxGeometry(9.66, 0.03, 0.03), frameMat);
  a.position.set(-0.12 + 0.12 * 0, 0.08, off);
  const b = new THREE.Mesh(new THREE.BoxGeometry(0.03, 0.03, 9.66), frameMat);
  b.position.set(off, 0.08, -0.12 + 0.12 * 0);
  board.add(a, b);
}

// digit textures
await document.fonts.load('10px SSP');
const ff = new FontFace('SSP', 'url(./fonts/SourceSansPro-Light.ttf)');
await ff.load();
document.fonts.add(ff);
const digitTex = [null];
for (let d = 1; d <= 9; d++) {
  const cv = document.createElement('canvas');
  cv.width = cv.height = 256;
  const ctx = cv.getContext('2d');
  ctx.fillStyle = '#fff';
  ctx.font = '200px SSP';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(String(d), 128, 140);
  const tex = new THREE.CanvasTexture(cv);
  tex.colorSpace = THREE.SRGBColorSpace;
  digitTex.push(tex);
}
const digitGeo = new THREE.PlaneGeometry(0.78, 0.78);
const digits = [];
for (let i = 0; i < 81; i++) {
  const d = solution[i];
  const m = new THREE.MeshBasicMaterial({ map: digitTex[d], transparent: true, blending: THREE.AdditiveBlending,
    depthWrite: false, toneMapped: false, color: new THREE.Color(1, 1, 1), opacity: 0 });
  const p = new THREE.Mesh(digitGeo, m);
  p.rotation.x = -Math.PI / 2;
  p.position.copy(cellPos(i)).add(new THREE.Vector3(0, 0.08, 0));
  board.add(p);
  digits.push(p);
}

// ---------------------------------------------------------------- candidate orbs (neural phase)
const empties = order.slice();
const orbGeo = new THREE.SphereGeometry(1, 16, 12);
const orbMat = new THREE.MeshBasicMaterial({ toneMapped: false });
const orbs = new THREE.InstancedMesh(orbGeo, orbMat, empties.length * 9);
orbs.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
orbs.frustumCulled = false;
board.add(orbs);
const dummy = new THREE.Object3D();
const tmpC = new THREE.Color();
const CYAN = new THREE.Color(0.35, 0.85, 1.6);
const VIOLET = new THREE.Color(0.8, 0.45, 1.8);
const GOLD = new THREE.Color(2.2, 1.45, 0.5);
const orbLocal = (k) => new THREE.Vector3(((k % 3) - 1) * 0.27, 0.55 + Math.floor(k / 3) * 0.0, (Math.floor(k / 3) - 1) * 0.27);

// ---------------------------------------------------------------- search tree (classic backtracking)
const tree = { segs: [], pos: null, col: null, geo: null };
{
  const segs = [];
  const root = new THREE.Vector3(0, 0.3, 0);
  let surviveId = 0;
  function grow(p, az, el, depth, t0, alive) {
    if (depth > 7) return;
    const n = depth < 2 ? 4 : 2 + Math.floor(rand() * 2);
    const aliveChild = alive ? Math.floor(rand() * n) : -1;
    for (let k = 0; k < n; k++) {
      const a2 = depth === 0 ? az + (k / n) * Math.PI * 2 + rand() * 0.5 : az + (rand() - 0.5) * 1.3;
      const e2 = Math.max(0.45, el - 0.05 - rand() * 0.07);
      const d = new THREE.Vector3(Math.cos(a2) * Math.cos(e2), Math.sin(e2), Math.sin(a2) * Math.cos(e2));
      const len = 1.55 * Math.pow(0.86, depth) * (0.8 + rand() * 0.4);
      const q = p.clone().addScaledVector(d, len);
      const birth = t0 + 0.12 + rand() * 0.45;
      const survive = k === aliveChild;
      const death = survive ? 1e9 : birth + 0.5 + rand() * 1.6;
      segs.push({ a: p.clone(), b: q, birth, death, survive });
      if (survive || rand() < 0.8) grow(q, a2, e2, depth + 1, birth, survive);
    }
  }
  grow(root, 0, 1.25, 0, 5.3, true);
  tree.segs = segs;
  const pos = new Float32Array(segs.length * 6), col = new Float32Array(segs.length * 6);
  segs.forEach((s, i) => pos.set([s.a.x, s.a.y, s.a.z, s.b.x, s.b.y, s.b.z], i * 6));
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  g.setAttribute('color', new THREE.BufferAttribute(col, 3));
  tree.geo = g; tree.col = col;
  const mat = new THREE.LineBasicMaterial({ vertexColors: true, transparent: true, blending: THREE.AdditiveBlending,
    depthWrite: false, toneMapped: false });
  const lines = new THREE.LineSegments(g, mat);
  lines.frustumCulled = false;
  scene.add(lines);
  tree.lines = lines;
  // bright nodes at branch tips
  const tp = new Float32Array(segs.length * 3), tc = new Float32Array(segs.length * 3);
  segs.forEach((s, i) => tp.set([s.b.x, s.b.y, s.b.z], i * 3));
  const tg = new THREE.BufferGeometry();
  tg.setAttribute('position', new THREE.BufferAttribute(tp, 3));
  tg.setAttribute('color', new THREE.BufferAttribute(tc, 3));
  tree.tipCol = tc; tree.tipGeo = tg;
  const pts = new THREE.Points(tg, new THREE.PointsMaterial({ size: 0.16, vertexColors: true, transparent: true,
    blending: THREE.AdditiveBlending, depthWrite: false, toneMapped: false }));
  pts.frustumCulled = false;
  scene.add(pts);
  tree.pts = pts;
}

// ---------------------------------------------------------------- attention arcs
const ARC_SEG = 18, ARC_MAX = 3 * 20;
const arcPos = new Float32Array(ARC_MAX * ARC_SEG * 6), arcCol = new Float32Array(ARC_MAX * ARC_SEG * 6);
const arcGeo = new THREE.BufferGeometry();
arcGeo.setAttribute('position', new THREE.BufferAttribute(arcPos, 3));
arcGeo.setAttribute('color', new THREE.BufferAttribute(arcCol, 3));
const arcs = new THREE.LineSegments(arcGeo, new THREE.LineBasicMaterial({ vertexColors: true, transparent: true,
  blending: THREE.AdditiveBlending, depthWrite: false, toneMapped: false }));
arcs.frustumCulled = false;
board.add(arcs);

// ---------------------------------------------------------------- camera path
function cameraAt(t) {
  let pos, look;
  if (t < 5.0) {
    const s = easeIO(t / 5.0);
    pos = lerpV([-7.5, 3.2, 7.5], [5.5, 4.8, 9.5], s);
    look = new THREE.Vector3(0, 0, 0);
  } else if (t < 12.5) {
    const s = easeIO((t - 5.0) / 7.5);
    pos = lerpV([5.5, 4.8, 9.5], [8, 10, 20], s);
    look = lerpV([0, 0, 0], [0, 3.6, 0], s);
  } else if (t < 15.0) {
    const s = easeIO((t - 12.5) / 2.5);
    pos = lerpV([8, 10, 20], [0, 11, 14], s);
    look = lerpV([0, 3.6, 0], [0, 0.3, 0], s);
  } else if (t < 32.5) {
    const s = (t - 15.0) / 17.5;
    const ang = lerp(-0.1, 1.1, easeIO(s));
    const rad = 14 - 5 * Math.sin(Math.PI * clamp((t - 19) / 11));
    const hgt = 11 - 3 * Math.sin(Math.PI * clamp((t - 19) / 11));
    pos = new THREE.Vector3(rad * Math.sin(ang), hgt, rad * Math.cos(ang));
    look = new THREE.Vector3(0, 0.3, 0);
  } else if (t < 37.5) {
    const s = easeIO((t - 32.5) / 5.0);
    const a0 = 1.1;
    const p0 = new THREE.Vector3(14 * Math.sin(a0), 11, 14 * Math.cos(a0));
    pos = p0.lerp(new THREE.Vector3(0.001, 19, 0.6), s);
    look = new THREE.Vector3(0, 0, 0);
  } else {
    const s = easeIO((t - 37.5) / 7.5);
    pos = lerpV([0.001, 19, 0.6], [0, 2.6, 25], s);
    look = lerpV([0, 0, 0], [0, 6.2, 0], s);
  }
  return { pos, look };
}

// ---------------------------------------------------------------- per-frame state
function renderAt(t) {
  const cam = cameraAt(t);
  camera.position.copy(cam.pos);
  camera.lookAt(cam.look);

  key.position.set(8 * Math.cos(t * 0.4), 6, 8 * Math.sin(t * 0.4));
  rim.position.set(-8 * Math.cos(t * 0.3), 3, -8 * Math.sin(t * 0.3));
  const beatPulse = Math.exp(-((t % BEAT) / 0.18));

  // global exposure: dip into darkness for the question, dim under the title
  let exposure = 1.0;
  if (t > 12.3 && t < 15.2) exposure = lerp(1.0, 0.12, smooth((t - 12.3) / 0.5)) * (1 - smooth((t - 14.6) / 0.6)) +
    smooth((t - 14.6) / 0.6) * 1.0;
  if (t > 38) exposure = lerp(1.0, 0.4, smooth((t - 38) / 2));
  if (t > 43.8) exposure *= 1 - smooth((t - 43.8) / 1.2);
  renderer.toneMappingExposure = exposure * 1.1;

  // board visibility: recedes during the search tree
  let boardDim = t > 5 && t < 15 ? 1 - 0.6 * smooth((t - 5.5) / 2) : 1;
  if (t > 38) boardDim *= 1 - 0.75 * smooth((t - 38) / 2);
  frameMat.color.setRGB(0.18 * boardDim, 0.42 * boardDim, 0.85 * boardDim);

  // tiles and edges
  for (let i = 0; i < 81; i++) {
    const m = tiles[i].material;
    m.emissive.setRGB(0, 0, 0);
    edges[i].material.opacity = 0.45 * boardDim;
    const d = digits[i].material;
    if (givens[i]) {
      d.opacity = boardDim * (t < 0.6 ? smooth(t / 0.6) : 1) * (1 + 0.25 * beatPulse * (t < 5 ? 1 : 0));
      d.color.setRGB(0.9, 1.5, 2.6);
    } else {
      const ts = settleTime[i];
      const land = smooth((t - ts) / 0.35);
      d.opacity = land * (t > 38 ? boardDim : 1);
      const flash = Math.exp(-Math.max(0, t - ts) / 0.4) * land;
      d.color.setRGB(2.0 + 0.9 * flash, 1.35 + 0.7 * flash, 0.45 + 0.4 * flash);
      if (flash > 0.01) m.emissive.setRGB(0.22 * flash, 0.13 * flash, 0.02 * flash);
    }
  }

  // verification: rows, columns, boxes light up in turn
  if (t > 32.5 && t < 38.5) {
    const units = [];
    for (let r = 0; r < 9; r++) units.push([...Array(9).keys()].map(c => r * 9 + c));
    for (let c = 0; c < 9; c++) units.push([...Array(9).keys()].map(r => r * 9 + c));
    for (let b = 0; b < 9; b++) {
      const br = 3 * Math.floor(b / 3), bc = 3 * (b % 3), u = [];
      for (let a = 0; a < 3; a++) for (let k = 0; k < 3; k++) u.push((br + a) * 9 + bc + k);
      units.push(u);
    }
    units.forEach((u, k) => {
      const tk = 32.7 + k * 0.17;
      const g = Math.exp(-Math.max(0, t - tk) / 0.35) * (t >= tk ? 1 : 0);
      if (g > 0.01) u.forEach(i => { tiles[i].material.emissive.r += 0.05 * g; tiles[i].material.emissive.g += 0.55 * g;
        tiles[i].material.emissive.b += 0.25 * g; });
    });
    const allDone = smooth((t - 37.4) / 0.4);
    if (allDone > 0) for (let i = 0; i < 81; i++) tiles[i].material.emissive.g += 0.12 * allDone;
  }

  // search tree
  {
    const vis = t > 5 && t < 13.5;
    tree.lines.visible = tree.pts.visible = vis;
    if (vis) {
      const fadeAll = 1 - smooth((t - 12.0) / 1.2);
      tree.segs.forEach((s, i) => {
        let r = 0, g = 0, b = 0;
        const grow = smooth((t - s.birth) / 0.25);
        if (grow > 0) {
          if (s.survive) { r = 2.0; g = 1.4; b = 0.5; }
          else {
            const dead = smooth((t - s.death) / 0.3);
            const gone = smooth((t - s.death - 0.6) / 1.0);
            r = lerp(0.4, 2.0, dead); g = lerp(0.9, 0.25, dead); b = lerp(1.8, 0.2, dead);
            const k = 1 - 0.85 * gone; r *= k; g *= k; b *= k;
          }
          r *= grow * fadeAll; g *= grow * fadeAll; b *= grow * fadeAll;
        }
        tree.col.set([r * 0.18, g * 0.18, b * 0.18, r * 0.45, g * 0.45, b * 0.45], i * 6);
        tree.tipCol.set([r * 0.6, g * 0.6, b * 0.6], i * 3);
      });
      tree.geo.attributes.color.needsUpdate = true;
      tree.tipGeo.attributes.color.needsUpdate = true;
    }
  }

  // candidate orbs
  const orbsOn = t > 15.0 && t < 33;
  orbs.visible = orbsOn;
  if (orbsOn) {
    const appear = smooth((t - 15.2) / 1.2);
    empties.forEach((cell, e) => {
      const ts = settleTime[cell], base = cellPos(cell), sol = solution[cell];
      for (let k = 0; k < 9; k++) {
        const dgt = k + 1;
        let p = 1 / 9 * (0.8 + 0.4 * Math.sin(t * 3.1 + cell * 1.7 + k * 2.3));
        if (excluded[cell].has(dgt)) p *= 1 - smooth((t - 16.3 - (cell % 9) * 0.06) / 0.9);  // propagation
        const x = smooth((t - (ts - 1.6)) / 1.6);                                         // decision
        if (decoys[cell].includes(dgt)) p = lerp(p, 0.45 * Math.sin(Math.PI * clamp(x * 1.4)), x);
        else if (dgt !== sol) p = lerp(p, 0, x);
        else p = lerp(p, 1, x);
        let pos = base.clone().add(orbLocal(k));
        let scale = 0.035 + 0.11 * Math.sqrt(Math.max(0, p));
        let bright = 0.25 + 2.4 * p;
        if (dgt === sol && t > ts - 0.2) {   // winner drops into the tile
          const drop = easeIO((t - ts + 0.2) / 0.4);
          pos.lerp(base.clone().add(new THREE.Vector3(0, 0.1, 0)), drop);
          scale *= 1 - drop;
        } else if (t > ts) { scale *= 1 - smooth((t - ts) / 0.3); }
        scale *= appear;
        dummy.position.copy(pos);
        dummy.scale.setScalar(Math.max(scale, 1e-4));
        dummy.updateMatrix();
        orbs.setMatrixAt(e * 9 + k, dummy.matrix);
        const hue = dgt === sol ? lerp(0, 1, x) : 0;
        tmpC.copy(CYAN).lerp(VIOLET, (k % 3) / 3).lerp(GOLD, hue).multiplyScalar(bright * (1 + 0.3 * beatPulse));
        orbs.setColorAt(e * 9 + k, tmpC);
      }
    });
    orbs.instanceMatrix.needsUpdate = true;
    orbs.instanceColor.needsUpdate = true;
  }

  // attention arcs: each beat, the next cell to settle attends to its 20 peers
  arcPos.fill(0); arcCol.fill(0);
  if (t > 16.5 && t < 31.5) {
    let slot = 0;
    const bi = Math.floor((t - 16.5) / BEAT);
    for (let back = 0; back < 3; back++) {
      const b = bi - back;
      if (b < 0) continue;
      const tb = 16.5 + b * BEAT;
      const age = t - tb;
      const focus = order[Math.min(order.length - 1, Math.floor(b * order.length / (15 / BEAT)))];
      const src = cellPos(focus).add(new THREE.Vector3(0, 0.6, 0));
      const fade = Math.exp(-age / 0.45);
      peers[focus].forEach((pj) => {
        if (slot >= ARC_MAX) return;
        const dst = cellPos(pj).add(new THREE.Vector3(0, 0.15, 0));
        const mid = src.clone().add(dst).multiplyScalar(0.5).add(new THREE.Vector3(0, 0.8 + src.distanceTo(dst) * 0.25, 0));
        const grow = clamp(age / 0.25);
        for (let q = 0; q < ARC_SEG; q++) {
          const s0 = q / ARC_SEG * grow, s1 = (q + 1) / ARC_SEG * grow;
          const P = (s) => new THREE.Vector3().copy(src).multiplyScalar((1 - s) ** 2)
            .addScaledVector(mid, 2 * (1 - s) * s).addScaledVector(dst, s * s);
          const a = P(s0), c = P(s1), o = (slot * ARC_SEG + q) * 6;
          arcPos.set([a.x, a.y, a.z, c.x, c.y, c.z], o);
          const k = fade * (0.6 + 0.4 * (q / ARC_SEG));
          arcCol.set([0.5 * k, 0.8 * k, 1.8 * k, 0.9 * k, 0.6 * k, 1.8 * k], o);
        }
        slot++;
      });
    }
  }
  arcGeo.attributes.position.needsUpdate = true;
  arcGeo.attributes.color.needsUpdate = true;

  bloom.strength = 1.0 + 0.25 * (t > 15 && t < 37.5 ? beatPulse : 0);
  composer.render();
}

window.renderAt = renderAt;
window.ready = true;
