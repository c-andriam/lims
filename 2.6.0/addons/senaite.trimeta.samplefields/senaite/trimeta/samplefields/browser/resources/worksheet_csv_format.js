// Le CSV natif utilise JSON.stringify au lieu de l'echappement CSV.
// Convertir uniquement les exports des deux grilles de Work Sheet.
(function (root) {
  "use strict";

  function csvCell(value) {
    if (value === null || value === undefined) { value = ""; }
    if (typeof value === "object") { value = JSON.stringify(value); }
    return '"' + String(value).replace(/"/g, '""') + '"';
  }

  function decodeRow(line) {
    var cells = [], start = 0, quoted = false, escaped = false, depth = 0;
    for (var i = 0; i < line.length; i++) {
      var character = line.charAt(i);
      if (quoted) {
        if (escaped) { escaped = false; }
        else if (character === "\\") { escaped = true; }
        else if (character === '"') { quoted = false; }
      } else if (character === '"') { quoted = true; }
      else if (character === "[" || character === "{") { depth += 1; }
      else if (character === "]" || character === "}") { depth -= 1; }
      else if (character === "," && depth === 0) {
        cells.push(line.slice(start, i));
        start = i + 1;
      }
    }
    if (quoted || depth !== 0) { throw new Error("Invalid native CSV row"); }
    cells.push(line.slice(start));
    return cells.map(function (cell) {
      return csvCell(cell.trim() === "" ? "" : JSON.parse(cell));
    }).join(",");
  }

  function normalize(csv) {
    var lines = String(csv).replace(/^\uFEFF/, "").split(/\r?\n/);
    if (lines.length > 1 && lines[lines.length - 1] === "") { lines.pop(); }
    return lines.map(decodeRow).join("\r\n");
  }

  if (typeof module !== "undefined" && module.exports) { module.exports = normalize; }
  if (!root.document) { return; }

  var pending = false;
  root.document.addEventListener("click", function (event) {
    var target = event.target;
    if (!target || !target.closest) { return; }
    var link = target.closest("a[download]");
    if (link && pending && /^blob:/.test(link.getAttribute("href") || "")) {
      var name = link.getAttribute("download") || "";
      if (name !== "download.csv" && !/-(classique|transposee)\.csv$/.test(name)) { return; }
      pending = false;
      event.preventDefault();
      event.stopImmediatePropagation();
      var original = link.getAttribute("href");
      root.fetch(original).then(function (response) {
        if (!response.ok) { throw new Error("CSV unavailable"); }
        return response.text();
      }).then(function (text) {
        var csv = normalize(text);
        var output = root.document.createElement("a");
        var url = root.URL.createObjectURL(new root.Blob(["\uFEFF", csv], {
          type: "text/csv;charset=UTF-8"
        }));
        output.href = url;
        output.download = name;
        output.style.display = "none";
        root.document.body.appendChild(output);
        output.click();
        output.remove();
        link.remove();
        root.URL.revokeObjectURL(original);
        root.setTimeout(function () { root.URL.revokeObjectURL(url); }, 1000);
      }).catch(function (error) {
        root.console.error("Worksheet CSV export failed", error);
        root.alert("Impossible de préparer le fichier CSV. Rechargez la page puis réessayez.");
      });
      return;
    }
    var button = target.closest(".pagination-controls button");
    var listing = button && button.closest("[data-listing_identifier]");
    if (!listing) { return; }
    pending = /-analyses_(classic|transposed)_view$/.test(
      listing.getAttribute("data-listing_identifier") || "");
    root.setTimeout(function () { pending = false; }, 0);
  }, true);
}(typeof window === "undefined" ? {} : window));
