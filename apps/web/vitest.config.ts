import { defineConfig, mergeConfig } from "vitest/config";

import viteConfig from "./vite.config";

export default mergeConfig(
	viteConfig,
	defineConfig({
		test: {
			environment: "jsdom",
			include: ["test/**/*.test.{ts,tsx}"],
			setupFiles: ["./test/setup.ts"],
			// Fake API base URL (`.test` is a reserved TLD): tests never reach a real server.
			env: { VITE_API_URL: "http://api.test" },
		},
	}),
);
