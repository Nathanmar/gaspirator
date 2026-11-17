import { copyFileSync, mkdirSync } from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";
import tailwindcss from "@tailwindcss/vite";
import { tanstackRouter } from "@tanstack/router-plugin/vite";
import react from "@vitejs/plugin-react";
import { defineConfig, type Plugin } from "vite";

// MapLibre runs its tiles in a self-contained worker that has to be served as a static file;
// copy it into public/ (git-ignored) so dev and build serve it at /maplibre/.
function maplibreWorker(): Plugin {
	return {
		name: "maplibre-worker",
		// `config` runs before Vite indexes public/, so the dev server serves the copy right away.
		config() {
			const source = createRequire(import.meta.url).resolve(
				"maplibre-gl/dist/maplibre-gl-worker.mjs",
			);
			const target = path.resolve(import.meta.dirname, "public/maplibre");
			mkdirSync(target, { recursive: true });
			copyFileSync(source, path.join(target, "maplibre-gl-worker.mjs"));
		},
	};
}

export default defineConfig({
	plugins: [maplibreWorker(), tailwindcss(), tanstackRouter({}), react()],
	resolve: {
		alias: {
			"@": path.resolve(import.meta.dirname, "./src"),
		},
	},
	server: {
		port: 5173,
	},
});
