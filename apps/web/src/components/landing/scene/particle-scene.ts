import {
  NormalBlending,
  BufferAttribute,
  BufferGeometry,
  PerspectiveCamera,
  Plane,
  Points,
  Raycaster,
  Scene,
  ShaderMaterial,
  Vector2,
  Vector3,
  WebGLRenderer,
} from "three";

import { buildDust, buildShapes, DUO_CENTER_X, DUO_CENTER_Y } from "./shapes";
import { dustFragment, dustVertex, particleFragment, particleVertex } from "./shaders";

/** Values written by the scroll timeline and read every frame. */
export interface SceneState {
  /** 0 → 5, one unit per landing section. */
  morph: number;
  /** Progress through the vortex section, 0 → 1. */
  dive: number;
  /** Progress through the horizontal "circuit" section, 0 → 1. */
  flow: number;
  /** Intro burst, 0 → 1. */
  intro: number;
}

interface CameraKey {
  position: [number, number, number];
  target: [number, number, number];
  /** Width of the layout; narrow screens pull the camera back to keep it in frame. */
  fit: number;
  /** Sideways shift on wide screens, to clear room for the text. */
  side: number;
}

const CAMERA_KEYS: CameraKey[] = [
  { position: [0, -0.7, 13], target: [0, -1, 0], fit: 0.7, side: 0 },
  { position: [0, 2.6, 11.5], target: [0, -1.1, 0], fit: 1.35, side: 0 },
  { position: [0, 0.8, 13], target: [0, 0.2, 0], fit: 1, side: -2.4 },
  { position: [0, 0.2, 11.5], target: [0, 0, 0], fit: 1.5, side: 0 },
  { position: [0, 0.4, 12], target: [0, 0.4, 0], fit: 1.55, side: 0 },
  { position: [0, 0, 10.5], target: [0, 0, 0], fit: 1, side: 0 },
];

// Camera move added on top of the vortex key: rise above the funnel and look down into it.
const DIVE_POSITION = new Vector3(0, 6.5, -8.5);
const DIVE_TARGET = new Vector3(0, -2.7, 0);

const smooth = (x: number) => x * x * (3 - 2 * x);
const damp = (current: number, target: number, lambda: number, dt: number) =>
  current + (target - current) * (1 - Math.exp(-lambda * dt));

export class ParticleScene {
  private readonly renderer: WebGLRenderer;
  private readonly scene = new Scene();
  private readonly camera = new PerspectiveCamera(35, 1, 0.1, 100);
  private readonly material: ShaderMaterial;
  private readonly dustMaterial: ShaderMaterial;
  private readonly geometries: BufferGeometry[] = [];
  private readonly raycaster = new Raycaster();
  private readonly plane = new Plane();
  private readonly pointer = new Vector2(0, 0);
  private readonly pointerSmooth = new Vector2(0, 0);
  private readonly cameraPosition = new Vector3();
  private readonly cameraTarget = new Vector3();
  private readonly tmp = new Vector3();
  private readonly mouseWorld = new Vector3(0, 0, 50);
  private pointerActive = false;
  private morph = 0;
  private dive = 0;
  private spin = 0;
  private drop = 0;
  private flowPhase = 0;
  private width = 1;
  private height = 1;

