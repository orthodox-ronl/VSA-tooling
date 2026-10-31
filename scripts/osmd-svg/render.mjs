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
  // Iets breder dan 900: minder maten per regel → geen lyric-overlap
  // bij S8-recite (mscz-leesbaarheid §2 / P3a; gemeten derde-antifoon).
  sheetWidthPx: 1000,
  contentPadPx: 10,
  // (a) verticaal — lyrics tussen de balken (geen negatieve Y: dat plakt
  //    ze tegen de bovenbalk).
  StaffDistance: 4.5,
  BetweenStaffDistance: 3.5,
  MinimumDistanceBetweenSystems: 3.0,
  MinSkyBottomDistBetweenStaves: 0.6,
  LyricsYOffsetToStaffHeight: 2.0,
  LyricsYMarginToBottomLine: 0.35,
  // (b) horizontaal — MeasureWidthFactor 1 (lager: S8-lettergrepen
  //    overlappen). FixedMeasureWidth niet: die trekt élke maat tot de
  //    breedste → blad veel te hoog voor CoriB-scherm.
  //    compacttight zet VoiceSpacing op 0.65/2.0; dat knelt lettergrepen
  //    (maat 2 «neer|gij»). Terug naar OSMD-default 0.85/3.0.
  MeasureWidthFactor: 1.0,
  VoiceSpacingMultiplierVexflow: 0.85,
  VoiceSpacingAddendVexflow: 3.0,
  // (c) lettergreep / streepje — OSMD-defaults (lager elongation/padding
  //    gaf overlap in maat 2 van derde-antifoon).
  BetweenSyllableMinimumDistance: 0.5,
  BetweenSyllableMaximumDistance: 10,
  HorizontalBetweenLyricsDistance: 0.2,
  MinimumDistanceBetweenDashes: 10,
  MaximumLyricsElongationFactor: 2.5,
  LyricsUseXPaddingForLongLyrics: true,
  LyricsXPaddingFactorForLongLyrics: 1.0,
  // (d) S10 — maatnummers alleen aan systeembegin (canonical-checklists).
  RenderMeasureNumbersOnlyAtSystemStart: true,
  // (e) stokken iets korter dan OSMD-default (3.0 / 2.5–4.5)
  IdealStemLength: 2.6,
  StemMinLength: 2.2,
  StemMaxLength: 3.6,
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
            // S10: alleen systeembegin (EngravingRules hieronder bevestigt).
            drawMeasureNumbers: true,
            drawMeasureNumbersOnlyAtSystemStart: true,
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
        // OSMD hangt lyrics aan de skyline van de bovenbalk; bij een
        // groter balkgat blijven ze te hoog. Verschuif lyrics+streepjes
        // per systeem naar het midden van treble-onder ↔ bas-boven.
        (function centerLyricsBetweenStaves() {
          const staffs = Array.from(mount.querySelectorAll(".staffline"));
          if (staffs.length < 2) return;
          // Alleen de vijf notenbalklijnen (niet de hele stave-bbox met
          // stokken/lyrics) — anders valt het «gat» al over de lyrics heen.
          const bands = staffs
            .map((el) => {
              const ys = [];
              for (const p of el.querySelectorAll("path")) {
                const d = p.getAttribute("d") || "";
                const m = d.match(
                  /^M([-\d.]+) ([-\d.]+)L([-\d.]+) ([-\d.]+)$/
                );
                if (!m) continue;
                if (Math.abs(Number(m[2]) - Number(m[4])) > 0.2) continue;
                if (Number(m[3]) - Number(m[1]) < 200) continue;
                ys.push(Number(m[2]));
              }
              if (ys.length < 4) return null;
              return { el, y: Math.min(...ys), bottom: Math.max(...ys) };
            })
            .filter(Boolean)
            .sort((a, b) => a.y - b.y);
          for (let i = 0; i + 1 < bands.length; i += 2) {
            const treble = bands[i];
            const bass = bands[i + 1];
            const gapTop = treble.bottom;
            const gapBot = bass.y;
            if (!(gapBot > gapTop + 20)) continue;
            const nodes = [];
            for (const sel of [
              ".vf-text.lyrics text",
              ".vf-text.dash text",
              ".vf-text.lyrics",
              ".vf-text.dash",
            ]) {
              for (const el of mount.querySelectorAll(sel)) {
                let bb;
                try {
                  bb = el.getBBox();
                } catch {
                  continue;
                }
                if (bb.y > gapTop - 2 && bb.y < gapBot + 2) {
                  nodes.push(el);
                }
              }
            }
            // Uniek op element
            const seen = new Set();
            const uniq = [];
            for (const el of nodes) {
              if (seen.has(el)) continue;
              seen.add(el);
              uniq.push(el);
            }
            if (!uniq.length) continue;
            let minY = Infinity;
            let maxY = -Infinity;
            for (const el of uniq) {
              try {
                const b = el.getBBox();
                minY = Math.min(minY, b.y);
                maxY = Math.max(maxY, b.y + b.height);
              } catch {
                /* skip */
              }
            }
            if (!Number.isFinite(minY) || !Number.isFinite(maxY)) continue;
            // Alleen omlaag schuiven als er onder meer lucht is dan boven
            // (OSMD plakt lyrics aan de bovenbalk). Nooit omhoog.
            const roomAbove = minY - gapTop;
            const roomBelow = gapBot - maxY;
            const dy = (roomBelow - roomAbove) / 2;
            if (!(dy > 3)) continue;
            // Alleen groepen verschuiven (tekst zit erin); voorkom dubbel.
            const groups = new Set();
            for (const el of uniq) {
              const g =
                el.classList && el.classList.contains("vf-text")
                  ? el
                  : el.closest(".vf-text");
              if (g) groups.add(g);
            }
            for (const g of groups) {
              const prev = g.getAttribute("transform") || "";
              g.setAttribute(
                "transform",
                `${prev} translate(0, ${dy.toFixed(2)})`.trim()
              );
            }
          }
        })();
        // S10-veiligheidsnet: mid-systeem-maatnummers weg (OSMD interval
        // kan ondanks OnlyAtSystemStart soms nog een nummer zetten).
        (function stripMidSystemMeasureNumbers() {
          const texts = Array.from(
            mount.querySelectorAll("g.vf-text text")
          ).filter((t) =>
            /^\d{1,3}$/.test(String(t.textContent || "").trim())
          );
          const byY = new Map();
          for (const t of texts) {
            let b;
            try {
              b = t.getBBox();
            } catch {
              continue;
            }
            const yKey = Math.round(b.y / 40) * 40;
            if (!byY.has(yKey)) byY.set(yKey, []);
            byY.get(yKey).push({ t, x: b.x });
          }
          for (const group of byY.values()) {
            group.sort((a, b) => a.x - b.x);
            const left = group[0].x;
            for (const g of group) {
              if (g.x > left + 35) {
                const el = g.t.closest("g.vf-text") || g.t;
                el.remove();
              }
            }
          }
        })();
        // OSMD tekent maatnummer 1 standaard niet (S10: wél aan
        // systeembegin). Zet «1» boven de eerste treble-maat.
        (function injectMeasureNumberOne() {
          const hasOne = Array.from(mount.querySelectorAll("text")).some(
            (t) => String(t.textContent || "").trim() === "1"
          );
          if (hasOne) return;
          const m1 = mount.querySelector('.vf-measure[id="1"]');
          if (!m1) return;
          let bb;
          try {
            bb = m1.getBBox();
          } catch {
            return;
          }
          const sample = Array.from(
            mount.querySelectorAll("g.vf-text text")
          ).find((t) =>
            /^\d{1,3}$/.test(String(t.textContent || "").trim())
          );
          const ns = "http://www.w3.org/2000/svg";
          const g = document.createElementNS(ns, "g");
          g.setAttribute("class", "vf-text");
          g.setAttribute("data-vsa-measure-number", "1");
          const text = document.createElementNS(ns, "text");
          text.textContent = "1";
          text.setAttribute("font-family", fontFamily);
          text.setAttribute("font-size", "15");
          text.setAttribute("font-weight", "bold");
          text.setAttribute("fill", "#000000");
          text.setAttribute("x", String(bb.x + 6.5));
          let y = bb.y - 9;
          if (sample) {
            const sampleY = Number(sample.getAttribute("y"));
            const sampleStaff = sample.closest(".staffline");
            const sampleMeasure =
              (sampleStaff && sampleStaff.querySelector(".vf-measure")) ||
              sample.closest(".vf-measure");
            if (sampleMeasure && Number.isFinite(sampleY)) {
              try {
                const smb = sampleMeasure.getBBox();
                y = bb.y + (sampleY - smb.y);
              } catch {
                /* keep default */
              }
            }
            for (const attr of [
              "font-family",
              "font-size",
              "font-weight",
              "font-style",
              "fill",
            ]) {
              const v = sample.getAttribute(attr);
              if (v) text.setAttribute(attr, v);
            }
          }
          text.setAttribute("y", String(y));
          g.appendChild(text);
          const staff = m1.closest(".staffline") || m1.parentElement;
          if (staff && staff.parentElement) {
            staff.parentElement.insertBefore(g, staff);
          } else {
            m1.parentElement.insertBefore(g, m1);
          }
        })();
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
