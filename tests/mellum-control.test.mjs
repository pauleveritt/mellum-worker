import { test } from "node:test";
import assert from "node:assert/strict";

import { parseState } from "../extensions/mellum-control.ts";

test("parseState: pause", () => assert.equal(parseState('{"state":"pause"}'), "pause"));
test("parseState: play", () => assert.equal(parseState('{"state":"play"}'), "play"));
test("parseState: unparseable defaults to play", () => assert.equal(parseState("not json"), "play"));
