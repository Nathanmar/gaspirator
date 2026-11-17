import "@/global.css";

import { Platform } from "react-native";

// Same palette as apps/web (index.css): light = the landing/auth "paper" tokens, dark = the base "ink" tokens.
export const Colors = {
	light: {
		text: "#10150f",
		background: "#f4f0e6",
		backgroundElement: "#ebe5d6",
		backgroundSelected: "#e0d9c8",
		textSecondary: "#56574f",
		lime: "#4c7a0c",
		tomato: "#c8341a",
		onAccent: "#f4f0e6",
	},
	dark: {
		text: "#efe9dc",
		background: "#060807",
		backgroundElement: "#121512",
		backgroundSelected: "#1c201b",
		textSecondary: "#a9a69c",
		lime: "#c6f432",
		tomato: "#ff4f2e",
		onAccent: "#060807",
	},
} as const;

export type ThemeColor = keyof typeof Colors.light & keyof typeof Colors.dark;

export const Fonts = Platform.select({
	ios: {
		/** iOS `UIFontDescriptorSystemDesignDefault` */
		sans: "system-ui",
		/** iOS `UIFontDescriptorSystemDesignSerif` */
		serif: "ui-serif",
		/** iOS `UIFontDescriptorSystemDesignRounded` */
		rounded: "ui-rounded",
		/** iOS `UIFontDescriptorSystemDesignMonospaced` */
		mono: "ui-monospace",
	},
	default: {
		sans: "normal",
		serif: "serif",
		rounded: "normal",
		mono: "monospace",
	},
	web: {
		sans: "var(--font-display)",
		serif: "var(--font-serif)",
		rounded: "var(--font-rounded)",
		mono: "var(--font-mono)",
	},
});

export const Spacing = {
	half: 2,
	one: 4,
	two: 8,
	three: 16,
	four: 24,
	five: 32,
	six: 64,
} as const;

export const MaxContentWidth = 800;
