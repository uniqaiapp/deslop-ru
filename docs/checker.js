/* In-browser port of scripts/deslop.py (deslop-ru 0.1.0). No dependencies, no network, no storage.
   The pattern table is exported from the Python source into <script id="ug-data"> and translated here, so the two
   checkers read the same rules. tests/test_site.py runs both over every example and a set of edge texts and fails
   on any difference in score, hits, metrics or stripped text. The text you paste never leaves the page. */
(function () {
  "use strict";
  var D = null, C = null;

  // ---- Python regex -> JS regex (Unicode-exact for \s \b . ^ $, lookarounds instead of the m flag)
  var WS = "\\t-\\r\\x1c-\\x20\\x85\\xa0\\u1680\\u2000-\\u200a\\u2028\\u2029\\u202f\\u205f\\u3000";
  var WC = "\\p{L}\\p{N}_";

  function tr(p) {
    var i = 0, out = "", cls = false;
    while (i < p.length) {
      var c = p.charAt(i);
      if (c === "\\") {
        var n = p.charAt(i + 1); i += 2;
        if (n === "w") out += cls ? WC : "[" + WC + "]";
        else if (n === "d") out += "\\p{Nd}";
        else if (n === "s") out += cls ? WS : "[" + WS + "]";
        else if (n === "b") out += cls ? "\\x08" : "(?:(?<=[" + WC + "])(?![" + WC + "])|(?<![" + WC + "])(?=[" + WC + "]))";
        else out += "\\" + n;
        continue;
      }
      if (cls) { if (c === "]") cls = false; out += c; i++; continue; }
      if (c === "[") {
        cls = true; out += c; i++;
        if (p.charAt(i) === "^") { out += "^"; i++; }
        continue;
      }
      if (c === ".") { out += "[^\\n]"; i++; continue; }
      if (c === "^") { out += "(?<![^\\n])"; i++; continue; }
      if (c === "$") { out += "(?![^\\n])"; i++; continue; }
      out += c; i++;
    }
    return out;
  }
  function mk(p, flags) { return new RegExp(tr(p), "u" + flags); }

  var WS_EDGE = new RegExp("^[" + WS + "]+|[" + WS + "]+$", "g");
  var WS_L = new RegExp("^[" + WS + "]+");
  var WS_R = new RegExp("[" + WS + "]+$");
  function pyStrip(s) { return s.replace(WS_EDGE, ""); }
  function pyRstrip(s) { return s.replace(WS_R, ""); }
  function cps(s) { return Array.from(s); }

  // Python round(): half to even, on the exact binary value
  function pyRound(x, nd) {
    var k = Math.pow(10, nd), y = x * k;
    if (y - Math.floor(y) === 0.5) {
      var f = Math.floor(y);
      return (f % 2 === 0 ? f : f + 1) / k;
    }
    return Number(x.toFixed(nd));
  }

  function esc(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#x27;");
  }
  function fmt(t, o) { return t.replace(/\{(\w+)\}/g, function (m, k) { return k in o ? o[k] : m; }); }
  function ruPlural(n, forms) {
    var a = Math.abs(n) % 100, b = a % 10;
    if (a > 10 && a < 20) return forms[2];
    if (b === 1) return forms[0];
    if (b >= 2 && b <= 4) return forms[1];
    return forms[2];
  }

  var WORD_RE = /[A-Za-zА-Яа-яЁё0-9][A-Za-zА-Яа-яЁё0-9'’\-]*/g;
  var CYR_RE = /[А-Яа-яЁё]/g, LAT_RE = /[A-Za-z]/g;

  function setData(d) {
    D = d;
    C = {
      pats: d.patterns.map(function (p) {
        return { id: p.id, lang: p.lang, category: p.category, label: p.label, fix: p.fix, weight: p.weight, cut: p.cut, rx: mk(p.re, "gi") };
      }),
      emoji: mk(d.rx.emoji, "g"), emojiY: mk(d.rx.emoji, "y"), bullet: mk(d.rx.bullet, "y"),
      boldLead: mk(d.rx.boldLead, "y"), heading: mk(d.rx.heading, "y")
    };
  }

  // ---- helpers ported from deslop.py
  function fold(t) { return t.toLowerCase().replace(/ё/g, "е"); }
  function wordCount(t) { return (t.match(WORD_RE) || []).length; }
  function detectLang(t) {
    var c = (t.match(CYR_RE) || []).length, l = (t.match(LAT_RE) || []).length;
    if (c === 0 && l === 0) return "ru";
    return c >= l ? "ru" : "en";
  }
  function lineOffsets(t) {
    var offs = [0];
    for (var i = 0; i < t.length; i++) if (t.charCodeAt(i) === 10) offs.push(i + 1);
    return offs;
  }
  function lineOf(offs, pos) {
    var lo = 0, hi = offs.length - 1;
    while (lo < hi) {
      var mid = Math.floor((lo + hi + 1) / 2);
      if (offs[mid] <= pos) lo = mid; else hi = mid - 1;
    }
    return lo + 1;
  }
  function stickyAt0(rx, s) { rx.lastIndex = 0; return rx.test(s); }
  function emojiHead(l) { return cps(pyStrip(l)).slice(0, 3).join(""); }
  function countMatches(rx, s) { rx.lastIndex = 0; var n = 0; while (rx.exec(s) !== null) n++; rx.lastIndex = 0; return n; }

  function findHits(text, lang) {
    var folded = fold(text), offs = lineOffsets(text), hits = [], m;
    C.pats.forEach(function (p) {
      if (p.lang !== lang) return;
      p.rx.lastIndex = 0;
      while ((m = p.rx.exec(folded)) !== null) {
        var start = m.index, end = start + m[0].length;
        if (end === start) { p.rx.lastIndex++; continue; }
        var ln = lineOf(offs, start);
        hits.push({
          id: p.id, category: p.category, label: p.label, fix: p.fix, weight: p.weight, line: ln,
          col: cps(text.slice(offs[ln - 1], start)).length + 1, text: pyStrip(text.slice(start, end)), start: start, end: end
        });
      }
    });
    hits.sort(function (a, b) {
      return a.line - b.line || a.col - b.col || (a.id < b.id ? -1 : a.id > b.id ? 1 : 0);
    });
    return hits;
  }

  function structureChecks(text, lang) {
    var lines = text.split("\n"), words = Math.max(wordCount(text), 1), hits = [], M = {};
    M.emoji = countMatches(C.emoji, text);
    M.emoji_per_100w = pyRound(M.emoji * 100 / words, 1);
    var emojiBullets = lines.filter(function (l) { return stickyAt0(C.emojiY, emojiHead(l)); }).length;
    M.emoji_bullets = emojiBullets;

    var dashes = text.split("—").length - 1 + text.split("–").length - 1 + countMatches(new RegExp("[" + WS + "]-[" + WS + "]", "g"), text);
    M.dashes = dashes;
    M.dashes_per_100w = pyRound(dashes * 100 / words, 1);

    var boldLeads = lines.filter(function (l) { return stickyAt0(C.boldLead, l); }).length;
    M.bold_lead_bullets = boldLeads;

    var run = 0, best = 0;
    lines.forEach(function (l) {
      if (stickyAt0(C.bullet, l) || stickyAt0(C.emojiY, emojiHead(l))) { run++; best = Math.max(best, run); }
      else if (pyStrip(l) !== "") run = 0;
    });
    M.longest_list = best;

    var excl = text.split("!").length - 1;
    M.exclamations = excl;
    M.exclamations_per_100w = pyRound(excl * 100 / words, 1);

    M.headings_with_emoji = lines.filter(function (l) {
      if (!stickyAt0(C.heading, l)) return false;
      C.emoji.lastIndex = 0;
      var r = C.emoji.test(l); C.emoji.lastIndex = 0; return r;
    }).length;

    var paras = text.split(new RegExp("\\n[" + WS + "]*\\n")).filter(function (p) {
      return pyStrip(p) !== "" && !stickyAt0(C.bullet, p) && !stickyAt0(C.heading, p);
    });
    var plens = paras.map(wordCount);
    if (plens.length >= 4) {
      var mean = plens.reduce(function (a, b) { return a + b; }, 0) / plens.length;
      var v = plens.reduce(function (a, x) { return a + (x - mean) * (x - mean); }, 0) / plens.length;
      var cv = mean ? Math.sqrt(v) / mean : 0;
      M.paragraph_cv = pyRound(cv, 2);
    } else M.paragraph_cv = null;

    function add(id, label, fix, weight) {
      hits.push({ id: id, category: "structure", label: label, fix: fix, weight: weight, line: 0, col: 0, text: "" });
    }
    var ru = lang === "ru", enough = words >= 40;
    if ((enough && M.emoji_per_100w >= 2.0) || emojiBullets >= 3)
      add("structure.emoji", ru ? "эмодзи вместо структуры" : "emoji as structure",
        ru ? "Оставьте не больше одного на пост, и то не в начале строки." : "At most one per post, never as a bullet.", 2);
    if (enough && M.dashes_per_100w >= 2.5)
      add("structure.dashes", ru ? "тире через слово" : "dash in every sentence",
        ru ? "Половину тире замените на точку или запятую." : "Replace half of them with a period or comma.", 2);
    if (boldLeads >= 3)
      add("structure.bold_leads", ru ? "жирный заголовок в каждом пункте" : "bold label in every bullet",
        ru ? "Уберите жирные подписи; пункт должен читаться без них." : "Drop the bold labels; a bullet should read without them.", 2);
    if (best >= 7)
      add("structure.list_wall", ru ? "простыня списка (" + best + " строк подряд)" : "list wall (" + best + " bullets in a row)",
        ru ? "Сверните в абзац или оставьте 3–5 пунктов." : "Fold into prose or keep 3-5 items.", 2);
    if (enough && M.exclamations_per_100w >= 2.0)
      add("structure.exclamations", ru ? "восклицательные знаки" : "exclamation marks",
        ru ? "Один на текст, лучше ноль." : "One per text, better none.", 1);
    if (M.headings_with_emoji)
      add("structure.heading_emoji", ru ? "эмодзи в заголовках" : "emoji in headings",
        ru ? "Заголовок без эмодзи." : "Headings without emoji.", 1);
    if (M.paragraph_cv !== null && M.paragraph_cv < 0.2)
      add("structure.uniform_paragraphs", ru ? "абзацы одинаковой длины" : "paragraphs of identical length",
        ru ? "Сделайте один абзац короче, один длиннее; ровный ритм выдаёт генерацию." : "Vary paragraph length; a flat rhythm reads as generated.", 1);
    return { hits: hits, metrics: M };
  }

  function verdict(score, lang) {
    var ru = lang === "ru";
    if (score < 10) return ru ? "чисто" : "clean";
    if (score < 30) return ru ? "лёгкий налёт" : "light";
    if (score < 60) return ru ? "заметно" : "heavy";
    return ru ? "читается как бот" : "reads like a bot";
  }
  function level(score) { return score < 10 ? 0 : score < 30 ? 1 : score < 60 ? 2 : 3; }

  function analyze(text, lang) {
    lang = lang || detectLang(text);
    var words = wordCount(text), hits = findHits(text, lang), s = structureChecks(text, lang);
    var all = hits.concat(s.hits), weighted = 0, byCat = {};
    all.forEach(function (h) { weighted += h.weight; byCat[h.category] = (byCat[h.category] || 0) + 1; });
    var per100 = weighted * 100 / Math.max(words, 1);
    var score = Math.min(100, pyRound(per100 * 8, 0));
    return {
      lang: lang, words: words, hits: all, score: score, weighted: weighted, per_100_words: pyRound(per100, 2),
      verdict: verdict(score, lang), by_category: byCat, metrics: s.metrics
    };
  }

  function stripText(text, lang) {
    lang = lang || detectLang(text);
    var folded = fold(text), spans = [], m;
    C.pats.forEach(function (p) {
      if (p.lang !== lang || !p.cut) return;
      p.rx.lastIndex = 0;
      while ((m = p.rx.exec(folded)) !== null) {
        if (m[0].length === 0) { p.rx.lastIndex++; continue; }
        spans.push([m.index, m.index + m[0].length]);
      }
    });
    spans.sort(function (a, b) { return a[0] - b[0] || a[1] - b[1]; });
    var merged = [];
    spans.forEach(function (sp) {
      if (merged.length && sp[0] <= merged[merged.length - 1][1]) merged[merged.length - 1][1] = Math.max(merged[merged.length - 1][1], sp[1]);
      else merged.push([sp[0], sp[1]]);
    });
    var out = [], last = 0;
    merged.forEach(function (sp) {
      var s = sp[0], e = sp[1];
      out.push(text.slice(last, s));
      var before = pyRstrip(out.join(""));
      var rest = text.slice(e);
      var tail = before.slice(before.lastIndexOf("\n") + 1);
      var plain = before.replace(/[*_`)"»]+$/, "");
      WORD_RE.lastIndex = 0;
      var startsSentence = plain === "" || ".!?\n:".indexOf(plain.charAt(plain.length - 1)) >= 0 || !WORD_RE.test(tail);
      WORD_RE.lastIndex = 0;
      var first = cps(rest)[0];
      if (startsSentence && first && /^\p{L}$/u.test(first)) {
        rest = first.toUpperCase() + rest.slice(first.length);
        text = text.slice(0, e) + rest;
      }
      last = e;
    });
    out.push(text.slice(last));
    var r = out.join("");
    r = r.replace(/[ \t]{2,}/g, " ");
    r = r.replace(/[ \t]+\n/g, "\n");
    r = r.replace(/\n{3,}/g, "\n\n").replace(/^\n+/, "");
    r = r.replace(new RegExp("((?<![^\\n])|[.!?][" + WS + "]+)[,;][ \\t]*", "gu"), "$1");
    r = r.replace(/(^|\n)([а-яёa-z])/g, function (_m, a, b) { return a + b.toUpperCase(); });
    return { text: r, removed: merged.length };
  }

  // ---- result rendering (browser only; the Python checker has no HTML)
  function levelClass(score) { return ["A", "B", "D", "F"][level(score)]; }

  function markedHtml(text, hits) {
    var spans = hits.filter(function (h) { return h.end > h.start; }).map(function (h) { return [h.start, h.end]; })
      .sort(function (a, b) { return a[0] - b[0] || a[1] - b[1]; });
    var merged = [];
    spans.forEach(function (s) {
      if (merged.length && s[0] <= merged[merged.length - 1][1]) merged[merged.length - 1][1] = Math.max(merged[merged.length - 1][1], s[1]);
      else merged.push([s[0], s[1]]);
    });
    var h = "", pos = 0;
    merged.forEach(function (s) { h += esc(text.slice(pos, s[0])) + "<mark>" + esc(text.slice(s[0], s[1])) + "</mark>"; pos = s[1]; });
    return h + esc(text.slice(pos));
  }

  function hitItem(h, ui) {
    var where = h.line ? fmt(ui.line, { l: h.line }) + " · " : "";
    var phrase = h.text ? "<mark>«" + esc(h.text) + "»</mark> " : "";
    return '<li class="' + (h.weight >= 3 ? "ug-err" : "ug-warn") + '"><p class="np-fh"><b>' + esc(h.label) + '</b><span class="np-pen">' +
      esc(where + fmt(ui.weight, { w: h.weight })) + '</span></p><p class="np-fx">' + phrase + esc(h.fix) + "</p></li>";
  }

  function hintsText(r, ui) {
    var lines = [fmt(ui.hintsTitle, { s: r.score, v: r.verdict }), ""];
    r.hits.forEach(function (h, i) {
      lines.push((i + 1) + ". " + (h.line ? fmt(ui.line, { l: h.line }) + ": " : "") + (h.text ? "«" + h.text + "» " : "") + "(" + h.label + ") " + h.fix);
    });
    return lines.join("\n");
  }

  function barText(r) {
    var ui = D.ui;
    return fmt(ui.bar, { s: r.score, v: r.verdict, n: r.hits.length + " " + ruPlural(r.hits.length, ui.hitForms) });
  }

  function renderResult(text, r) {
    var ui = D.ui, st = stripText(text, r.lang), n = r.hits.length;
    var h = '<div class="np-score np-g' + levelClass(r.score) + '"><p class="np-num"><span class="sr">' + esc(ui.scoreWord) + "</span><b>" + r.score +
      "</b><span>/100</span></p><div><p class=\"np-grade\"><b>" + esc(r.verdict.charAt(0).toUpperCase() + r.verdict.slice(1)) + "</b></p><p class=\"np-sub\">" +
      esc(r.words + " " + ruPlural(r.words, ui.wordForms) + " · " + n + " " + ruPlural(n, ui.hitForms)) + "</p></div></div>";
    h += '<div class="np-meter" role="meter" aria-label="' + esc(ui.meter) + '" aria-valuemin="0" aria-valuemax="100" aria-valuenow="' + r.score + '"><i style="width:' + r.score + '%"></i></div>';
    h += '<p class="np-next">' + esc(ui.level[level(r.score)]) + "</p>";
    if (n) {
      h += "<h3>" + esc(ui.markedH) + '</h3><div class="dr-marked" tabindex="0" role="region" aria-label="' + esc(ui.markedH) + '">' + markedHtml(text, r.hits) + "</div>";
      var order = D.catOrder, groups = {};
      r.hits.forEach(function (x) { (groups[x.category] = groups[x.category] || []).push(x); });
      h += "<h3>" + esc(ui.hitsH) + "</h3>";
      order.forEach(function (c) {
        if (!groups[c]) return;
        h += '<h4 class="dr-cat">' + esc(D.cats[c].ru) + ' <span>' + groups[c].length + '</span></h4><ul class="ug-checks">' + groups[c].map(function (x) { return hitItem(x, ui); }).join("") + "</ul>";
      });
      h += "<h3>" + esc(ui.hintsH) + '</h3><pre id="dr-hints">' + esc(hintsText(r, ui)) + '</pre><div class="ug-actions"><button type="button" class="btn btn-sm" data-copy="dr-hints" data-kind="hints" data-label="' +
        esc(ui.copyHints) + '">' + esc(ui.copyHints) + "</button></div>";
    } else {
      h += '<p class="ug-ok">' + esc(ui.noHits) + "</p>";
    }
    h += "<h3>" + esc(ui.cleanH) + "</h3>";
    if (st.removed) {
      h += '<p class="ug-small">' + esc(fmt(ui.cleanN, { n: st.removed, f: ruPlural(st.removed, ui.phraseForms) })) + '</p><pre id="dr-clean">' + esc(st.text) +
        '</pre><div class="ug-actions"><button type="button" class="btn btn-sm" data-copy="dr-clean" data-kind="clean" data-label="' + esc(ui.copyClean) + '">' + esc(ui.copyClean) + "</button></div>";
    } else {
      h += '<p class="ug-small">' + esc(ui.cleanNone) + "</p>";
    }
    h += '<div class="ug-cta"><p>' + esc(ui.cta.text) + '</p><a class="btn btn-sm" href="' + esc(ui.cta.href) + '" data-out="result">' + esc(ui.cta.label) + "</a></div>";
    return h;
  }

  function lenBucket(n) { return n < 200 ? "lt200" : n < 1000 ? "200-999" : n < 5000 ? "1000-4999" : "5000+"; }

  var API = {
    setData: setData, analyze: analyze, stripText: stripText, tr: tr, renderResult: renderResult, barText: barText,
    hintsText: function (r) { return hintsText(r, D.ui); }, lenBucket: lenBucket, level: level, wordCount: wordCount
  };
  if (typeof module !== "undefined" && module.exports) { module.exports = API; return; }
  window.DR = API;

  // ---- page wiring
  function init() {
    var dataEl = document.getElementById("ug-data");
    var ta = document.getElementById("dr-text");
    if (!dataEl || !ta) return;
    var out = document.getElementById("ug-lint"), bar = document.getElementById("ug-bar"), status = document.getElementById("dr-status"), count = document.getElementById("dr-count");
    var data = JSON.parse(dataEl.textContent);
    try { setData(data); } catch (e) { status.textContent = data.ui.oldBrowser; return; }
    var ui = data.ui;

    function updateCount() {
      var w = wordCount(ta.value);
      count.textContent = w + " " + ruPlural(w, ui.wordForms);
    }
    function setBar(cls, msg) { bar.className = "ug-bar " + cls; bar.firstElementChild.textContent = msg; }
    function sampleBtns(slug) {
      Array.prototype.forEach.call(document.querySelectorAll("[data-sample]"), function (b) { b.setAttribute("aria-pressed", b.getAttribute("data-sample") === slug ? "true" : "false"); });
    }
    function run(track) {
      var text = ta.value;
      if (pyStrip(text) === "") { out.innerHTML = '<p class="ug-small">' + esc(ui.empty) + "</p>"; setBar("ug-bar-empty", ui.emptyBar); status.textContent = ui.emptyRun; return; }
      var r = analyze(text);
      out.innerHTML = renderResult(text, r);
      setBar(r.score < 30 ? "ug-bar-ok" : "ug-bar-bad", barText(r));
      status.textContent = barText(r);
      if (track && window.ugTrack) window.ugTrack("tool_used", { action: "check", len_bucket: lenBucket(text.length), lang: r.lang, verdict: level(r.score) });
    }
    function loadSample(slug) {
      var s = data.samples.filter(function (x) { return x.slug === slug; })[0];
      if (!s) return false;
      ta.value = s.before; updateCount(); sampleBtns(slug);
      status.textContent = fmt(ui.loaded, { t: s.title });
      return true;
    }
    document.getElementById("dr-run").addEventListener("click", function () { sampleBtns(""); run(true); });
    document.getElementById("dr-clear").addEventListener("click", function () {
      ta.value = ""; updateCount(); sampleBtns(""); run(false); ta.focus();
    });
    ta.addEventListener("input", updateCount);
    Array.prototype.forEach.call(document.querySelectorAll("[data-sample]"), function (b) {
      b.addEventListener("click", function () { loadSample(b.getAttribute("data-sample")); run(true); });
    });
    var q = /[?&]sample=([\w-]+)/.exec(location.search);
    if (q && loadSample(q[1])) run(false);
    else run(false);
    updateCount();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init); else init();
})();
