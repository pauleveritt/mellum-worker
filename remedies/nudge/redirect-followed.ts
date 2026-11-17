/** Remedy unit: when a run's output shows a redirect (3xx) read back as 200, say why. A test client
 * that follows redirects (the default for Starlette/FastAPI's TestClient and httpx-based clients)
 * reports the final page's 200, with the 3xx in `response.history`. Generic HTTP test-client
 * knowledge: no route, path or expected value from any suite. */
import type { PiLike, UnitMeta } from "../install.ts";

export const meta: UnitMeta = {
	pathology:
		"Asserts a redirect with a client that follows redirects, reads the final page's 200, and debugs a route that already redirects",
	does: "When a command's output shows 200 against an expected 3xx, appends a note: the client followed the redirect; use follow_redirects=False or response.history (at most 3 notes)",
	lesson: "",
	evidence:
		"failure-reasons screen (docs/superpowers/research/2026-11-13-reply-to-handover.md): 2 of 3 medium reps stalled in this debug, 17 and 23 turns; unmeasured as a remedy",
};

/** 200 compared with a 3xx in either order, as pytest (`assert 200 == 303`) and unittest (`200 != 303`) print it. */
const MISMATCH = /(?<![\w.])(?:200\s*(?:==|!=)\s*30[1-8]|30[1-8]\s*(?:==|!=)\s*200)(?![\w.])/;
const RAN = new Set(["bash"]);

export const NOTE =
	"\n\n[note: a 200 where a redirect (3xx) was expected usually means the test client FOLLOWED the redirect " +
	"and reports the final page. The default test client follows redirects; the 3xx is in `response.history`. " +
	"To check the redirect itself, build the client with `follow_redirects=False` " +
	"(for example `TestClient(app, follow_redirects=False)`) and assert the status and the `location` header. " +
	"If that shows the 3xx, the route is already right: fix the test, not the route.]";

export function install(pi: PiLike, opts: { max?: number } = {}): void {
	const max = opts.max ?? 3;
	let used = 0;
	pi.on("tool_result", (event: any) => {
		if (used >= max || !RAN.has(event?.toolName)) return undefined;
		const content: any[] = event.content ?? [];
		const text = content.filter((c) => c.type === "text").map((c) => c.text ?? "").join("");
		if (!MISMATCH.test(text)) return undefined;
		used += 1;
		return { content: [{ type: "text", text: text + NOTE }, ...content.filter((c) => c.type !== "text")] };
	});
}

export default (pi: PiLike) => install(pi);
