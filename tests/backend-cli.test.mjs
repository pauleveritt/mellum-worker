import { spawnSync } from "node:child_process";
import { resolve } from "node:path";
import test from "node:test";
import assert from "node:assert/strict";

const ROOT = resolve(import.meta.dirname, "..");
const run = (...args) => {
  const r = spawnSync("uv", ["run", "scripts/backend.py", ...args], {
    cwd: ROOT, encoding: "utf8",
  });
  assert.equal(r.status, 0, r.stderr);
  return r.stdout.trim();
};

const ARGV = [
  "llama-server", "-hf", "JetBrains/Mellum2.1-12B-A2.5B-Thinking-GGUF:Q4_K_M",
  "-a", "Mellum2.1-12B-A2.5B-Thinking", "--host", "127.0.0.1", "--port", "8002",
  "-c", "50000", "-np", "1", "--jinja", "-fa", "auto",
  "-b", "512", "-ub", "512", "-ctk", "q8_0", "-ctv", "q8_0",
];

// serve --dry-run inherits the environment, so pin MELLUM_NGL off by default;
// a test that wants full-GPU offload sets it.
const serveArgv = (env = {}) => {
  const r = spawnSync("uv", ["run", "scripts/backend.py", "serve", "--dry-run"], {
    cwd: ROOT, encoding: "utf8", env: { ...process.env, MELLUM_NGL: "", ...env },
  });
  assert.equal(r.status, 0, r.stderr);
  return r.stdout.trim();
};

test("serve builds llama-server's argv from the settings", () => {
  assert.equal(serveArgv(), ARGV.join(" "));
});

test("MELLUM_NGL forces full GPU offload by appending -ngl", () => {
  assert.equal(serveArgv({ MELLUM_NGL: "999" }), [...ARGV, "-ngl", "999"].join(" "));
});

const progress = (log) => {
  const r = spawnSync("uv", ["run", "python", "-c",
    "import sys; sys.path.insert(0, 'scripts'); import backend; " +
    "print(backend.progress_line(sys.stdin.read()))"], {
    cwd: ROOT, encoding: "utf8", input: log,
  });
  assert.equal(r.status, 0, r.stderr);
  return r.stdout.trim();
};

test("start's progress line reads the download out of the log", () => {
  const log = "common_download_file: downloading\n" +
    " 45 7697M   45 3467M    0     0  15.9M      0  0:08:01  0:03:37  0:04:24 16.3M\r" +
    " 47 7697M   47 3634M    0     0  16.0M      0  0:08:00  0:03:46  0:04:14 17.0M\r";
  assert.equal(progress(log), "downloading the model: 47% of 7697M, 0:04:14 left");
});

test("start's progress line otherwise shows the log's last line", () => {
  assert.equal(progress("a\nload_tensors: loading model tensors\n\n"),
    "load_tensors: loading model tensors");
  assert.equal(progress(""), "None");
});

// Calls one backend.py function with JSON arguments and returns its JSON result.
const call = (fn, ...args) => {
  const r = spawnSync("uv", ["run", "python", "-c",
    "import json, sys; sys.path.insert(0, 'scripts'); import backend; " +
    `print(json.dumps(backend.${fn}(*json.loads(sys.stdin.read()))))`], {
    cwd: ROOT, encoding: "utf8", input: JSON.stringify(args),
  });
  assert.equal(r.status, 0, r.stderr);
  return JSON.parse(r.stdout);
};

test("a progress line that has not changed says how long the log has been quiet", () => {
  assert.equal(call("progress_report", 10, "loading", null, 0), "[10s] loading");
  assert.equal(call("progress_report", 20, "downloading 5%", "loading", 10), "[20s] downloading 5%");
  assert.equal(call("progress_report", 30, "loading", "loading", 10),
    "[30s] no new output for 20s; last: loading");
  assert.equal(call("progress_report", 10, null, null, 0), "[10s] waiting for output");
});

test("the build number comes from llama-server --version", () => {
  assert.equal(call("parse_build", "load_backend: x\nversion: 7360 (53ecd4fdb)\nbuilt with Clang"), 7360);
  assert.equal(call("parse_build", "version: 0.7.0-dev (build 11829, commit 184f65360)\n"), 11829);
  assert.equal(call("parse_build", "v25.2.1\n"), null);
});

test("an old llama-server is named with the build that added mellum", () => {
  assert.equal(call("version_problem", 11669), null);
  assert.equal(call("version_problem", 9482), null);
  const msg = call("version_problem", 7360);
  assert.match(msg, /build 7360/);
  assert.match(msg, /9482/);
  assert.match(msg, /docs\/backends\/llamacpp\.md/);
});

