// Nommer uniquement le CSV cree par l'export natif de cette Work Sheet.
(function (root) {
  "use strict";
  function filename(worksheet, identifier) {
    var layout;
    if (/-analyses_classic_view$/.test(identifier)) { layout = "classique"; }
    if (/-analyses_transposed_view$/.test(identifier)) { layout = "transposee"; }
    if (!layout) { return null; }
    var name = String(worksheet || "").replace(/[^A-Za-z0-9_-]+/g, "-")
      .replace(/^-+|-+$/g, "").slice(0, 100) || "feuille-de-travail";
    return name + "-" + layout + ".csv";
  }
  if (typeof module !== "undefined" && module.exports) { module.exports = filename; }
  if (!root.document) { return; }
  var script = root.document.currentScript;
  var worksheet = script && script.getAttribute("data-worksheet-id");
  var pending = null;
  root.document.addEventListener("click", function (event) {
    var target = event.target;
    if (!target || !target.closest) { return; }
    var link = target.closest("a[download]");
    if (link && pending && link.getAttribute("download") === "download.csv" &&
        /^blob:/.test(link.getAttribute("href") || "")) {
      link.setAttribute("download", pending);
      pending = null;
      return;
    }
    var button = target.closest("button");
    var listing = button && button.closest("[data-listing_identifier]");
    if (!listing) { return; }
    pending = filename(worksheet, listing.getAttribute("data-listing_identifier") || "");
    // Le telechargement natif est synchrone au clic du bouton. Ne pas
    // renommer un autre fichier declenche ulterieurement sur la page.
    root.setTimeout(function () { pending = null; }, 0);
  }, true);
}(typeof window !== "undefined" ? window : this));
