import { createEnv } from "@t3-oss/env-core";
import { z } from "zod";

export const env = createEnv({
  clientPrefix: "VITE_",
  client: {
    // Base URL of the API contract (`servers` in `openapi.yaml`), without a trailing slash.
    VITE_API_URL: z.url(),
  },
  // Must stay written exactly `import.meta.env`: Vite only injects the variables where it finds
  // that text (a cast such as `(import.meta as …).env` leaves `env` undefined at runtime).
  runtimeEnv: import.meta.env,
  emptyStringAsUndefined: true,
});
