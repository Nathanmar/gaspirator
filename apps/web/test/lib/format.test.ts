import { describe, expect, it } from "vitest";

import {
	formatDate,
	formatDateTime,
	formatDistance,
	formatPickupCode,
	formatPickupWindow,
	formatQuantity,
} from "@/lib/format";

// French typography puts non-breaking spaces before units: compare with plain spaces.
const plain = (text: string) => text.replace(/\s/g, " ");

describe("formatDistance", () => {
	it("gives short distances in metres", () => {
		expect(plain(formatDistance(0.35))).toBe("350 m");
	});

	it("gives other distances in kilometres, to one decimal", () => {
		expect(plain(formatDistance(4.267))).toBe("4,3 km");
		expect(plain(formatDistance(12))).toBe("12 km");
	});
});

describe("formatQuantity", () => {
	it("writes the unit of the lot in French", () => {
		expect(plain(formatQuantity(12, "portions"))).toBe("12 portions");
		expect(plain(formatQuantity(3.5, "kg"))).toBe("3,5 kg");
		expect(plain(formatQuantity(24, "pieces"))).toBe("24 pièces");
	});

	it("keeps portions and pieces singular for one", () => {
		expect(plain(formatQuantity(1, "portions"))).toBe("1 portion");
		expect(plain(formatQuantity(1, "pieces"))).toBe("1 pièce");
	});
});

describe("formatDateTime", () => {
	it("shows the time in Lyon, whatever the time zone of the device", () => {
		expect(plain(formatDateTime("2026-11-03T14:15:00Z"))).toBe(
			"mar. 3 nov. à 15:15",
		);
		expect(plain(formatDateTime("2026-07-03T14:15:00Z"))).toBe(
			"ven. 3 juil. à 16:15",
		);
	});
});

describe("formatPickupWindow", () => {
	it("gives the time range of a window within one day", () => {
		expect(
			plain(formatPickupWindow("2026-11-03T13:00:00Z", "2026-11-03T15:00:00Z")),
		).toBe("mar. 3 nov., entre 14:00 et 16:00");
	});

	it("gives a single time when the window starts and ends together", () => {
		expect(
			plain(formatPickupWindow("2026-11-03T13:00:00Z", "2026-11-03T13:00:00Z")),
		).toBe("mar. 3 nov. à 14:00");
	});

	it("gives both days of a window over midnight in Lyon", () => {
		expect(
			plain(formatPickupWindow("2026-11-03T21:00:00Z", "2026-11-04T08:00:00Z")),
		).toBe("du mar. 3 nov. à 22:00 au mer. 4 nov. à 09:00");
	});
});

describe("formatDate", () => {
	it("gives the day of a calendar date, such as a use-by date", () => {
		expect(plain(formatDate("2026-11-04"))).toBe("mer. 4 nov.");
	});
});

describe("formatPickupCode", () => {
	it("splits the code in two groups of three digits, easier to read out", () => {
		expect(plain(formatPickupCode("482913"))).toBe("482 913");
	});
});