test("start uses the first new-enough llama-server on PATH and names any it skips", () => {
  const [path, build, notes] = call("choose_server", [["/old/llama-server", 7360], ["/new/llama-server", 11829]]);
  assert.equal(path, "/new/llama-server");
  assert.equal(build, 11829);
  assert.match(notes.join("\n"), /skipping \/old\/llama-server \(build 7360/);
  assert.match(notes.join("\n"), /remove \/old from PATH/);
  assert.deepEqual(call("choose_server", [["/new/llama-server", 11829]]), ["/new/llama-server", 11829, []]);
});

test("with only old llama-servers on PATH, none is chosen and each is listed", () => {
  const [path, , notes] = call("choose_server", [["/a/llama-server", 7360], ["/b/llama-server", 9000]]);
  assert.equal(path, null);
  const text = notes.join("\n");
  assert.match(text, /9482/);
  assert.match(text, /\/a\/llama-server \(build 7360\)/);
  assert.match(text, /\/b\/llama-server \(build 9000\)/);
});

test("a llama-server whose build cannot be read is tried, with a warning", () => {
  const [path, build, notes] = call("choose_server", [["/a/llama-server", null]]);
  assert.equal(path, "/a/llama-server");
  assert.equal(build, null);
  assert.match(notes[0], /could not read a build/);
});

test("a log that names an unknown architecture says to upgrade llama.cpp", () => {
  const hints = call("diagnose", "llama_model_load: error loading model: error loading model architecture: unknown model architecture: 'mellum'\n");
  assert.equal(hints.length, 1);
  assert.match(hints[0], /too old/);
});

test("a log with a failed load, or a file another server holds, points at verify and stop", () => {
  const log = "write_file: unable to rename file: a.tmp to a\n" +
    "common_init_from_params: failed to load model 'C:\\cache\\m.gguf', try reducing --n-gpu-layers\n";
  const hints = call("diagnose", log).join("\n");
  assert.match(hints, /another llama-server/);
  assert.match(hints, /uv run scripts\/backend\.py stop/);
  assert.match(hints, /uv run scripts\/backend\.py verify/);
});

test("the cached model's path is read from the newest log line that names it", () => {
  const log = "trying to download model from https://x to /old/m.gguf.downloadInProgress (etag)\n" +
    "common_download_file_single_online: using cached file: C:\\Users\\a\\AppData\\Local\\llama.cpp\\m.gguf\n";
  assert.equal(call("logged_model_file", log), "C:\\Users\\a\\AppData\\Local\\llama.cpp\\m.gguf");
  assert.equal(call("logged_model_file", "failed to load model '/c/m.gguf', try"), "/c/m.gguf");
  assert.equal(call("logged_model_file", "to /c/m.gguf.downloadInProgress (x)"), "/c/m.gguf");
  assert.equal(call("logged_model_file", "nothing"), null);
});

test("the model file is looked for in llama.cpp's cache on each OS, and in the Hugging Face cache", () => {
  const model = "JetBrains/M-GGUF:Q4_K_M";
  const file = "JetBrains_M-GGUF_M-Q4_K_M.gguf";
  const names = (os, env) => call("model_candidates", model, "M-Q4_K_M.gguf", os, env);
  assert.deepEqual(names("nt", { LOCALAPPDATA: "C:\\L", USERPROFILE: "C:\\U" })[0], `C:\\L\\llama.cpp\\${file}`);
  assert.deepEqual(names("darwin", { HOME: "/Users/a" })[0], `/Users/a/Library/Caches/llama.cpp/${file}`);
  assert.deepEqual(names("linux", { HOME: "/home/a" })[0], `/home/a/.cache/llama.cpp/${file}`);
  assert.deepEqual(names("linux", { HOME: "/home/a", LLAMA_CACHE: "/big" })[0], `/big/${file}`);
  assert.equal(names("linux", { HOME: "/home/a" })[1],
    "/home/a/.cache/huggingface/hub/models--JetBrains--M-GGUF/snapshots/*/M-Q4_K_M.gguf");
});

test("the quant's file, size and sha256 are picked from the Hugging Face tree", () => {
  const tree = [
    { path: "M-Q4_K_M.gguf", size: 8, lfs: { oid: "abc", size: 8 } },
    { path: "mtp-M-BF16.gguf", size: 2, lfs: { oid: "def", size: 2 } },
  ];
  assert.deepEqual(call("pick_file", tree, "Q4_K_M"), ["M-Q4_K_M.gguf", 8, "abc"]);
  assert.equal(call("pick_file", tree, "Q8_0"), null);
});

test("chat sends the settings as request parameters", () => {
  assert.deepEqual(JSON.parse(run("chat", "hi", "--dry-run")), {
    messages: [{ role: "user", content: "hi" }],
    max_tokens: 16384, temperature: 1.0, top_p: 0.95, top_k: 20,
  });
});
