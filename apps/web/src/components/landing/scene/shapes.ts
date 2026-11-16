// Target layouts for the landing particles. Each particle owns one slot in every layout and
// the vertex shader morphs between them as the page scrolls:
// apple → waste heap → vortex → braided flow → crate & heart → ring.
// Some layouts store parameters (angles, heights) instead of positions so the shader can animate them.

const TAU = Math.PI * 2;

export const DUO_CENTER_X = 3.3;
export const DUO_CENTER_Y = 1.2;

export interface ShapeData {
  count: number;
  apple: Float32Array;
  appleTone: Float32Array;
  heap: Float32Array;
  vortex: Float32Array;
  flow: Float32Array;
  duo: Float32Array;
  ring: Float32Array;
  rand: Float32Array;
}

function gauss() {
  let u = 0;
  while (u === 0) u = Math.random();
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(TAU * Math.random());
}

function writeApple(out: Float32Array, tones: Float32Array, i: number) {
  const roll = Math.random();
  let x: number;
  let y: number;
  let z: number;

  if (roll < 0.87) {
    // Body: a sphere with a dimple at both poles and five soft lobes at the bottom.
    const t = Math.acos(1 - 2 * Math.random());
    const phi = Math.random() * TAU;
    const top = Math.exp(-((t / 0.5) ** 2));
    const bottom = Math.exp(-(((Math.PI - t) / 0.55) ** 2));
    const lobes = 1 + 0.04 * Math.sin(5 * phi) * (t / Math.PI) ** 2;
    const radius = 2 * lobes * (1 - 0.16 * Math.random() ** 5);
    x = radius * Math.sin(t) * Math.cos(phi) * 1.05;
    z = radius * Math.sin(t) * Math.sin(phi) * 1.05;
    y = radius * Math.cos(t) * 0.92 - 0.7 * top + 0.6 * bottom;
    tones[i] = 0;
  } else if (roll < 0.955) {
    // Leaf: a curled ellipse with a central vein, rising from the stem.
    const u = Math.random();
    const width = 0.42 * Math.sin(Math.PI * u) ** 0.75;
    const v = Math.random() < 0.2 ? gauss() * 0.03 : (Math.random() * 2 - 1) * width;
    const lx = u * 1.3;
    const lz = 0.18 * u * u - 0.1 * (v / 0.42) ** 2;
    const lift = 0.55;
    const px = lx * Math.cos(lift) - v * Math.sin(lift);
    const py = lx * Math.sin(lift) + v * Math.cos(lift);
    const yaw = -0.7;
    x = 0.1 + px * Math.cos(yaw) + lz * Math.sin(yaw);
    y = 1.35 + py;
    z = -px * Math.sin(yaw) + lz * Math.cos(yaw);
    tones[i] = 1;
  } else {
    const k = Math.random();
    x = 0.16 * k * k + gauss() * 0.025;
    y = 1 + k * 0.85;
    z = gauss() * 0.025;
    tones[i] = 2;
  }

  out[i * 3] = x;
  out[i * 3 + 1] = y;
  out[i * 3 + 2] = z;
}

function writeHeap(out: Float32Array, i: number) {
  const rr = Math.sqrt(Math.random());
  const phi = Math.random() * TAU;
  const height = 2.3 * Math.exp(-rr * rr * 3.4);
  const fill = Math.random() ** 0.3;
  const x = rr * 5 * Math.cos(phi) * 1.2;
  const z = rr * 5 * Math.sin(phi) * 0.75;
  out[i * 3] = x;
  out[i * 3 + 1] = -2.6 + height * fill + 0.18 * Math.sin(x * 1.7) * Math.cos(z * 2.3) * fill;
  out[i * 3 + 2] = z;
}

function writeCrate(out: Float32Array, i: number) {
  const half = 1.05;
  const face = Math.floor(Math.random() * 6);
  const a = Math.random() * 2 - 1;
  let b = Math.random() * 2 - 1;
  // Most points snap to five slats per face so the cube reads as a wooden crate.
  if (Math.random() < 0.7) b = Math.round(b * 2) / 2 + gauss() * 0.012;
  const axis = face >> 1;
  const point = [0, 0, 0];
  point[axis] = face & 1 ? 1 : -1;
  point[(axis + 1) % 3] = a;
  point[(axis + 2) % 3] = b;
  out[i * 3] = -DUO_CENTER_X + point[0] * half;
  out[i * 3 + 1] = DUO_CENTER_Y + point[1] * half;
  out[i * 3 + 2] = point[2] * half;
}

function writeHeart(out: Float32Array, i: number) {
  // Taubin's heart surface, z up. Keep only points in a thin shell under the surface.
  let hx = 0;
  let hy = 0;
  let hz = 0;
  for (let tries = 0; tries < 400; tries++) {
    hx = (Math.random() * 2 - 1) * 1.25;
    hy = (Math.random() * 2 - 1) * 0.8;
    hz = (Math.random() * 2 - 1) * 1.3;
    const a = hx * hx + 2.25 * hy * hy + hz * hz - 1;
    const f = a * a * a - hx * hx * hz * hz * hz - 0.1125 * hy * hy * hz * hz * hz;
    if (f <= 0 && f > -0.08) break;
  }
  out[i * 3] = DUO_CENTER_X + hx * 1.25;
  out[i * 3 + 1] = DUO_CENTER_Y + 0.15 + hz * 1.25;
  out[i * 3 + 2] = hy * 1.25;
}

export function buildShapes(count: number): ShapeData {
  const data: ShapeData = {
    count,
    apple: new Float32Array(count * 3),
    appleTone: new Float32Array(count),
    heap: new Float32Array(count * 3),
    vortex: new Float32Array(count * 3),
    flow: new Float32Array(count * 3),
    duo: new Float32Array(count * 3),
    ring: new Float32Array(count * 3),
    rand: new Float32Array(count * 4),
  };

  for (let i = 0; i < count; i++) {
    const i3 = i * 3;
    const i4 = i * 4;

    writeApple(data.apple, data.appleTone, i);
    writeHeap(data.heap, i);

    // Vortex: start angle, height along the funnel, radial jitter.
    data.vortex[i3] = Math.random() * TAU;
    data.vortex[i3 + 1] = Math.random();
    data.vortex[i3 + 2] = Math.random();

    // Flow: position along the stream, strand index, distance from the strand.
    data.flow[i3] = Math.random();
    data.flow[i3 + 1] = Math.floor(Math.random() * 6);
    data.flow[i3 + 2] = Math.random();

    if (i % 2 === 0) writeCrate(data.duo, i);
    else writeHeart(data.duo, i);

    // Ring: angle around the ring, angle around the tube, tube radius.
    data.ring[i3] = Math.random() * TAU;
    data.ring[i3 + 1] = Math.random() * TAU;
    data.ring[i3 + 2] = 0.55 + 0.45 * Math.random();

    data.rand[i4] = Math.random();
    data.rand[i4 + 1] = Math.random();
    data.rand[i4 + 2] = Math.random();
    data.rand[i4 + 3] = Math.random();
  }

  return data;
}

export function buildDust(count: number) {
  const positions = new Float32Array(count * 3);
  const rand = new Float32Array(count * 4);
  for (let i = 0; i < count; i++) {
    positions[i * 3] = (Math.random() * 2 - 1) * 16;
    positions[i * 3 + 1] = (Math.random() * 2 - 1) * 10;
    positions[i * 3 + 2] = (Math.random() * 2 - 1) * 10 - 2;
    for (let k = 0; k < 4; k++) rand[i * 4 + k] = Math.random();
  }
  return { positions, rand };
}
