"use strict";
const assert = require("assert"), fs = require("fs"), vm = require("vm");
const source = require("path").join(__dirname, "../browser/resources/export_names.js");
const names = require(source);
assert.strictEqual(names.filename("Échantillons", "Client-Sambava", "Samples", "2026-11-27"),
  "Echantillons-Client-Sambava-2026-11-27.csv");
assert.strictEqual(names.filename("WS", "Feuille-de-travail-WS-001", "Analysis-analyses_classic_view", "2026-11-27"), "WS-001-classique.csv");
assert.strictEqual(names.filename("WS", "Feuille-de-travail-WS-001", "Analysis-analyses_transposed_view", "2026-11-27"), "WS-001-transposee.csv");
assert.strictEqual(names.safe("CON"), "CON_");
assert.strictEqual(names.safe("../\r\n"), "Export-LIMS");
const handlers = {}, timers = [], downloads = [], alerts = [];
const reportCode = "LOT.24-" + "A".repeat(170);
let pdfCalls = 0;
const root = {
  document: {
    currentScript: {getAttribute: name => name === "data-export-pdf" ? reportCode : "Echantillon-ECH-DEMO-002"},
    addEventListener: (name, fn) => { handlers[name] = fn; },
    querySelector: () => ({textContent: "Rapports d’analyses"}),
    createElement: () => ({style: {}, click() { downloads.push(this.download); }, remove() {}}),
    body: {appendChild() {}}
  },
  location: {pathname: "/senaite/worksheets/WS-001/print"},
  URL: {createObjectURL: () => "blob:pdf", revokeObjectURL() {}},
  impress: {createPDF: () => { pdfCalls++; return Promise.resolve(new Blob(["pdf"], {type: "application/pdf"})); }},
  setTimeout: fn => { timers.push(fn); },
  alert: value => alerts.push(value), console: {error() {}}
};
vm.runInNewContext(fs.readFileSync(source, "utf8"), {window: root});
handlers.DOMContentLoaded();
assert.strictEqual(root.document.title, names.safe(reportCode));
function click(selectors) {
  let prevented = false;
  handlers.click({target: {closest: selector => selectors[selector] || null},
    preventDefault() { prevented = true; }, stopImmediatePropagation() {}});
  return prevented;
}
function listing(identifier) {
  click({".pagination-controls button": {closest: () => ({getAttribute: () => identifier})}});
}
function link(name) {
  const attrs = {href: "blob:csv", download: name};
  click({"a[download]": {getAttribute: key => attrs[key], setAttribute: (key, value) => { attrs[key] = value; }}});
  return attrs.download;
}
async function run() {
  listing("reports");
  assert.match(link("download.csv"), /^Rapports-d-analyses-Echantillon-ECH-DEMO-002-\d{4}-\d\d-\d\d.csv$/);
  assert.strictEqual(link("download.csv"), "download.csv");
  listing("reports");
  assert.strictEqual(link("ECH-DEMO-002.pdf"), "ECH-DEMO-002.pdf");
  timers.forEach(fn => fn());
  assert.strictEqual(link("download.csv"), "download.csv");
  const button = {disabled: false};
  assert(click({"button[name='impress_download_pdf']": button}));
  assert(button.disabled);
  assert(!click({"button[name='impress_download_pdf']": button}));
  await new Promise(setImmediate);
  assert.deepStrictEqual(downloads, [reportCode + ".pdf"]);
  assert.strictEqual(pdfCalls, 1);
  assert(!button.disabled);
  root.impress.createPDF = () => Promise.resolve(new Blob(["error"], {type: "text/html"}));
  click({"button[name='impress_download_pdf']": button});
  await new Promise(setImmediate);
  assert.strictEqual(downloads.length, 1);
  assert.strictEqual(alerts.length, 1);
  assert(!button.disabled);
  console.log("Export filenames: lists, layouts, Unicode, PDF, errors and unrelated downloads OK");
}
run().catch(error => { console.error(error); process.exitCode = 1; });
