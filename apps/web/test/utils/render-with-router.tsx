import type { ReactNode } from "react";

import {
  RouterProvider,
  createMemoryHistory,
  createRootRoute,
  createRoute,
  createRouter,
} from "@tanstack/react-router";
import { render } from "@testing-library/react";

/**
 * Renders `ui` at `path` inside an in-memory router, so `Link` and `useNavigate` work.
 * Any other path renders nothing: after a navigation, check `router.state.location`.
 */
export function renderWithRouter(ui: ReactNode, { path = "/" }: { path?: string } = {}) {
  const rootRoute = createRootRoute();
  const pageRoute = createRoute({ getParentRoute: () => rootRoute, path, component: () => ui });
  const otherRoutes = createRoute({ getParentRoute: () => rootRoute, path: "$" });

  const router = createRouter({
    routeTree: rootRoute.addChildren([pageRoute, otherRoutes]),
    history: createMemoryHistory({ initialEntries: [path] }),
  });
  render(<RouterProvider router={router} />);
  return router;
}
