import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import Loader from "@/components/loader";

describe("Loader", () => {
	it("announces loading to screen readers", () => {
		render(<Loader />);

		expect(
			screen.getByRole("status", { name: "Loading…" }),
		).toBeInTheDocument();
	});
});