  constructor(
    private readonly canvas: HTMLCanvasElement,
    private readonly state: SceneState,
    private readonly options: { reducedMotion: boolean },
  ) {
    this.renderer = new WebGLRenderer({
      canvas,
      alpha: true,
      antialias: false,
      powerPreference: "high-performance",
    });
    this.renderer.setClearColor(0x000000, 0);

    const compact = window.matchMedia("(max-width: 767px)").matches;
    const shapes = buildShapes(compact ? 9000 : 22000);

    const geometry = new BufferGeometry();
    geometry.setAttribute("position", new BufferAttribute(shapes.apple, 3));
    geometry.setAttribute("aTone", new BufferAttribute(shapes.appleTone, 1));
    geometry.setAttribute("aHeap", new BufferAttribute(shapes.heap, 3));
    geometry.setAttribute("aVortex", new BufferAttribute(shapes.vortex, 3));
    geometry.setAttribute("aFlow", new BufferAttribute(shapes.flow, 3));
    geometry.setAttribute("aDuo", new BufferAttribute(shapes.duo, 3));
    geometry.setAttribute("aRing", new BufferAttribute(shapes.ring, 3));
    geometry.setAttribute("aRand", new BufferAttribute(shapes.rand, 4));
    this.geometries.push(geometry);

    this.material = new ShaderMaterial({
      vertexShader: particleVertex,
      fragmentShader: particleFragment,
      transparent: true,
      depthWrite: false,
      blending: NormalBlending,
      uniforms: {
        uTime: { value: 0 },
        uMorph: { value: 0 },
        uIntro: { value: 0 },
        uSpin: { value: 0 },
        uDrop: { value: 0 },
        uFlowPhase: { value: 0 },
        uSize: { value: compact ? 3.6 : 3.2 },
        uScale: { value: 1 },
        uMotion: { value: options.reducedMotion ? 0.2 : 1 },
        uMouse: { value: this.mouseWorld },
        uMouseForce: { value: 0 },
        uDuoCenter: { value: new Vector2(DUO_CENTER_X, DUO_CENTER_Y) },
        uDuoLayout: { value: new Vector3(DUO_CENTER_X, DUO_CENTER_Y, 1) },
      },
    });

    const particles = new Points(geometry, this.material);
    particles.frustumCulled = false;
    this.scene.add(particles);

    const dust = buildDust(compact ? 500 : 1400);
    const dustGeometry = new BufferGeometry();
    dustGeometry.setAttribute("position", new BufferAttribute(dust.positions, 3));
    dustGeometry.setAttribute("aRand", new BufferAttribute(dust.rand, 4));
    this.geometries.push(dustGeometry);

    this.dustMaterial = new ShaderMaterial({
      vertexShader: dustVertex,
      fragmentShader: dustFragment,
      transparent: true,
      depthWrite: false,
      blending: NormalBlending,
      uniforms: {
        uTime: { value: 0 },
        uScale: { value: 1 },
        uMotion: { value: options.reducedMotion ? 0.2 : 1 },
      },
    });
    const dustPoints = new Points(dustGeometry, this.dustMaterial);
    dustPoints.frustumCulled = false;
    this.scene.add(dustPoints);

    this.resize();
  }

  /** Pointer in normalized device coordinates, or null when it leaves the window. */
  setPointer(x: number | null, y = 0) {
    this.pointerActive = x !== null;
    if (x !== null) this.pointer.set(x, y);
  }

  resize() {
    const dpr = Math.min(window.devicePixelRatio, 2);
    this.width = this.canvas.clientWidth || window.innerWidth;
    this.height = this.canvas.clientHeight || window.innerHeight;
    this.renderer.setPixelRatio(dpr);
    this.renderer.setSize(this.width, this.height, false);
    this.camera.aspect = this.width / this.height;
    this.camera.updateProjectionMatrix();
    const scale = (this.height / 900) * dpr;
    this.material.uniforms.uScale.value = scale;
    // Portrait screens can't fit the crate and the heart side by side at full size.
    const portrait = this.camera.aspect < 0.8;
    this.material.uniforms.uDuoLayout.value.set(
      portrait ? 1.9 : DUO_CENTER_X,
      portrait ? 1.6 : DUO_CENTER_Y,
      portrait ? 0.72 : 1,
    );
    this.dustMaterial.uniforms.uScale.value = scale;
  }

