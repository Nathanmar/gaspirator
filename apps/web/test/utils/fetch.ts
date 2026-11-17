import { vi } from "vitest";

/** Replaces fetch with a mock that resolves with the given response. Restored by `setup.ts`. */
export function mockFetch(response: Response) {
	const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(response);
	globalThis.fetch = fetchMock;
	return fetchMock;
}

/**
 * Replaces fetch with a mock that answers by path (`/me`, `/suppliers`…), whatever the query
 * string. Each call gets a fresh copy, as a body can only be read once.
 */
export function mockApi(responses: Record<string, Response>) {
	const fetchMock = vi.fn<typeof fetch>(async (input) => {
		const { pathname } = new URL(String(input));
		const response = responses[pathname];
		if (!response) throw new Error(`Unexpected request to ${pathname}`);
		return response.clone();
	});
	globalThis.fetch = fetchMock;
	return fetchMock;
}

/** Paths requested from the fetch mock, in order. */
export function requestedPaths(
	fetchMock: ReturnType<typeof vi.fn<typeof fetch>>,
) {
	return fetchMock.mock.calls.map(([input]) => {
		const url = new URL(String(input));
		return url.pathname + url.search;
	});
}

export function jsonResponse(status: number, body: unknown) {
	return new Response(JSON.stringify(body), {
		status,
		headers: { "Content-Type": "application/json" },
	});
}

/** Parses the JSON body of the first request sent to the fetch mock. */
export function sentBody(fetchMock: ReturnType<typeof mockFetch>): unknown {
	const [, init] = fetchMock.mock.calls[0];
	return JSON.parse(String(init?.body));
}
