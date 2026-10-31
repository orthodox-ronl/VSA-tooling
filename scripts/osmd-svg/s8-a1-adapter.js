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

  function markBreveStaveNotes(notes) {
    for (var i = 0; i < notes.length; i += 1) {
      notes[i].setAttribute("data-osmd-breve", "1");
      Array.prototype.forEach.call(
        notes[i].querySelectorAll(".vf-stem, .vf-flag"),
        osmdHideSvgEl
      );
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

  function hideNoteheadNoneGraphics(mount, xmlText) {
    var byPart = s8PrintSlotsByPartMeasure(xmlText);
    if (!byPart.length) {
      return;
    }
    var raw = Array.prototype.map.call(
      mount.querySelectorAll(".vf-measure"),
      function (m) {
        var b = m.getBBox();
        return {
          el: m,
          id: m.getAttribute("id"),
          x: b.x,
          y: b.y,
        };
      }
    );
    raw.sort(function (a, b) {
      return a.y - b.y || a.x - b.x;
    });
    var systems = [];
    for (var i = 0; i < raw.length; i += 1) {
      var mm = raw[i];
      var sys = systems[systems.length - 1];
      if (!sys || mm.y - sys.lastY > 150) {
        systems.push({ lastY: mm.y, ms: [mm] });
      } else {
        sys.ms.push(mm);
        sys.lastY = mm.y;
      }
    }
    for (var si = 0; si < systems.length; si += 1) {
      var ms = systems[si].ms.slice();
      ms.sort(function (a, b) {
        return a.x - b.x || a.y - b.y;
      });
      var colStart = 0;
      for (var j = 1; j <= ms.length; j += 1) {
        if (j < ms.length && Math.abs(ms[j].x - ms[colStart].x) < 8) {
          continue;
        }
        var col = ms.slice(colStart, j);
        colStart = j;
        col.sort(function (a, b) {
          return a.y - b.y;
        });
        for (var pi = 0; pi < col.length && pi < byPart.length; pi += 1) {
          var measureNum = col[pi].id;
          if (!measureNum) {
            continue;
          }
          var slots = byPart[pi][String(measureNum)];
          if (!slots || !slots.length) {
            continue;
          }
          var notes = Array.prototype.slice.call(
            col[pi].el.querySelectorAll(".vf-stavenote")
          );
          hideS8SlotsInMeasure(col[pi].el, slots, notes);
        }
      }
    }
    if (xmlText.indexOf("<notehead>none</notehead>") !== -1) {
      Array.prototype.forEach.call(
        mount.querySelectorAll(
          "g.vf-text.dash, g.vf-text.lyrics line, g.vf-text.lyrics path"
        ),
        osmdHideSvgEl
      );
      Array.prototype.forEach.call(mount.querySelectorAll("text"), function (t) {
        if (String(t.textContent || "").trim() !== "-") {
          return;
        }
        osmdHideSvgEl(t);
        if (t.parentElement) {
          osmdHideSvgEl(t.parentElement);
        }
      });
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
    // Na hide hebben spacer-noten vaak lege bbox; tel daarom op
    // data-osmd-* attributen i.p.v. opnieuw te clusteren op x-positie.
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
    var measures = Array.prototype.slice.call(
      mount.querySelectorAll(".vf-measure")
    );
    // Twee staven delen measure-id; pak de stave die bij partIndex hoort
    // (sorteer op y: 0 = boven, 1 = bas).
    measures.sort(function (a, b) {
      return a.getBBox().y - b.getBBox().y;
    });
    var m = measures[partIndex];
    var spacerVisible = 0;
    var spacerMarked = 0;
    var keepVisible = 0;
    var breveMarked = 0;
    if (!m) {
      return {
        spacerVisibleHeads: 0,
        spacerMarked: 0,
        keepVisibleHeads: 0,
        breveMarked: 0,
        expectSpacers: expectSpacers,
      };
    }
    var notes = Array.prototype.slice.call(
      m.querySelectorAll(".vf-stavenote")
    );
    for (var i = 0; i < notes.length; i += 1) {
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
        }
      }
    }
    return {
      spacerVisibleHeads: spacerVisible,
      spacerMarked: spacerMarked,
      keepVisibleHeads: keepVisible,
      breveMarked: breveMarked,
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
    var ok =
      (boven.spacerVisibleHeads || 0) === 0 &&
      (bas.spacerVisibleHeads || 0) === 0 &&
      (boven.keepVisibleHeads || 0) > 0 &&
      (!hasMarkers ||
        ((boven.spacerMarked || 0) > 0 && (bas.spacerMarked || 0) > 0));
    return {
      ok: ok,
      staven: { boven: boven, bas: bas },
    };
  }

  window.__vsaOsmdS8FinalizePrint = finalizePrint;
  window.__vsaOsmdS8Diagnose = diagnose;
})();
