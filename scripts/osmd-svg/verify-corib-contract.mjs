/**
 * Contract-check op OSMD-SVG (CoriB):
 * - geen lyric-overlap (mscz-leesbaarheid §2 / P3a)
 * - maatnummers alleen aan systeembegin (S10)
 * - maatnummer 1 aanwezig (S10)
 *
 * Usage:
 *   node verify-corib-contract.mjs path/to/a.osmd.svg [more…]
 * Exit 0 = pass; 1 = fail.
 */
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath, pathToFileURL } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(import.meta.url);
const puppeteer = require(path.join(__dirname, "node_modules", "puppeteer"));

const MIN_LYRIC_GAP_PX = 1.5;
const MID_SYSTEM_X_SLACK = 40;

async function checkSvg(browser, svgPath) {
  const svgText = fs.readFileSync(svgPath, "utf8");
  const page = await browser.newPage();
  page.setDefaultTimeout(120_000);
  try {
    await page.setContent(
      `<!DOCTYPE html><html><body style="margin:0;background:#fff">${svgText}</body></html>`,
      { waitUntil: "domcontentloaded" }
    );
    return await page.evaluate(
      (minGap, midSlack) => {
        const root = document.querySelector("svg");
        if (!root) return { ok: false, errors: ["geen <svg>"] };

        const lyrics = [...root.querySelectorAll(".vf-text.lyrics text")]
          .map((t) => {
            let b;
            try {
              b = t.getBBox();
            } catch {
              return null;
            }
            return {
              t: t.textContent,
              x: b.x,
              y: b.y,
              r: b.x + b.width,
            };
          })
          .filter(Boolean);

        const rows = new Map();
        for (const L of lyrics) {
          const k = Math.round(L.y);
          if (!rows.has(k)) rows.set(k, []);
          rows.get(k).push(L);
        }
        const overlaps = [];
        let minLyricGap = Infinity;
        for (const row of rows.values()) {
          row.sort((a, b) => a.x - b.x);
          for (let i = 0; i < row.length - 1; i++) {
            const gap = row[i + 1].x - row[i].r;
            minLyricGap = Math.min(minLyricGap, gap);
            if (gap < minGap) {
              overlaps.push({
                a: row[i].t,
                b: row[i + 1].t,
                gap: Math.round(gap * 10) / 10,
                y: Math.round(row[i].y),
              });
            }
          }
        }

        const nums = [...root.querySelectorAll("g.vf-text text")]
          .filter((t) => /^\d{1,3}$/.test(String(t.textContent || "").trim()))
          .map((t) => {
            const b = t.getBBox();
            return {
              n: t.textContent.trim(),
              x: Math.round(b.x),
              y: Math.round(b.y),
            };
          });

        const byY = new Map();
        for (const n of nums) {
          const k = Math.round(n.y / 40) * 40;
          if (!byY.has(k)) byY.set(k, []);
          byY.get(k).push(n);
        }
        const midNums = [];
        for (const group of byY.values()) {
          group.sort((a, b) => a.x - b.x);
          const left = group[0].x;
          for (const g of group.slice(1)) {
            if (g.x > left + midSlack) midNums.push(g);
          }
        }

        const hasOne = nums.some((n) => n.n === "1");
        const errors = [];
        if (overlaps.length) {
          errors.push(
            `lyric-overlap ×${overlaps.length} (minGap=${
              Number.isFinite(minLyricGap)
                ? Math.round(minLyricGap * 10) / 10
                : "?"
            }): ` +
              overlaps
                .slice(0, 5)
                .map((o) => `${o.a}|${o.b}=${o.gap}`)
                .join(", ")
          );
        }
        if (midNums.length) {
          errors.push(
            `S10 mid-systeem-maatnummers: ` +
              midNums.map((m) => `${m.n}@(${m.x},${m.y})`).join(", ")
          );
        }
        if (!hasOne) {
          errors.push("S10: maatnummer 1 ontbreekt");
        }
        return {
          ok: errors.length === 0,
          errors,
          nLyrics: lyrics.length,
          nNums: nums.length,
          nums: nums.map((n) => n.n),
          minLyricGap: Number.isFinite(minLyricGap)
            ? Math.round(minLyricGap * 10) / 10
            : null,
        };
      },
      MIN_LYRIC_GAP_PX,
      MID_SYSTEM_X_SLACK
    );
  } finally {
    await page.close();
  }
}

async function main() {
  const args = process.argv.slice(2).filter((a) => !a.startsWith("-"));
  if (!args.length) {
    console.error(
      "Gebruik: node verify-corib-contract.mjs file.osmd.svg […]"
    );
    process.exit(2);
  }
  const browser = await puppeteer.launch({
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
  });
  let failed = 0;
  try {
    for (const arg of args) {
      const p = path.resolve(arg);
      if (!fs.existsSync(p)) {
        console.error(`FAIL\t${p}\tbestand ontbreekt`);
        failed++;
        continue;
      }
      const r = await checkSvg(browser, p);
      if (r.ok) {
        console.log(
          `PASS\t${path.basename(p)}\tlyrics=${r.nLyrics}\tnums=${r.nums.join(",")}\tminGap=${r.minLyricGap}`
        );
      } else {
        failed++;
        console.error(`FAIL\t${path.basename(p)}\t${r.errors.join(" | ")}`);
      }
    }
  } finally {
    await browser.close();
  }
  process.exit(failed ? 1 : 0);
}

main().catch((err) => {
  console.error(err && err.stack ? err.stack : err);
  process.exit(1);
});
