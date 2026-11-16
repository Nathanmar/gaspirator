// Ashima Arts 3D simplex noise (MIT), used for idle drift and the turbulence between layouts.
const simplexNoise = /* glsl */ `
vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec4 mod289(vec4 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec4 permute(vec4 x) { return mod289(((x * 34.0) + 1.0) * x); }
vec4 taylorInvSqrt(vec4 r) { return 1.79284291400159 - 0.85373472095314 * r; }

float snoise(vec3 v) {
  const vec2 C = vec2(1.0 / 6.0, 1.0 / 3.0);
  const vec4 D = vec4(0.0, 0.5, 1.0, 2.0);
  vec3 i = floor(v + dot(v, C.yyy));
  vec3 x0 = v - i + dot(i, C.xxx);
  vec3 g = step(x0.yzx, x0.xyz);
  vec3 l = 1.0 - g;
  vec3 i1 = min(g.xyz, l.zxy);
  vec3 i2 = max(g.xyz, l.zxy);
  vec3 x1 = x0 - i1 + C.xxx;
  vec3 x2 = x0 - i2 + C.yyy;
  vec3 x3 = x0 - D.yyy;
  i = mod289(i);
  vec4 p = permute(permute(permute(
    i.z + vec4(0.0, i1.z, i2.z, 1.0))
    + i.y + vec4(0.0, i1.y, i2.y, 1.0))
    + i.x + vec4(0.0, i1.x, i2.x, 1.0));
  float n_ = 0.142857142857;
  vec3 ns = n_ * D.wyz - D.xzx;
  vec4 j = p - 49.0 * floor(p * ns.z * ns.z);
  vec4 x_ = floor(j * ns.z);
  vec4 y_ = floor(j - 7.0 * x_);
  vec4 x = x_ * ns.x + ns.yyyy;
  vec4 y = y_ * ns.x + ns.yyyy;
  vec4 h = 1.0 - abs(x) - abs(y);
  vec4 b0 = vec4(x.xy, y.xy);
  vec4 b1 = vec4(x.zw, y.zw);
  vec4 s0 = floor(b0) * 2.0 + 1.0;
  vec4 s1 = floor(b1) * 2.0 + 1.0;
  vec4 sh = -step(h, vec4(0.0));
  vec4 a0 = b0.xzyw + s0.xzyw * sh.xxyy;
  vec4 a1 = b1.xzyw + s1.xzyw * sh.zzww;
  vec3 p0 = vec3(a0.xy, h.x);
  vec3 p1 = vec3(a0.zw, h.y);
  vec3 p2 = vec3(a1.xy, h.z);
  vec3 p3 = vec3(a1.zw, h.w);
  vec4 norm = taylorInvSqrt(vec4(dot(p0, p0), dot(p1, p1), dot(p2, p2), dot(p3, p3)));
  p0 *= norm.x;
  p1 *= norm.y;
  p2 *= norm.z;
  p3 *= norm.w;
  vec4 m = max(0.6 - vec4(dot(x0, x0), dot(x1, x1), dot(x2, x2), dot(x3, x3)), 0.0);
  m = m * m;
  return 42.0 * dot(m * m, vec4(dot(p0, x0), dot(p1, x1), dot(p2, x2), dot(p3, x3)));
}
`;

