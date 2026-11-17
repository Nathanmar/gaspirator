import {
	createRootRouteWithContext,
	HeadContent,
	Outlet,
	useRouterState,
} from "@tanstack/react-router";
import { TanStackRouterDevtools } from "@tanstack/react-router-devtools";

import Header from "@/components/header";
import { ThemeProvider } from "@/components/theme-provider";
import { Toaster } from "@/components/ui/sonner";

import "../index.css";

export type RouterAppContext = Record<string, never>;

const FULL_BLEED_PATHS = new Set(["/", "/login", "/register"]);

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
	}),
});

function RootComponent() {
	// The landing and auth pages are full-bleed and bring their own navigation.
	const isFullBleed = useRouterState({
		select: (state) => FULL_BLEED_PATHS.has(state.location.pathname),
	});

	return (
		<>
			<HeadContent />

			<ThemeProvider
				attribute="class"
				defaultTheme="dark"
				disableTransitionOnChange
				storageKey="vite-ui-theme"
			>
				{isFullBleed ? (
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
