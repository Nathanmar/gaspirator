import {
  HeadContent,
  Outlet,
  createRootRouteWithContext,
  useRouterState,
} from "@tanstack/react-router";
import { TanStackRouterDevtools } from "@tanstack/react-router-devtools";

import Header from "@/components/header";
import { ThemeProvider } from "@/components/theme-provider";
import { Toaster } from "@/components/ui/sonner";

import "../index.css";

export type RouterAppContext = Record<string, never>;

export const Route = createRootRouteWithContext<RouterAppContext>()({
  component: RootComponent,
  head: () => ({
    meta: [
      {
        title: "gaspirator",
      },
      {
        name: "description",
        content: "gaspirator is a web application",
      },
    ],
    links: [
      {
        rel: "icon",
        href: "/favicon.ico",
      },
      {
        rel: "icon",
        type: "image/svg+xml",
        href: "/favicon.svg",
      },
    ],
  }),
});

function RootComponent() {
  // The landing page is full-bleed and brings its own navigation.
  const isLanding = useRouterState({ select: (state) => state.location.pathname === "/" });

  return (
    <>
      <HeadContent />

      <ThemeProvider
        attribute="class"
        defaultTheme="dark"
        disableTransitionOnChange
        storageKey="vite-ui-theme"
      >
        {isLanding ? (
          <Outlet />
        ) : (
          <div className="grid h-svh grid-rows-[auto_1fr]">
            <Header />
            <Outlet />
          </div>
        )}
        <Toaster richColors />
      </ThemeProvider>

      <TanStackRouterDevtools position="bottom-left" />
    </>
  );
}
