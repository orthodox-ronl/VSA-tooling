/**
 * MusicXML → SVG via OpenSheetMusicDisplay in headless Chromium.
 *
 * Productpad: ``mvsa svg --engine osmd`` (Python start dit script).
 * Spike: ``examples/spikes/partituur-osmd-svg/`` wijst hierheen.
 *
 * S8 (contract A1): na OSMD-render draait ``s8-a1-adapter.js`` zodat
 * spacer-koppen (``notehead none``) verdwijnen; lyrics blijven.
 *
 * Usage:
 *   npm install
 *   node render.mjs INPUT.musicxml OUTPUT.svg
 */

import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath, pathToFileURL } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OSMD_CDN =
  "https://cdn.jsdelivr.net/npm/opensheetmusicdisplay@1.9.3/build/opensheetmusicdisplay.min.js";
/** Zelfde lyric-font als MuseScore Style / bibliotheek-scherm (Source Sans 3). */
const FONT_FAMILY = "Source Sans 3";
const FONTS_DIR = path.join(__dirname, "fonts");
const ADAPTER_PATH = path.join(__dirname, "s8-a1-adapter.js");

/**
 * coribCompact — graveerprofiel voor het CoriB-scherm (OSMD).
 *
 * Startpunt is ``drawingParameters: "compacttight"``. Daarna deze
 * afstanden. OSMD-eenheid = 1 balkspatie (ongeveer 10 px).
 *
 * Doel: dichtere leesbaarheid dan de kale compacttight-stand, in de
 * buurt van de MuseScore-referentie (balkafstand). Geen pixel-pariteit
 * (corib-mvp). Contract S8/S13 blijft in from-ir + A1-adapter; dit
 * profiel verplaatst geen noten of melisma.
 *
 * MeasureWidthFactor blijft 1. Lager trekken pakt meer maten op een
 * regel en laat lettergrepen van een S8-recite overlappen (gemeten op
 * derde-antifoon-zondag-hemelum). De bladbreedte is de container;
 * een stuk dat korter is dan die breedte wordt na het tekenen
 * bijgesneden op de inkt (geen lege rechterpagina).
 */
const CORIB_COMPACT = {
  name: "coribCompact",
  sheetWidthPx: 900,
  contentPadPx: 10,
  // (a) verticaal — skyline-marge hoort erbij, anders wint die van StaffDistance
  StaffDistance: 4.0,
  BetweenStaffDistance: 3.0,
  MinimumDistanceBetweenSystems: 3.0,
  MinSkyBottomDistBetweenStaves: 0.5,
  LyricsYOffsetToStaffHeight: -1.05,
  LyricsYMarginToBottomLine: 0.1,
  // (b) horizontaal
  MeasureWidthFactor: 1.0,
  // (c) lettergreep / streepje
  BetweenSyllableMinimumDistance: 0.4,
  BetweenSyllableMaximumDistance: 8,
  HorizontalBetweenLyricsDistance: 0.15,
  MinimumDistanceBetweenDashes: 8,
};

function coribCompactRuleEntries() {
  const skip = new Set([
    "name",
    "sheetWidthPx",
    "contentPadPx",
    "MeasureWidthFactor",
  ]);
  return Object.entries(CORIB_COMPACT).filter(([key]) => !skip.has(key));
}

/** Lokale WOFF2 → @font-face (geen Google Fonts-afhankelijkheid in de VM). */
function buildSourceSansFaceCss() {
  const faces = [
    ["source-sans-3-400.woff2", "400", "normal"],
    ["source-sans-3-400-italic.woff2", "400", "italic"],
    ["source-sans-3-600.woff2", "600", "normal"],
  ];
  const parts = [];
  for (const [file, weight, style] of faces) {
    const fp = path.join(FONTS_DIR, file);
    if (!fs.existsSync(fp)) {
      throw new Error(
        `Font ontbreekt: ${fp}. Zie scripts/osmd-svg/fonts/README.md`
      );
    }
    const b64 = fs.readFileSync(fp).toString("base64");
    parts.push(
      `@font-face{font-family:'${FONT_FAMILY}';font-style:${style};` +
        `font-weight:${weight};font-display:swap;` +
        `src:url(data:font/woff2;base64,${b64}) format('woff2');}`
    );
  }
  return parts.join("");
}

