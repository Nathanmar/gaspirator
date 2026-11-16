import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

afterEach(() => {
  cleanup();
  // Stores persisted with zustand write to localStorage: start every test from a clean slate.
  localStorage.clear();
});
