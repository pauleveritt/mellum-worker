// The two run lines of one lesson, as the lesson check runs them: the page's n, into a runs
// folder per arm, on a profile. Prints one shell-quoted command per line, before then after.
// Used by scripts/lesson-check.sh; the parser is the /lesson tutor's, so the page is the source.
//
//   node scripts/lesson-lines.mjs <lesson number> <runs dir> [profile dir]
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { lessonIndex, parseLesson, runArgv } from "../extensions/mellum-lessons.ts";

const [number, runs, profile] = process.argv.slice(2);
const root = new URL("..", import.meta.url).pathname;
const entry = lessonIndex(root).find((e) => e.number === number);
if (!entry) throw new Error(`no lesson ${number}`);
const lesson = parseLesson(readFileSync(entry.file, "utf8"));
if (!lesson.before || !lesson.after) throw new Error(`${number} has no before and after line`);
const quote = (a) => (/^[\w@%+=:,./-]+$/.test(a) ? a : `'${a.replace(/'/g, "'\\''")}'`);
for (const [arm, line] of [["before", lesson.before], ["after", lesson.after]])
	console.log(runArgv(line, join(runs, arm), true, profile).map(quote).join(" "));
