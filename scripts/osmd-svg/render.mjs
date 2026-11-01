/**
 * MusicXML → SVG via OpenSheetMusicDisplay in headless Chromium.
 *
 * Productpad: ``mvsa svg --engine osmd`` (Python start dit script).
 * Spike: ``examples/spikes/partituur-osmd-svg/`` wijst hierheen.
 *
 * S8 (contract A1): na OSMD-render draait ``s8-a1-adapter.js`` zodat
 * spacer-koppen (``notehead none``) verdwijnen; lyrics blijven.
 *
 * Cues (S15/S19/C6/C7 / schermpartituur §4.2): ``cue-layout.js`` zet
 * maat-WidthFactor, wrap/``...``, cue-X op eerste noot, centreren,
 * eenregel-cue-baseline (C7). Graveerprofiel: P3c/P3d/L2/S22.
 * Post-layout: S2/S5 melisma-boogankers; L4 extender-dashes.
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
const CUE_LAYOUT_PATH = path.join(__dirname, "cue-layout.js");

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
  // (a) verticaal — P3c: OSMD-default LyricsYOffset=0; eerdere 1.05/1.7
  //    blies het SA↔TB-gat op (alleluia-8 ~148 px). LyricsHeight > 2
  //    voor leesbaar font *vóór* layout (niet post-hoc font-size).
  //    P3d: systeemlucht blijft ruimer.
  StaffDistance: 2.6,
  BetweenStaffDistance: 2.2,
  MinimumDistanceBetweenSystems: 5.0,
  MinSkyBottomDistBetweenStaves: 0.25,
  MinimumStaffLineDistance: 2.8,
  LyricsHeight: 3.4,
  LyricsYOffsetToStaffHeight: 0,
  LyricsYMarginToBottomLine: 0.15,
  // (b) horizontaal — VoiceSpacing + syllable-min zodat S8-recite
  //    niet tot «iaAl» plakt terwijl rechts wit blijft (alleluia-8).
  MeasureWidthFactor: 1.05,
  VoiceSpacingMultiplierVexflow: 1.0,
  VoiceSpacingAddendVexflow: 6.0,
  // (c) lettergreep — P3a; grotere LyricsHeight vraagt meer x-ruimte.
  BetweenSyllableMinimumDistance: 2.0,
  BetweenSyllableMaximumDistance: 12,
  HorizontalBetweenLyricsDistance: 0.85,
  MinimumDistanceBetweenDashes: 8,
  MaximumLyricsElongationFactor: 3.0,
  LyricsUseXPaddingForLongLyrics: true,
  LyricsXPaddingFactorForLongLyrics: 1.35,
  LyricOverlapAllowedIntoNextMeasure: false,
  // (d) S10 — maatnummers alleen aan systeembegin (canonical-checklists).
  RenderMeasureNumbersOnlyAtSystemStart: true,
  // (e) stoklengte — OSMD 1.9.3/VexFlow negeert IdealStemLength in de
  // praktijk (altijd ~35 px). P3c-klaring A↓/T↑↔lyrics gebeurt post-layout
  // (trimStemsClearOfLyricsScreen na balkgat-compressie).
  IdealStemLength: 2.2,
  StemMinLength: 1.8,
  StemMaxLength: 2.8,
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
  if (!fs.existsSync(CUE_LAYOUT_PATH)) {
    console.error(`Cue-layout niet gevonden: ${CUE_LAYOUT_PATH}`);
    process.exit(1);
  }

  const musicxml = fs.readFileSync(inputPath, "utf8");
  const adapterJs = fs.readFileSync(ADAPTER_PATH, "utf8");
  const cueLayoutJs = fs.readFileSync(CUE_LAYOUT_PATH, "utf8");
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
    await page.addScriptTag({ content: cueLayoutJs });
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
        // Cues §4.2 / S15/S19/C6: WidthFactor + wrap + X op eerste noot
        // (rendert zelf; geen kale osmd.render() hierna vóór S8).
        if (typeof window.__vsaOsmdCueLayout === "function") {
          window.__vsaOsmdCueLayout(osmd, mount, xml);
        } else {
          osmd.render();
        }
        if (typeof window.__vsaOsmdS8FinalizePrint === "function") {
          window.__vsaOsmdS8FinalizePrint(mount, xml);
        }
        // S22 / P3e — ná S8 zodat spacer-kolommen data-osmd-anchor-x hebben.
        if (typeof window.__vsaOsmdCenterSyllableSlots === "function") {
          window.__vsaOsmdCenterSyllableSlots(mount);
        }
        // L2 — Source Sans 3; grootte volgt EngravingRules.LyricsHeight
        // (niet post-hoc vergroten: dat veroorzaakte «iaAl»-overlap).
        (function enforceLyricCueFontFamily() {
          for (const t of mount.querySelectorAll(
            ".vf-text.lyrics text, .vf-text.dash text"
          )) {
            t.setAttribute("font-family", "'" + fontFamily + "'");
          }
          for (const t of mount.querySelectorAll("text")) {
            const s = String(t.textContent || "").trim();
            if (!(/^P:/.test(s) || s.startsWith("..."))) continue;
            t.setAttribute("font-family", "'" + fontFamily + "'");
          }
        })();
        // Zelfde font op lyric-px laden vóór gap/compress-metingen
        // (anders fallback-metrics → schijnbaar genoeg wit, later «iaAl»).
        if (document.fonts && document.fonts.load) {
          const sample = mount.querySelector(".vf-text.lyrics text");
          const px = sample?.getAttribute("font-size") || "34px";
          await document.fonts.load(px + ' "' + fontFamily + '"');
          await document.fonts.ready;
        }
        // P3c — balkgat comprimeren. Meet op balk*lijnen* (niet `.staffline`-
        // groep: die omvat stokken én lyrics). Ruimte houden voor S5-bogen
        // + lyrics; alleen de bas-groep omhoog. S5-pull volgt ná compressie.
        (function compressStaffGapScreen() {
          const PAD = 14;
          const svgEl = mount.querySelector("svg");
          const ctm = svgEl && svgEl.getScreenCTM && svgEl.getScreenCTM();
          const sy = ctm && ctm.d ? ctm.d : 1;
          function staffLineBand(el) {
            const tops = [];
            const bots = [];
            for (const p of el.querySelectorAll("path")) {
              const d = p.getAttribute("d") || "";
              const m = d.match(
                /^M([-\d.]+) ([-\d.]+)L([-\d.]+) ([-\d.]+)$/
              );
              if (!m) continue;
              if (Math.abs(Number(m[2]) - Number(m[4])) > 0.2) continue;
              if (Number(m[3]) - Number(m[1]) < 200) continue;
              const r = p.getBoundingClientRect();
              if (!(r.width > 50)) continue;
              tops.push(r.top);
              bots.push(r.bottom);
            }
            if (tops.length < 4) return null;
            return {
              el,
              top: Math.min(...tops),
              bottom: Math.max(...bots),
            };
          }
          function appendTranslateY(el, dySvg) {
            if (!(Math.abs(dySvg) >= 0.2)) return;
            const prev = el.getAttribute("transform") || "";
            el.setAttribute(
              "transform",
              `${prev} translate(0, ${dySvg.toFixed(2)})`.trim()
            );
          }
          const bands = Array.from(mount.querySelectorAll(".staffline"))
            .map(staffLineBand)
            .filter(Boolean)
            .sort((a, b) => a.top - b.top);
          if (bands.length < 2) return;
          for (let i = 0; i + 1 < bands.length; i += 2) {
            const treble = bands[i];
            const bass = bands[i + 1];
            const lyricGs = [];
            for (const g of mount.querySelectorAll(
              ".vf-text.lyrics, .vf-text.dash"
            )) {
              const r = g.getBoundingClientRect();
              if (!(r.width > 0 || r.height > 0)) continue;
              if (r.bottom <= treble.bottom - 2) continue;
              if (r.top >= bass.top + 2) continue;
              lyricGs.push(g);
            }
            if (!lyricGs.length) continue;
            let lyricBot = -Infinity;
            for (const g of lyricGs) {
              lyricBot = Math.max(
                lyricBot,
                g.getBoundingClientRect().bottom
              );
            }
            const band2 = staffLineBand(bass.el) || bass;
            // Geen stok-overhang reserveren: MuseScore-ref deelt die band.
            const bassDyPx = lyricBot + PAD - band2.top;
            if (bassDyPx < -4) {
              appendTranslateY(bass.el, bassDyPx / sy);
            }
            // Lyrics centreren in het (nieuwe) balkgat — niet tegen de bas.
            const band2b = staffLineBand(bass.el) || band2;
            let lyricTop = Infinity;
            lyricBot = -Infinity;
            for (const g of lyricGs) {
              const r = g.getBoundingClientRect();
              lyricTop = Math.min(lyricTop, r.top);
              lyricBot = Math.max(lyricBot, r.bottom);
            }
            const gapMid = (treble.bottom + band2b.top) / 2;
            const lyricMid = (lyricTop + lyricBot) / 2;
            const centerDy = gapMid - lyricMid;
            if (Math.abs(centerDy) >= 2) {
              const dySvg = centerDy / sy;
              for (const g of lyricGs) appendTranslateY(g, dySvg);
            }
          }
        })();
        // P3c — A↓/T↑-stokken inkorten zodat ze de lyric-band niet snijden.
        // OSMD/VexFlow houdt IdealStemLength ~35 px; in een compact balkgat
        // steken die stokken door de lettergrepen (dichte maten / derde).
        (function trimStemsClearOfLyricsScreen() {
          // CLEAR: lucht tussen stokpunt en lyric-bbox; MIN: leesbare stok
          // (VexFlow-default ~35 px; bij dichte balkgat tot ~10 px inkorten).
          const CLEAR_PX = 6;
          const MIN_STEM_PX = 10;
          const svgEl = mount.querySelector("svg");
          const ctm = svgEl && svgEl.getScreenCTM && svgEl.getScreenCTM();
          const sy = ctm && ctm.d ? ctm.d : 1;
          function staffLineBand(el) {
            const tops = [];
            const bots = [];
            for (const p of el.querySelectorAll("path")) {
              const d = p.getAttribute("d") || "";
              const m = d.match(
                /^M([-\d.]+) ([-\d.]+)L([-\d.]+) ([-\d.]+)$/
              );
              if (!m) continue;
              if (Math.abs(Number(m[2]) - Number(m[4])) > 0.2) continue;
              if (Number(m[3]) - Number(m[1]) < 200) continue;
              const r = p.getBoundingClientRect();
              if (!(r.width > 50)) continue;
              tops.push(r.top);
              bots.push(r.bottom);
            }
            if (tops.length < 4) return null;
            return {
              top: Math.min(...tops),
              bottom: Math.max(...bots),
            };
          }
          const bands = Array.from(mount.querySelectorAll(".staffline"))
            .map(staffLineBand)
            .filter(Boolean)
            .sort((a, b) => a.top - b.top);
          if (bands.length < 2) return;
          for (let i = 0; i + 1 < bands.length; i += 2) {
            const treble = bands[i];
            const bass = bands[i + 1];
            const lyricGs = [];
            for (const g of mount.querySelectorAll(".vf-text.lyrics")) {
              const r = g.getBoundingClientRect();
              if (!(r.width > 0 || r.height > 0)) continue;
              if (r.bottom <= treble.bottom - 2) continue;
              if (r.top >= bass.top + 2) continue;
              lyricGs.push(r);
            }
            if (!lyricGs.length) continue;
            let lyricTop = Infinity;
            let lyricBot = -Infinity;
            for (const r of lyricGs) {
              lyricTop = Math.min(lyricTop, r.top);
              lyricBot = Math.max(lyricBot, r.bottom);
            }
            const limitDown = lyricTop - CLEAR_PX;
            const limitUp = lyricBot + CLEAR_PX;
            for (const stemG of mount.querySelectorAll("g.vf-stem")) {
              const p = stemG.querySelector("path");
              if (!p) continue;
              const d = p.getAttribute("d") || "";
              const m = d.match(
                /^M([-\d.]+)\s+([-\d.]+)L([-\d.]+)\s+([-\d.]+)$/
              );
              if (!m) continue;
              const x1 = Number(m[1]);
              const y1 = Number(m[2]);
              const x2 = Number(m[3]);
              const y2 = Number(m[4]);
              if (Math.abs(x2 - x1) > 0.5) continue;
              const r = p.getBoundingClientRect();
              if (!(r.height >= 8)) continue;
              // Alleen stokken die dit SA↔TB-balkgat raken.
              if (r.bottom <= treble.bottom - 2 || r.top >= bass.top + 2) {
                continue;
              }
              // Tip = uiteinde weg van de nootkop (y2 in VexFlow-pad).
              const stemDown = y2 > y1;
              const stemUp = y2 < y1;
              // A↓: tip (r.bottom) niet in de lyric-band.
              if (stemDown && r.bottom > limitDown) {
                const tipScreen = Math.max(
                  r.top + MIN_STEM_PX,
                  Math.min(r.bottom, limitDown)
                );
                const dyScreen = tipScreen - r.bottom;
                if (dyScreen < -0.5) {
                  const tipLocal = y2 + dyScreen / sy;
                  p.setAttribute(
                    "d",
                    `M${x1} ${y1}L${x2} ${tipLocal.toFixed(3)}`
                  );
                }
                continue;
              }
              // T↑: tip (r.top) niet in de lyric-band (ook als hele stok
              // boven bass.top in het gat hangt).
              if (stemUp && r.top < limitUp) {
                const tipScreen = Math.min(
                  r.bottom - MIN_STEM_PX,
                  Math.max(r.top, limitUp)
                );
                const dyScreen = tipScreen - r.top;
                if (dyScreen > 0.5) {
                  const tipLocal = y2 + dyScreen / sy;
                  p.setAttribute(
                    "d",
                    `M${x1} ${y1}L${x2} ${tipLocal.toFixed(3)}`
                  );
                }
              }
            }
          }
        })();
        // S2 (+ S5) — melisma-bogen herankeren op stem-juiste punten:
        // A: onderkant nootkop→nootkop; T: bovenkant nootkop→nootkop;
        // S: bovenkant stok→stok; B: onderkant stok→stok. Boog blijft
        // dicht bij de balk (kleine bulge). Toets: alleluia-toon-2.
        (function reanchorMelismaSlursS2() {
          function staffLineBand(el) {
            const tops = [];
            const bots = [];
            for (const p of el.querySelectorAll("path")) {
              const d = p.getAttribute("d") || "";
              const m = d.match(
                /^M([-\d.]+) ([-\d.]+)L([-\d.]+) ([-\d.]+)$/
              );
              if (!m) continue;
              if (Math.abs(Number(m[2]) - Number(m[4])) > 0.2) continue;
              if (Number(m[3]) - Number(m[1]) < 200) continue;
              const r = p.getBoundingClientRect();
              if (!(r.width > 50)) continue;
              tops.push(r.top);
              bots.push(r.bottom);
            }
            if (tops.length < 4) return null;
            return { top: Math.min(...tops), bottom: Math.max(...bots) };
          }
          function parseCubicStartEnd(d) {
            const m = d.match(
              /M([-\d.]+)\s+([-\d.]+)C([-\d.]+)\s+([-\d.]+),([-\d.]+)\s+([-\d.]+),([-\d.]+)\s+([-\d.]+)/
            );
            if (!m) return null;
            return {
              x0: Number(m[1]),
              y0: Number(m[2]),
              x3: Number(m[7]),
              y3: Number(m[8]),
            };
          }
          function toScreen(el, x, y) {
            const ctm = el.getScreenCTM();
            if (!ctm) return null;
            const pt = el.ownerSVGElement.createSVGPoint();
            pt.x = x;
            pt.y = y;
            const s = pt.matrixTransform(ctm);
            return { x: s.x, y: s.y };
          }
          function toLocal(el, x, y) {
            const ctm = el.getScreenCTM();
            if (!ctm) return null;
            const inv = ctm.inverse();
            const pt = el.ownerSVGElement.createSVGPoint();
            pt.x = x;
            pt.y = y;
            const s = pt.matrixTransform(inv);
            return { x: s.x, y: s.y };
          }
          const bands = Array.from(mount.querySelectorAll(".staffline"))
            .map(staffLineBand)
            .filter(Boolean)
            .sort((a, b) => a.top - b.top);
          const notes = [];
          for (const n of mount.querySelectorAll(".vf-stavenote")) {
            if (n.getAttribute("data-osmd-spacer") === "1") continue;
            const head = n.querySelector(
              ".vf-notehead path, [data-osmd-breve-glyph='1'] path"
            );
            if (!head) continue;
            const hb = head.getBoundingClientRect();
            if (!(hb.width > 0.5)) continue;
            const stem = n.querySelector(".vf-stem path");
            let stemUp = null;
            let tip = null;
            if (stem) {
              const sb = stem.getBoundingClientRect();
              stemUp =
                sb.top + sb.height / 2 < hb.top + hb.height / 2;
              tip = stemUp
                ? { x: sb.left + sb.width / 2, y: sb.top }
                : { x: sb.left + sb.width / 2, y: sb.bottom };
            }
            notes.push({
              id: n.id,
              head: {
                cx: (hb.left + hb.right) / 2,
                cy: (hb.top + hb.bottom) / 2,
                top: hb.top,
                bottom: hb.bottom,
              },
              stemUp,
              tip,
            });
          }
          function bandIndex(y) {
            let best = -1;
            let bd = Infinity;
            for (let i = 0; i < bands.length; i += 1) {
              const mid = (bands[i].top + bands[i].bottom) / 2;
              const d = Math.abs(mid - y);
              if (d < bd) {
                bd = d;
                best = i;
              }
            }
            return best;
          }
          function roleFor(note, bIdx, preferRole, preferCy) {
            // Even index = SA (boven); oneven = TB.
            const sa = bIdx % 2 === 0;
            if (note.stemUp === true) return sa ? "S" : "T";
            if (note.stemUp === false) return sa ? "A" : "B";
            // Stokloos: niet via balkmidden (S én A zitten vaak beide
            // onder de middellijn). Bij bekende startstem: zelfde stem als
            // |cy−preferCy| klein is, anders de tegenstem.
            if (preferRole && preferCy != null) {
              if (Math.abs(note.head.cy - preferCy) <= 8) {
                return preferRole;
              }
              if (sa) return preferRole === "S" ? "A" : "S";
              return preferRole === "T" ? "B" : "T";
            }
            return sa ? "S" : "T";
          }
          function anchorFor(note, role) {
            if (role === "A") {
              return { x: note.head.cx, y: note.head.bottom };
            }
            if (role === "T") {
              return { x: note.head.cx, y: note.head.top };
            }
            if (role === "S") {
              return note.tip
                ? { x: note.tip.x, y: note.tip.y }
                : { x: note.head.cx, y: note.head.top };
            }
            if (role === "B") {
              return note.tip
                ? { x: note.tip.x, y: note.tip.y }
                : { x: note.head.cx, y: note.head.bottom };
            }
            return { x: note.head.cx, y: note.head.cy };
          }
          function pickNote(px, py, preferRole, preferCy) {
            let best = null;
            let bestScore = Infinity;
            for (const n of notes) {
              const bIdx = bandIndex(n.head.cy);
              const role = roleFor(n, bIdx, preferRole, preferCy);
              const useRole = preferRole || role;
              const anc = anchorFor(n, useRole);
              const dx = Math.abs(anc.x - px);
              const dy = Math.abs(anc.y - py);
              if (dx > 60) continue;
              let score = dx + dy * 0.35;
              if (preferRole && role !== preferRole) score += 45;
              if (
                preferCy != null &&
                Math.abs(n.head.cy - preferCy) > 6
              ) {
                score += Math.abs(n.head.cy - preferCy) * 0.8;
              }
              if (score < bestScore) {
                bestScore = score;
                best = { note: n, role: useRole, bIdx, score };
              }
            }
            return best;
          }
          for (const g of mount.querySelectorAll(".vf-curve")) {
            const pathEl = g.querySelector("path");
            if (!pathEl) continue;
            const d0 = pathEl.getAttribute("d") || "";
            const ends = parseCubicStartEnd(d0);
            if (!ends) continue;
            const p0 = toScreen(pathEl, ends.x0, ends.y0);
            const p3 = toScreen(pathEl, ends.x3, ends.y3);
            if (!p0 || !p3) continue;
            if (Math.abs(p3.x - p0.x) < 24) continue;
            const startHit = pickNote(p0.x, p0.y, null, null);
            if (!startHit) continue;
            const role = startHit.role;
            const endHit = pickNote(
              p3.x,
              p3.y,
              role,
              startHit.note.head.cy
            );
            if (!endHit) continue;
            const a0 = anchorFor(startHit.note, role);
            const a3 = anchorFor(endHit.note, role);
            const loc0 = toLocal(pathEl, a0.x, a0.y);
            const loc3 = toLocal(pathEl, a3.x, a3.y);
            if (!loc0 || !loc3) continue;
            const span = Math.abs(loc3.x - loc0.x);
            // S5: kleine bulge; A/T (richting balkgat) strakker dan S/B.
            const above = role === "S" || role === "T";
            const intoGap = role === "A" || role === "T";
            const bulge = intoGap
              ? Math.min(7, Math.max(3, span * 0.055))
              : Math.min(12, Math.max(5, span * 0.09));
            const by = above ? -bulge : bulge;
            const thick = 0.55;
            const ty = above ? -thick : thick;
            const c1x = loc0.x + span * 0.28 * Math.sign(loc3.x - loc0.x || 1);
            const c2x = loc3.x - span * 0.28 * Math.sign(loc3.x - loc0.x || 1);
            const c1y = loc0.y + by;
            const c2y = loc3.y + by;
            const d =
              `M${loc0.x} ${loc0.y}` +
              `C${c1x} ${c1y},${c2x} ${c2y},${loc3.x} ${loc3.y}` +
              `L${loc3.x} ${loc3.y + ty}` +
              `C${c2x} ${c2y + ty},${c1x} ${c1y + ty},${loc0.x} ${loc0.y + ty}` +
              `L${loc0.x} ${loc0.y}Z`;
            pathEl.setAttribute("d", d);
            g.setAttribute("data-osmd-s2", role);
          }
          // S5-clamp: restant-uitsteek in het balkgat terugduwen (na ankers).
          const MAX_OUT_PX = 18;
          const svgEl = mount.querySelector("svg");
          const sy =
            svgEl && svgEl.getScreenCTM && svgEl.getScreenCTM()
              ? svgEl.getScreenCTM().d || 1
              : 1;
          for (let i = 0; i + 1 < bands.length; i += 2) {
            const treble = bands[i];
            const bass = bands[i + 1];
            const gapMid = (treble.bottom + bass.top) / 2;
            for (const g of mount.querySelectorAll(".vf-curve")) {
              const r = g.getBoundingClientRect();
              if (!(r.width > 24)) continue;
              if (r.bottom <= treble.bottom - 2) continue;
              if (r.top >= bass.top + 2) continue;
              const midY = (r.top + r.bottom) / 2;
              let dyPx = 0;
              if (midY < gapMid) {
                const limit = treble.bottom + MAX_OUT_PX;
                if (r.bottom > limit) dyPx = limit - r.bottom;
              } else {
                const limit = bass.top - MAX_OUT_PX;
                if (r.top < limit) dyPx = limit - r.top;
              }
              if (!(Math.abs(dyPx) >= 1)) continue;
              const prev = g.getAttribute("transform") || "";
              g.setAttribute(
                "transform",
                `${prev} translate(0, ${(dyPx / sy).toFixed(2)})`.trim()
              );
            }
          }
        })();
        // P3a — glyph-overlap herstellen. Screen-px → SVG-user units via CTM.
        // Woordgrens (ia,|Al / ja,|Al) strenger. Dashes mee verschuiven —
        // anders blijft «-» op oude x en snijdt door de volgende lettergreep
        // (alleluia-2/3).
        (function enforceScreenLyricGaps() {
          const MIN_GAP_PX = 16;
          const MIN_WORD_GAP_PX = 48;
          // S22: gap-shift mag lyric niet >MAX_NOTE_DX_PX van nootkolom trekken.
          const MAX_NOTE_DX_PX = 28;
          const svgEl = mount.querySelector("svg");
          const ctm = svgEl && svgEl.getScreenCTM && svgEl.getScreenCTM();
          const sx = ctm && ctm.a ? ctm.a : 1;
          function appendTranslateX(el, dxSvg) {
            if (!(dxSvg > 0.2)) return;
            const prev = el.getAttribute("transform") || "";
            el.setAttribute(
              "transform",
              `${prev} translate(${dxSvg.toFixed(2)}, 0)`.trim()
            );
          }
          // Nootkolommen (screen): zichtbare koppen + breve-glyphs + spacer-
          // ankers via tijdelijke probe-cirkel op data-osmd-anchor-x.
          const noteCols = [];
          for (const n of mount.querySelectorAll(".vf-stavenote")) {
            const glyph = n.querySelector("[data-osmd-breve-glyph='1']");
            const head = n.querySelector(".vf-notehead path");
            const el = glyph || head;
            if (el) {
              const r = el.getBoundingClientRect();
              if (r.width > 0.5) {
                noteCols.push({
                  cx: (r.left + r.right) / 2,
                  cy: (r.top + r.bottom) / 2,
                });
                continue;
              }
            }
            const anchor = n.getAttribute("data-osmd-anchor-x");
            if (anchor == null || !Number.isFinite(Number(anchor))) continue;
            const ns = "http://www.w3.org/2000/svg";
            const probe = document.createElementNS(ns, "circle");
            probe.setAttribute("cx", String(Number(anchor)));
            probe.setAttribute("cy", "0");
            probe.setAttribute("r", "0.01");
            probe.setAttribute("fill", "none");
            n.appendChild(probe);
            // cy=0 is verkeerd; gebruik staf-y van een sibling-noot.
            let staffY = null;
            const sib = n.parentElement && n.parentElement.querySelector(
              ".vf-stavenote .vf-notehead path, .vf-stavenote [data-osmd-breve-glyph='1']"
            );
            if (sib) {
              staffY = sib.getBoundingClientRect().top;
            }
            const pr = probe.getBoundingClientRect();
            n.removeChild(probe);
            if (!(pr.width >= 0) && !(pr.left || pr.right)) continue;
            noteCols.push({
              cx: (pr.left + pr.right) / 2 || pr.x,
              cy: staffY != null ? staffY + 5 : pr.top,
            });
          }
          function nearestNoteDx(lyricCx, lyricCy, extraDxPx) {
            let best = Infinity;
            for (const c of noteCols) {
              if (Math.abs(c.cy - lyricCy) > 100) continue;
              best = Math.min(best, Math.abs(c.cx - (lyricCx + extraDxPx)));
            }
            return best;
          }
          const groups = Array.from(
            mount.querySelectorAll(".vf-text.lyrics")
          ).filter((g) => {
            const t = g.querySelector("text");
            const r = g.getBoundingClientRect();
            return t && r.width > 0;
          });
          groups.sort((a, b) => {
            const ra = a.getBoundingClientRect();
            const rb = b.getBoundingClientRect();
            return ra.top - rb.top || ra.left - rb.left;
          });
          const dashes = Array.from(
            mount.querySelectorAll(".vf-text.dash")
          ).filter((g) => g.getBoundingClientRect().width > 0);
          function shiftLyricWithDashes(i, needSvg, force) {
            const curG = groups[i];
            const curR = curG.getBoundingClientRect();
            const nextR =
              i + 1 < groups.length
                ? groups[i + 1].getBoundingClientRect()
                : null;
            const prevR =
              i > 0 ? groups[i - 1].getBoundingClientRect() : null;
            if (
              prevR &&
              nextR &&
              Math.abs(curR.top - prevR.top) > 28
            ) {
              /* other band */
            }
            // Beperk shift t.o.v. nootkolom (S22/P3e). Force (gap <12):
            // nog steeds max ~28 px van de noot — anders faalt
            // lyric↔noot op brede eindlettergrepen («heid,»).
            const lyricCx = (curR.left + curR.right) / 2;
            const lyricCy = (curR.top + curR.bottom) / 2;
            let dx = needSvg;
            const cap = force ? 28 : MAX_NOTE_DX_PX;
            const before = nearestNoteDx(lyricCx, lyricCy, 0);
            if (Number.isFinite(before) && before < 90) {
              while (dx > 0.3) {
                const after = nearestNoteDx(lyricCx, lyricCy, dx * sx);
                if (after <= cap) break;
                dx *= 0.7;
              }
              if (
                !force &&
                nearestNoteDx(lyricCx, lyricCy, dx * sx) > cap + 8
              ) {
                return; // liever krappe gap dan losse lyric
              }
            }
            if (!(dx > 0.2)) return;
            appendTranslateX(curG, dx);
            // Dashes die bij deze lettergreep horen: tussen prev en next,
            // dichter bij cur dan bij de buur.
            for (const d of dashes) {
              const dr = d.getBoundingClientRect();
              if (Math.abs(dr.top - curR.top) > 28) continue;
              const mid = (dr.left + dr.right) / 2;
              const leftBound = prevR ? prevR.right - 4 : -Infinity;
              const rightBound = nextR ? nextR.left + 4 : Infinity;
              if (mid < leftBound || mid > rightBound) continue;
              const distCur = Math.abs(mid - (curR.left + curR.right) / 2);
              const distPrev = prevR
                ? Math.abs(mid - (prevR.left + prevR.right) / 2)
                : Infinity;
              const distNext = nextR
                ? Math.abs(mid - (nextR.left + nextR.right) / 2)
                : Infinity;
              if (distCur <= distPrev && distCur <= distNext) {
                appendTranslateX(d, dx);
              }
            }
          }
          for (let pass = 0; pass < 12; pass += 1) {
            let moved = false;
            for (let i = 1; i < groups.length; i += 1) {
              const prevG = groups[i - 1];
              const curG = groups[i];
              const prevR = prevG.getBoundingClientRect();
              const curR = curG.getBoundingClientRect();
              if (Math.abs(curR.top - prevR.top) > 28) continue;
              const prevT = String(
                prevG.querySelector("text")?.textContent || ""
              ).trim();
              const curT = String(
                curG.querySelector("text")?.textContent || ""
              ).trim();
              // Woordgap alleen na leesteken — niet bij mid-zin kapitaal
              // («ren Gods»: heilige naam) want 48px trok lyrics van de
              // nootkolom (P3e / maat 16).
              const wordBoundary = /[,.;:!?]$/.test(prevT);
              const needMin = wordBoundary ? MIN_WORD_GAP_PX : MIN_GAP_PX;
              const gapPx = curR.left - prevR.right;
              if (gapPx >= needMin) continue;
              const needSvg = (needMin - gapPx) / sx;
              if (!(needSvg > 0.2)) continue;
              // Onder verify-drempel (12px) of echte overlap: forceer shift
              // (S22-cap mag dan wijken).
              const force = gapPx < 12;
              shiftLyricWithDashes(i, needSvg, force);
              moved = true;
            }
            if (!moved) break;
          }
          // Woordgrens: streepjes in de gap tussen woorden weg (geen
          // «ja, - Al»); hyphen hoort tussen lettergrepen van één woord.
          for (let i = 1; i < groups.length; i += 1) {
            const prevR = groups[i - 1].getBoundingClientRect();
            const curR = groups[i].getBoundingClientRect();
            if (Math.abs(curR.top - prevR.top) > 28) continue;
            const prevT = String(
              groups[i - 1].querySelector("text")?.textContent || ""
            ).trim();
            const curT = String(
              groups[i].querySelector("text")?.textContent || ""
            ).trim();
            const wordBoundary =
              /[,.;:!?]$/.test(prevT) ||
              (/^[A-ZÀ-ÖØ-Þ]/.test(curT) && !/-$/.test(prevT));
            if (!wordBoundary) continue;
            for (const d of dashes) {
              const dr = d.getBoundingClientRect();
              if (Math.abs(dr.top - curR.top) > 28) continue;
              const mid = (dr.left + dr.right) / 2;
              if (mid > prevR.right - 2 && mid < curR.left + 2) {
                d.remove();
              }
            }
          }
        })();
        // P3e — zachte her-snap na gap-enforce: alleen lyrics die >28 px
        // van hun nootkolom staan (verify lyric↔noot), zonder volle
        // her-centrering die P3a opnieuw breekt.
        if (typeof window.__vsaOsmdSnapLyricsToNotes === "function") {
          window.__vsaOsmdSnapLyricsToNotes(mount);
        }
        // L3 — lettergreepstreepjes tussen syllabic begin/middle/end.
        // OSMD laat ze soms weg in krappe gaps (alleluia-8, derde-antifoon).
        // Alleen waar MusicXML een binnenwoord-overgang markeert — geen
        // streepjes tussen losse woorden («want van»).
        (function ensureSyllableHyphensL3() {
          const svgEl = mount.querySelector("svg");
          if (!svgEl) return;
          const ns = "http://www.w3.org/2000/svg";
          // Geordende lyric-syllabes uit MusicXML (lyric number 1).
          const syls = [];
          const re =
            /<lyric\b[^>]*>\s*<syllabic>([^<]*)<\/syllabic>\s*<text>([^<]*)<\/text>/g;
          let m;
          while ((m = re.exec(xml))) {
            syls.push({
              syl: String(m[1]).trim().toLowerCase(),
              text: String(m[2])
                .replace(/&lt;/g, "<")
                .replace(/&gt;/g, ">")
                .replace(/&amp;/g, "&")
                .replace(/&quot;/g, '"')
                .trim(),
            });
          }
          const needHyphen = new Set();
          for (let i = 0; i + 1 < syls.length; i += 1) {
            const a = syls[i].syl;
            const b = syls[i + 1].syl;
            const join =
              (a === "begin" || a === "middle") &&
              (b === "middle" || b === "end");
            if (!join) continue;
            needHyphen.add(syls[i].text + "\0" + syls[i + 1].text);
          }
          if (!needHyphen.size) return;
          const lyrics = Array.from(
            mount.querySelectorAll(".vf-text.lyrics")
          ).filter((g) => {
            const t = g.querySelector("text");
            const r = g.getBoundingClientRect();
            return t && r.width > 0;
          });
          lyrics.sort((a, b) => {
            const ra = a.getBoundingClientRect();
            const rb = b.getBoundingClientRect();
            return ra.top - rb.top || ra.left - rb.left;
          });
          const tpl = mount.querySelector(".vf-text.dash text");
          for (let i = 0; i + 1 < lyrics.length; i += 1) {
            const a = lyrics[i];
            const b = lyrics[i + 1];
            const ar = a.getBoundingClientRect();
            const br = b.getBoundingClientRect();
            if (Math.abs(ar.top - br.top) > 28) continue;
            const aT = String(
              a.querySelector("text")?.textContent || ""
            ).trim();
            const bT = String(
              b.querySelector("text")?.textContent || ""
            ).trim();
            if (!needHyphen.has(aT + "\0" + bT)) continue;
            const gap = br.left - ar.right;
            if (gap < 6 || gap > 100) continue;
            const midX = (ar.right + br.left) / 2;
            const hasDash = Array.from(
              mount.querySelectorAll(".vf-text.dash")
            ).some((d) => {
              const r = d.getBoundingClientRect();
              if (!(r.width > 0)) return false;
              if (Math.abs(r.top - ar.top) > 28) return false;
              const cx = (r.left + r.right) / 2;
              return cx > ar.right - 2 && cx < br.left + 2;
            });
            if (hasDash) continue;
            const aCtm = a.getScreenCTM();
            if (!aCtm) continue;
            const inv = aCtm.inverse();
            const pt = svgEl.createSVGPoint();
            pt.x = midX;
            pt.y = ar.top + ar.height * 0.7;
            const loc = pt.matrixTransform(inv);
            const aText = a.querySelector("text");
            const g = document.createElementNS(ns, "g");
            g.setAttribute("class", "vf-text dash");
            g.setAttribute("data-osmd-l3", "1");
            g.setAttribute("transform", a.getAttribute("transform") || "");
            const text = document.createElementNS(ns, "text");
            text.textContent = "-";
            for (const attr of [
              "font-family",
              "font-size",
              "font-weight",
              "font-style",
              "fill",
              "stroke",
              "stroke-width",
            ]) {
              const v =
                (tpl && tpl.getAttribute(attr)) ||
                (aText && aText.getAttribute(attr));
              if (v) text.setAttribute(attr, v);
            }
            text.setAttribute("x", String(loc.x));
            text.setAttribute("y", aText?.getAttribute("y") || "0");
            g.appendChild(text);
            (a.parentElement || mount).appendChild(g);
          }
        })();
        // L4 — melisma-extender vullen tot onder de laatste melisma-noot.
        // OSMD tekent soms één kort streepje of niets in een lang melisma
        // (alleluia-3 «lu…ja»). Herhaalde «-» in de gap; geen woordgrens.
        (function fillMelismaExtendersL4() {
          const DASH_STEP_PX = 22;
          const MIN_GAP_PX = 72;
          const svgEl = mount.querySelector("svg");
          if (!svgEl) return;
          const lyrics = Array.from(
            mount.querySelectorAll(".vf-text.lyrics")
          ).filter((g) => {
            const t = g.querySelector("text");
            const r = g.getBoundingClientRect();
            return t && r.width > 0;
          });
          lyrics.sort((a, b) => {
            const ra = a.getBoundingClientRect();
            const rb = b.getBoundingClientRect();
            return ra.top - rb.top || ra.left - rb.left;
          });
          const curves = Array.from(
            mount.querySelectorAll(".vf-curve")
          ).map((g) => g.getBoundingClientRect());
          const ns = "http://www.w3.org/2000/svg";
          for (let i = 0; i + 1 < lyrics.length; i += 1) {
            const a = lyrics[i];
            const b = lyrics[i + 1];
            const ar = a.getBoundingClientRect();
            const br = b.getBoundingClientRect();
            if (Math.abs(ar.top - br.top) > 28) continue;
            const aText = a.querySelector("text");
            const aT = String(aText?.textContent || "").trim();
            const bT = String(
              b.querySelector("text")?.textContent || ""
            ).trim();
            const wordBoundary =
              /[,.;:!?]$/.test(aT) ||
              (/^[A-ZÀ-ÖØ-Þ]/.test(bT) && !/-$/.test(aT));
            if (wordBoundary) continue;
            const gapPx = br.left - ar.right;
            if (gapPx < MIN_GAP_PX) continue;
            const gapL = ar.right + 4;
            const gapR = br.left - 4;
            const midY = (ar.top + ar.bottom) / 2;
            const slurHits = curves.some((c) => {
              if (!(c.width > 40)) return false;
              if (Math.abs((c.top + c.bottom) / 2 - midY) > 120) {
                return false;
              }
              const overlap =
                Math.min(c.right, gapR) - Math.max(c.left, gapL);
              return overlap > Math.min(60, gapPx * 0.25);
            });
            const existing = Array.from(
              mount.querySelectorAll(".vf-text.dash")
            ).filter((d) => {
              const r = d.getBoundingClientRect();
              if (!(r.width > 0)) return false;
              if (Math.abs(r.top - ar.top) > 28) return false;
              const cx = (r.left + r.right) / 2;
              return cx >= gapL - 2 && cx <= gapR + 2;
            });
            if (!slurHits && existing.length === 0) continue;
            const covered = new Set(
              existing.map((d) =>
                Math.round(
                  ((d.getBoundingClientRect().left +
                    d.getBoundingClientRect().right) /
                    2) /
                    DASH_STEP_PX
                )
              )
            );
            const aCtm = a.getScreenCTM();
            if (!aCtm) continue;
            const inv = aCtm.inverse();
            const parent = a.parentElement || mount;
            const baseY = aText?.getAttribute("y") || "0";
            const tpl = mount.querySelector(".vf-text.dash text");
            for (
              let xPx = gapL + DASH_STEP_PX * 0.4;
              xPx < gapR - 2;
              xPx += DASH_STEP_PX
            ) {
              const bucket = Math.round(xPx / DASH_STEP_PX);
              if (covered.has(bucket)) continue;
              covered.add(bucket);
              const pt = svgEl.createSVGPoint();
              pt.x = xPx;
              pt.y = ar.top + ar.height * 0.7;
              const loc = pt.matrixTransform(inv);
              const g = document.createElementNS(ns, "g");
              g.setAttribute("class", "vf-text dash");
              g.setAttribute("data-osmd-l4", "1");
              g.setAttribute("transform", a.getAttribute("transform") || "");
              const text = document.createElementNS(ns, "text");
              text.textContent = "-";
              for (const attr of [
                "font-family",
                "font-size",
                "font-weight",
                "font-style",
                "fill",
                "stroke",
                "stroke-width",
              ]) {
                const v =
                  (tpl && tpl.getAttribute(attr)) ||
                  (aText && aText.getAttribute(attr));
                if (v) text.setAttribute(attr, v);
              }
              text.setAttribute("x", String(loc.x));
              text.setAttribute("y", baseY);
              g.appendChild(text);
              parent.appendChild(g);
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
