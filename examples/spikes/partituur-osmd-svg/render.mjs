/**
 * Spike-wrapper: delegeert naar scripts/osmd-svg/render.mjs.
 * Default input = sibling browser-spike MusicXML.
 */

import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { spawn } from "node:child_process";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const product = path.resolve(
  __dirname,
  "..",
  "..",
  "..",
  "scripts",
  "osmd-svg",
  "render.mjs"
);

const args = process.argv.slice(2);
const input =
  args[0] ??
  path.join(__dirname, "..", "partituur-browser", "score.musicxml");
const output = args[1] ?? path.join(__dirname, "out", "score.svg");

const child = spawn(
  process.execPath,
  [product, path.resolve(input), path.resolve(output)],
  { stdio: "inherit", cwd: path.dirname(product) }
);
child.on("exit", (code) => process.exit(code ?? 1));
