import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Hud } from "@/components/landing/hud";

import { renderWithRouter } from "../../utils/render-with-router";

describe("Hud", () => {
  it("sends the join button to the registration page", async () => {
    renderWithRouter(<Hud />);

    expect(await screen.findByRole("link", { name: "Rejoindre" })).toHaveAttribute(
      "href",
      "/register",
    );
  });
});
