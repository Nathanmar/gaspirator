import { vi } from "vitest";

/** Replaces fetch with a mock that resolves with the given response. Restored by `setup.ts`. */
export function mockFetch(response: Response) {
  const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(response);
  globalThis.fetch = fetchMock;
  return fetchMock;
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
