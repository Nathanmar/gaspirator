import { createEnv } from "@t3-oss/env-core";
import { z } from "zod";

export const env = createEnv({
  clientPrefix: "EXPO_PUBLIC_",
  client: {
    // Base URL of the API contract (`servers` in `openapi.yaml`), without a trailing slash.
    EXPO_PUBLIC_API_URL: z.url(),
  },
  // Expo only inlines variables read as `process.env.EXPO_PUBLIC_X`, so each one is listed by name.
  runtimeEnv: { EXPO_PUBLIC_API_URL: process.env.EXPO_PUBLIC_API_URL },
  emptyStringAsUndefined: true,
});
