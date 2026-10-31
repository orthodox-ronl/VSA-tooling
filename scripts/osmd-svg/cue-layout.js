/**
 * Cue-layout voor headless OSMD (schermpartituur §4.2 / S15 / S19 / C6).
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
        var entry = {
          el: m,
          x: b.x,
          y: b.y,
          w: b.width,
          musicStart: musicStart,
          right: b.x + b.width,
        };
        if (!byId[id] || entry.y < byId[id].y) {
          byId[id] = entry;
        }
      }
    );
    Object.keys(byId).forEach(function (id) {
      var m = byId[id];
      var notes = m.el.querySelectorAll(
        ".vf-stavenote, .vf-text.lyrics, .vf-text.dash"
      );
      if (!notes.length) {
        return;
      }
      var minX = Infinity;
      var maxX = -Infinity;
      Array.prototype.forEach.call(notes, function (n) {
        try {
          var nb = n.getBBox();
          minX = Math.min(minX, nb.x);
          maxX = Math.max(maxX, nb.x + nb.width);
        } catch (e) {
          /* skip */
        }
      });
      if (!(maxX > minX)) {
        return;
      }
      var roomLeft = minX - m.musicStart;
      var roomRight = m.right - 6 - maxX;
      if (roomLeft < 8 || roomRight < 8) {
        return;
      }
      var dx = (roomRight - roomLeft) / 2;
      if (!(Math.abs(dx) > 2)) {
        return;
      }
      Array.prototype.forEach.call(notes, function (n) {
        var g =
          n.classList && n.classList.contains("vf-text")
            ? n
            : n.closest(".vf-stavenote") || n;
        if (!g || g.getAttribute("data-osmd-center") === "1") {
          return;
        }
        var prev = g.getAttribute("transform") || "";
        g.setAttribute(
          "transform",
          (prev + " translate(" + dx.toFixed(2) + ", 0)").trim()
        );
        g.setAttribute("data-osmd-center", "1");
      });
    });
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
    centerMeasureContents(mount);
  }

  global.__vsaOsmdCueLayout = runCueLayout;
})(typeof window !== "undefined" ? window : globalThis);
