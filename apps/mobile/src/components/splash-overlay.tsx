import * as SplashScreen from "expo-splash-screen";
import { useEffect, useState } from "react";
import { StyleSheet, View } from "react-native";
import Animated, {
	Easing,
	FadeOut,
	Keyframe,
	useAnimatedStyle,
	useSharedValue,
	withTiming,
} from "react-native-reanimated";
import Svg, { Path } from "react-native-svg";
import { scheduleOnRN } from "react-native-worklets";

import { LAYERS } from "@/components/logo-mark";
import { ThemedText } from "@/components/themed-text";
import { useTheme } from "@/hooks/use-theme";

const LOGO_WIDTH = 150;
const LOGO_HEIGHT = (LOGO_WIDTH * 435) / 391;
const STAGGER = 90;
// The bands stack up from the tip, then the leaf lands; the vortex holds, then swallows itself.
const EXIT_AT = 1900;

// A band rises from below and widens into place.
const bandIn = new Keyframe({
	0: { opacity: 0, transform: [{ translateY: 36 }, { scaleX: 0.4 }] },
	100: {
		opacity: 1,
		transform: [{ translateY: 0 }, { scaleX: 1 }],
		easing: Easing.out(Easing.back(1.6)),
	},
});

// The leaf falls in from above with a little swing.
const leafIn = new Keyframe({
	0: { opacity: 0, transform: [{ translateY: -60 }, { rotate: "-35deg" }] },
	70: {
		opacity: 1,
		transform: [{ translateY: 6 }, { rotate: "8deg" }],
		easing: Easing.out(Easing.quad),
	},
	100: {
		opacity: 1,
		transform: [{ translateY: 0 }, { rotate: "0deg" }],
		easing: Easing.inOut(Easing.quad),
	},
});

const ringPulse = new Keyframe({
	0: { opacity: 0.8, transform: [{ scale: 0.3 }] },
	100: {
		opacity: 0,
		transform: [{ scale: 1.6 }],
		easing: Easing.out(Easing.cubic),
	},
});

const wordIn = new Keyframe({
	0: { opacity: 0, transform: [{ translateY: 16 }] },
	100: {
		opacity: 1,
		transform: [{ translateY: 0 }],
		easing: Easing.out(Easing.cubic),
	},
});

// Leaf last; the food and the back of the top ring arrive with the top ring.
const LEAF_LEVEL = 6;
const LEAF_DELAY = LEAF_LEVEL * STAGGER + 120;

/** Branded launch animation, drawn over the app until it ends. */
export function SplashOverlay() {
	const theme = useTheme();
	const [visible, setVisible] = useState(true);
	const exit = useSharedValue(0);

	useEffect(() => {
		const timer = setTimeout(() => {
			exit.value = withTiming(
				1,
				{ duration: 420, easing: Easing.in(Easing.cubic) },
				(finished) => {
					if (finished) scheduleOnRN(setVisible, false);
				},
			);
		}, EXIT_AT);
		return () => clearTimeout(timer);
	}, [exit]);

	// Sucked into its own vortex: spins, shrinks toward the tip and fades.
	const swallow = useAnimatedStyle(() => ({
		opacity: 1 - exit.value,
		transform: [
			{ translateY: exit.value * 40 },
			{ rotate: `${exit.value * 120}deg` },
			{ scale: 1 - exit.value * 0.9 },
		],
	}));

	if (!visible) return null;

	return (
		<Animated.View
			exiting={FadeOut.duration(250)}
			// The native splash (same background) stays until this first frame is drawn.
			onLayout={() => SplashScreen.hideAsync()}
			style={[styles.overlay, { backgroundColor: theme.background }]}
			accessibilityLabel="Gaspirator"
		>
			<Animated.View style={[styles.logo, swallow]}>
				<Animated.View
					entering={ringPulse.delay(LEAF_DELAY).duration(900)}
					style={[styles.ring, { borderColor: theme.lime }]}
				/>
				{LAYERS.map((layer) => {
					const isLeaf = layer.level === LEAF_LEVEL;
					const entering = isLeaf
						? leafIn.delay(LEAF_DELAY).duration(650)
						: bandIn.delay(layer.level * STAGGER).duration(480);
					return (
						<Animated.View
							key={layer.d}
							entering={entering}
							style={StyleSheet.absoluteFill}
						>
							<Svg width="100%" height="100%" viewBox="0 0 391 435">
								<Path d={layer.d} fill={layer.fill} />
							</Svg>
						</Animated.View>
					);
				})}
			</Animated.View>

			<Animated.View
				entering={wordIn.delay(LEAF_DELAY + 250).duration(500)}
				style={styles.word}
			>
				<Animated.View style={swallow}>
					<ThemedText style={styles.brand}>gaspirator</ThemedText>
				</Animated.View>
			</Animated.View>
			<View style={styles.spacer} />
		</Animated.View>
	);
}

const styles = StyleSheet.create({
	overlay: {
		...StyleSheet.absoluteFill,
		alignItems: "center",
		justifyContent: "center",
		zIndex: 1000,
	},
	logo: {
		width: LOGO_WIDTH,
		height: LOGO_HEIGHT,
		alignItems: "center",
		justifyContent: "center",
	},
	ring: {
		position: "absolute",
		width: LOGO_WIDTH * 1.4,
		height: LOGO_WIDTH * 1.4,
		borderRadius: LOGO_WIDTH,
		borderWidth: 2,
	},
	word: {
		marginTop: 20,
	},
	brand: {
		fontSize: 36,
		lineHeight: 40,
		fontWeight: 700,
		letterSpacing: -1,
	},
	// Balances the wordmark so the logo sits at the screen's centre.
	spacer: {
		height: 60,
	},
});
