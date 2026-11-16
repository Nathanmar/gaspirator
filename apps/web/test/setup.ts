import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

const originalFetch = globalThis.fetch;

afterEach(() => {
  cleanup();
  // Tests replace fetch with a mock (`globalThis.fetch = vi.fn()…`): put the real one back so a
  // mock never leaks into the next test.
  globalThis.fetch = originalFetch;
  // Stores persisted with zustand write to localStorage: start every test from a clean slate.
  localStorage.clear();
});
