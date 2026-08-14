// senaite.trimeta.samplefields - ajustements formulaire Add Sample
//
// 1. Separateur visuel discret au-dessus de la section "Reception".
// 2. Correctif fiable pour l'affichage inline des erreurs "champ
//    requis" sur les widgets complexes (Client, Contact, Sample Type,
//    Date Sampled).
// 3. Autocompletion dynamique et partagee (façon barre de recherche
//    YouTube) pour Designation, Sample Condition, Packaging
//    Condition, Origin et Received By : champ libre au depart, les
//    valeurs validees sont proposees ensuite a tous les postes.
// 4. Clavier/validation numerique amelioree pour les champs Poids,
//    Quantite, etc.
(function () {
  "use strict";

  var SUGGEST_FIELDS = [
    "Designation",
    "SampleCondition",
    "PackagingCondition",
    "Origin",
    "SupplierCustomerDetail",
    "Contract",
    "Aroma",
    "Color",
    "Texture",
    "AromaDevelopment"
  ];

  var NUMERIC_FIELDS = [
    "ReceptionWeight",
    "QuantityReceived",
    "QuantityUnderAnalysis",
    "TechSampleWeight",
    "PodLength"
  ];

  var API_URL = null; // resolu au premier usage

  function getApiUrl() {
    if (API_URL === null) {
      var scriptTag = document.getElementById(
        "trimeta-samplefields-script"
      );
      var portalUrl = scriptTag ?
        scriptTag.getAttribute("data-portal-url") : null;
      if (!portalUrl) {
        var parts = window.location.href.split("/senaite/");
        portalUrl = parts.length > 1 ? parts[0] + "/senaite" : "";
      }
      API_URL = portalUrl + "/@@trimeta-suggestions";
    }
    return API_URL;
  }

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
      // Si la creation a reussi, les valeurs viennent d'etre
      // enregistrees cote serveur comme suggestions (evenement
      // IObjectAddedEvent) : on invalide notre cache local pour que
      // la prochaine ouverture de suggestion les propose bien.
      if (data && !data.errors) {
        suggestionCache = {};
      }
    });
  }

  // ---------------------------------------------------------------
  // 3. Autocompletion dynamique partagee
  // ---------------------------------------------------------------
  var suggestionCache = {};

  function fetchSuggestions(fieldname, callback) {
    if (suggestionCache[fieldname]) {
      callback(suggestionCache[fieldname]);
      return;
    }
    var xhr = new XMLHttpRequest();
    xhr.open(
      "GET",
      getApiUrl() + "?field=" + encodeURIComponent(fieldname),
      true
    );
    xhr.onload = function () {
      if (xhr.status === 200) {
        try {
          var data = JSON.parse(xhr.responseText);
          suggestionCache[fieldname] = data.suggestions || [];
          callback(suggestionCache[fieldname]);
        } catch (e) {
          callback([]);
        }
      } else {
        callback([]);
      }
    };
    xhr.onerror = function () {
      callback([]);
    };
    xhr.send();
  }

  function removeSuggestionRemote(fieldname, value, callback) {
    var xhr = new XMLHttpRequest();
    xhr.open("POST", getApiUrl(), true);
    xhr.setRequestHeader(
      "Content-Type", "application/x-www-form-urlencoded"
    );
    xhr.onload = function () {
      if (suggestionCache[fieldname]) {
        suggestionCache[fieldname] = suggestionCache[fieldname].filter(
          function (v) { return v !== value; }
        );
      }
      if (callback) { callback(); }
    };
    xhr.send(
      "action=remove&field=" + encodeURIComponent(fieldname) +
      "&value=" + encodeURIComponent(value)
    );
  }

  function closeAllDropdowns() {
    document.querySelectorAll(".trimeta-suggest-dropdown").forEach(
      function (el) { el.remove(); }
    );
  }

  function buildDropdown(input, fieldname, filterText) {
    closeAllDropdowns();
    fetchSuggestions(fieldname, function (items) {
      var lower = (filterText || "").toLowerCase();
      var filtered = items.filter(function (v) {
        return v.toLowerCase().indexOf(lower) !== -1;
      });
      // On affiche toujours le menu (meme vide) pour signaler que ce
      // champ accepte des suggestions dynamiques, meme s'il n'y en a
      // pas encore d'enregistree.

      var dropdown = document.createElement("div");
      dropdown.className = "trimeta-suggest-dropdown";
      dropdown.style.cssText =
        "position:absolute;z-index:9999;background:#fff;" +
        "border:1px solid #d6d6d6;border-radius:2px;" +
        "box-shadow:0 2px 6px rgba(0,0,0,0.12);" +
        "max-height:200px;overflow-y:auto;font-size:13px;" +
        "font-family:inherit;";

      var rect = input.getBoundingClientRect();
      dropdown.style.left = (rect.left + window.scrollX) + "px";
      dropdown.style.top = (rect.bottom + window.scrollY) + "px";
      dropdown.style.width = Math.max(rect.width, 200) + "px";

      // En-tete discret, dans le style des colonnes du widget de
      // recherche natif (ex: "Nom" / "Identifiant" pour Client).
      var header = document.createElement("div");
      header.textContent = "Suggestions";
      header.style.cssText =
        "padding:6px 10px;font-weight:600;font-size:11px;" +
        "text-transform:uppercase;letter-spacing:0.03em;" +
        "color:#888;background:#fafafa;" +
        "border-bottom:1px solid #eee;";
      dropdown.appendChild(header);

      filtered.forEach(function (value) {
        var row = document.createElement("div");
        row.style.cssText =
          "display:flex;justify-content:space-between;" +
          "align-items:center;padding:6px 10px;cursor:pointer;" +
          "border-bottom:1px solid #f5f5f5;";
        row.onmouseenter = function () {
          row.style.background = "#f0f0f0";
          remove.style.visibility = "visible";
        };
        row.onmouseleave = function () {
          row.style.background = "";
          remove.style.visibility = "hidden";
        };

        var label = document.createElement("span");
        label.textContent = value;
        label.style.cssText = "flex:1;color:#333;";
        label.onmousedown = function (e) {
          e.preventDefault();
          input.value = value;
          input.dispatchEvent(new Event("change", { bubbles: true }));
          closeAllDropdowns();
        };

        var remove = document.createElement("span");
        remove.textContent = "\u2715";
        remove.title = "Remove suggestion";
        remove.style.cssText =
          "color:#aaa;padding:2px 5px;margin-left:6px;" +
          "cursor:pointer;visibility:hidden;font-size:11px;" +
          "border-radius:2px;";
        remove.onmouseenter = function () {
          remove.style.color = "#fff";
          remove.style.background = "#c00";
        };
        remove.onmouseleave = function () {
          remove.style.color = "#aaa";
          remove.style.background = "";
        };
        remove.onmousedown = function (e) {
          e.preventDefault();
          e.stopPropagation();
          removeSuggestionRemote(fieldname, value, function () {
            buildDropdown(input, fieldname, input.value);
          });
        };

        row.appendChild(label);
        row.appendChild(remove);
        dropdown.appendChild(row);
      });

      if (filtered.length === 0) {
        var empty = document.createElement("div");
        empty.textContent = "No suggestions yet";
        empty.style.cssText =
          "padding:8px 10px;color:#bbb;font-style:italic;font-size:12px;";
        dropdown.appendChild(empty);
      }

      document.body.appendChild(dropdown);
    });
  }

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

  var globalClickListenerRegistered = false;

  function registerGlobalClickListener() {
    if (globalClickListenerRegistered) {
      return;
    }
    globalClickListenerRegistered = true;
    document.addEventListener("click", function (e) {
      if (!e.target.matches || !e.target.matches("input")) {
        closeAllDropdowns();
      }
    });
  }

  function addSuggestionRemote(fieldname, value) {
    value = (value || "").trim();
    if (!value) {
      return;
    }
    var xhr = new XMLHttpRequest();
    xhr.open("POST", getApiUrl(), true);
    xhr.setRequestHeader(
      "Content-Type", "application/x-www-form-urlencoded"
    );
    xhr.onload = function () {
      // Invalide le cache pour ce champ afin que la prochaine
      // ouverture du menu propose bien la valeur tout juste ajoutee.
      delete suggestionCache[fieldname];
    };
    xhr.send(
      "action=add&field=" + encodeURIComponent(fieldname) +
      "&value=" + encodeURIComponent(value)
    );
  }

  function attachSuggestBehavior(fieldname) {
    var $ = window.jQuery;
    var elements = findAllFieldElements($, fieldname);
    elements.forEach(function (field) {
      var input = field.is("input") ? field[0] :
        field.find("input[type=text]").first()[0];
      if (!input || input.getAttribute("data-trimeta-bound")) {
        return;
      }
      input.setAttribute("data-trimeta-bound", "1");

      input.addEventListener("focus", function () {
        buildDropdown(input, fieldname, input.value);
      });
      input.addEventListener("input", function () {
        buildDropdown(input, fieldname, input.value);
      });
      // Valide (= enregistre comme suggestion future) des que le
      // champ perd le focus (changement de champ) ou sur Entree.
      input.addEventListener("blur", function () {
        addSuggestionRemote(fieldname, input.value);
        setTimeout(closeAllDropdowns, 150);
      });
      input.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.keyCode === 13) {
          addSuggestionRemote(fieldname, input.value);
        }
      });
    });
    registerGlobalClickListener();
  }

  function attachAllSuggestFields() {
    SUGGEST_FIELDS.forEach(attachSuggestBehavior);
  }

  // ---------------------------------------------------------------
  // 4. Champs numeriques : clavier/validation amelioree
  // ---------------------------------------------------------------
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
      attachAllSuggestFields();
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
    // Reverifie periodiquement pour couvrir les colonnes ajoutees
    // dynamiquement via le bouton "+Add" (idempotent grace aux
    // gardes data-trimeta-*).
    setInterval(function () {
      if (window.jQuery) {
        attachAllSuggestFields();
        enhanceNumericFields();
      }
    }, 2000);
  });
})();
