"use strict";
const assert = require("assert");
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const sourcePath = path.join(__dirname, "../browser/resources/worksheet_csv_format.js");
const normalize = require(sourcePath);
const row = values => values.map(value => JSON.stringify(value)).join(",");
const native = row(["Code", "Resultat", "Analyste"]) + "\n" +
  row(['ECH-"VAN", été', "2.0500", 'Marie "Test"']);
assert.strictEqual(normalize(native),
  '"Code","Resultat","Analyste"\r\n"ECH-""VAN"", été","2.0500","Marie ""Test"""');
assert.strictEqual(normalize(row(["ligne 1\nligne 2", "C:\\dossier", "0", "<0.5"])),
  '"ligne 1\nligne 2","C:\\dossier","0","<0.5"');
assert.strictEqual(normalize('\uFEFF"A","B"\r\n"x",\r\n'), '"A","B"\r\n"x",""');
assert.strictEqual(normalize('"A","B"\n'), '"A","B"');
assert.strictEqual(normalize('0,false,null,'), '"0","false","",""');
assert.strictEqual(normalize('"A",["x","y"]'), '"A","[""x"",""y""]"');
assert.throws(() => normalize('"A"\n"unfinished'));

async function testDownload() {
  let handler;
  const downloads = [], fetched = [], timers = [], urls = [], alerts = [];
  let outputBlob;
  const click = target => {
    const event = {target, prevented:false,
      preventDefault() { this.prevented = true; }, stopImmediatePropagation() {}};
    handler(event);
    if (!event.prevented && target.download) { downloads.push(target); }
    return event;
  };
  const link = (href, download) => ({href, download, style:{},
    closest(selector) { return selector === "a[download]" ? this : null; },
    getAttribute(name) { return this[name]; },
    click() { click(this); }, remove() {}});
  const root = {
    document: {
      addEventListener(name, callback, capture) {
        assert.strictEqual(name, "click"); assert.strictEqual(capture, true); handler = callback;
      },
      createElement() { return link("", ""); }, body:{appendChild() {}}
    },
    fetch(url) { fetched.push(url); return Promise.resolve({ok:true, text:() => Promise.resolve(native)}); },
    Blob,
    URL:{createObjectURL(blob) { outputBlob = blob; return "blob:converted"; },
      revokeObjectURL(url) { urls.push(url); }},
    setTimeout(callback, delay) { timers.push({callback,delay}); },
    console:{error() {}}, alert(message) { alerts.push(message); }
  };
  vm.runInNewContext(fs.readFileSync(sourcePath, "utf8"), {window:root});
  const button = identifier => {
    const listing = {getAttribute:() => identifier};
    const node = {closest:selector => selector === "[data-listing_identifier]" ? listing : null};
    handler({target:{closest:selector => selector === ".pagination-controls button" ? node : null}});
  };
  button("Analysis-analyses_classic_view");
  assert(click(link("blob:native", "WS-001-classique.csv")).prevented);
  await new Promise(resolve => setImmediate(resolve));
  assert.strictEqual(downloads.length, 1);
  assert.strictEqual(downloads[0].download, "WS-001-classique.csv");
  assert.strictEqual(await outputBlob.text(), normalize(native));
  assert.deepStrictEqual(Array.from(new Uint8Array(await outputBlob.arrayBuffer()).slice(0, 3)),
    [239, 187, 191]);
  assert.deepStrictEqual(fetched, ["blob:native"]);
  button("Analysis-analyses_transposed_view");
  assert(click(link("blob:transpose", "WS-001-transposee.csv")).prevented);
  await new Promise(resolve => setImmediate(resolve));
  assert.strictEqual(downloads[1].download, "WS-001-transposee.csv");
  button("Analysis-other");
  assert(click(link("blob:other", "Clients-LIMS-2026-11-27.csv")).prevented);
  await new Promise(resolve => setImmediate(resolve));
  assert.strictEqual(downloads[2].download, "Clients-LIMS-2026-11-27.csv");
  button("Analysis-analyses_classic_view");
  assert(!click(link("blob:pdf", "report.pdf")).prevented);
  timers.filter(timer => timer.delay === 0).forEach(timer => timer.callback());
  assert(!click(link("blob:later", "download.csv")).prevented);
  button("");
  assert(!click(link("blob:not-a-listing", "download.csv")).prevented);
  assert.strictEqual(fetched.length, 3);
  assert.deepStrictEqual(alerts, []);
  const completed = downloads.length;
  root.fetch = () => Promise.resolve({ok:true, text:() => Promise.resolve('"unfinished')});
  button("Analysis-analyses_classic_view");
  assert(click(link("blob:invalid", "WS-001-classique.csv")).prevented);
  await new Promise(resolve => setImmediate(resolve));
  assert.strictEqual(downloads.length, completed);
  assert.strictEqual(alerts.length, 1);
}

testDownload().then(() => console.log("Listing CSV: quotes, unicode, multiline, precision and scoped downloads OK"))
  .catch(error => { console.error(error); process.exitCode = 1; });
