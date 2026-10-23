/**
 * Spike: MusicXML → SVG via OpenSheetMusicDisplay in headless Chromium.
 *
 * Geen MuseScore, geen Python-CLI. Input default = sibling browser-spike.
 *
 * Usage:
 *   npm install
 *   npm run render
 *   node render.mjs path\to\file.musicxml [out.svg]
 */

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import puppeteer from "puppeteer";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OSMD_CDN =
  "https://cdn.jsdelivr.net/npm/opensheetmusicdisplay@1.8.3/build/opensheetmusicdisplay.min.js";

function usage() {
  console.error(
    "Gebruik: node render.mjs [input.musicxml] [output.svg]\n" +
      "Default input: ..\\partituur-browser\\score.musicxml\n" +
      "Default output: out\\score.svg"
  );
}

async function main() {
  const args = process.argv.slice(2);
  if (args.includes("-h") || args.includes("--help")) {
    usage();
    process.exit(0);
  }

  const inputPath = path.resolve(
    args[0] ?? path.join(__dirname, "..", "partituur-browser", "score.musicxml")
  );
  const outputPath = path.resolve(
    args[1] ?? path.join(__dirname, "out", "score.svg")
  );

  if (!fs.existsSync(inputPath)) {
    console.error(`MusicXML niet gevonden: ${inputPath}`);
    console.error(
      "Genereer eerst (in VSA-tooling-root):\n" +
        "  mvsa score-ir examples\\mvsa\\1a-vredeslitanie.mvsa " +
        "-o examples\\spikes\\partituur-browser\\score.score-ir.json " +
        "--musicxml examples\\spikes\\partituur-browser\\score.musicxml"
    );
    process.exit(1);
  }

  const musicxml = fs.readFileSync(inputPath, "utf8");
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });

  const browser = await puppeteer.launch({
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
  });

  try {
    const page = await browser.newPage();
    page.setDefaultTimeout(120_000);

    // Lege pagina + OSMD via CDN (zelfde versie als partituur-browser-spike).
    await page.setContent(
      `<!DOCTYPE html>
<html lang="nl">
<head><meta charset="utf-8" /><title>osmd-svg-spike</title></head>
<body>
  <div id="osmd" style="width: 900px;"></div>
  <script src="${OSMD_CDN}"></script>
</body>
</html>`,
      { waitUntil: "networkidle0" }
    );

    await page.waitForFunction(
      () => typeof window.opensheetmusicdisplay !== "undefined"
    );

    const pageCount = await page.evaluate(async (xml) => {
      const osmd = new window.opensheetmusicdisplay.OpenSheetMusicDisplay(
        "osmd",
        {
          autoResize: false,
          backend: "svg",
          drawTitle: false,
          drawSubtitle: false,
          drawComposer: false,
          drawLyricist: false,
          drawingParameters: "compacttight",
        }
      );
      // Endless page: één SVG i.p.v. A4-pagina’s.
      osmd.setOptions({
        pageFormat: "Endless",
      });
      await osmd.load(xml);
      osmd.render();

      const svgs = document.querySelectorAll("#osmd svg");
      return svgs.length;
    }, musicxml);

    if (!pageCount) {
      throw new Error("OSMD renderde geen SVG (0 elementen in #osmd)");
    }

    // Eén of meer pagina-SVG’s; bij Endless meestal één.
    const markupParts = await page.evaluate(() => {
      const nodes = document.querySelectorAll("#osmd svg");
      return Array.from(nodes).map((svg, i) => {
        svg.setAttribute("xmlns", "http://www.w3.org/2000/svg");
        if (!svg.getAttribute("xmlns:xlink")) {
          svg.setAttribute("xmlns:xlink", "http://www.w3.org/1999/xlink");
        }
        // Stabiele id voor multi-page.
        if (!svg.id) svg.id = `osmdSvgPage${i + 1}`;
        return svg.outerHTML;
      });
    });

    let outText;
    if (markupParts.length === 1) {
      outText = `<?xml version="1.0" encoding="UTF-8"?>\n${markupParts[0]}\n`;
    } else {
      // Meerdere pagina’s → wrapper-SVG (spike; product mag later één pagina eisen).
      const bodies = markupParts
        .map(
          (m, i) =>
            `<g id="page${i + 1}" transform="translate(0, ${i * 1200})">${m}</g>`
        )
        .join("\n");
      outText =
        `<?xml version="1.0" encoding="UTF-8"?>\n` +
        `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">\n` +
        `${bodies}\n</svg>\n`;
    }

    fs.writeFileSync(outputPath, outText, "utf8");
    const rel = path.relative(process.cwd(), outputPath);
    console.log(
      `Geschreven: ${rel} (${markupParts.length} OSMD-pagina` +
        `${markupParts.length === 1 ? "" : "'s"}; bron ${path.basename(inputPath)})`
    );
    console.log(`file:///${outputPath.replace(/\\/g, "/")}`);
  } finally {
    await browser.close();
  }
}

main().catch((err) => {
  console.error(err && err.stack ? err.stack : err);
  process.exit(1);
});