export const particleVertex = /* glsl */ `
uniform float uTime;
uniform float uMorph;
uniform float uIntro;
uniform float uSpin;
uniform float uDrop;
uniform float uFlowPhase;
uniform float uSize;
uniform float uScale;
uniform float uMotion;
uniform vec3 uMouse;
uniform float uMouseForce;
uniform vec2 uDuoCenter;
uniform vec3 uDuoLayout; // on-screen centre x, centre y, scale

attribute float aTone;
attribute vec3 aHeap;
attribute vec3 aVortex;
attribute vec3 aFlow;
attribute vec3 aDuo;
attribute vec3 aRing;
attribute vec4 aRand;

varying vec3 vColor;
varying float vAlpha;

const float PI = 3.141592653589793;
const float TAU = 6.283185307179586;
const vec3 LIME = vec3(0.776, 0.957, 0.196);
const vec3 TOMATO = vec3(1.0, 0.31, 0.18);
const vec3 ORANGE = vec3(1.0, 0.56, 0.22);
const vec3 CREAM = vec3(0.937, 0.914, 0.863);
const vec3 SOIL = vec3(0.62, 0.5, 0.38);
const vec3 ASH = vec3(0.66, 0.65, 0.6);
const vec3 STEM = vec3(0.6, 0.42, 0.25);

${simplexNoise}

vec2 rot2(vec2 v, float a) {
  float c = cos(a);
  float s = sin(a);
  return vec2(c * v.x - s * v.y, s * v.x + c * v.y);
}

// Staggered progress of the morph into layout k + 1, so particles leave one by one.
float stageT(float k) {
  return smoothstep(0.0, 1.0, clamp((uMorph - k) * 1.7 - aRand.x * 0.7, 0.0, 1.0));
}

void main() {
  float tone = aRand.z;
  float t = uTime * uMotion;

  // 0 — apple
  vec3 p0 = position * (1.0 + sin(t * 1.3) * 0.015);
  p0.xz = rot2(p0.xz, t * 0.2);
  vec3 c0 = aTone < 0.5 ? mix(TOMATO, ORANGE, tone * 0.7) : (aTone < 1.5 ? LIME : STEM);
  c0 = mix(c0, CREAM, step(0.94, tone) * 0.7);
  // Light the apple body as a sphere: key light from the top left plus a rim on the silhouette.
  if (aTone < 0.5) {
    vec3 normal = normalize(p0);
    vec3 viewNormal = normalize((modelViewMatrix * vec4(normal, 0.0)).xyz);
    float key = max(dot(normal, normalize(vec3(-0.6, 0.7, 0.5))), 0.0);
    float rim = pow(1.0 - abs(viewNormal.z), 2.5);
    c0 *= 0.35 + key * 0.9 + rim * 0.9;
  }

  // 1 — waste heap, with scraps still falling on it
  vec3 p1 = aHeap;
  float a1 = 1.0;
  if (aRand.w < 0.16) {
    float fall = fract(aRand.w * 37.0 + t * 0.11);
    p1.y = mix(5.5, aHeap.y, fall * fall);
    a1 = smoothstep(0.0, 0.15, fall);
  }
  p1.xz = rot2(p1.xz, t * 0.03);
  vec3 c1 = mix(SOIL, ASH, tone);
  c1 = mix(c1, TOMATO, step(0.93, tone) * 0.85);

  // 2 — vortex: particles spiral down the funnel, faster near the core
  float s = fract(aVortex.y - uDrop);
  float r = (0.1 + 2.7 * pow(s, 1.8)) * (0.8 + aVortex.z * 0.4);
  float ang = aVortex.x + uSpin * (0.35 + 0.8 / (r + 0.3));
  vec3 p2 = vec3(cos(ang) * r, mix(-3.6, 3.4, s), sin(ang) * r);
  vec3 c2 = mix(LIME, CREAM, smoothstep(0.2, 1.0, s) * 0.8);
  float a2 = smoothstep(0.0, 0.06, s) * smoothstep(1.0, 0.9, s);

  // 3 — braided flow, from suppliers (left) to charities (right)
  float fs = fract(aFlow.x + uFlowPhase);
  float fx = mix(-9.0, 9.0, fs);
  float strand = aFlow.y;
  vec3 p3 = vec3(
    fx,
    sin(fx * 0.42 + strand * 1.3 + t * 0.5) * 0.95,
    cos(fx * 0.33 + strand * 2.1 + t * 0.35) * 1.4
  );
  float thick = 0.05 + 0.3 * aFlow.z * aFlow.z;
  float fa = aRand.w * TAU * 3.0;
  p3.y += sin(fa) * thick;
  p3.z += cos(fa) * thick;
  vec3 c3 = mix(CREAM, LIME, step(0.72, tone));
  float a3 = smoothstep(0.0, 0.1, fs) * smoothstep(1.0, 0.9, fs);

  // 4 — a crate (suppliers) and a beating heart (charities)
  bool crate = aDuo.x < 0.0;
  vec3 center = vec3(crate ? -uDuoCenter.x : uDuoCenter.x, uDuoCenter.y, 0.0);
  vec3 q = aDuo - center;
  if (crate) {
    q.xz = rot2(q.xz, t * 0.35);
    q.yz = rot2(q.yz, 0.35);
  } else {
    q.xz = rot2(q.xz, sin(t * 0.7) * 0.6);
    q *= 1.0 + pow(0.5 + 0.5 * sin(t * 2.6), 8.0) * 0.08;
  }
  vec3 p4 = vec3(crate ? -uDuoLayout.x : uDuoLayout.x, uDuoLayout.y, 0.0) + q * uDuoLayout.z;
  vec3 c4 = mix(crate ? LIME : TOMATO, CREAM, step(0.9, tone) * 0.7);

  // 5 — the "0": an upright ring with particles flowing around it, plus a loose orbit
  float u = aRing.x + t * 0.12 * (0.6 + aRand.y * 0.8);
  float ringR = 1.85;
  float tubeR = 0.42 * aRing.z;
  if (aRand.w > 0.86) {
    ringR = 3.0 + aRing.z * 0.6;
    tubeR = 0.06;
    u = aRing.x - t * 0.05;
  }
  float band = ringR + tubeR * cos(aRing.y);
  vec3 p5 = vec3(band * cos(u), band * sin(u) * 1.28, tubeR * sin(aRing.y));
  p5.xz = rot2(p5.xz, sin(t * 0.4) * 0.35);
  vec3 c5 = mix(LIME, CREAM, step(0.78, tone));

  float t1 = stageT(0.0);
  float t2 = stageT(1.0);
  float t3 = stageT(2.0);
  float t4 = stageT(3.0);
  float t5 = stageT(4.0);

  vec3 p = mix(p0, p1, t1);
  p = mix(p, p2, t2);
  p = mix(p, p3, t3);
  p = mix(p, p4, t4);
  p = mix(p, p5, t5);

  vec3 color = mix(c0, c1, t1);
  color = mix(color, c2, t2);
  color = mix(color, c3, t3);
  color = mix(color, c4, t4);
  color = mix(color, c5, t5);

  float alpha = mix(1.0, a1, t1);
  alpha = mix(alpha, a2, t2);
  alpha = mix(alpha, a3, t3);
  alpha = mix(alpha, 1.0, t4);

  // Particles swirl while travelling between layouts, and burst in during the intro.
  float transit = sin(t1 * PI) + sin(t2 * PI) + sin(t3 * PI) + sin(t4 * PI) + sin(t5 * PI);
  float scatter = 1.0 - uIntro;
  vec3 np = p * 0.3 + t * 0.06;
  vec3 drift = vec3(
    snoise(np),
    snoise(np + vec3(17.0, 3.0, 9.0)),
    snoise(np + vec3(-7.0, 23.0, 11.0))
  );
  p += drift * (0.05 * uMotion + transit * 1.3 + scatter * 5.0);
  p *= 1.0 + scatter * 1.2;

  vec3 d = p - uMouse;
  float dist = length(d);
  float push = exp(-dist * dist * 0.8) * uMouseForce;
  p += d / max(dist, 0.001) * push * 0.9;

  vec4 mv = modelViewMatrix * vec4(p, 1.0);
  gl_Position = projectionMatrix * mv;
  gl_PointSize = uSize * (0.35 + aRand.y * aRand.y * 1.6) * uScale * (10.0 / -mv.z);

  vColor = color + push * 0.35;
  vAlpha = alpha * uIntro;
}
`;

