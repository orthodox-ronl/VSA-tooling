/**
 * Peiling: render elke S8-variant met OSMD (geen JS-hide) en tel
 * zichtbare nootkoppen + lyric-teksten.
 *
 * Gebruik (vanuit deze map of tooling-root):
 *   node generate-variants.mjs
 *   node probe.mjs
 *
 * Puppeteer: hergebruikt ../partituur-osmd-svg/node_modules indien aanwezig.
 */
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath, pathToFileURL } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OSMD_CDN =
  "https://cdn.jsdelivr.net/npm/opensheetmusicdisplay@1.9.3/build/opensheetmusicdisplay.min.js";

async function loadPuppeteer() {
  const candidates = [
    path.join(__dirname, "node_modules", "puppeteer", "lib", "esm", "puppeteer", "puppeteer.js"),
    path.join(__dirname, "..", "partituur-osmd-svg", "node_modules", "puppeteer"),
  ];
  for (const c of candidates) {
    try {
      if (fs.existsSync(c) || fs.existsSync(c + ".js")) {
        const mod = await import(pathToFileURL(
          fs.existsSync(c) && fs.statSync(c).isDirectory()
            ? path.join(c, "lib", "esm", "puppeteer", "puppeteer.js")
            : c
        ).href);
        return mod.default ?? mod;
      }
    } catch {
      /* try next */
    }
  }
  // createRequire fallback for CJS resolve
  try {
    const req = createRequire(
      path.join(__dirname, "..", "partituur-osmd-svg", "package.json")
    );
    return req("puppeteer");
  } catch {
    /* fall through */
  }
  throw new Error(
    "puppeteer niet gevonden. Draai eerst:\n" +
      "  cd examples\\spikes\\partituur-osmd-svg && npm install"
  );
}

async function probeOne(page, xml) {
  return page.evaluate(async (musicxml) => {
    const host = document.getElementById("osmd");
    host.innerHTML = "";
    const osmd = new window.opensheetmusicdisplay.OpenSheetMusicDisplay(host, {
      autoResize: false,
      backend: "svg",
      drawTitle: false,
      drawSubtitle: false,
      drawComposer: false,
      drawLyricist: false,
      drawPartNames: false,
      drawTimeSignatures: false,
      drawingParameters: "compacttight",
    });
    osmd.setOptions({ pageFormat: "Endless" });
    await osmd.load(musicxml);
    osmd.render();

    const root = host;
    const notes = Array.from(root.querySelectorAll("g.vf-stavenote"));
    const perNote = notes.map((n, i) => {
      const heads = Array.from(
        n.querySelectorAll(
          "g.vf-notehead, path.vf-notehead, .vf-notehead"
        )
      );
      const headBoxes = heads.map((el) => {
        let bb = { w: 0, h: 0 };
        try {
          const b = el.getBBox();
          bb = { w: +b.width.toFixed(2), h: +b.height.toFixed(2) };
        } catch {
          /* ignore */
        }
        const d = el.getAttribute("d") || "";
        return {
          tag: el.tagName,
          className: el.getAttribute("class") || "",
          w: bb.w,
          h: bb.h,
          pathLen: d.length,
          fill: el.getAttribute("fill") || "",
          opacity: el.getAttribute("opacity") || "",
        };
      });
      const lyrics = Array.from(n.querySelectorAll("text"))
        .map((t) => String(t.textContent || "").trim())
        .filter(Boolean);
      // Fallback: lyrics often sit outside stavenote — collect by x proximity later
      return {
        i,
        headCount: heads.length,
        headBoxes,
        maxHeadArea: headBoxes.reduce((a, h) => a + h.w * h.h, 0),
        lyricsInNote: lyrics,
      };
    });

    const allTexts = Array.from(root.querySelectorAll("text"))
      .map((t) => String(t.textContent || "").trim())
      .filter((t) => t && t !== "-");
    const wanted = ["Al", "le", "lu", "i", "a", "al"];
    const foundLyrics = wanted.filter((w) => allTexts.includes(w));

    // Spacer slots = indices 2,3,4 (0=Al, 1=le breve, 5=al)
    const spacerSlots = perNote.slice(2, 5);
    const spacerHeadsVisible = spacerSlots.filter((s) => s.maxHeadArea > 1).length;
    const edgeHeadsVisible = [perNote[0], perNote[5]]
      .filter(Boolean)
      .filter((s) => s.maxHeadArea > 1).length;
    const breveHeadVisible =
      perNote[1] && perNote[1].maxHeadArea > 1 ? true : false;

    return {
      staveNotes: notes.length,
      foundLyrics,
      missingLyrics: wanted.filter((w) => !foundLyrics.includes(w)),
      edgeHeadsVisible,
      breveHeadVisible,
      spacerHeadsVisible,
      spacerMaxAreas: spacerSlots.map((s) => +s.maxHeadArea.toFixed(1)),
      perNote,
      hasSvg: !!root.querySelector("svg"),
    };
  }, xml);
}

async function main() {
  const variantsDir = path.join(__dirname, "variants");
  const outDir = path.join(__dirname, "out");
  fs.mkdirSync(outDir, { recursive: true });

  const files = fs
    .readdirSync(variantsDir)
    .filter((f) => f.endsWith(".musicxml"))
    .sort();
  if (!files.length) {
    console.error("Geen variants/*.musicxml — draai eerst generate-variants.mjs");
    process.exit(1);
  }

  const puppeteer = await loadPuppeteer();
  const chromeCandidates = [
    process.env.PUPPETEER_EXECUTABLE_PATH,
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
    `${process.env.LOCALAPPDATA}\\Google\\Chrome\\Application\\chrome.exe`,
  ].filter(Boolean);
  const executablePath = chromeCandidates.find((p) => fs.existsSync(p));
  const browser = await puppeteer.launch({
    headless: true,
    executablePath,
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
  });

  const results = [];
  try {
    const page = await browser.newPage();
    page.setDefaultTimeout(120_000);
    await page.setContent(
      `<!DOCTYPE html><html><head><meta charset="utf-8"></head>
<body><div id="osmd" style="width:960px"></div>
<script src="${OSMD_CDN}"></script></body></html>`,
      { waitUntil: "networkidle0" }
    );
    await page.waitForFunction(
      () => typeof window.opensheetmusicdisplay !== "undefined"
    );

    for (const file of files) {
      const xml = fs.readFileSync(path.join(variantsDir, file), "utf8");
      const id = file.replace(/\.musicxml$/, "");
      let metrics;
      try {
        metrics = await probeOne(page, xml);
        // Save SVG for manual inspection
        const svg = await page.evaluate(() => {
          const svgEl = document.querySelector("#osmd svg");
          if (!svgEl) return "";
          svgEl.setAttribute("xmlns", "http://www.w3.org/2000/svg");
          return svgEl.outerHTML;
        });
        if (svg) {
          fs.writeFileSync(
            path.join(outDir, `${id}.svg`),
            `<?xml version="1.0" encoding="UTF-8"?>\n${svg}\n`,
            "utf8"
          );
        }
      } catch (err) {
        metrics = { error: String(err && err.message ? err.message : err) };
      }
      const row = { id, ...metrics };
      results.push(row);
      console.log(JSON.stringify(row));
    }
  } finally {
    await browser.close();
  }

  const summaryPath = path.join(outDir, "peiling-summary.json");
  fs.writeFileSync(summaryPath, JSON.stringify(results, null, 2), "utf8");
  console.log("summary:", summaryPath);
}

main().catch((err) => {
  console.error(err && err.stack ? err.stack : err);
  process.exit(1);
});
