/**
 * Contract-check op OSMD-SVG (CoriB):
 * - geen lyric-overlap (mscz-leesbaarheid §2 / P3a)
 * - maatnummers alleen aan systeembegin (S10)
 * - maatnummer 1 aanwezig (S10)
 * - @tekst-cues (indien aanwezig): binnen maatstrepen (C6/S15);
 *   wrap op ``...`` als twee regels óf één regel die past (S19 / §4.2)
 * - S21: eerste zichtbare nootkoppen SA↔TB per maat-id in één kolom
 * - lyrics horen bij een nootkolom (geen «Heer» boven lege balk na centreren)
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
const S21_COLUMN_SLACK_PX = 3;
const LYRIC_NOTE_SLACK_PX = 28;

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
      (minGap, midSlack, s21Slack, lyricNoteSlack) => {
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

        // Cues (P: … / …): bbox mag niet voorbij de maatstreep van de
        // dichtstbijzijnde treble-maat (C6 / S15).
        const byId = {};
        for (const m of root.querySelectorAll(".vf-measure[id]")) {
          const id = String(m.id || "").trim();
          if (!/^\d+$/.test(id)) continue;
          let b;
          try {
            b = m.getBBox();
          } catch {
            continue;
          }
          if (!byId[id] || b.y < byId[id].y) {
            byId[id] = { id, x: b.x, y: b.y, r: b.x + b.width };
          }
        }
        const measures = Object.values(byId).sort(
          (a, b) => Number(a.id) - Number(b.id)
        );
        const cueOverflow = [];
        const cueTexts = [...root.querySelectorAll("text")].filter((t) =>
          /^(P:|\.\.\.)/.test(String(t.textContent || "").trim())
        );
        const seenCue = new Set();
        for (const t of cueTexts) {
          const s = String(t.textContent || "").trim();
          let b;
          try {
            b = t.getBBox();
          } catch {
            continue;
          }
          const key = `${s}@${Math.round(b.x)},${Math.round(b.y)}`;
          if (seenCue.has(key)) continue;
          seenCue.add(key);
          // Maat waarin de cue begint (zelfde y-band); anders dichtstbijzijnde
          // linker maatrand — niet centrum (lange cues starten links in m2).
          let best = null;
          for (const m of measures) {
            if (b.y > m.y + 8 || b.y < m.y - 160) continue;
            if (b.x >= m.x - 4 && b.x < m.r - 4) {
              best = m;
              break;
            }
          }
          if (!best) {
            let bestDist = Infinity;
            for (const m of measures) {
              if (b.y > m.y + 8 || b.y < m.y - 160) continue;
              const d = Math.abs(b.x - m.x);
              if (d < bestDist) {
                bestDist = d;
                best = m;
              }
            }
          }
          if (!best) continue;
          const pad = 12;
          if (b.x + b.width > best.r + pad) {
            cueOverflow.push(
              `${s.slice(0, 28)}… m${best.id} (cueR=${Math.round(
                b.x + b.width
              )} maatR=${Math.round(best.r)})`
            );
          }
        }
        // S19 / §4.2: bij `...` in de bron óf wrap (twee DOM-regels) óf
        // één regel die in de maat past (OSMD-inklappen). Losse `...`-
        // regel zonder bijbehorende eerste regel = fout.
        const cueByMeasure = new Map();
        for (const t of cueTexts) {
          let b;
          try {
            b = t.getBBox();
          } catch {
            continue;
          }
          const s = String(t.textContent || "").trim();
          let mid = null;
          for (const m of measures) {
            if (b.y > m.y + 8 || b.y < m.y - 160) continue;
            if (b.x >= m.x - 4 && b.x < m.r - 4) {
              mid = m;
              break;
            }
          }
          if (!mid) continue;
          if (!cueByMeasure.has(mid.id)) cueByMeasure.set(mid.id, []);
          cueByMeasure.get(mid.id).push({ s, x: b.x, r: b.x + b.width });
        }
        const wrapFails = [];
        for (const [mid, parts] of cueByMeasure) {
          const uniq = [];
          const seen = new Set();
          for (const p of parts) {
            const k = p.s;
            if (seen.has(k)) continue;
            seen.add(k);
            uniq.push(p);
          }
          const hasEllipsisLine = uniq.some((p) => p.s.startsWith("..."));
          const hasInlineEllipsis = uniq.some(
            (p) => p.s.includes("...") && !p.s.startsWith("...")
          );
          const hasLead = uniq.some(
            (p) => p.s.startsWith("P:") && !p.s.includes("...")
          );
          if (hasEllipsisLine && !hasLead && !hasInlineEllipsis) {
            wrapFails.push(`m${mid}: '...'-regel zonder eerste regel`);
          }
          if (hasInlineEllipsis) {
            const m = measures.find((x) => x.id === mid);
            const long = uniq.find(
              (p) => p.s.includes("...") && !p.s.startsWith("...")
            );
            if (m && long && long.r > m.r + 12) {
              wrapFails.push(
                `m${mid}: ingeklapte cue past niet (cueR=${Math.round(
                  long.r
                )} maatR=${Math.round(m.r)})`
              );
            }
          }
        }

        // S21: per maat-id eerste zichtbare nootkoppen op alle balken
        // (SA/TB) delen ongeveer dezelfde scherm-x (één kolom).
        const s21Fails = [];
        const measuresById = {};
        for (const m of root.querySelectorAll(".vf-measure[id]")) {
          const id = String(m.id || "").trim();
          if (!/^\d+$/.test(id)) continue;
          if (!measuresById[id]) measuresById[id] = [];
          measuresById[id].push(m);
        }
        function firstVisibleHeadX(measureEl) {
          const notes = [...measureEl.querySelectorAll(".vf-stavenote")];
          let best = null;
          for (const n of notes) {
            // Alleen noteheads (geen stem/accidental) — anders valse Δx.
            const heads = n.querySelectorAll(".vf-notehead path");
            const paths = heads.length
              ? heads
              : n.querySelectorAll("[data-osmd-breve-glyph='1'] path");
            for (const p of paths) {
              const st = getComputedStyle(p);
              if (st.visibility === "hidden" || st.display === "none") {
                continue;
              }
              let bb;
              try {
                bb = p.getBBox();
              } catch {
                continue;
              }
              if (!(bb.width > 0.5 && bb.height > 0.5)) continue;
              const ctm = p.getScreenCTM();
              if (!ctm) continue;
              const pt = p.ownerSVGElement.createSVGPoint();
              pt.x = bb.x;
              pt.y = bb.y;
              const screen = pt.matrixTransform(ctm);
              if (best == null || screen.x < best) best = screen.x;
            }
          }
          return best;
        }
        for (const [id, els] of Object.entries(measuresById)) {
          if (els.length < 2) continue;
          const xs = els
            .map(firstVisibleHeadX)
            .filter((x) => Number.isFinite(x));
          if (xs.length < 2) continue;
          const lo = Math.min(...xs);
          const hi = Math.max(...xs);
          if (hi - lo > s21Slack) {
            s21Fails.push(
              `m${id}: Δx=${Math.round((hi - lo) * 10) / 10}px`
            );
          }
        }

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
        if (cueOverflow.length) {
          errors.push(
            `C6 cue buiten maat: ` + cueOverflow.slice(0, 4).join(" | ")
          );
        }
        if (wrapFails.length) {
          errors.push(`S19/§4.2 wrap: ` + wrapFails.slice(0, 4).join(" | "));
        }
        if (s21Fails.length) {
          errors.push(
            `S21 stemkolom: ` + s21Fails.slice(0, 6).join(" | ")
          );
        }

        // Lyrics ↔ dichtstbijzijnde noot-/spacer-kolom. S8-spacers kort
        // zichtbaar maken voor getBBox (anders 0×0).
        const noteCols = [];
        for (const n of root.querySelectorAll(".vf-stavenote")) {
          const spacer = n.getAttribute("data-osmd-spacer") === "1";
          const breve = n.getAttribute("data-osmd-breve") === "1";
          const restored = [];
          if (spacer) {
            n.querySelectorAll("g, path").forEach((el) => {
              const cs = getComputedStyle(el);
              if (cs.visibility !== "hidden" && cs.display !== "none") {
                return;
              }
              restored.push([
                el,
                el.getAttribute("visibility"),
                el.getAttribute("display"),
                el.style.visibility,
                el.style.display,
              ]);
              el.setAttribute("visibility", "visible");
              el.removeAttribute("display");
              el.style.visibility = "visible";
              el.style.display = "";
            });
          }
          try {
            if (spacer) {
              const bb = n.getBBox();
              const ctm = n.getScreenCTM();
              if (ctm && bb.width + bb.height > 0) {
                const pt = n.ownerSVGElement.createSVGPoint();
                pt.x = bb.x + bb.width / 2;
                pt.y = bb.y;
                noteCols.push(pt.matrixTransform(ctm).x);
              }
            } else {
              const paths = breve
                ? n.querySelectorAll("[data-osmd-breve-glyph='1'] path")
                : n.querySelectorAll(".vf-notehead path");
              for (const p of paths) {
                const st = getComputedStyle(p);
                if (st.visibility === "hidden" || st.display === "none") {
                  continue;
                }
                let bb;
                try {
                  bb = p.getBBox();
                } catch {
                  continue;
                }
                const ctm = p.getScreenCTM();
                if (!ctm) continue;
                const pt = p.ownerSVGElement.createSVGPoint();
                pt.x = bb.x + bb.width / 2;
                pt.y = bb.y;
                noteCols.push(pt.matrixTransform(ctm).x);
              }
            }
          } finally {
            for (const [el, vis, disp, sVis, sDisp] of restored) {
              if (vis == null) el.removeAttribute("visibility");
              else el.setAttribute("visibility", vis);
              if (disp == null) el.removeAttribute("display");
              else el.setAttribute("display", disp);
              el.style.visibility = sVis;
              el.style.display = sDisp;
            }
          }
        }
        noteCols.sort((a, b) => a - b);
        const uniqCols = [];
        for (const x of noteCols) {
          if (
            !uniqCols.length ||
            Math.abs(x - uniqCols[uniqCols.length - 1]) > 5
          ) {
            uniqCols.push(x);
          }
        }
        const lyricNoteFails = [];
        for (const t of root.querySelectorAll(
          ".vf-text.lyrics text, g.vf-text.lyrics text"
        )) {
          const s = String(t.textContent || "").trim();
          if (!s || s === "-" || s === "–") continue;
          let bb;
          try {
            bb = t.getBBox();
          } catch {
            continue;
          }
          const ctm = t.getScreenCTM();
          if (!ctm) continue;
          const pt = t.ownerSVGElement.createSVGPoint();
          pt.x = bb.x + bb.width / 2;
          pt.y = bb.y;
          const sx = pt.matrixTransform(ctm).x;
          let best = Infinity;
          for (const cx of uniqCols) {
            best = Math.min(best, Math.abs(cx - sx));
          }
          if (best > lyricNoteSlack) {
            lyricNoteFails.push(
              `${s}@${Math.round(sx)} Δ=${Math.round(best)}`
            );
          }
        }
        if (lyricNoteFails.length) {
          errors.push(
            `lyric↔noot: ` + lyricNoteFails.slice(0, 6).join(", ")
          );
        }

        return {
          ok: errors.length === 0,
          errors,
          nLyrics: lyrics.length,
          nNums: nums.length,
          nums: nums.map((n) => n.n),
          nCues: seenCue.size,
          minLyricGap: Number.isFinite(minLyricGap)
            ? Math.round(minLyricGap * 10) / 10
            : null,
        };
      },
      MIN_LYRIC_GAP_PX,
      MID_SYSTEM_X_SLACK,
      S21_COLUMN_SLACK_PX,
      LYRIC_NOTE_SLACK_PX
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
          `PASS\t${path.basename(p)}\tlyrics=${r.nLyrics}\tcues=${r.nCues}\tnums=${r.nums.join(",")}\tminGap=${r.minLyricGap}`
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
