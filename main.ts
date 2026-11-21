// Velarca — entry runner.
//
// The poster itself (entry.png, sitting next to this file) is rendered
// ahead of time by poster/build_poster.py. This program's only job is
// the competition hand-off: place a copy of that baked image where the
// runner expects to find it.
//
// The destination is $MAKEFUN_OUTPUT_DIR when that variable is set, and
// /output otherwise. The directory is created when it does not exist
// yet. Only Node's standard library is used, and the copy is a plain
// byte copy, so running this twice yields two byte-identical outputs.

import { chmodSync, copyFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

// Resolve the folder this file lives in, so the baked image is found
// relative to main.ts itself rather than the caller's working directory.
const here = dirname(fileURLToPath(import.meta.url));
const source = join(here, "entry.png");

// Work out where the runner wants the deliverable, then make sure the
// folder is there before copying into it.
const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? "/output";
mkdirSync(outDir, { recursive: true });

const target = join(outDir, "entry.png");
copyFileSync(source, target);

// The grader collects the output as a different user than the one the
// program runs as, so leave the file readable by everyone.
chmodSync(target, 0o644);

console.log(`velarca: copied entry.png to ${target}`);
