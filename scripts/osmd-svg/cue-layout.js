/**
 * Cue-layout voor headless OSMD (schermpartituur §4.2 / S15 / S19 / C6 / C7).
 *
 * Port van bibliotheek ``score-osmd.js`` (applyInitialWidthFactors,
 * redistribute, collapse wrap, layoutCues, centerMeasureContents) — zodat
 * ``mvsa svg --engine osmd`` dezelfde cue-contracten haalt als de site.
 *
 * - ``...`` blijft wrap (twee regels); inklappen naar één regel alleen als
 *   die ene regel in de maat past.
 * - Maatbreedte via SourceMeasure.WidthFactor zodat de cue binnen de
 *   maatstrepen past (C6-intentie voor OSMD; MusicXML ``width`` negeert OSMD).
 * - Cue X op eerste noot van de maat; niet meeschuiven bij centreren.
 * - C7: eenregelige cues delen baseline met regel 2 van twee-regelige cues.
 * - S22 / P3e: lettergreep-slot (nootkolom + lyric) centreren in de slot-ruimte.
 */
(function (global) {
  var CUE_GAP_PX = 10;
  var CUE_LINE_PX = 22;

  function textContentTrim(el) {
    return String(el.textContent || "").trim();
  }

  function cueTextsPerMeasure(xmlText) {
    var doc = new DOMParser().parseFromString(xmlText, "application/xml");
    var part = doc.querySelector("part");
    if (!part) {
      return [];
    }
    return Array.prototype.map.call(
      part.querySelectorAll(":scope > measure"),
      function (m) {
        var w = m.querySelector("direction-type words");
        return w ? String(w.textContent || "").trim() : null;
      }
    );
  }

  function cueLines(text) {
    return String(text || "")
      .split(/\r?\n/)
      .map(function (s) {
        return s.trim();
      })
      .filter(Boolean);
  }

  function maxCueLineLen(text) {
    var lines = cueLines(text);
    var max = 0;
    for (var i = 0; i < lines.length; i += 1) {
      if (lines[i].length > max) {
        max = lines[i].length;
      }
    }
    return max;
  }

  /**
   * Eén layout-slot per maatnummer (treble), stabiel bij compacte
   * CoriB-afstanden (geen y-systeemdrempel — die mengt systemen).
   */
  function measureLayout(mount) {
    var byId = {};
    Array.prototype.forEach.call(
      mount.querySelectorAll(".vf-measure[id]"),
      function (m) {
        var id = String(m.id || "").trim();
        if (!/^\d+$/.test(id)) {
          return;
        }
        var b;
        try {
          b = m.getBBox();
        } catch (e) {
          return;
        }
        var n0 = m.querySelector(".vf-stavenote");
        var nb = null;
        try {
          nb = n0 ? n0.getBBox() : null;
        } catch (e2) {
          nb = null;
        }
        var entry = {
          id: Number(id),
          x: b.x,
          y: b.y,
          w: b.width,
          firstX: nb ? nb.x : b.x + 20,
        };
        if (!byId[id] || entry.y < byId[id].y) {
          byId[id] = entry;
        }
      }
    );
    var ids = Object.keys(byId)
      .map(Number)
      .sort(function (a, b) {
        return a - b;
      });
    var firstXs = [];
    var staffTops = [];
    var lefts = [];
    var rights = [];
    for (var i = 0; i < ids.length; i += 1) {
      var mm = byId[String(ids[i])];
      firstXs.push(mm.firstX);
      staffTops.push(mm.y);
      lefts.push(mm.x);
      rights.push(mm.x + mm.w);
    }
    return {
      firstXs: firstXs,
      staffTops: staffTops,
      lefts: lefts,
      rights: rights,
    };
  }

  function applyInitialWidthFactors(osmd, xmlText) {
    var cues = cueTextsPerMeasure(xmlText);
    var sms = osmd.Sheet && osmd.Sheet.SourceMeasures;
    if (!sms) {
      return;
    }
    // Zonder cue: factor 1.0 (niet 0.9 — dat kneep S8-recite-lyrics).
    // Ruimte voor cues komt uit redistributeForOverflow.
    for (var i = 0; i < sms.length; i += 1) {
      var f = 1.0;
      if (cues[i]) {
        var len = maxCueLineLen(cues[i]);
        f = Math.min(1.28, 1.0 + len * 0.012);
      }
      sms[i].widthFactor = f;
      sms[i].WidthFactor = f;
    }
  }

  function measureTextWidth(svg, sampleEl, text) {
    var probe = sampleEl.cloneNode(false);
    probe.textContent = text;
    probe.setAttribute("x", "0");
    probe.setAttribute("y", "0");
    svg.appendChild(probe);
    var w = 0;
    try {
      w = probe.getBBox().width;
    } catch (e) {
      w = text.length * 7.5;
    }
    svg.removeChild(probe);
    return w;
  }

  function cueExtent(mount, cueText, staffTop) {
    var lines = cueLines(cueText);
    var matchTexts = lines.length === 1 ? [cueText] : lines;
    var allText = mount.querySelectorAll("text");
    var left = Infinity;
    var right = -Infinity;
    for (var li = 0; li < matchTexts.length; li += 1) {
      for (var i = 0; i < allText.length; i += 1) {
        if (textContentTrim(allText[i]) !== matchTexts[li]) {
          continue;
        }
        var b = allText[i].getBBox();
        if (b.y > staffTop + 8 || b.y < staffTop - 160) {
          continue;
        }
        left = Math.min(left, b.x);
        right = Math.max(right, b.x + b.width);
      }
    }
    if (!(right > left)) {
      return null;
    }
    return { left: left, right: right };
  }

  function redistributeForOverflow(osmd, mount, xmlText) {
    var cues = cueTextsPerMeasure(xmlText);
    var layout = measureLayout(mount);
    var sms = osmd.Sheet && osmd.Sheet.SourceMeasures;
    if (!sms || !layout.rights.length) {
      return false;
    }
    var bumped = false;
    var pad = 8;

    for (var mi = 0; mi < cues.length && mi < layout.rights.length; mi += 1) {
      if (!cues[mi]) {
        continue;
      }
      var ext = cueExtent(mount, cues[mi], layout.staffTops[mi]);
      if (!ext) {
        continue;
      }
      var mRight = layout.rights[mi];
      var mLeft = layout.lefts[mi];
      var overflow = ext.right - (mRight - pad);
      if (overflow <= 0) {
        continue;
      }
      var mWidth = Math.max(mRight - mLeft, 50);
      var grow = Math.min(1.28, 1 + overflow / mWidth);
      var cur = sms[mi].widthFactor || 1;
      var next = Math.min(1.4, cur * Math.max(grow, 1.1));
      if (next > cur + 0.03) {
        sms[mi].widthFactor = next;
        sms[mi].WidthFactor = next;
        bumped = true;
      }
      var st = layout.staffTops[mi];
      for (var j = 0; j < layout.staffTops.length; j += 1) {
        if (j === mi || cues[j]) {
          continue;
        }
        if (Math.abs(layout.staffTops[j] - st) > 40) {
          continue;
        }
        var sj = sms[j].widthFactor || 1;
        var reduced = Math.max(0.72, sj * 0.9);
        if (reduced < sj - 0.02) {
          sms[j].widthFactor = reduced;
          sms[j].WidthFactor = reduced;
          bumped = true;
        }
      }
    }
    return bumped;
  }

  function collapseWrappedCuesIfTheyFit(mount, xmlText) {
    var svg = mount.querySelector("svg");
    if (!svg) {
      return;
    }
    var cues = cueTextsPerMeasure(xmlText);
    var layout = measureLayout(mount);
    var allText = Array.prototype.slice.call(mount.querySelectorAll("text"));

    for (var mi = 0; mi < cues.length && mi < layout.rights.length; mi += 1) {
      if (!cues[mi]) {
        continue;
      }
      var lines = cueLines(cues[mi]);
      if (lines.length < 2) {
        continue;
      }
      var single = lines.join(" ");
      var staffTop = layout.staffTops[mi];
      var targetX = Math.max(layout.firstXs[mi], layout.lefts[mi] + 4);
      var maxW = layout.rights[mi] - targetX - 8;
      if (!(maxW > 20)) {
        continue;
      }

      var tops = [];
      var bottoms = [];
      for (var i = 0; i < allText.length; i += 1) {
        var el = allText[i];
        var s = textContentTrim(el);
        var b;
        try {
          b = el.getBBox();
        } catch (e) {
          continue;
        }
        if (b.y > staffTop + 8 || b.y < staffTop - 160) {
          continue;
        }
        if (s === lines[0]) {
          tops.push(el);
        } else if (lines.indexOf(s) > 0) {
          bottoms.push(el);
        }
      }
      if (!tops.length || !bottoms.length) {
        continue;
      }

      var sample = tops[0];
      var needW = measureTextWidth(svg, sample, single);
      if (needW > maxW) {
        continue;
      }

      var keeper = bottoms[0];
      for (var bi = 1; bi < bottoms.length; bi += 1) {
        if (bottoms[bi].getBBox().y > keeper.getBBox().y) {
          keeper = bottoms[bi];
        }
      }
      keeper.textContent = single;
      for (var k = 0; k < allText.length; k += 1) {
        var el3 = allText[k];
        if (el3 === keeper || !el3.parentNode) {
          continue;
        }
        var s3 = textContentTrim(el3);
        var b3;
        try {
          b3 = el3.getBBox();
        } catch (e3) {
          continue;
        }
        if (b3.y > staffTop + 8 || b3.y < staffTop - 160) {
          continue;
        }
        if (s3 === single || s3 === lines[0] || lines.indexOf(s3) > 0) {
          el3.parentNode.removeChild(el3);
        }
      }

      var yAttr = parseFloat(keeper.getAttribute("y"));
      var box = keeper.getBBox();
      if (isFinite(yAttr)) {
        var targetBottom = staffTop - CUE_GAP_PX;
        keeper.setAttribute("x", String(targetX));
        keeper.setAttribute(
          "y",
          String(yAttr + (targetBottom - (box.y + box.height)))
        );
      }
    }
  }

  function resolveCueOverlaps(mount, cues, layout) {
    var allText = Array.prototype.slice.call(mount.querySelectorAll("text"));
    var placed = [];
    for (var mi = 0; mi < cues.length; mi += 1) {
      if (!cues[mi] || mi >= layout.staffTops.length) {
        continue;
      }
      var lines = cueLines(cues[mi]);
      if (!lines.length) {
        continue;
      }
      var staffTop = layout.staffTops[mi];
      var els = allText.filter(function (t) {
        if (textContentTrim(t) !== lines[0]) {
          return false;
        }
        var b = t.getBBox();
        return b.y <= staffTop + 8 && b.y >= staffTop - 160;
      });
      if (!els.length) {
        continue;
      }
      var el = els[0];
      var box = el.getBBox();
      var x0 = box.x;
      for (var p = 0; p < placed.length; p += 1) {
        var prev = placed[p];
        if (Math.abs(prev.staffTop - staffTop) > 40) {
          continue;
        }
        if (
          x0 < prev.right + 8 &&
          box.y < prev.bottom + 4 &&
          box.y + box.height > prev.top - 4
        ) {
          x0 = prev.right + 8;
        }
      }
      var maxX = layout.rights[mi] - 8 - box.width;
      if (maxX < layout.lefts[mi] + 4) {
        maxX = layout.lefts[mi] + 4;
      }
      if (x0 > maxX) {
        x0 = maxX;
      }
      var dx = x0 - box.x;
      if (Math.abs(dx) > 0.5) {
        for (var li = 0; li < lines.length; li += 1) {
          for (var j = 0; j < allText.length; j += 1) {
            var t = allText[j];
            if (textContentTrim(t) !== lines[li]) {
              continue;
            }
            var tb = t.getBBox();
            if (tb.y > staffTop + 8 || tb.y < staffTop - 160) {
              continue;
            }
            var xa = parseFloat(t.getAttribute("x"));
            if (!isFinite(xa)) {
              continue;
            }
            t.setAttribute("x", String(xa + dx));
          }
        }
        box = el.getBBox();
      }
      placed.push({
        staffTop: staffTop,
        right: box.x + box.width,
        top: box.y,
        bottom: box.y + box.height,
      });
    }
  }

  function layoutCues(mount, xmlText) {
    var cues = cueTextsPerMeasure(xmlText);
    var layout = measureLayout(mount);
    var firstXs = layout.firstXs;
    var staffTops = layout.staffTops;
    var lefts = layout.lefts;
    if (!cues.length || !firstXs.length) {
      return;
    }
    var allText = Array.prototype.slice.call(mount.querySelectorAll("text"));

    var maxLinesByStaffTop = {};
    for (var mi0 = 0; mi0 < cues.length && mi0 < staffTops.length; mi0 += 1) {
      if (!cues[mi0]) {
        continue;
      }
      var n0 = cueLines(cues[mi0]).length;
      var key0 = String(Math.round(staffTops[mi0]));
      if (!maxLinesByStaffTop[key0] || n0 > maxLinesByStaffTop[key0]) {
        maxLinesByStaffTop[key0] = n0;
      }
    }

    for (var mi = 0; mi < cues.length && mi < firstXs.length; mi += 1) {
      if (!cues[mi]) {
        continue;
      }
      var lines = cueLines(cues[mi]);
      if (!lines.length) {
        continue;
      }
      var targetX = Math.max(firstXs[mi], lefts[mi] + 4);
      var staffTop = staffTops[mi];
      var maxLines = maxLinesByStaffTop[String(Math.round(staffTop))] || 1;
      for (var li = 0; li < lines.length; li += 1) {
        var row = lines.length === 1 ? maxLines - 1 : li;
        var targetGlyphBottom =
          staffTop - CUE_GAP_PX - (maxLines - 1 - row) * CUE_LINE_PX;
        for (var j = 0; j < allText.length; j += 1) {
          var el = allText[j];
          if (textContentTrim(el) !== lines[li]) {
            continue;
          }
          var box;
          try {
            box = el.getBBox();
          } catch (e) {
            continue;
          }
          if (box.y > staffTop + 8 || box.y < staffTop - 160) {
            continue;
          }
          var yAttr = parseFloat(el.getAttribute("y"));
          if (!isFinite(yAttr)) {
            continue;
          }
          el.setAttribute("x", String(targetX));
          el.setAttribute(
            "y",
            String(yAttr + (targetGlyphBottom - (box.y + box.height)))
          );
        }
      }
    }

    resolveCueOverlaps(mount, cues, layout);
  }

  /**
   * Centreer noten+lyrics in de maatbreedte. S21: zelfde ``dx`` op alle
   * balken van het maat-id (SA én TB) — nooit alleen de bovenbalk.
   */
  function centerMeasureContents(mount) {
    var byId = {};
    Array.prototype.forEach.call(
      mount.querySelectorAll(".vf-measure[id]"),
      function (m) {
        var id = String(m.id || "").trim();
        if (!/^\d+$/.test(id)) {
          return;
        }
        var b;
        try {
          b = m.getBBox();
        } catch (e) {
          return;
        }
        var clef = m.querySelector(".vf-clef");
        var key = m.querySelector(".vf-keysignature");
        var musicStart = b.x + 6;
        if (clef) {
          try {
            var cb = clef.getBBox();
            musicStart = Math.max(musicStart, cb.x + cb.width + 4);
          } catch (e2) {
            /* keep */
          }
        }
        if (key) {
          try {
            var kb = key.getBBox();
            musicStart = Math.max(musicStart, kb.x + kb.width + 4);
          } catch (e3) {
            /* keep */
          }
        }
        if (!byId[id]) {
          byId[id] = [];
        }
        byId[id].push({
          el: m,
          x: b.x,
          y: b.y,
          musicStart: musicStart,
          right: b.x + b.width,
        });
      }
    );

    var lyricGs = Array.prototype.slice.call(
      mount.querySelectorAll("g.vf-text.lyrics, g.vf-text.dash")
    );

    // Eerst dx per maat-id (S21: zelfde dx op SA én TB), dan pas
    // lyrics/curves toewijzen via dichtstbijzijnde balk — anders claimt
    // de vorige maatkolom met overlapping y-band de slur van de volgende
    // (bijv. «stich» SA-slur dx van m14 i.p.v. m15).
    var columns = [];
    Object.keys(byId)
      .sort(function (a, b) {
        return Number(a) - Number(b);
      })
      .forEach(function (id) {
        var col = byId[id];
        col.sort(function (a, b) {
          return a.y - b.y;
        });
        // Bounds vanaf treble (bovenste); extent over alle balken (S21).
        var treble = col[0];
        var left = treble.musicStart;
        var right = treble.right - 8;
        var cMin = Infinity;
        var cMax = -Infinity;
        for (var c = 0; c < col.length; c += 1) {
          var notes = col[c].el.querySelectorAll(".vf-stavenote");
          for (var n = 0; n < notes.length; n += 1) {
            try {
              var bb = notes[n].getBBox();
              if (!(bb.width > 0 || bb.height > 0)) {
                continue;
              }
              cMin = Math.min(cMin, bb.x);
              cMax = Math.max(cMax, bb.x + bb.width);
            } catch (e) {
              /* skip */
            }
          }
        }
        var staves = [];
        for (var s = 0; s < col.length; s += 1) {
          var sm = col[s];
          var sh = 90;
          try {
            var sb = sm.el.getBBox();
            if (sb.height > 0) {
              sh = sb.height;
            }
          } catch (eStaff) {
            /* default */
          }
          staves.push({
            x: sm.x,
            right: sm.right,
            midY: sm.y + sh / 2,
          });
        }
        var dx = 0;
        if (cMax > cMin) {
          var padL = cMin - left;
          var padR = right - cMax;
          dx = (padR - padL) / 2;
          // Drempel laag genoeg voor S22-achtige maten met weinig restwit
          // (anders blijft de eerste lettergreep links kleven).
          if (padR + padL < 12 || Math.abs(dx) < 3) {
            dx = 0;
          } else {
            if (cMin + dx < left) {
              dx = left - cMin;
            }
            if (cMax + dx > right) {
              dx = right - cMax;
            }
            if (Math.abs(dx) < 3) {
              dx = 0;
            }
          }
        }
        columns.push({
          id: id,
          dx: dx,
          x: treble.x,
          right: treble.right,
          staves: staves,
          els: col,
        });
      });

    function nearestColumnDx(midX, midY) {
      var bestDx = null;
      var bestDist = Infinity;
      for (var i = 0; i < columns.length; i += 1) {
        var col = columns[i];
        if (midX < col.x || midX >= col.right) {
          continue;
        }
        for (var j = 0; j < col.staves.length; j += 1) {
          var st = col.staves[j];
          if (midX < st.x || midX >= st.right) {
            continue;
          }
          var dist = Math.abs(midY - st.midY);
          if (dist < bestDist) {
            bestDist = dist;
            bestDx = col.dx;
          }
        }
      }
      // Geen match verder dan ±1 systeemhoogte (~220 px) — voorkomt
      // dat een boog aan een verre maat hangt.
      if (bestDx === null || bestDist > 220) {
        return null;
      }
      return bestDx;
    }

    function applyDx(el, dx) {
      if (!(Math.abs(dx) >= 3)) {
        return;
      }
      if (el.getAttribute("data-osmd-center") === "1") {
        return;
      }
      var prev = el.getAttribute("transform") || "";
      el.setAttribute(
        "transform",
        (prev ? prev + " " : "") + "translate(" + dx.toFixed(2) + ", 0)"
      );
      el.setAttribute("data-osmd-center", "1");
    }

    for (var ci = 0; ci < columns.length; ci += 1) {
      var column = columns[ci];
      if (!(Math.abs(column.dx) >= 3)) {
        continue;
      }
      for (var c2 = 0; c2 < column.els.length; c2 += 1) {
        var moveEls = column.els[c2].el.querySelectorAll(
          ".vf-stavenote, .vf-ledgers"
        );
        for (var e = 0; e < moveEls.length; e += 1) {
          applyDx(moveEls[e], column.dx);
        }
      }
    }

    // Melisma-slurs / ties (leesbaarheid S2): zelfde dx als noten van de
    // dichtstbijzijnde balk (niet first-wins over losse y-band).
    var curves = mount.querySelectorAll(".vf-curve, .vf-stavetie");
    for (var cj = 0; cj < curves.length; cj += 1) {
      var cg = curves[cj];
      var cb;
      try {
        cb = cg.getBBox();
      } catch (e5) {
        continue;
      }
      var curveDx = nearestColumnDx(
        cb.x + cb.width / 2,
        cb.y + cb.height / 2
      );
      if (curveDx === null) {
        continue;
      }
      applyDx(cg, curveDx);
    }

    for (var li = 0; li < lyricGs.length; li += 1) {
      var g = lyricGs[li];
      var gb;
      try {
        gb = g.getBBox();
      } catch (e4) {
        continue;
      }
      var lyricDx = nearestColumnDx(
        gb.x + gb.width / 2,
        gb.y + gb.height / 2
      );
      if (lyricDx === null) {
        continue;
      }
      applyDx(g, lyricDx);
    }
  }

  function renderAndLayout(osmd, mount, xmlText) {
    osmd.render();
    layoutCues(mount, xmlText);
  }

  /**
   * Volledige cue-pass (schermpartituur §4.2). Aanroepen ná ``osmd.load``,
   * vóór S8 A1-finalize.
   */
  function runCueLayout(osmd, mount, xmlText) {
    if (!osmd || !mount || !xmlText) {
      return;
    }
    applyInitialWidthFactors(osmd, xmlText);
    renderAndLayout(osmd, mount, xmlText);
    for (var pass = 0; pass < 3; pass += 1) {
      if (!redistributeForOverflow(osmd, mount, xmlText)) {
        break;
      }
      renderAndLayout(osmd, mount, xmlText);
    }
    // Maatbreedtes vast → inklappen; cues niet opnieuw layouten (XML-
    // regels bestaan niet meer in de DOM na inklappen). Zelfde volgorde
    // als bibliotheek ``score-osmd.js`` fullLayout.
    collapseWrappedCuesIfTheyFit(mount, xmlText);
    // C7 ná inklappen: eenregel-cues (ook na collapse) op baseline van
    // regel 2 van twee-regelige cues in hetzelfde systeem.
    alignOneLineCueBaselines(mount, xmlText);
    centerMeasureContents(mount);
    // S22 / P3e: per lettergreep-slot nootkolom+lyric centreren.
    centerSyllableSlots(mount);
  }

  /**
   * C7 — eenregelige ``@tekst`` deelt baseline met regel 2 van twee-regelige
   * cues in hetzelfde systeem (ektinia maat 5 t.o.v. «Want van U»).
   */
  function alignOneLineCueBaselines(mount, xmlText) {
    var cues = cueTextsPerMeasure(xmlText);
    var layout = measureLayout(mount);
    if (!cues.length || !layout.staffTops.length) {
      return;
    }
    var allText = Array.prototype.slice.call(mount.querySelectorAll("text"));
    // Per afgeronde staffTop: verzamel cue-glyphs.
    var bands = {};
    for (var mi = 0; mi < cues.length && mi < layout.staffTops.length; mi += 1) {
      if (!cues[mi]) {
        continue;
      }
      var lines = cueLines(cues[mi]);
      if (!lines.length) {
        continue;
      }
      var staffTop = layout.staffTops[mi];
      var key = String(Math.round(staffTop / 40) * 40);
      if (!bands[key]) {
        bands[key] = { staffTop: staffTop, els: [] };
      }
      // Gebruik de laagste staffTop in de band (echte balklijn).
      if (staffTop < bands[key].staffTop) {
        bands[key].staffTop = staffTop;
      }
      for (var li = 0; li < lines.length; li += 1) {
        for (var j = 0; j < allText.length; j += 1) {
          var el = allText[j];
          if (textContentTrim(el) !== lines[li] && textContentTrim(el) !== lines.join(" ")) {
            continue;
          }
          var box;
          try {
            box = el.getBBox();
          } catch (e) {
            continue;
          }
          if (box.y > staffTop + 8 || box.y < staffTop - 160) {
            continue;
          }
          bands[key].els.push({
            el: el,
            box: box,
            lineCount: lines.length,
            isCollapsedSingle: lines.length >= 2 && textContentTrim(el) === lines.join(" "),
          });
        }
      }
    }

    Object.keys(bands).forEach(function (key) {
      var band = bands[key];
      var els = band.els;
      if (!els.length) {
        return;
      }
      // Uniek op element.
      var seen = [];
      var uniq = [];
      for (var i = 0; i < els.length; i += 1) {
        if (seen.indexOf(els[i].el) >= 0) {
          continue;
        }
        seen.push(els[i].el);
        uniq.push(els[i]);
      }
      // Baseline van regel 2 = laagste glyph-bottom onder de cues die tot
      // een twee-regelige cue behoren (of staffTop - gap als fallback).
      var line2Bottom = -Infinity;
      for (var u = 0; u < uniq.length; u += 1) {
        if (uniq[u].lineCount >= 2 && !uniq[u].isCollapsedSingle) {
          line2Bottom = Math.max(
            line2Bottom,
            uniq[u].box.y + uniq[u].box.height
          );
        }
      }
      if (!(line2Bottom > -Infinity)) {
        line2Bottom = band.staffTop - CUE_GAP_PX;
      }
      for (var v = 0; v < uniq.length; v += 1) {
        var item = uniq[v];
        // Eenregel (origineel of na collapse): snap glyph-bottom naar line2.
        if (item.lineCount === 1 || item.isCollapsedSingle) {
          var yAttr = parseFloat(item.el.getAttribute("y"));
          if (!isFinite(yAttr)) {
            continue;
          }
          var curBottom = item.box.y + item.box.height;
          var dy = line2Bottom - curBottom;
          if (Math.abs(dy) < 0.5) {
            continue;
          }
          item.el.setAttribute("y", String(yAttr + dy));
        }
      }
    });
  }

  /**
   * S22 / P3e — per lettergreep-slot: S21-nootkolom + lyric horizontaal
   * centreren in de ruimte tussen vorige en volgende kolom (of maatrand).
   */
  function centerSyllableSlots(mount) {
    var measures = Array.prototype.slice.call(
      mount.querySelectorAll(".vf-measure[id]")
    );
    // Groepeer treble-maten (bovenste per id) als slot-anker.
    var byId = {};
    for (var i = 0; i < measures.length; i += 1) {
      var m = measures[i];
      var id = String(m.id || "").trim();
      if (!/^\d+$/.test(id)) {
        continue;
      }
      var mb;
      try {
        mb = m.getBBox();
      } catch (e) {
        continue;
      }
      if (!byId[id] || mb.y < byId[id].y) {
        byId[id] = { el: m, x: mb.x, y: mb.y, right: mb.x + mb.width, staffs: [] };
      }
    }
    Object.keys(byId).forEach(function (id) {
      byId[id].staffs = measures.filter(function (m) {
        return String(m.id) === id;
      });
    });

    var lyricGs = Array.prototype.slice.call(
      mount.querySelectorAll("g.vf-text.lyrics, g.vf-text.dash")
    );

    Object.keys(byId)
      .sort(function (a, b) {
        return Number(a) - Number(b);
      })
      .forEach(function (id) {
        var info = byId[id];
        // Nootkolommen: cluster mid-x over alle balken van dit maat-id.
        var heads = [];
        for (var s = 0; s < info.staffs.length; s += 1) {
          var notes = info.staffs[s].querySelectorAll(".vf-stavenote");
          for (var n = 0; n < notes.length; n += 1) {
            if (notes[n].getAttribute("data-osmd-spacer") === "1") {
              continue;
            }
            var nb;
            try {
              nb = notes[n].getBBox();
            } catch (e2) {
              continue;
            }
            if (!(nb.width > 0)) {
              continue;
            }
            heads.push({
              el: notes[n],
              mid: nb.x + nb.width / 2,
              x: nb.x,
              right: nb.x + nb.width,
            });
          }
        }
        if (heads.length < 1) {
          return;
        }
        heads.sort(function (a, b) {
          return a.mid - b.mid;
        });
        // Cluster binnen 8 px = één stemkolom.
        var cols = [];
        for (var h = 0; h < heads.length; h += 1) {
          var hd = heads[h];
          var col = cols.length ? cols[cols.length - 1] : null;
          if (!col || Math.abs(hd.mid - col.mid) > 8) {
            col = {
              mid: hd.mid,
              x: hd.x,
              right: hd.right,
              notes: [],
              sum: 0,
              n: 0,
            };
            cols.push(col);
          }
          col.notes.push(hd.el);
          col.x = Math.min(col.x, hd.x);
          col.right = Math.max(col.right, hd.right);
          col.sum += hd.mid;
          col.n += 1;
          col.mid = col.sum / col.n;
        }
        // musicStart: voorbij clef/key in treble.
        var musicStart = info.x + 6;
        var clef = info.el.querySelector(".vf-clef");
        var key = info.el.querySelector(".vf-keysignature");
        try {
          if (clef) {
            var cb = clef.getBBox();
            musicStart = Math.max(musicStart, cb.x + cb.width + 4);
          }
          if (key) {
            var kb = key.getBBox();
            musicStart = Math.max(musicStart, kb.x + kb.width + 4);
          }
        } catch (e3) {
          /* keep */
        }
        var musicEnd = info.right - 8;

        for (var c = 0; c < cols.length; c += 1) {
          var slot = cols[c];
          var leftBound = c === 0 ? musicStart : (cols[c - 1].mid + slot.mid) / 2;
          var rightBound =
            c === cols.length - 1
              ? musicEnd
              : (slot.mid + cols[c + 1].mid) / 2;
          if (!(rightBound > leftBound + 10)) {
            continue;
          }
          // Lyric in deze kolom (zelfde x-band, y tussen SA/TB van deze maat).
          var colY0 = info.y - 20;
          var colY1 = info.y + 280;
          var lyricUnion = null;
          for (var li = 0; li < lyricGs.length; li += 1) {
            var g = lyricGs[li];
            var gb;
            try {
              gb = g.getBBox();
            } catch (e4) {
              continue;
            }
            var gmid = gb.x + gb.width / 2;
            var gy = gb.y + gb.height / 2;
            if (gy < colY0 || gy > colY1) {
              continue;
            }
            if (Math.abs(gmid - slot.mid) > 28) {
              continue;
            }
            if (!lyricUnion) {
              lyricUnion = {
                x: gb.x,
                right: gb.x + gb.width,
                mid: gmid,
                els: [g],
              };
            } else {
              lyricUnion.x = Math.min(lyricUnion.x, gb.x);
              lyricUnion.right = Math.max(
                lyricUnion.right,
                gb.x + gb.width
              );
              lyricUnion.els.push(g);
              lyricUnion.mid =
                (lyricUnion.x + lyricUnion.right) / 2;
            }
          }
          var contentLeft = slot.x;
          var contentRight = slot.right;
          if (lyricUnion) {
            contentLeft = Math.min(contentLeft, lyricUnion.x);
            contentRight = Math.max(contentRight, lyricUnion.right);
          }
          var contentMid = (contentLeft + contentRight) / 2;
          var slotMid = (leftBound + rightBound) / 2;
          var dx = slotMid - contentMid;
          // Niet voorbij slotgrenzen duwen.
          if (Math.abs(dx) >= 4) {
            if (contentLeft + dx < leftBound) {
              dx = leftBound - contentLeft;
            }
            if (contentRight + dx > rightBound) {
              dx = rightBound - contentRight;
            }
          } else {
            dx = 0;
          }
          function shiftEl(el, amount, mark) {
            if (!(Math.abs(amount) >= 3)) {
              return;
            }
            if (mark && el.getAttribute(mark) === "1") {
              return;
            }
            var prev = el.getAttribute("transform") || "";
            el.setAttribute(
              "transform",
              (prev ? prev + " " : "") +
                "translate(" +
                amount.toFixed(2) +
                ", 0)"
            );
            if (mark) {
              el.setAttribute(mark, "1");
            }
          }
          if (Math.abs(dx) >= 4) {
            // Alleen noten + lyrics hier; melisma-slurs blijven op de
            // measure-dx uit centerMeasureContents (S2) — slot-shift op
            // boog-start brak slur↔noot.
            for (var ni = 0; ni < slot.notes.length; ni += 1) {
              shiftEl(slot.notes[ni], dx, "data-osmd-slot");
            }
            if (lyricUnion) {
              for (var lei = 0; lei < lyricUnion.els.length; lei += 1) {
                shiftEl(lyricUnion.els[lei], dx, "data-osmd-slot");
              }
            }
            slot.mid += dx;
            if (lyricUnion) {
              lyricUnion.mid += dx;
            }
          }
          // L2 / S22: lyric-midden op de nootkolom (alle stemmen delen
          // slot.mid). Breve/melisma-eerste: zelfde anker.
          if (lyricUnion && Math.abs(lyricUnion.mid - slot.mid) >= 3) {
            var ldx = slot.mid - lyricUnion.mid;
            for (var lj = 0; lj < lyricUnion.els.length; lj += 1) {
              shiftEl(lyricUnion.els[lj], ldx, null);
            }
          }
        }
      });
  }

  global.__vsaOsmdCueLayout = runCueLayout;
})(typeof window !== "undefined" ? window : globalThis);
