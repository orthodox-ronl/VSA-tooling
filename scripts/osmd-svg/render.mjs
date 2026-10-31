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
  // (e) kortere stokken: minder inbraak in het lyric-balkgat (P3c/alleluia-8).
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
        // groep: die omvat stokken én lyrics). Stokken mogen verticaal met de
        // lyric-band overlappen (zoals MuseScore-ref); alleen de bas-groep
        // omhoog tot een kleine marge onder de lyrics.
        (function compressStaffGapScreen() {
          const PAD = 8;
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
        // P3a — glyph-overlap herstellen. Screen-px → SVG-user units via CTM.
        // Woordgrens (ia,|Al) strenger dan hyphen-gaps: voldoende wit.
        (function enforceScreenLyricGaps() {
          const MIN_GAP_PX = 16;
          const MIN_WORD_GAP_PX = 36;
          const svgEl = mount.querySelector("svg");
          const ctm = svgEl && svgEl.getScreenCTM && svgEl.getScreenCTM();
          const sx = ctm && ctm.a ? ctm.a : 1;
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
          for (let pass = 0; pass < 6; pass += 1) {
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
              const wordBoundary =
                /[,.;:!?]$/.test(prevT) ||
                (/^[A-ZÀ-ÖØ-Þ]/.test(curT) && !/-$/.test(prevT));
              const needMin = wordBoundary ? MIN_WORD_GAP_PX : MIN_GAP_PX;
              const gapPx = curR.left - prevR.right;
              if (gapPx >= needMin) continue;
              const needSvg = (needMin - gapPx) / sx;
              if (!(needSvg > 0.2)) continue;
              const prevTf = curG.getAttribute("transform") || "";
              curG.setAttribute(
                "transform",
                `${prevTf} translate(${needSvg.toFixed(2)}, 0)`.trim()
              );
              moved = true;
            }
            if (!moved) break;
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
