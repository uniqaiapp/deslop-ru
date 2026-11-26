/* Copy buttons and cookieless analytics. No dependencies, no cookies, no storage. */
(function () {
  var cfg = window.UQ || {};
  var id = "gh-" + Math.random().toString(36).slice(2) + Date.now().toString(36); // in memory only
  function track(event, props) {
    if (!cfg.key || navigator.doNotTrack === "1") return;
    var body = JSON.stringify({
      api_key: cfg.key, event: event, distinct_id: id,
      properties: Object.assign({ $current_url: location.href, $pathname: location.pathname, $referrer: document.referrer,
        $process_person_profile: false, site: "github-pages", repo: cfg.repo }, props || {})
    });
    try {
      if (navigator.sendBeacon) navigator.sendBeacon("https://eu.i.posthog.com/i/v0/e/", new Blob([body], { type: "text/plain" }));
      else fetch("https://eu.i.posthog.com/i/v0/e/", { method: "POST", body: body, keepalive: true, mode: "no-cors" });
    } catch (e) {}
  }
  window.ugTrack = track;
  track("$pageview");

  document.addEventListener("click", function (e) {
    var a = e.target.closest("a[data-out]");
    if (a) track("outbound_click", { placement: a.getAttribute("data-out"), href: a.href });
  });

  document.addEventListener("click", function (e) {
    var b = e.target.closest("[data-copy]");
    if (!b) return;
    var src = document.getElementById(b.getAttribute("data-copy"));
    if (!src) return;
    var text = src.tagName === "PRE" ? src.textContent : (src.querySelector("pre") || src).textContent;
    if (text === "(empty)") text = "";
    var label = b.getAttribute("data-label") || "Copy prompt";
    var flash = function (msg, ok) {
      b.classList.toggle("done", ok); b.textContent = msg;
      setTimeout(function () { b.classList.remove("done"); b.textContent = label; }, ok ? 1600 : 3200);
    };
    var kind = b.getAttribute("data-kind") || "prompt";
    var ok = function () {
      flash("Copied", true);
      track("tool_used", { action: "copy_" + kind, mode: b.getAttribute("data-mode") || "", example: b.getAttribute("data-example") || "custom" });
    };
    var fail = function () {
      // copying was blocked: select the text so the visitor can press Ctrl/Cmd+C, and say so
      try { var rg = document.createRange(); rg.selectNodeContents(src.tagName === "PRE" ? src : (src.querySelector("pre") || src)); var sel = getSelection(); sel.removeAllRanges(); sel.addRange(rg); } catch (x) {}
      flash("Press Ctrl+C to copy", false);
    };
    if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(text).then(ok, fail);
    else {
      var t = document.createElement("textarea"); t.value = text; t.setAttribute("readonly", ""); t.style.cssText = "position:fixed;top:0;left:0;opacity:0";
      document.body.appendChild(t); t.select();
      var done = false;
      try { done = document.execCommand("copy"); } catch (x) {}
      t.remove();
      if (done) ok(); else fail();
    }
  });
})();
