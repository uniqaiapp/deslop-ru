// Reads {data, texts:[text]} on stdin, prints {result, strip, html} per text. Used by tests/test_site.py.
var C = require("../site/checker.js");
var buf = "";
process.stdin.on("data", function (d) { buf += d; });
process.stdin.on("end", function () {
  var inp = JSON.parse(buf);
  C.setData(inp.data);
  var out = inp.texts.map(function (t) {
    var r = C.analyze(t);
    var s = C.stripText(t, r.lang);
    return { result: r, strip: s, html: C.renderResult(t, r) };
  });
  process.stdout.write(JSON.stringify(out));
});
