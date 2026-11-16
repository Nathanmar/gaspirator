import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import Lenis from "lenis";
import { type RefObject, useEffect } from "react";

import type { ParticleScene, SceneState } from "./scene/particle-scene";

import { STAGES } from "./content";

// Background glow behind the particles for each stage, as RGB.
const GLOWS: [number, number, number][] = [
  [255, 79, 46],
  [140, 110, 80],
  [198, 244, 50],
  [239, 233, 220],
  [198, 244, 50],
  [198, 244, 50],
];

const damp = (current: number, target: number, lambda: number, dt: number) =>
  current + (target - current) * (1 - Math.exp(-lambda * dt));

/**
 * Wires the landing page: smooth scroll, scroll-driven 3D morphs, reveals, HUD and cursor.
 * Everything runs client-side; the server-rendered markup is complete without it.
 */
export function useLandingMotion(
  rootRef: RefObject<HTMLDivElement | null>,
  canvasRef: RefObject<HTMLCanvasElement | null>,
) {
  useEffect(() => {
    const root = rootRef.current;
    const canvas = canvasRef.current;
    if (!root || !canvas) return;

    gsap.registerPlugin(ScrollTrigger);
    ScrollTrigger.config({ ignoreMobileResize: true });
    gsap.ticker.lagSmoothing(0);

    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const finePointer = window.matchMedia("(pointer: fine)").matches;
    const sceneState: SceneState = { morph: 0, dive: 0, flow: 0, intro: reducedMotion ? 1 : 0 };
    const cleanups: (() => void)[] = [];
    let scene: ParticleScene | null = null;
    let disposed = false;

    const q = <T extends HTMLElement = HTMLElement>(selector: string, scope: Element = root) =>
      scope.querySelector<T>(selector);
    const qa = <T extends HTMLElement = HTMLElement>(selector: string, scope: Element = root) =>
      Array.from(scope.querySelectorAll<T>(selector));
    const listen = <K extends keyof WindowEventMap>(
      target: Window | HTMLElement,
      type: K,
      handler: (event: WindowEventMap[K]) => void,
    ) => {
      target.addEventListener(type, handler as EventListener, { passive: true });
      cleanups.push(() => target.removeEventListener(type, handler as EventListener));
    };

    document.documentElement.classList.add("landing-active");

    const lenis = reducedMotion ? null : new Lenis({ autoRaf: false, lerp: 0.085 });
    lenis?.on("scroll", ScrollTrigger.update);
    lenis?.stop();

    const sceneReady = import("./scene/particle-scene")
      .then(({ ParticleScene }) => {
        if (!disposed) scene = new ParticleScene(canvas, sceneState, { reducedMotion });
      })
      .catch((error: unknown) => {
        console.warn("Landing 3D scene unavailable", error);
        root.dataset.noWebgl = "";
      });

    const morphTriggers: ScrollTrigger[] = [];
    let pageTrigger: ScrollTrigger | undefined;
    let diveTrigger: ScrollTrigger | undefined;
    let flowTrigger: ScrollTrigger | undefined;
    let marquee: gsap.core.Tween | undefined;

    const preloader = q("[data-preloader]");
    const count = q("[data-preloader-count]");
    const titleChars = qa("[data-hero] h1 [data-char]");
    const heroFades = qa("[data-hero-fade]");
    const hud = qa("[data-hud]");
    const scrollHint = q("[data-scroll-hint]");

    const ctx = gsap.context(() => {
      pageTrigger = ScrollTrigger.create({ trigger: root, start: "top top", end: "bottom bottom" });

      // Intro state, revealed once the preloader leaves.
      gsap.set(titleChars, { yPercent: 115 });
      gsap.set(heroFades, { opacity: 0, y: 24 });
      gsap.set(hud, { opacity: 0 });

      const counter = { value: 0 };
      const loadDuration = reducedMotion ? 0.4 : 2.2;
      const loading = gsap
        .timeline()
        .to(counter, {
          value: 100,
          duration: loadDuration,
          ease: "power2.inOut",
          onUpdate: () => {
            if (count) count.textContent = String(Math.round(counter.value)).padStart(3, "0");
          },
        })
        .to("[data-preloader-bar]", { scaleX: 1, duration: loadDuration, ease: "power2.inOut" }, 0);

      void Promise.all([loading.then(), sceneReady, document.fonts?.ready]).then(() => {
        if (disposed) return;
        ScrollTrigger.refresh();
        ctx.add(() => {
          gsap
            .timeline()
            .to(count, { yPercent: -110, duration: 0.7, ease: "expo.in" })
            .to(
              preloader,
              { clipPath: "inset(0% 0% 100% 0%)", duration: 1.1, ease: "expo.inOut" },
              "-=0.15",
            )
            .set(preloader, { display: "none" })
            .to(sceneState, { intro: 1, duration: 2.6, ease: "expo.out" }, 0.55)
            .to(titleChars, { yPercent: 0, duration: 1.3, ease: "expo.out", stagger: 0.045 }, 0.9)
            .to(
              heroFades,
              { opacity: 1, y: 0, duration: 1, ease: "power3.out", stagger: 0.07 },
              1.1,
            )
            .to(hud, { opacity: 1, duration: 1, stagger: 0.1 }, 1.2)
            .call(
              () => {
                lenis?.start();
                delete scrollHint?.dataset.hidden;
              },
              [],
              1.4,
            );
        });
      });

      // Sections are wired in page order so that triggers below the pinned section
      // are measured after its pin spacing exists.
      for (const section of qa(":scope > main > section")) {
        if (section.matches("[data-stage]")) {
          morphTriggers.push(
            ScrollTrigger.create({ trigger: section, start: "top bottom", end: "top 25%" }),
          );
        }

        if (section.matches("[data-hero]")) {
          gsap.to(q("[data-hero-inner]", section), {
            yPercent: -18,
            opacity: 0,
            ease: "none",
            scrollTrigger: { trigger: section, start: "top top", end: "bottom top", scrub: true },
          });
        }

        if (section.matches("[data-vortex]")) {
          diveTrigger = ScrollTrigger.create({
            trigger: section,
            start: "top top",
            end: "bottom bottom",
          });
          gsap.fromTo(
            qa("[data-word]", section),
            { opacity: 0.14 },
            {
              opacity: 1,
              ease: "none",
              stagger: 0.12,
              scrollTrigger: {
                trigger: section,
                start: "top 35%",
                end: "bottom 140%",
                scrub: true,
              },
            },
          );
        }

        if (section.matches("[data-circuit]")) {
          const track = q("[data-circuit-track]", section);
          const bar = q("[data-circuit-progress]", section);
          if (track) {
            const distance = () => Math.max(0, track.scrollWidth - window.innerWidth);
            const horizontal = gsap.to(track, {
              x: () => -distance(),
              ease: "none",
              scrollTrigger: {
                trigger: section,
                start: "top top",
                end: () => `+=${distance()}`,
                pin: true,
                scrub: true,
                invalidateOnRefresh: true,
                onUpdate: (self) => gsap.set(bar, { scaleX: self.progress }),
              },
            });
            flowTrigger = horizontal.scrollTrigger;

            for (const step of qa("[data-step]", section)) {
              gsap.fromTo(
                step,
                { rotate: 5, yPercent: 12 },
                {
                  rotate: 0,
                  yPercent: 0,
                  ease: "none",
                  scrollTrigger: {
                    trigger: step,
                    containerAnimation: horizontal,
                    start: "left 105%",
                    end: "left 55%",
                    scrub: true,
                  },
                },
              );
            }
          }
        }

        const actors = qa("[data-actor]", section);
        if (actors.length) {
          gsap.from(actors, {
            y: 140,
            opacity: 0,
            rotate: (i: number) => (i % 2 ? 3 : -3),
            duration: 1.4,
            ease: "expo.out",
            stagger: 0.12,
            scrollTrigger: {
              trigger: actors[0],
              start: "top 92%",
              toggleActions: "play none none reverse",
            },
          });
        }

        if (section.matches("[data-zero]")) {
          gsap.fromTo(
            q("[data-zero-word]", section),
            { scale: 0.55, opacity: 0, filter: "blur(24px)" },
            {
              scale: 1,
              opacity: 1,
              filter: "blur(0px)",
              ease: "none",
              scrollTrigger: { trigger: section, start: "top 80%", end: "top 10%", scrub: true },
            },
          );
          gsap.from(q("[data-zero-top]", section), {
            yPercent: 60,
            opacity: 0,
            ease: "none",
            scrollTrigger: { trigger: section, start: "top 85%", end: "top 35%", scrub: true },
          });
          if (!reducedMotion) {
            marquee = gsap.to(q("[data-marquee]", section), {
              xPercent: -50,
              duration: 36,
              ease: "none",
              repeat: -1,
            });
          }
        }

        for (const label of qa("[data-label]", section)) {
          gsap
            .timeline({
              scrollTrigger: {
                trigger: label,
                start: "top 90%",
                toggleActions: "play none none reverse",
              },
            })
            .from(q("[data-label-line]", label), { scaleX: 0, duration: 1.2, ease: "expo.out" })
            .from(label.children, { opacity: 0, duration: 0.8, stagger: 0.08 }, 0);
        }

        for (const element of qa("[data-reveal]", section)) {
          gsap.from(element, {
            y: 70,
            opacity: 0,
            duration: 1.3,
            ease: "expo.out",
            scrollTrigger: {
              trigger: element,
              start: "top 88%",
              toggleActions: "play none none reverse",
            },
          });
        }

        for (const element of qa("[data-count-to]", section)) {
          const target = Number(element.dataset.countTo);
          const counter = { value: 0 };
          element.textContent = "0";
          gsap.to(counter, {
            value: target,
            duration: 2,
            ease: "power3.out",
            onUpdate: () => {
              element.textContent = String(Math.round(counter.value));
            },
            scrollTrigger: {
              trigger: element,
              start: "top 85%",
              toggleActions: "play none none reverse",
            },
          });
        }
      }
    }, root);

    // HUD, background glow and 3D scene, all driven from GSAP's ticker.
    const marker = q("[data-ruler-marker]");
    const rulerValue = q("[data-ruler-value]");
    const stageIndex = q("[data-stage-index]");
    const stageName = q("[data-stage-name]");
    const stageHud = q("[data-stage-hud]");
    let rulerHeight = marker?.parentElement?.clientHeight ?? 0;
    let lastStage = -1;
    let lastPercent = -1;
    let lastGlow = "";
    let marqueeSpeed = 1;

    const tick = (time: number, deltaTime: number) => {
      lenis?.raf(time * 1000);
      const dt = Math.min(deltaTime / 1000, 0.05);

      sceneState.morph = morphTriggers.reduce((sum, trigger) => sum + trigger.progress, 0);
      sceneState.dive = diveTrigger?.progress ?? 0;
      sceneState.flow = flowTrigger?.progress ?? 0;
      scene?.update(time, dt);

      const progress = pageTrigger?.progress ?? 0;
      if (marker) marker.style.transform = `translate3d(0, ${progress * rulerHeight}px, 0)`;
      const percent = Math.round((1 - progress) * 100);
      if (rulerValue && percent !== lastPercent) {
        rulerValue.textContent = `${percent}%`;
        lastPercent = percent;
      }

      const stage = Math.min(STAGES.length - 1, Math.round(sceneState.morph));
      if (stage !== lastStage) {
        if (stageIndex) stageIndex.textContent = `0${stage}`;
        if (stageName) stageName.textContent = STAGES[stage].label;
        lastStage = stage;
      }
      if (scrollHint && progress > 0.01) scrollHint.dataset.hidden = "";
      // Make room for the footer links at the very bottom.
      stageHud?.toggleAttribute("data-hidden", progress > 0.985);

      const from = Math.min(Math.floor(sceneState.morph), GLOWS.length - 2);
      const f = Math.min(Math.max(sceneState.morph - from, 0), 1);
      const glow = GLOWS[from]
        .map((channel, i) => Math.round(channel + (GLOWS[from + 1][i] - channel) * f))
        .join(" ");
      if (glow !== lastGlow) {
        root.style.setProperty("--glow", glow);
        lastGlow = glow;
      }

      if (marquee && lenis) {
        marqueeSpeed = damp(marqueeSpeed, 1 + Math.min(Math.abs(lenis.velocity) * 0.08, 5), 4, dt);
        marquee.timeScale(marqueeSpeed);
      }
    };
    gsap.ticker.add(tick);

    const onRefresh = () => {
      rulerHeight = marker?.parentElement?.clientHeight ?? 0;
    };
    ScrollTrigger.addEventListener("refresh", onRefresh);
    cleanups.push(() => ScrollTrigger.removeEventListener("refresh", onRefresh));
    listen(window, "resize", () => scene?.resize());

    // Smooth in-page navigation.
    const onClick = (event: MouseEvent) => {
      const link = (event.target as Element).closest<HTMLAnchorElement>('a[href^="#"]');
      const hash = link?.getAttribute("href");
      if (!hash || hash === "#") return;
      const target = hash === "#top" ? 0 : root.querySelector<HTMLElement>(hash);
      if (target === null) return;
      event.preventDefault();
      if (lenis) lenis.scrollTo(target, { duration: 2, easing: (t) => 1 - Math.pow(1 - t, 4) });
      else if (target === 0) window.scrollTo({ top: 0 });
      else target.scrollIntoView();
    };
    root.addEventListener("click", onClick);
    cleanups.push(() => root.removeEventListener("click", onClick));

    // Pointer: pushes particles away, drives the custom cursor and magnetic buttons.
    listen(window, "pointermove", (event) => {
      if (event.pointerType !== "mouse") return;
      scene?.setPointer(
        (event.clientX / window.innerWidth) * 2 - 1,
        -(event.clientY / window.innerHeight) * 2 + 1,
      );
    });
    const onLeave = () => scene?.setPointer(null);
    document.documentElement.addEventListener("pointerleave", onLeave);
    cleanups.push(() => document.documentElement.removeEventListener("pointerleave", onLeave));

    if (finePointer && !reducedMotion) {
      const cursor = q("[data-cursor]");
      const ring = q("[data-cursor-ring]");
      const dot = q("[data-cursor-dot]");
      if (cursor && ring && dot) {
        cursor.classList.remove("hidden");
        gsap.set(cursor, { opacity: 0 });
        const ringX = gsap.quickTo(ring, "x", { duration: 0.5, ease: "power3" });
        const ringY = gsap.quickTo(ring, "y", { duration: 0.5, ease: "power3" });
        const dotX = gsap.quickTo(dot, "x", { duration: 0.1, ease: "power3" });
        const dotY = gsap.quickTo(dot, "y", { duration: 0.1, ease: "power3" });
        listen(window, "pointermove", (event) => {
          gsap.to(cursor, { opacity: 1, duration: 0.3, overwrite: "auto" });
          ringX(event.clientX);
          ringY(event.clientY);
          dotX(event.clientX);
          dotY(event.clientY);
        });
        listen(window, "pointerover", (event) => {
          const interactive = (event.target as Element).closest("a, button");
          ring.dataset.hover = interactive ? "true" : "false";
        });
        cleanups.push(() => cursor.classList.add("hidden"));
      }

      for (const element of qa("[data-magnetic]")) {
        const xTo = gsap.quickTo(element, "x", { duration: 0.8, ease: "elastic.out(1, 0.4)" });
        const yTo = gsap.quickTo(element, "y", { duration: 0.8, ease: "elastic.out(1, 0.4)" });
        const onMove = (event: PointerEvent) => {
          const rect = element.getBoundingClientRect();
          xTo((event.clientX - rect.left - rect.width / 2) * 0.3);
          yTo((event.clientY - rect.top - rect.height / 2) * 0.3);
        };
        const onOut = () => {
          xTo(0);
          yTo(0);
        };
        element.addEventListener("pointermove", onMove);
        element.addEventListener("pointerleave", onOut);
        cleanups.push(() => {
          element.removeEventListener("pointermove", onMove);
          element.removeEventListener("pointerleave", onOut);
          gsap.set(element, { x: 0, y: 0 });
        });
      }
    }

    return () => {
      disposed = true;
      gsap.ticker.remove(tick);
      gsap.ticker.lagSmoothing(500, 33);
      for (const cleanup of cleanups) cleanup();
      ctx.revert();
      lenis?.destroy();
      scene?.dispose();
      document.documentElement.classList.remove("landing-active");
      root.style.removeProperty("--glow");
    };
  }, [rootRef, canvasRef]);
}
