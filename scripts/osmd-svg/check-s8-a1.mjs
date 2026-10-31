/**
 * CI/local: S8 A1-adapter op from-ir MusicXML (productketen).
 *
 * Usage:
 *   node check-s8-a1.mjs [path/to/from-ir.musicxml]
 *
 * Default: examples/bug-cases/corib/alleluia-toon-8 via generated from-ir,
 * of regen via score-ir als nodig — pass an existing from-ir path.
 */
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..", "..");
const OSMD_CDN =
  "https://cdn.jsdelivr.net/npm/opensheetmusicdisplay@1.9.3/build/opensheetmusicdisplay.min.js";
const FONT_FAMILY = "Source Sans 3";
const FONT_CSS =
  "https://fonts.googleapis.com/css2?family=Source+Sans+3:ital,wght@0,400;0,600;1,400&display=swap";
const ADAPTER_PATH = path.join(__dirname, "s8-a1-adapter.js");

async function loadPuppeteer() {
  const require = createRequire(import.meta.url);
  return require(path.join(__dirname, "node_modules", "puppeteer"));
}

async function main() {
  const xmlPath = path.resolve(
    process.argv[2] ||
      path.join(
        ROOT,
        "generated/corib-s8-toets/from-ir/alleluia-toon-8.from-ir.musicxml"
      )
  );
  if (!fs.existsSync(xmlPath)) {
    console.error("MusicXML niet gevonden:", xmlPath);
    process.exit(1);
  }
  const xmlText = fs.readFileSync(xmlPath, "utf8");
  const adapterJs = fs.readFileSync(ADAPTER_PATH, "utf8");
  if (!xmlText.includes("<notehead>none</notehead>")) {
    console.error("Geen A1-marker (notehead none) in", xmlPath);
    process.exit(1);
  }

  const puppeteer = await loadPuppeteer();
  const browser = await puppeteer.launch({
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
  });
  try {
    const page = await browser.newPage();
    await page.setContent(
      `<!DOCTYPE html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="${FONT_CSS}">
<script src="${OSMD_CDN}"></script></head>
<body><div id="osmd" style="width:960px"></div></body></html>`,
      { waitUntil: "networkidle0" }
    );
    await page.waitForFunction(
      () => typeof window.opensheetmusicdisplay !== "undefined"
    );
    await page.evaluate(async (fontFamily) => {
      if (document.fonts && document.fonts.load) {
        await document.fonts.load('13px "' + fontFamily + '"');
        await document.fonts.ready;
      }
    }, FONT_FAMILY);
    await page.addScriptTag({ content: adapterJs });
    const result = await page.evaluate(
      async (xml, fontFamily) => {
        const mount = document.getElementById("osmd");
        const osmd = new opensheetmusicdisplay.OpenSheetMusicDisplay(mount, {
          autoResize: false,
          backend: "svg",
          drawTitle: false,
          drawPartNames: false,
          drawTimeSignatures: false,
          defaultFontFamily: fontFamily,
          drawingParameters: "compacttight",
        });
        osmd.setOptions({ pageFormat: "Endless" });
        await osmd.load(xml);
        osmd.render();
        window.__vsaOsmdS8FinalizePrint(mount, xml);
        return window.__vsaOsmdS8Diagnose(mount, xml);
      },
      xmlText,
      FONT_FAMILY
    );

    if (!result.ok) {
      console.error("S8 A1 adapter check FAILED");
      console.error(JSON.stringify(result, null, 2));
      process.exit(1);
    }
    console.log("S8 A1 adapter check OK");
    console.log(
      "boven keep=" +
        result.staven.boven.keepVisibleHeads +
        " spacerVisible=" +
        result.staven.boven.spacerVisibleHeads +
        " spacerMarked=" +
        result.staven.boven.spacerMarked
    );
  } finally {
    await browser.close();
  }
}

main().catch((e) => {
  console.error(e && e.stack ? e.stack : e);
  process.exit(1);
});