function injectFontFaceIntoSvg(svgMarkup, faceCss) {
  // OSMD schrijft font-family="Source Sans 3" zonder quotes; SVG parseert
  // dat als drie families (Source, Sans, 3) → fallback Times. Quote verplicht.
  let out = svgMarkup.replaceAll(
    `font-family="${FONT_FAMILY}"`,
    `font-family="'${FONT_FAMILY}'"`
  );
  const style = `<defs><style type="text/css"><![CDATA[${faceCss}]]></style></defs>`;
  const m = out.match(/<svg\b[^>]*>/);
  if (!m) {
    return out;
  }
  const insertAt = m.index + m[0].length;
  return out.slice(0, insertAt) + style + out.slice(insertAt);
}

/**
 * Witte pagina-achtergrond (zelfde idee als MuseScore ``vsa-page-bg``).
 * Zonder rect is de SVG transparant → grijze/donkere viewers tonen “zwart”.
 */
function injectWhitePageBackground(svgMarkup) {
  if (/class="vsa-page-bg"/.test(svgMarkup)) {
    return svgMarkup;
  }
  const m = svgMarkup.match(/<svg\b([^>]*)>/);
  if (!m) {
    return svgMarkup;
  }
  const attrs = m[1];
  let x = 0;
  let y = 0;
  let w = null;
  let h = null;
  const vb = attrs.match(/\bviewBox="([^"]+)"/);
  if (vb) {
    const parts = vb[1].trim().split(/[\s,]+/).map(Number);
    if (parts.length === 4 && parts.every((n) => Number.isFinite(n))) {
      [x, y, w, h] = parts;
    }
  }
  if (w == null || h == null) {
    const wm = attrs.match(/\bwidth="([0-9.]+)/);
    const hm = attrs.match(/\bheight="([0-9.]+)/);
    if (wm && hm) {
      w = Number(wm[1]);
      h = Number(hm[1]);
    }
  }
  if (w == null || h == null || !(w > 0) || !(h > 0)) {
    return svgMarkup;
  }
  const rect =
    `<rect class="vsa-page-bg" x="${x}" y="${y}" width="${w}" height="${h}" fill="#ffffff"/>`;
  const insertAt = m.index + m[0].length;
  // Achtergrond vóór defs/muziek, zodat noten eroverheen liggen.
  return svgMarkup.slice(0, insertAt) + rect + svgMarkup.slice(insertAt);
}

async function loadPuppeteer() {
  const require = createRequire(import.meta.url);
  const candidates = [
    path.join(__dirname, "node_modules", "puppeteer"),
    path.join(
      __dirname,
      "..",
      "..",
      "examples",
      "spikes",
      "partituur-osmd-svg",
      "node_modules",
      "puppeteer"
    ),
  ];
  for (const c of candidates) {
    try {
      if (fs.existsSync(c)) {
        return require(c);
      }
    } catch {
      /* try next */
    }
  }
  try {
    return require("puppeteer");
  } catch {
    throw new Error(
      "puppeteer niet gevonden. Draai: cd scripts/osmd-svg && npm install " +
        "&& npx puppeteer browsers install chrome"
    );
  }
}

function usage() {
  console.error("Gebruik: node render.mjs INPUT.musicxml OUTPUT.svg");
}

async function main() {
  const args = process.argv.slice(2);
  if (args.includes("-h") || args.includes("--help") || args.length < 2) {
    usage();
    process.exit(args.includes("-h") || args.includes("--help") ? 0 : 1);
  }

  const inputPath = path.resolve(args[0]);
  const outputPath = path.resolve(args[1]);

  if (!fs.existsSync(inputPath)) {
    console.error(`MusicXML niet gevonden: ${inputPath}`);
    process.exit(1);
  }
  if (!fs.existsSync(ADAPTER_PATH)) {
    console.error(`S8 A1-adapter niet gevonden: ${ADAPTER_PATH}`);
    process.exit(1);
  }

  const musicxml = fs.readFileSync(inputPath, "utf8");
  const adapterJs = fs.readFileSync(ADAPTER_PATH, "utf8");
  const fontFaceCss = buildSourceSansFaceCss();
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });

  const puppeteer = await loadPuppeteer();
  const browser = await puppeteer.launch({
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
  });

  try {
    const page = await browser.newPage();
    page.setDefaultTimeout(120_000);

    await page.setContent(
      `<!DOCTYPE html>
<html lang="nl">
<head>
  <meta charset="utf-8" />
  <title>osmd-svg</title>
  <style>${fontFaceCss}</style>
</head>
<body>
  <div id="osmd" style="width: ${CORIB_COMPACT.sheetWidthPx}px;"></div>
  <script src="${OSMD_CDN}"></script>
</body>
</html>`,
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

    const pageCount = await page.evaluate(
      async (xml, fontFamily, ruleEntries, measureWidthFactor, contentPadPx) => {
        const mount = document.getElementById("osmd");
        const osmd = new window.opensheetmusicdisplay.OpenSheetMusicDisplay(
          mount,
          {
            autoResize: false,
            backend: "svg",
            drawTitle: false,
            drawSubtitle: false,
            drawComposer: false,
            drawLyricist: false,
            drawPartNames: false,
            drawTimeSignatures: false,
            defaultFontFamily: fontFamily,
            drawingParameters: "compacttight",
          }
        );
        // Regels vóór load: OSMD meet lyrics al bij het inlezen.
        const rules = osmd.EngravingRules;
        for (const [key, value] of ruleEntries) {
          rules[key] = value;
        }
        osmd.setOptions({ pageFormat: "Endless" });
        await osmd.load(xml);
        if (osmd.Sheet && measureWidthFactor != null) {
          osmd.Sheet.MeasureWidthFactor = measureWidthFactor;
        }
        osmd.render();
        if (typeof window.__vsaOsmdS8FinalizePrint === "function") {
          window.__vsaOsmdS8FinalizePrint(mount, xml);
        }
        // Blad bijsnijden op de inkt. Korte stukken vullen de
        // container niet; zonder dit blijft een lege rechterpagina.
        const svg = mount.querySelector("svg");
        if (svg && typeof svg.getBBox === "function") {
          const bb = svg.getBBox();
          const pad = contentPadPx;
          if (bb && bb.width > 32 && bb.height > 32) {
            const x = Math.min(0, bb.x - 2);
            const y = Math.min(0, bb.y - 2);
            const w = Math.ceil(bb.x + bb.width + pad - x);
            const h = Math.ceil(bb.y + bb.height + pad - y);
            svg.setAttribute("viewBox", `${x} ${y} ${w} ${h}`);
            svg.setAttribute("width", String(w));
            svg.setAttribute("height", String(h));
          }
        }
        return document.querySelectorAll("#osmd svg").length;
      },
      musicxml,
      FONT_FAMILY,
      coribCompactRuleEntries(),
      CORIB_COMPACT.MeasureWidthFactor,
      CORIB_COMPACT.contentPadPx
    );

    if (!pageCount) {
      throw new Error("OSMD renderde geen SVG (0 elementen in #osmd)");
    }

    const markupParts = await page.evaluate(() => {
      const nodes = document.querySelectorAll("#osmd svg");
      return Array.from(nodes).map((svg, i) => {
        svg.setAttribute("xmlns", "http://www.w3.org/2000/svg");
        if (!svg.getAttribute("xmlns:xlink")) {
          svg.setAttribute("xmlns:xlink", "http://www.w3.org/1999/xlink");
        }
        if (!svg.id) svg.id = `osmdSvgPage${i + 1}`;
        return svg.outerHTML;
      });
    });

    let outText;
    if (markupParts.length === 1) {
      outText = `<?xml version="1.0" encoding="UTF-8"?>\n${markupParts[0]}\n`;
    } else {
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
    outText = injectFontFaceIntoSvg(outText, fontFaceCss);
    outText = injectWhitePageBackground(outText);

    fs.writeFileSync(outputPath, outText, "utf8");
    // Machine-readable line for Python callers.
    console.log(`OSMD_SVG_OK\t${pathToFileURL(outputPath).href}`);
  } finally {
    await browser.close();
  }
}

main().catch((err) => {
  console.error(err && err.stack ? err.stack : err);
  process.exit(1);
});
