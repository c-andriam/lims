// Noms des exports generes dans le navigateur; le contenu reste natif.
(function (root) {
  "use strict";
  function safe(value) {
    var text = String(value || "");
    if (text.normalize) { text = text.normalize("NFKD"); }
    text = text.replace(/[\u0300-\u036f]/g, "").replace(/[^A-Za-z0-9_-]+/g, "-")
      .replace(/^-+|-+$/g, "").slice(0, 150);
    if (/^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])$/i.test(text)) { text += "_"; }
    return text || "Export-LIMS";
  }
  function filename(title, context, identifier, date) {
    if (/-analyses_(classic|transposed)_view$/.test(identifier)) {
      return safe(context.replace(/^Feuille-de-travail-/, "")) +
        (/-analyses_classic_view$/.test(identifier) ? "-classique.csv" : "-transposee.csv");
    }
    return safe(title) + "-" + safe(context) + "-" + date + ".csv";
  }
  if (typeof module !== "undefined" && module.exports) {
    module.exports = {safe: safe, filename: filename};
  }
  if (!root.document) { return; }
  var script = root.document.currentScript;
  var context = script.getAttribute("data-export-context") || "LIMS";
  var pdf = script.getAttribute("data-export-pdf") || context;
  var pending = null;
  function download(blob, name) {
    var link = root.document.createElement("a");
    var url = root.URL.createObjectURL(blob);
    link.href = url; link.download = name; link.style.display = "none";
    root.document.body.appendChild(link); link.click(); link.remove();
    root.setTimeout(function () { root.URL.revokeObjectURL(url); }, 1000);
  }
  root.document.addEventListener("DOMContentLoaded", function () {
    if (/\/(print|sticker|stickers)(\/|$)/.test(root.location.pathname)) {
      root.document.title = safe(pdf);
    }
  });
  root.document.addEventListener("click", function (event) {
    var target = event.target;
    if (!target || !target.closest) { return; }
    var link = target.closest("a[download]");
    if (link && pending && link.getAttribute("download") === "download.csv" &&
        /^blob:/.test(link.getAttribute("href") || "")) {
      link.setAttribute("download", pending); pending = null; return;
    }
    var button = target.closest("button[name='impress_download_pdf']");
    if (button && root.impress && !button.disabled) {
      event.preventDefault(); event.stopImmediatePropagation();
      button.disabled = true;
      // Reutiliser le PDF courant du moteur natif, sans sauvegarde/publication.
      root.impress.createPDF().then(function (blob) {
        if (blob.type.split(";")[0] !== "application/pdf") { throw new Error("PDF unavailable"); }
        download(blob, pdf + ".pdf");
      }).catch(function (error) {
        root.console.error("PDF export failed", error);
        root.alert("Impossible de preparer le PDF. Rechargez la page puis reessayez.");
      }).then(function () { button.disabled = false; });
      return;
    }
    button = target.closest(".pagination-controls button");
    var listing = button && button.closest("[data-listing_identifier]");
    if (!listing) { return; }
    var heading = root.document.querySelector("h1.documentFirstHeading, h1");
    var now = new Date();
    var date = [now.getFullYear(), ("0" + (now.getMonth() + 1)).slice(-2),
      ("0" + now.getDate()).slice(-2)].join("-");
    pending = filename(heading ? heading.textContent.trim() : "Export", context,
      listing.getAttribute("data-listing_identifier") || "", date);
    root.setTimeout(function () { pending = null; }, 0);
  }, true);
}(typeof window === "undefined" ? {} : window));
