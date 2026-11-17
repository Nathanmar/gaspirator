import { createFileRoute } from "@tanstack/react-router";

import { Landing } from "@/components/landing/landing";

export const Route = createFileRoute("/")({
	head: () => ({
		meta: [
			{ title: "Gaspirator - Le surplus des uns, le repas des autres" },
			{
				name: "description",
				content:
					"Gaspirator relie cantines, hôpitaux et supermarchés aux associations proches pour que leurs invendus alimentaires soient donnés plutôt que jetés.",
			},
			{ name: "theme-color", content: "#060807" },
		],
	}),
	component: Landing,
});
