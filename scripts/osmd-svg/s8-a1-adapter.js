/**
 * S8-recite A1-adapter for headless OSMD (mvsa svg --engine osmd).
 *
 * from-ir marks spacers as ``<notehead>none</notehead>`` (+ stem none).
 * OSMD/VexFlow still draws those heads; this script hides spacer graphics
 * after render while keeping lyrics. Same contract as bibliotheek
 * ``static/js/score-osmd.js`` (schermpartituur §5.1 / osmd-s8-recite).
 *
 * Exposes: window.__vsaOsmdS8FinalizePrint(mount, xmlText)
 *          window.__vsaOsmdS8Diagnose(mount, xmlText)  // optional CI
 */
(function () {
  "use strict";

  function xmlLocalTag(el) {
    if (!el) {
      return "";
    }
    if (el.localName) {
      return String(el.localName).toLowerCase();
    }
    return String(el.tagName || "")
      .replace(/^[^:]+:/, "")
      .toLowerCase();
  }

  function textContentTrim(el) {
    return String(el.textContent || "").trim();
  }

  function noteheadKindFromXmlNote(noteEl) {
    var nh = noteEl.querySelector("notehead");
    if (!nh) {
      return "normal";
    }
    return textContentTrim(nh).toLowerCase();
  }

  /**
   * S8 per part/measure: one slot per metric position (v1 + v2).
   */
  function s8PrintSlotsByPartMeasure(xmlText) {
    var doc = new DOMParser().parseFromString(xmlText, "application/xml");
    var parts = Array.prototype.slice.call(doc.querySelectorAll("part"));
    return parts.map(function (part) {
      var byNum = {};
      var measures = [];
      Array.prototype.forEach.call(part.children, function (ch) {
        if (xmlLocalTag(ch) === "measure") {
          measures.push(ch);
        }
      });
      Array.prototype.forEach.call(measures, function (measure, mi) {
        var num = measure.getAttribute("number");
        if (!num) {
          num = String(mi + 1);
        }
        var byVoice = { 1: [], 2: [] };
        Array.prototype.forEach.call(measure.children, function (ch) {
          if (xmlLocalTag(ch) !== "note") {
            return;
          }
          if (ch.querySelector("rest")) {
            return;
          }
          if (ch.querySelector("chord")) {
            return;
          }
          var vEl = ch.querySelector("voice");
          var v = vEl ? parseInt(textContentTrim(vEl), 10) : 1;
          if (v !== 1 && v !== 2) {
            v = 1;
          }
          byVoice[v].push(noteheadKindFromXmlNote(ch));
        });
        var slots = [];
        var n = Math.max(byVoice[1].length, byVoice[2].length);
        var i;
        for (i = 0; i < n; i += 1) {
          var h1 = i < byVoice[1].length ? byVoice[1][i] : "normal";
          var h2 = i < byVoice[2].length ? byVoice[2][i] : "normal";
          var spacer = h1 === "none" || h2 === "none";
          slots.push({
            spacer: spacer,
            breve: !spacer && (h1 === "breve" || h2 === "breve"),
          });
        }
        byNum[String(num)] = slots;
      });
      return byNum;
    });
  }

  function osmdHideSvgEl(el) {
    el.setAttribute("visibility", "hidden");
    el.setAttribute("display", "none");
    el.style.visibility = "hidden";
    el.style.display = "none";
  }

  function svgElIsVisible(el) {
    var s = window.getComputedStyle(el);
    return s.display !== "none" && s.visibility !== "hidden";
  }

  function staveNoteHasVisibleNotehead(staveNoteEl) {
    var shapes = staveNoteEl.querySelectorAll(
      ".vf-note path, .vf-note circle, .vf-note ellipse, .vf-note rect, .vf-note use, .vf-notehead, path.vf-notehead, .vf-stavenote > path"
    );
    for (var i = 0; i < shapes.length; i += 1) {
      if (svgElIsVisible(shapes[i])) {
        return true;
      }
    }
    return false;
  }

  function hideStaveNoteheadGraphics(staveNoteEl) {
    staveNoteEl.setAttribute("data-osmd-spacer", "1");
    Array.prototype.forEach.call(
      staveNoteEl.querySelectorAll(".vf-stem, .vf-flag, .vf-beam"),
      osmdHideSvgEl
    );
    var note = staveNoteEl.querySelector(".vf-note");
    if (note) {
      osmdHideSvgEl(note);
      Array.prototype.forEach.call(note.querySelectorAll("*"), osmdHideSvgEl);
    }
    Array.prototype.forEach.call(
      staveNoteEl.querySelectorAll(
        ".vf-beam, .vf-modifiers, .vf-notehead, path.vf-notehead"
      ),
      osmdHideSvgEl
    );
    Array.prototype.forEach.call(
      staveNoteEl.querySelectorAll("path, circle, ellipse, rect, use, polygon"),
      function (el) {
        if (el.closest && el.closest("text")) {
          return;
        }
        osmdHideSvgEl(el);
      }
    );
  }

  var S8_CLUSTER_X_TOL = 6;

  function clusterStaveNotesBySvgX(staveNoteEls, xTol) {
    var items = [];
    for (var i = 0; i < staveNoteEls.length; i += 1) {
      var bb = staveNoteEls[i].getBBox();
      if (bb.width <= 0.5 && bb.height <= 0.5) {
        continue;
      }
      items.push({ el: staveNoteEls[i], x: bb.x + bb.width / 2 });
    }
    items.sort(function (a, b) {
      return a.x - b.x;
    });
    var clusters = [];
    for (var j = 0; j < items.length; j += 1) {
      var it = items[j];
      var last = clusters[clusters.length - 1];
      if (!last || Math.abs(it.x - last.x) > xTol) {
        clusters.push({ x: it.x, notes: [it.el] });
      } else {
        last.notes.push(it.el);
        last.x = (last.x + it.x) / 2;
      }
    }
    return clusters;
  }

  function alignClustersToSlotCount(clusters, slotCount) {
    if (!clusters.length || !slotCount) {
      return clusters;
    }
    if (clusters.length === slotCount) {
      return clusters;
    }
    if (clusters.length > slotCount) {
      return clusters.slice(0, slotCount);
    }
    return clusters;
  }

  function hideLedgersNearX(measureEl, xCenter, xTol) {
    var tol = xTol + 10;
    Array.prototype.forEach.call(
      measureEl.querySelectorAll(".vf-ledgers, .vf-ledger"),
      function (el) {
        var bb;
        try {
          bb = el.getBBox();
        } catch (e) {
          return;
        }
        var cx = bb.x + bb.width / 2;
        if (Math.abs(cx - xCenter) <= tol) {
          osmdHideSvgEl(el);
        }
      }
    );
  }

  /**
   * Vervang OSMD's gevulde breve-kop door de MuseScore ``||O||``-glyph
   * (path uit alleluia-toon-8.mvsa.svg, unit height=1, centrum 0,0).
   */
  var MUSESCORE_BREVE_UNIT_PATH = "M-0.68906 -0.50000C-0.70031 -0.50000 -0.70310 -0.50000 -0.71419 -0.50000C-0.73670 -0.50000 -0.75345 -0.48320 -0.75345 -0.46073C-0.75345 -0.43838 -0.75345 0.44110 -0.75345 0.46074C-0.75345 0.48028 -0.73670 0.50000 -0.71419 0.50000C-0.70310 0.50000 -0.70031 0.50000 -0.68906 0.50000C-0.66934 0.50000 -0.64979 0.47749 -0.64979 0.46074C-0.64979 0.44390 -0.64979 -0.43838 -0.64979 -0.46073C-0.64979 -0.48320 -0.66663 -0.50000 -0.68906 -0.50000M0.50975 -0.50000C0.49849 -0.50000 0.49570 -0.50000 0.48453 -0.50000C0.46211 -0.50000 0.44535 -0.48320 0.44535 -0.46073C0.44535 -0.45518 0.44535 -0.36276 0.44535 -0.24230C0.36124 -0.32348 0.21849 -0.37954 0.00279 -0.37954C-0.21570 -0.37954 -0.35853 -0.32348 -0.44264 -0.24230C-0.44264 -0.36276 -0.44264 -0.45518 -0.44264 -0.46073C-0.44264 -0.48320 -0.45940 -0.50000 -0.48174 -0.50000C-0.49299 -0.50000 -0.49579 -0.50000 -0.50704 -0.50000C-0.52938 -0.50000 -0.54613 -0.48320 -0.54613 -0.46073C-0.54613 -0.43838 -0.54613 0.44110 -0.54613 0.46074C-0.54613 0.48028 -0.52938 0.50000 -0.50704 0.50000C-0.49579 0.50000 -0.49299 0.50000 -0.48174 0.50000C-0.46219 0.50000 -0.44264 0.47749 -0.44264 0.46074C-0.44264 0.45515 -0.44264 0.36275 -0.44264 0.23954C-0.35853 0.32348 -0.21570 0.37950 0.00279 0.37950C0.21849 0.37950 0.36124 0.32348 0.44535 0.23954C0.44535 0.36275 0.44535 0.45515 0.44535 0.46074C0.44535 0.48028 0.46211 0.50000 0.48453 0.50000C0.49570 0.50000 0.49849 0.50000 0.50975 0.50000C0.52930 0.50000 0.54884 0.47749 0.54884 0.46074C0.54884 0.44390 0.54884 -0.43838 0.54884 -0.46073C0.54884 -0.48320 0.53209 -0.50000 0.50975 -0.50000M0.14563 0.27305C0.11204 0.28143 0.06719 0.28989 0.02513 0.28989C-0.05323 0.28989 -0.10654 0.26459 -0.14292 0.19749C-0.17922 0.12738 -0.22974 -0.05469 -0.23253 -0.13031C-0.23253 -0.13587 -0.23253 -0.14142 -0.23253 -0.14710C-0.23253 -0.21150 -0.20453 -0.25076 -0.14292 -0.27311C-0.10933 -0.28157 -0.06448 -0.28990 -0.01963 -0.28990C0.05593 -0.28990 0.10637 -0.27033 0.14563 -0.19749C0.18489 -0.12185 0.23803 0.05743 0.23803 0.13015C0.23803 0.20299 0.21282 0.25063 0.14563 0.27305M0.71419 -0.50000C0.70293 -0.50000 0.70014 -0.50000 0.68906 -0.50000C0.66655 -0.50000 0.64979 -0.48320 0.64979 -0.46073C0.64979 -0.43838 0.64979 0.44110 0.64979 0.46074C0.64979 0.48028 0.66655 0.50000 0.68906 0.50000C0.70014 0.50000 0.70293 0.50000 0.71419 0.50000C0.73374 0.50000 0.75345 0.47749 0.75345 0.46074C0.75345 0.44390 0.75345 -0.43838 0.75345 -0.46073C0.75345 -0.48320 0.73661 -0.50000 0.71419 -0.50000";
  var MUSESCORE_BREVE_ASPECT = 1.50690504;

  function drawBrevePipeOGlyph(staveNoteEl) {
    var ns = "http://www.w3.org/2000/svg";
    if (staveNoteEl.querySelector("[data-osmd-breve-glyph='1']")) {
      return;
    }
    var head =
      staveNoteEl.querySelector(".vf-notehead") ||
      staveNoteEl.querySelector("path.vf-notehead") ||
      staveNoteEl.querySelector(".vf-note");
    if (!head) {
      return;
    }
    var bb;
    try {
      bb = head.getBBox();
    } catch (e) {
      return;
    }
    if (bb.width < 0.5 && bb.height < 0.5) {
      return;
    }
    Array.prototype.forEach.call(
      staveNoteEl.querySelectorAll(
        ".vf-notehead, path.vf-notehead, .vf-note path, .vf-note circle, .vf-note ellipse, .vf-note rect"
      ),
      function (el) {
        if (el.closest && el.closest(".vf-stem, .vf-flag")) {
          return;
        }
        osmdHideSvgEl(el);
      }
    );

    var cx = bb.x + bb.width / 2;
    var cy = bb.y + bb.height / 2;
    // Iets groter dan OSMD-kop; MuseScore-breve is ~1.3× heelnoothoogte.
    var scale = Math.max(bb.height, 8) * 1.35;

    var g = document.createElementNS(ns, "g");
    g.setAttribute("class", "vsa-breve-glyph");
    g.setAttribute("data-osmd-breve-glyph", "1");
    g.setAttribute("pointer-events", "none");
    g.setAttribute(
      "transform",
      "translate(" + cx + "," + cy + ") scale(" + scale + ")"
    );

    var path = document.createElementNS(ns, "path");
    path.setAttribute("d", MUSESCORE_BREVE_UNIT_PATH);
    path.setAttribute("fill", "#000000");
    path.setAttribute("fill-rule", "evenodd");
    path.setAttribute("stroke", "none");
    g.appendChild(path);
    staveNoteEl.appendChild(g);
  }

  function markBreveStaveNotes(notes) {
    for (var i = 0; i < notes.length; i += 1) {
      notes[i].setAttribute("data-osmd-breve", "1");
      Array.prototype.forEach.call(
        notes[i].querySelectorAll(".vf-stem, .vf-flag"),
        osmdHideSvgEl
      );
      drawBrevePipeOGlyph(notes[i]);
    }
  }

  function hideS8SlotsInMeasure(measureEl, slots, staveNoteEls) {
    if (!slots || !slots.length) {
      return;
    }
    var clusters = alignClustersToSlotCount(
      clusterStaveNotesBySvgX(staveNoteEls, S8_CLUSTER_X_TOL),
      slots.length
    );
    var s;
    for (s = 0; s < slots.length && s < clusters.length; s += 1) {
      var slot = slots[s];
      var col = clusters[s].notes;
      var ni;
      if (slot.spacer) {
        for (ni = 0; ni < col.length; ni += 1) {
          hideStaveNoteheadGraphics(col[ni]);
        }
        hideLedgersNearX(measureEl, clusters[s].x, S8_CLUSTER_X_TOL);
      } else if (slot.breve) {
        markBreveStaveNotes(col);
      }
    }
  }

  /**
   * Groepeer OSMD-maten op measure-id (zelfde nummer = treble+bas).
   * Geen y-drempel: bij compacte CoriB-layout is de tussen-systeem-
   * afstand (~40 px) kleiner dan treble→bas binnen een systeem (~120 px),
   * dus een vaste y-split (oude 150) mengt alle systemen en mist S8-slots.
   */
  function measuresByIdSortedByStaff(mount) {
    var byId = {};
    Array.prototype.forEach.call(
      mount.querySelectorAll(".vf-measure"),
      function (m) {
        var id = m.getAttribute("id");
        if (!id) {
          return;
        }
        if (!byId[id]) {
          byId[id] = [];
        }
        byId[id].push(m);
      }
    );
    Object.keys(byId).forEach(function (id) {
      byId[id].sort(function (a, b) {
        return a.getBBox().y - b.getBBox().y;
      });
    });
    return byId;
  }

  function hideNoteheadNoneGraphics(mount, xmlText) {
    var byPart = s8PrintSlotsByPartMeasure(xmlText);
    if (!byPart.length) {
      return;
    }
    var byId = measuresByIdSortedByStaff(mount);
    Object.keys(byId).forEach(function (measureNum) {
      var col = byId[measureNum];
      var pi;
      for (pi = 0; pi < col.length && pi < byPart.length; pi += 1) {
        var slots = byPart[pi][String(measureNum)];
        if (!slots || !slots.length) {
          continue;
        }
        var notes = Array.prototype.slice.call(
          col[pi].querySelectorAll(".vf-stavenote")
        );
        hideS8SlotsInMeasure(col[pi], slots, notes);
      }
    });
    if (xmlText.indexOf("<notehead>none</notehead>") !== -1) {
      // Alleen melisma-lijnen/paden onder lyrics verbergen — niet de
      // lettergreepstreepjes (g.vf-text.dash / tekst "-"). Die hoort de
      // lezer te zien tussen lettergrepen van één woord (S8-recite ook).
      Array.prototype.forEach.call(
        mount.querySelectorAll("g.vf-text.lyrics line, g.vf-text.lyrics path"),
        osmdHideSvgEl
      );
      Array.prototype.forEach.call(
        mount.querySelectorAll(".vf-ledgers"),
        function (g) {
          if (g.getAttribute("data-osmd-spacer-ledger") === "1") {
            return;
          }
          var bb = g.getBBox();
          if (bb.width > 80 && bb.height < 8) {
            osmdHideSvgEl(g);
            g.setAttribute("data-osmd-spacer-ledger", "1");
          }
        }
      );
    }
  }

  function diagnoseStaff(mount, xmlText, partIndex) {
    // Tel over alle maten van deze partij (id-groep, stave = partIndex).
    var byPart = s8PrintSlotsByPartMeasure(xmlText);
    var slotsMap = byPart[partIndex] || {};
    var expectSpacers = 0;
    Object.keys(slotsMap).forEach(function (k) {
      slotsMap[k].forEach(function (s) {
        if (s.spacer) {
          expectSpacers += 1;
        }
      });
    });
    var byId = measuresByIdSortedByStaff(mount);
    var spacerVisible = 0;
    var spacerMarked = 0;
    var keepVisible = 0;
    var breveMarked = 0;
    var breveGlyphs = 0;
    Object.keys(byId).forEach(function (id) {
      var col = byId[id];
      if (partIndex >= col.length) {
        return;
      }
      var notes = Array.prototype.slice.call(
        col[partIndex].querySelectorAll(".vf-stavenote")
      );
      var i;
      for (i = 0; i < notes.length; i += 1) {
        var n = notes[i];
        if (n.getAttribute("data-osmd-spacer") === "1") {
          spacerMarked += 1;
          if (staveNoteHasVisibleNotehead(n)) {
            spacerVisible += 1;
          }
        } else {
          if (staveNoteHasVisibleNotehead(n)) {
            keepVisible += 1;
          }
          if (n.getAttribute("data-osmd-breve") === "1") {
            breveMarked += 1;
            if (n.querySelector("[data-osmd-breve-glyph='1']")) {
              breveGlyphs += 1;
            }
          }
        }
      }
    });
    return {
      spacerVisibleHeads: spacerVisible,
      spacerMarked: spacerMarked,
      keepVisibleHeads: keepVisible,
      breveMarked: breveMarked,
      breveGlyphs: breveGlyphs,
      expectSpacers: expectSpacers,
    };
  }

  function finalizePrint(mount, xmlText) {
    hideNoteheadNoneGraphics(mount, xmlText);
  }

  function diagnose(mount, xmlText) {
    var boven = diagnoseStaff(mount, xmlText, 0);
    var bas = diagnoseStaff(mount, xmlText, 1);
    var hasMarkers =
      xmlText.indexOf("<notehead>none</notehead>") !== -1;
    var hasBreve =
      xmlText.indexOf("<notehead>breve</notehead>") !== -1;
    var ok =
      (boven.spacerVisibleHeads || 0) === 0 &&
      (bas.spacerVisibleHeads || 0) === 0 &&
      (boven.keepVisibleHeads || 0) > 0 &&
      (!hasMarkers ||
        ((boven.spacerMarked || 0) > 0 && (bas.spacerMarked || 0) > 0)) &&
      (!hasBreve ||
        ((boven.breveGlyphs || 0) > 0 && (bas.breveGlyphs || 0) > 0));
    return {
      ok: ok,
      staven: { boven: boven, bas: bas },
    };
  }

  window.__vsaOsmdS8FinalizePrint = finalizePrint;
  window.__vsaOsmdS8Diagnose = diagnose;
})();