  update(time: number, dt: number) {
    const { uniforms } = this.material;
    const motion = this.options.reducedMotion ? 0.2 : 1;

    this.morph = damp(this.morph, this.state.morph, 6, dt);
    this.dive = damp(this.dive, this.state.dive, 6, dt);
    // Speeds are integrated rather than multiplied by time so that changing them never jumps.
    this.spin += dt * (0.6 + this.dive * 2.4) * motion;
    this.drop += dt * (0.04 + this.dive * 0.12) * motion;
    this.flowPhase += dt * 0.035 * motion;

    uniforms.uTime.value = time;
    uniforms.uMorph.value = this.morph;
    uniforms.uIntro.value = this.state.intro;
    uniforms.uSpin.value = this.spin;
    uniforms.uDrop.value = this.drop;
    uniforms.uFlowPhase.value = this.flowPhase + this.state.flow * 0.6;
    this.dustMaterial.uniforms.uTime.value = time;

    this.updateCamera(dt);
    this.updatePointer(dt);

    this.renderer.render(this.scene, this.camera);
  }

  private updateCamera(dt: number) {
    const last = CAMERA_KEYS.length - 1;
    const clamped = Math.min(Math.max(this.morph, 0), last);
    const index = Math.min(Math.floor(clamped), last - 1);
    const f = smooth(clamped - index);
    const from = CAMERA_KEYS[index];
    const to = CAMERA_KEYS[index + 1];
    const aspect = this.camera.aspect;
    const distance = (key: CameraKey) => Math.min(Math.max(key.fit / aspect, 1), 2.4);
    const pullBack = distance(from) + (distance(to) - distance(from)) * f;

    this.cameraPosition.set(
      from.position[0] + (to.position[0] - from.position[0]) * f,
      from.position[1] + (to.position[1] - from.position[1]) * f,
      (from.position[2] + (to.position[2] - from.position[2]) * f) * pullBack,
    );
    this.cameraTarget.set(
      from.target[0] + (to.target[0] - from.target[0]) * f,
      from.target[1] + (to.target[1] - from.target[1]) * f,
      from.target[2] + (to.target[2] - from.target[2]) * f,
    );

    const diveWeight = Math.max(0, 1 - Math.abs(this.morph - 2)) * smooth(this.dive);
    this.cameraPosition.addScaledVector(DIVE_POSITION, diveWeight);
    this.cameraTarget.addScaledVector(DIVE_TARGET, diveWeight);

    // Diving re-centres the funnel, since the camera ends up looking straight down into it.
    const wide = Math.min(Math.max((aspect - 1) / 0.6, 0), 1);
    const side = (from.side + (to.side - from.side) * f) * wide * (1 - diveWeight);
    this.cameraPosition.x += side;
    this.cameraTarget.x += side;

    this.pointerSmooth.x = damp(this.pointerSmooth.x, this.pointer.x, 3, dt);
    this.pointerSmooth.y = damp(this.pointerSmooth.y, this.pointer.y, 3, dt);
    this.cameraPosition.x += this.pointerSmooth.x * 0.5;
    this.cameraPosition.y += this.pointerSmooth.y * 0.3;

    this.camera.position.copy(this.cameraPosition);
    this.camera.lookAt(this.cameraTarget);
  }

  private updatePointer(dt: number) {
    const { uniforms } = this.material;
    const force = this.pointerActive && !this.options.reducedMotion ? 1 : 0;
    uniforms.uMouseForce.value = damp(uniforms.uMouseForce.value, force, 4, dt);
    if (!this.pointerActive) return;

    // Project the pointer onto the plane facing the camera through its target.
    this.camera.getWorldDirection(this.tmp);
    this.plane.setFromNormalAndCoplanarPoint(this.tmp, this.cameraTarget);
    this.raycaster.setFromCamera(this.pointerSmooth, this.camera);
    if (this.raycaster.ray.intersectPlane(this.plane, this.tmp)) {
      this.mouseWorld.lerp(this.tmp, 1 - Math.exp(-10 * dt));
    }
  }

  dispose() {
    for (const geometry of this.geometries) geometry.dispose();
    this.material.dispose();
    this.dustMaterial.dispose();
    this.renderer.dispose();
  }
}
