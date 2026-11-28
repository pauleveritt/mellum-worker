/** Remedy unit: refuse the live-server debugging spiral — any server start (foreground OR
 * background) and any loopback HTTP probe — and point the worker at the in-process test client.
 * Stricter than foreground-server, which allows the background form the spiral runs on. */
import { liveServerGuard } from "../../extensions/mellum-guards.ts";
import { installGuard, type PiLike, type UnitMeta } from "../install.ts";

export const meta: UnitMeta = {
	pathology:
		"Debugs an HTTP behaviour by starting a live server and curling localhost, forking a server that disagrees with the in-process test client and thrashing to the deadline before settle",
	does: "Blocks any server start (foreground or background) and any loopback HTTP probe, and points at the in-process test client (TestClient, follow_redirects=False)",
	lesson: "",
	evidence:
		"screen: 2 of 3 gated one-pass medium reps never reached the exit-gate, they stalled in this spiral before settle (docs/superpowers/research/2026-11-08-one-pass-vs-architect-loop.md); unmeasured as a remedy",
};

export function install(pi: PiLike): void {
	installGuard(pi, liveServerGuard);
}

export default install;