export const particleFragment = /* glsl */ `
varying vec3 vColor;
varying float vAlpha;

void main() {
  float d = length(gl_PointCoord - 0.5);
  float a = pow(smoothstep(0.5, 0.0, d), 1.6);
  if (a < 0.01) discard;
  gl_FragColor = vec4(vColor, a * vAlpha * 0.9);
}
`;

export const dustVertex = /* glsl */ `
uniform float uTime;
uniform float uScale;
uniform float uMotion;

attribute vec4 aRand;

varying float vAlpha;

void main() {
  float t = uTime * uMotion;
  vec3 p = position;
  p.y = mod(p.y + t * 0.08 * (0.3 + aRand.x) + 10.0, 20.0) - 10.0;
  p.x += sin(t * 0.2 + aRand.y * 6.2831) * 0.3;
  vec4 mv = modelViewMatrix * vec4(p, 1.0);
  gl_Position = projectionMatrix * mv;
  gl_PointSize = (1.0 + aRand.z * 2.0) * uScale * (10.0 / -mv.z);
  vAlpha = 0.12 + aRand.w * 0.3;
}
`;

export const dustFragment = /* glsl */ `
varying float vAlpha;

void main() {
  float d = length(gl_PointCoord - 0.5);
  float a = smoothstep(0.5, 0.1, d);
  if (a < 0.01) discard;
  gl_FragColor = vec4(0.937, 0.914, 0.863, a * vAlpha);
}
`;
