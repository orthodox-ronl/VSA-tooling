/**
 * Contract-check op OSMD-SVG (CoriB):
 * - geen lyric-overlap (mscz-leesbaarheid §2 / P3a)
 * - maatnummers alleen aan systeembegin (S10)
 * - maatnummer 1 aanwezig (S10)
 * - @tekst-cues (indien aanwezig): binnen maatstrepen (C6/S15);
 *   wrap op ``...`` als twee regels óf één regel die past (S19 / §4.2)
 * - S21: eerste zichtbare nootkoppen SA↔TB per maat-id in één kolom
 * - lyrics horen bij een nootkolom (geen «Heer» boven lege balk na centreren)
 * - melisma-slur (leesbaarheid S2): boog-uiteinden dicht bij stem-ankers
 *   (A/T nootkoprand; S/B stokpunt) met zelfde stem links/rechts
 * - L4: lange melisma-gaps (met slur) hebben extender-dashes
 * - L2: lyrics in Source Sans 3 (≥12.5 px)
 * - C7: eenregel-``@tekst`` deelt baseline met regel 2 van twee-regelige cues
 *   (zelfde systeem-y-band)
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

// P3a / alleluia-8: woordgrens «ia,|Al» moet zichtbaar wit houden.
const MIN_LYRIC_GAP_PX = 12;
const MID_SYSTEM_X_SLACK = 40;
const S21_COLUMN_SLACK_PX = 3;
const LYRIC_NOTE_SLACK_PX = 28;
const SLUR_NOTE_SLACK_PX = 26;

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
      (minGap, midSlack, s21Slack, lyricNoteSlack, slurNoteSlack) => {
        const root = document.querySelector("svg");
        if (!root) return { ok: false, errors: ["geen <svg>"] };

        // Screen-rects: getBBox onderschat glyph-ink (alleluia-8 «iaAl»).
        const lyrics = [...root.querySelectorAll(".vf-text.lyrics")]
          .map((g) => {
            const t = g.querySelector("text");
            if (!t) return null;
            const b = g.getBoundingClientRect();
            if (!(b.width > 0)) return null;
            return {
              t: t.textContent,
              x: b.left,
              y: b.top,
              r: b.right,
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

        // Leesbaarheid S2: boog-uiteinden dicht bij stem-ankers; start/eind
        // zelfde stem (A/T nootkoprand, S/B stokpunt).
        const slurFails = [];
        function noteAnchors() {
          const out = [];
          for (const n of root.querySelectorAll(".vf-stavenote")) {
            if (n.getAttribute("data-osmd-spacer") === "1") continue;
            const breve = n.getAttribute("data-osmd-breve") === "1";
            const head = breve
              ? n.querySelector("[data-osmd-breve-glyph='1'] path")
              : n.querySelector(".vf-notehead path");
            if (!head) continue;
            const st = getComputedStyle(head);
            if (st.visibility === "hidden" || st.display === "none") {
              continue;
            }
            const hr = head.getBoundingClientRect();
            if (!(hr.width > 0.5)) continue;
            const stem = n.querySelector(".vf-stem path");
            let stemUp = null;
            let tip = null;
            if (stem) {
              const sr = stem.getBoundingClientRect();
              stemUp =
                sr.top + sr.height / 2 < hr.top + hr.height / 2;
              tip = stemUp
                ? { x: sr.left + sr.width / 2, y: sr.top }
                : { x: sr.left + sr.width / 2, y: sr.bottom };
            }
            out.push({
              cx: (hr.left + hr.right) / 2,
              cy: (hr.top + hr.bottom) / 2,
              top: hr.top,
              bottom: hr.bottom,
              stemUp,
              tip,
            });
          }
          return out;
        }
        const anchors = noteAnchors();
        function parseCubicEnds(d) {
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
        function screenPt(el, x, y) {
          const ctm = el.getScreenCTM();
          if (!ctm) return null;
          const pt = el.ownerSVGElement.createSVGPoint();
          pt.x = x;
          pt.y = y;
          return pt.matrixTransform(ctm);
        }
        function nearestAnchor(px, py, preferStemUp, preferCy) {
          let best = null;
          let bd = Infinity;
          for (const a of anchors) {
            const dx = Math.abs(a.cx - px);
            const dy = Math.abs(a.cy - py);
            if (dx > 55) continue;
            let score = dx + dy * 0.35;
            if (preferStemUp != null && a.stemUp != null) {
              if (a.stemUp !== preferStemUp) score += 40;
            } else if (preferCy != null) {
              score += Math.abs(a.cy - preferCy) * 0.6;
            }
            if (score < bd) {
              bd = score;
              best = a;
            }
          }
          return best;
        }
        for (const g of root.querySelectorAll(".vf-curve")) {
          const pathEl = g.querySelector("path");
          if (!pathEl) continue;
          const ends = parseCubicEnds(pathEl.getAttribute("d") || "");
          if (!ends) continue;
          const left = screenPt(pathEl, ends.x0, ends.y0);
          const right = screenPt(pathEl, ends.x3, ends.y3);
          if (!left || !right || Math.abs(right.x - left.x) < 24) continue;
          const s = nearestAnchor(left.x, left.y, null, null);
          if (!s) continue;
          const e = nearestAnchor(
            right.x,
            right.y,
            s.stemUp,
            s.cy
          );
          if (!e) continue;
          // S/T (stok omhoog): anker = stokpunt óf kop-top ( dichtst bij pad).
          // A/B (stok omlaag): anker = stokpunt óf kop-bodem.
          function expectY(a, yRef) {
            const cands = [];
            if (a.stemUp === true) {
              cands.push(a.top);
              if (a.tip) cands.push(a.tip.y);
            } else if (a.stemUp === false) {
              cands.push(a.bottom);
              if (a.tip) cands.push(a.tip.y);
            } else {
              cands.push(a.top, a.bottom);
            }
            return cands.reduce((best, y) =>
              Math.abs(y - yRef) < Math.abs(best - yRef) ? y : best
            );
          }
          const sd = Math.hypot(
            s.cx - left.x,
            expectY(s, left.y) - left.y
          );
          const ed = Math.hypot(
            e.cx - right.x,
            expectY(e, right.y) - right.y
          );
          const voiceMismatch =
            s.stemUp != null &&
            e.stemUp != null &&
            s.stemUp !== e.stemUp;
          if (sd > slurNoteSlack || ed > slurNoteSlack || voiceMismatch) {
            slurFails.push(
              `boog@${Math.round(left.x)}–${Math.round(right.x)} Δstart=${
                Math.round(sd)
              } Δend=${Math.round(ed)}${voiceMismatch ? " stem≠" : ""}`
            );
          }
        }
        if (slurFails.length) {
          errors.push(`S2 slur↔anker: ` + slurFails.slice(0, 4).join(" | "));
        }

        // L4 — lange melisma-gap met overlappinge slur: extender-dashes.
        const l4Fails = [];
        const lyricGs = [...root.querySelectorAll(".vf-text.lyrics")].filter(
          (g) => g.querySelector("text") && g.getBoundingClientRect().width > 0
        );
        lyricGs.sort((a, b) => {
          const ra = a.getBoundingClientRect();
          const rb = b.getBoundingClientRect();
          return ra.top - rb.top || ra.left - rb.left;
        });
        const dashGs = [...root.querySelectorAll(".vf-text.dash")];
        const curveBoxes = [...root.querySelectorAll(".vf-curve")].map((g) =>
          g.getBoundingClientRect()
        );
        for (let i = 0; i + 1 < lyricGs.length; i += 1) {
          const ar = lyricGs[i].getBoundingClientRect();
          const br = lyricGs[i + 1].getBoundingClientRect();
          if (Math.abs(ar.top - br.top) > 28) continue;
          const aT = String(
            lyricGs[i].querySelector("text")?.textContent || ""
          ).trim();
          const bT = String(
            lyricGs[i + 1].querySelector("text")?.textContent || ""
          ).trim();
          const wordBoundary =
            /[,.;:!?]$/.test(aT) ||
            (/^[A-ZÀ-ÖØ-Þ]/.test(bT) && !/-$/.test(aT));
          if (wordBoundary) continue;
          const gap = br.left - ar.right;
          if (gap < 72) continue;
          const midY = (ar.top + ar.bottom) / 2;
          const slurHits = curveBoxes.some((c) => {
            if (!(c.width > 40)) return false;
            if (Math.abs((c.top + c.bottom) / 2 - midY) > 120) return false;
            const overlap =
              Math.min(c.right, br.left) - Math.max(c.left, ar.right);
            return overlap > Math.min(60, gap * 0.25);
          });
          if (!slurHits) continue;
          const dashes = dashGs.filter((d) => {
            const r = d.getBoundingClientRect();
            if (!(r.width > 0)) return false;
            if (Math.abs(r.top - ar.top) > 28) return false;
            const cx = (r.left + r.right) / 2;
            return cx > ar.right && cx < br.left;
          });
          const need = Math.max(2, Math.floor(gap / 40));
          if (dashes.length < need) {
            l4Fails.push(
              `«${aT}…${bT}» gap=${Math.round(gap)} dashes=${dashes.length}<${need}`
            );
          }
        }
        if (l4Fails.length) {
          errors.push(`L4 extender: ` + l4Fails.slice(0, 4).join(" | "));
        }

        // L2 — Source Sans 3 op lyrics (leesbaarheid).
        const lyricFonts = [
          ...root.querySelectorAll(".vf-text.lyrics text"),
        ];
        let badFont = 0;
        for (const t of lyricFonts) {
          const ff = String(t.getAttribute("font-family") || "");
          const fs = parseFloat(t.getAttribute("font-size"));
          if (!/Source Sans 3/i.test(ff)) {
            badFont += 1;
          } else if (Number.isFinite(fs) && fs < 14) {
            badFont += 1;
          }
        }
        if (lyricFonts.length && badFont > lyricFonts.length * 0.2) {
          errors.push(
            `L2 font: ${badFont}/${lyricFonts.length} lyrics niet Source Sans 3 ≥14px (OSMD-SVG)`
          );
        }

        // C7 — eenregel-cue-baseline ≈ regel-2 van twee-regelige cues
        // in dezelfde y-band (boven de balk).
        const cueLike = [...root.querySelectorAll("text")]
          .map((t) => {
            const s = String(t.textContent || "").trim();
            if (!(/^P:/.test(s) || s.startsWith("..."))) return null;
            let b;
            try {
              b = t.getBBox();
            } catch {
              return null;
            }
            return { s, y: b.y, bottom: b.y + b.height, x: b.x };
          })
          .filter(Boolean);
        if (cueLike.length >= 2) {
          // Cluster op y-band (~systeem).
          const bands = [];
          const sorted = [...cueLike].sort((a, b) => a.y - b.y);
          for (const c of sorted) {
            let band = bands.find((b) => Math.abs(b.y0 - c.y) < 80);
            if (!band) {
              band = { y0: c.y, items: [] };
              bands.push(band);
            }
            band.items.push(c);
          }
          const C7_SLACK = 10;
          for (const band of bands) {
            const items = band.items;
            // Twee-regel: paar met Δy in [14, 30] en overlappende x.
            let line2Bottom = null;
            for (let i = 0; i < items.length; i += 1) {
              for (let j = i + 1; j < items.length; j += 1) {
                const dy = Math.abs(items[i].y - items[j].y);
                if (dy < 14 || dy > 32) continue;
                if (Math.abs(items[i].x - items[j].x) > 40) continue;
                const lower =
                  items[i].bottom > items[j].bottom ? items[i] : items[j];
                line2Bottom = lower.bottom;
              }
            }
            if (line2Bottom == null) continue;
            // Eenregel: geen partner in Δy-band; bottom ≈ line2.
            for (const c of items) {
              const hasPartner = items.some(
                (o) =>
                  o !== c &&
                  Math.abs(o.y - c.y) >= 14 &&
                  Math.abs(o.y - c.y) <= 32 &&
                  Math.abs(o.x - c.x) < 40
              );
              if (hasPartner) continue;
              // Lange één-regel (of gecollapte twee-regel).
              if (c.s.length < 12 && !c.s.startsWith("...")) continue;
              if (Math.abs(c.bottom - line2Bottom) > C7_SLACK) {
                errors.push(
                  `C7 baseline: «${c.s.slice(0, 28)}» Δ=${Math.round(
                    c.bottom - line2Bottom
                  )}px t.o.v. regel-2`
                );
                break;
              }
            }
          }
        }

        // M11 — hulplijn horizontaal bij nootkop (id …ledgers ↔ …stavenote).
        const LEDGER_SLACK_PX = 8;
        let ledgerBad = 0;
        let ledgerChecked = 0;
        for (const led of root.querySelectorAll(".vf-ledgers")) {
          const id = String(led.id || "");
          if (!id.endsWith("ledgers")) continue;
          const noteId = id.slice(0, -"ledgers".length);
          const note = noteId ? root.getElementById(noteId) : null;
          if (!note) continue;
          const lr = led.getBoundingClientRect();
          const nr = note.getBoundingClientRect();
          if (!(lr.width > 2 && nr.width > 2)) continue;
          ledgerChecked += 1;
          const lmid = (lr.left + lr.right) / 2;
          const nmid = (nr.left + nr.right) / 2;
          if (Math.abs(lmid - nmid) > LEDGER_SLACK_PX) {
            ledgerBad += 1;
          }
        }
        if (ledgerChecked >= 3 && ledgerBad > 0) {
          errors.push(
            `M11 ledger↔noot: ${ledgerBad}/${ledgerChecked} hulplijnen niet op nootkop (slack ${LEDGER_SLACK_PX}px)`
          );
        }

        // S5 — SA/TB-bogen in het balkgat: niet diep door lyrics; niet kruisen.
        const staffBands = [];
        for (const el of root.querySelectorAll(".staffline")) {
          const tops = [];
          const bots = [];
          for (const p of el.querySelectorAll("path")) {
            const d = p.getAttribute("d") || "";
            const m = d.match(/^M([-\d.]+) ([-\d.]+)L([-\d.]+) ([-\d.]+)$/);
            if (!m) continue;
            if (Math.abs(Number(m[2]) - Number(m[4])) > 0.2) continue;
            if (Number(m[3]) - Number(m[1]) < 200) continue;
            const r = p.getBoundingClientRect();
            if (!(r.width > 50)) continue;
            tops.push(r.top);
            bots.push(r.bottom);
          }
          if (tops.length >= 4) {
            staffBands.push({
              top: Math.min(...tops),
              bottom: Math.max(...bots),
            });
          }
        }
        staffBands.sort((a, b) => a.top - b.top);
        const MAX_SLUR_OUT = 22;
        for (let si = 0; si + 1 < staffBands.length; si += 2) {
          const treble = staffBands[si];
          const bass = staffBands[si + 1];
          const gapMid = (treble.bottom + bass.top) / 2;
          const upper = [];
          const lower = [];
          for (const p of root.querySelectorAll("path")) {
            const d = p.getAttribute("d") || "";
            if (!/[Cc]/.test(d)) continue;
            const r = p.getBoundingClientRect();
            if (!(r.width > 40 && r.height > 4 && r.height < 90)) continue;
            if (r.bottom <= treble.bottom - 2) continue;
            if (r.top >= bass.top + 2) continue;
            const midY = (r.top + r.bottom) / 2;
            if (midY < gapMid) {
              upper.push(r);
              if (r.bottom > treble.bottom + MAX_SLUR_OUT) {
                errors.push(
                  `S5 alto-boog steekt ${Math.round(
                    r.bottom - treble.bottom
                  )}px onder SA (max ${MAX_SLUR_OUT})`
                );
                break;
              }
            } else {
              lower.push(r);
              if (r.top < bass.top - MAX_SLUR_OUT) {
                errors.push(
                  `S5 tenor-boog steekt ${Math.round(
                    bass.top - r.top
                  )}px boven TB (max ${MAX_SLUR_OUT})`
                );
                break;
              }
            }
          }
          // Kruising: upper.bottom > lower.top in overlappende x.
          outer: for (const u of upper) {
            for (const l of lower) {
              if (u.right < l.left || l.right < u.left) continue;
              if (u.bottom > l.top + 2) {
                errors.push(
                  `S5 SA/TB-bogen kruisen in balkgat (overlap ${Math.round(
                    u.bottom - l.top
                  )}px)`
                );
                break outer;
              }
            }
          }
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
      LYRIC_NOTE_SLACK_PX,
      SLUR_NOTE_SLACK_PX
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
