"use strict";
const assert = require("assert");
const fs = require("fs");
const vm = require("vm");
const path = require("path");
const sourcePath = path.join(__dirname, "../browser/resources/worksheet_csv.js");
const filename = require(sourcePath);
assert.strictEqual(filename("WS-001", "Analysis-analyses_classic_view"), "WS-001-classique.csv");
assert.strictEqual(filename("WS-022", "Analysis-analyses_transposed_view"), "WS-022-transposee.csv");
assert.strictEqual(filename("../../\r\n", "Analysis-analyses_classic_view"), "feuille-de-travail-classique.csv");
assert.strictEqual(filename("WS-001", "Analysis-other"), null);

let handler, expires;
const window = {document: {
  currentScript: {getAttribute: () => "WS-001"},
  addEventListener: (name, callback, capture) => {
    assert.strictEqual(name, "click"); assert.strictEqual(capture, true); handler = callback;
  }}, setTimeout: callback => { expires = callback; }};
vm.runInNewContext(fs.readFileSync(sourcePath, "utf8"), {window});
function button(identifier) {
  const listing = {getAttribute: () => identifier};
  const node = {closest: selector => selector === "[data-listing_identifier]" ? listing : null};
  handler({target: {closest: selector => selector === "button" ? node : null}});
}
function download(href, name) {
  const attrs = {href, download: name};
  const link = {getAttribute: key => attrs[key], setAttribute: (key, value) => { attrs[key] = value; }};
  handler({target: {closest: selector => selector === "a[download]" ? link : null}});
  return attrs.download;
}
button("Analysis-analyses_classic_view");
assert.strictEqual(download("blob:local", "download.csv"), "WS-001-classique.csv");
assert.strictEqual(download("blob:local", "download.csv"), "download.csv");
button("Analysis-analyses_transposed_view");
assert.strictEqual(download("blob:local", "download.csv"), "WS-001-transposee.csv");
button("Analysis-other");
assert.strictEqual(download("blob:local", "download.csv"), "download.csv");
button("Analysis-analyses_classic_view");
assert.strictEqual(download("https://example.invalid/report", "download.csv"), "download.csv");
expires();
assert.strictEqual(download("blob:local", "download.csv"), "download.csv");
button("Analysis-analyses_classic_view");
assert.strictEqual(download("blob:local", "report.pdf"), "report.pdf");
console.log("Worksheet CSV filenames: names, safe characters, native click and download isolation OK");
