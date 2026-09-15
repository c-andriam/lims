// senaite.trimeta.samplefields - ajustements formulaire Add Sample
//
// 1. Separateur visuel discret au-dessus des sections "Reception" et
//    "Analyse".
// 2. Correctif fiable pour l'affichage inline des erreurs "champ
//    requis" sur les widgets complexes (Client, Contact, Sample Type,
//    Date Sampled).
// 3. Clavier/validation numerique amelioree pour les champs Poids,
//    Quantite, etc.
//
// L'autocompletion des champs libres est dans field_suggestions.js,
// charge aussi sur la page de l'echantillon et base_edit.
(function () {
  "use strict";

  var NUMERIC_FIELDS = [
    "ReceptionWeight",
    "QuantityReceived",
    "QuantityUnderAnalysis",
    "TechSampleWeight",
    "PodLength"
  ];

  // ---------------------------------------------------------------
  // 1. Separateur visuel
  // ---------------------------------------------------------------
  function insertOneSeparator(id, firstFieldName, label) {
    var target = document.querySelector(
      'tr[fieldName="' + firstFieldName + '-0"]'
    ) || document.querySelector('tr[fieldName="' + firstFieldName + '"]');
    if (!target) {
      return false;
    }
    if (document.getElementById(id)) {
      return true;
    }
    var row = document.createElement("tr");
    row.id = id;
    row.innerHTML =
      '<td colspan="10" style="' +
      'background:#f7f7f7;border-top:2px solid #ddd;padding:4px 8px;' +
      'font-size:11px;font-weight:600;text-transform:uppercase;' +
      'letter-spacing:0.03em;color:#888;">' + label + '</td>';
    target.parentNode.insertBefore(row, target);
    return true;
  }

  function insertSeparator() {
    var a = insertOneSeparator(
      "trimeta-reception-separator", "SampleCode", "Reception"
    );
    var b = insertOneSeparator(
      "trimeta-analyse-separator", "AnalysisSheetNumber", "Analyse"
    );
    return a && b;
  }

  // ---------------------------------------------------------------
  // 2. Correctif erreurs inline (widgets complexes)
  // ---------------------------------------------------------------
  function findFieldElement($, fieldname) {
    var selectors = [
      "#" + fieldname,
      "#archetypes-fieldname-" + fieldname,
      '[data-fieldname="' + fieldname + '"]',
      '[data-name="' + fieldname + '"]'
    ];
    for (var i = 0; i < selectors.length; i++) {
      var el;
      try {
        el = $(selectors[i]);
      } catch (e) {
        continue;
      }
      if (el.length > 0) {
        return el.first();
      }
    }
    return null;
  }

  function ensureErrorBox(container) {
    var box = container.find("> div.fieldErrorBox");
    if (box.length === 0) {
      box = window.jQuery('<div class="fieldErrorBox"></div>')
        .appendTo(container);
    }
    return box;
  }

  function fixInlineErrors(fielderrors) {
    if (!fielderrors) {
      return;
    }
    var $ = window.jQuery;
    Object.keys(fielderrors).forEach(function (fieldname) {
      var field = findFieldElement($, fieldname);
      if (!field) {
        return;
      }
      var container = field.closest(".field");
      if (container.length === 0) {
        return;
      }
      container.addClass("error");
      var box = ensureErrorBox(container);
      box.text(fielderrors[fieldname]);
    });
  }

  var ajaxWatcherRegistered = false;

  function watchAjaxSubmit() {
    if (!window.jQuery || ajaxWatcherRegistered) {
      return;
    }
    ajaxWatcherRegistered = true;
    window.jQuery(document).ajaxComplete(function (event, xhr) {
      if (!xhr || !xhr.responseJSON) {
        return;
      }
      var data = xhr.responseJSON;
      if (data && data.errors && data.errors.fielderrors) {
        fixInlineErrors(data.errors.fielderrors);
      }
    });
  }

  // ---------------------------------------------------------------
  // 3. Champs numeriques : clavier/validation amelioree
  // ---------------------------------------------------------------
  function findAllFieldElements($, basename) {
    // Couvre toutes les colonnes (arnum) du formulaire multi-echantillons :
    // basename-0, basename-1, basename-2, ...
    var results = [];
    var selectors = [
      '[id^="' + basename + '-"]',
      '[id^="archetypes-fieldname-' + basename + '-"]',
      '[data-fieldname^="' + basename + '-"]',
      '[data-name^="' + basename + '-"]'
    ];
    var seen = {};
    selectors.forEach(function (sel) {
      var found;
      try {
        found = $(sel);
      } catch (e) {
        return;
      }
      found.each(function () {
        var el = this;
        var key = el.tagName + ":" +
          (el.id || el.getAttribute("data-fieldname") ||
           el.getAttribute("data-name"));
        if (!seen[key]) {
          seen[key] = true;
          results.push($(el));
        }
      });
    });
    return results;
  }

  function enhanceNumericFields() {
    var $ = window.jQuery;
    NUMERIC_FIELDS.forEach(function (fieldname) {
      var elements = findAllFieldElements($, fieldname);
      elements.forEach(function (field) {
        var input = field.is("input") ? field[0] :
          field.find("input[type=text]").first()[0];
        if (!input || input.getAttribute("data-trimeta-numeric")) {
          return;
        }
        input.setAttribute("data-trimeta-numeric", "1");
        input.setAttribute("inputmode", "decimal");
        input.addEventListener("keypress", function (e) {
          var char = String.fromCharCode(e.which);
          if (!/[0-9.,]/.test(char)) {
            e.preventDefault();
          }
        });
      });
    });
  }

  // ---------------------------------------------------------------
  // Init
  // ---------------------------------------------------------------
  function tryInit(retries) {
    var sepDone = insertSeparator();
    var jqReady = !!window.jQuery;
    if (jqReady) {
      watchAjaxSubmit();
      enhanceNumericFields();
    }
    if (sepDone && jqReady) {
      return;
    }
    if (retries <= 0) {
      return;
    }
    setTimeout(function () {
      tryInit(retries - 1);
    }, 300);
  }

  document.addEventListener("DOMContentLoaded", function () {
    tryInit(20);
    // Colonnes ajoutees dynamiquement via "+Add" (idempotent).
    setInterval(function () {
      if (window.jQuery) {
        enhanceNumericFields();
      }
    }, 2000);
  });
})();
