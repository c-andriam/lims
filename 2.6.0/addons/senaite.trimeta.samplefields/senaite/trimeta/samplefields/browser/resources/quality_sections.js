// senaite.trimeta.samplefields - separateurs de sous-sections
//
// La section "Assurance Qualite" compte 41 champs. Sans reperes
// visuels, le formulaire est une longue liste indifferenciee ou l'on
// ne sait plus si l'on remplit l'extraction ou le dosage HPLC.
//
// Ce script insere un intitule avant le premier champ de chaque
// sous-section. Les sous-sections sont definies cote Python
// (qualitydata/extender.py, constante SECTIONS) et transmises ici par
// le viewlet: une seule source de verite.
//
// Le script s'adapte a deux rendus differents:
//   - le formulaire d'ajout d'echantillon, ou chaque champ est une
//     ligne de tableau <tr fieldName="X-0">;
//   - le formulaire de modification Archetypes, ou chaque champ est un
//     bloc <div id="archetypes-fieldname-X">.
// S'il ne reconnait ni l'un ni l'autre, il ne fait rien.
(function () {
  "use strict";

  var STYLE_ID = "trimeta-qa-section-style";
  var PREFIX = "trimeta-qa-section-";

  function getSections() {
    var raw = window.TRIMETA_QA_SECTIONS;
    return Object.prototype.toString.call(raw) === "[object Array]"
      ? raw
      : [];
  }

  // Retourne l'element conteneur du champ et le type de rendu detecte.
  function findFieldNode(fieldName) {
    var row = document.querySelector('tr[fieldName="' + fieldName + '-0"]')
      || document.querySelector('tr[fieldName="' + fieldName + '"]');
    if (row) {
      return { node: row, layout: "table" };
    }
    var block = document.getElementById(
      "archetypes-fieldname-" + fieldName
    );
    if (block) {
      return { node: block, layout: "block" };
    }
    return null;
  }

  function injectStyle() {
    if (document.getElementById(STYLE_ID)) {
      return;
    }
    var style = document.createElement("style");
    style.id = STYLE_ID;
    style.textContent =
      "." + PREFIX + "label {" +
      "  background: #f7f7f7;" +
      "  border-top: 2px solid #ddd;" +
      "  padding: 4px 8px;" +
      "  font-size: 11px;" +
      "  font-weight: 600;" +
      "  text-transform: uppercase;" +
      "  letter-spacing: 0.03em;" +
      "  color: #888;" +
      "  margin: 1.25em 0 0.5em;" +
      "}";
    document.head.appendChild(style);
  }

  function insertSeparator(section) {
    var id = PREFIX + section.id;
    if (document.getElementById(id)) {
      return true;
    }
    var fields = section.fields || [];
    for (var i = 0; i < fields.length; i++) {
      var found = findFieldNode(fields[i]);
      if (!found) {
        continue;
      }
      var separator;
      if (found.layout === "table") {
        separator = document.createElement("tr");
        separator.innerHTML =
          '<td colspan="10" class="' + PREFIX + 'label">' +
          section.title + "</td>";
      } else {
        separator = document.createElement("div");
        separator.className = PREFIX + "label";
        separator.textContent = section.title;
      }
      separator.id = id;
      found.node.parentNode.insertBefore(separator, found.node);
      return true;
    }
    // Aucun champ de la sous-section n'est rendu sur cette page.
    return false;
  }

  function insertAll() {
    var sections = getSections();
    if (!sections.length) {
      return true;
    }
    injectStyle();
    var done = 0;
    for (var i = 0; i < sections.length; i++) {
      if (insertSeparator(sections[i])) {
        done += 1;
      }
    }
    return done > 0;
  }

  // Le formulaire d'ajout se construit en AJAX: on retente quelques
  // fois, puis on abandonne silencieusement plutot que de tourner
  // indefiniment.
  var attempts = 0;
  var MAX_ATTEMPTS = 20;

  function tryInsert() {
    attempts += 1;
    if (insertAll() || attempts >= MAX_ATTEMPTS) {
      return;
    }
    window.setTimeout(tryInsert, 250);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", tryInsert);
  } else {
    tryInsert();
  }
})();
