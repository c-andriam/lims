// senaite.trimeta.samplefields - suggestions des champs libres
//
// Charge sur le formulaire de creation d'echantillon, la page d'un
// echantillon (en-tete modifiable) et base_edit. Les lots de solvants
// et numeros de serie de l'Assurance Qualite se saisissent APRES la
// creation: sans ce script sur ces pages, le "rajout memorise" demande
// n'etait jamais propose.
//
// La liste des champs vient de Python (suggestions.SUGGESTION_FIELDS),
// publiee par le viewlet dans window.TRIMETA_SUGGEST_FIELDS: une seule
// source de verite.
(function () {
  "use strict";

  var SCRIPT_ID = "trimeta-suggestions-script";
  var cache = {};

  function getFields() {
    return window.TRIMETA_SUGGEST_FIELDS || [];
  }

  function getApiUrl() {
    var tag = document.getElementById(SCRIPT_ID);
    var portalUrl = tag ? tag.getAttribute("data-portal-url") : "";
    return portalUrl + "/@@trimeta-suggestions";
  }

  // Formulaire de creation: "Champ-0", "Champ-1"... ; ailleurs: "Champ".
  function findInputs(fieldname) {
    var pattern = new RegExp("^" + fieldname + "(-\\d+)?$");
    var inputs = document.querySelectorAll("input[type=text][name]");
    return Array.prototype.filter.call(inputs, function (input) {
      return pattern.test(input.name);
    });
  }

  function fetchSuggestions(fieldname, callback) {
    if (cache[fieldname]) {
      callback(cache[fieldname]);
      return;
    }
    var xhr = new XMLHttpRequest();
    xhr.open("GET", getApiUrl() + "?field=" + encodeURIComponent(fieldname), true);
    xhr.onload = function () {
      var items = [];
      if (xhr.status === 200) {
        try {
          items = JSON.parse(xhr.responseText).suggestions || [];
        } catch (e) {
          items = [];
        }
      }
      cache[fieldname] = items;
      callback(items);
    };
    xhr.onerror = function () { callback([]); };
    xhr.send();
  }

  function postSuggestion(action, fieldname, value, callback) {
    value = (value || "").trim();
    if (!value) {
      return;
    }
    var xhr = new XMLHttpRequest();
    xhr.open("POST", getApiUrl(), true);
    xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
    xhr.onload = function () {
      delete cache[fieldname];
      if (callback) { callback(); }
    };
    xhr.send("action=" + action + "&field=" + encodeURIComponent(fieldname) +
             "&value=" + encodeURIComponent(value));
  }

  function closeAllDropdowns() {
    document.querySelectorAll(".trimeta-suggest-dropdown").forEach(
      function (el) { el.remove(); }
    );
  }

  // Ferme les menus, sauf celui du champ qui a le focus. Utilise par le
  // delai de sortie de champ: passer d'un champ a suggestions a un autre
  // ouvre le menu du second AVANT l'expiration de ce delai, qui le
  // refermait aussitot.
  function closeDropdownsNotFor(active) {
    document.querySelectorAll(".trimeta-suggest-dropdown").forEach(
      function (el) {
        if (el.trimetaInput !== active) { el.remove(); }
      }
    );
  }

  function buildDropdown(input, fieldname) {
    fetchSuggestions(fieldname, function (items) {
      closeAllDropdowns();
      if (document.activeElement !== input) {
        return;
      }
      var needle = (input.value || "").toLowerCase();
      var filtered = items.filter(function (v) {
        return v.toLowerCase().indexOf(needle) !== -1;
      });

      var dropdown = document.createElement("div");
      dropdown.className = "trimeta-suggest-dropdown";
      dropdown.setAttribute("data-field", fieldname);
      dropdown.trimetaInput = input;
      dropdown.style.cssText =
        "position:absolute;z-index:9999;background:#fff;" +
        "border:1px solid #d6d6d6;border-radius:2px;" +
        "box-shadow:0 2px 6px rgba(0,0,0,0.12);" +
        "max-height:200px;overflow-y:auto;font-size:13px;font-family:inherit;";
      var rect = input.getBoundingClientRect();
      dropdown.style.left = (rect.left + window.scrollX) + "px";
      dropdown.style.top = (rect.bottom + window.scrollY) + "px";
      dropdown.style.width = Math.max(rect.width, 200) + "px";

      var header = document.createElement("div");
      header.textContent = "Suggestions";
      header.style.cssText =
        "padding:6px 10px;font-weight:600;font-size:11px;" +
        "text-transform:uppercase;letter-spacing:0.03em;color:#888;" +
        "background:#fafafa;border-bottom:1px solid #eee;";
      dropdown.appendChild(header);

      filtered.forEach(function (value) {
        var row = document.createElement("div");
        row.className = "trimeta-suggest-item";
        row.style.cssText =
          "display:flex;justify-content:space-between;align-items:center;" +
          "padding:6px 10px;cursor:pointer;border-bottom:1px solid #f5f5f5;";

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
        remove.textContent = "✕";
        remove.title = "Retirer cette suggestion";
        remove.style.cssText =
          "color:#aaa;padding:2px 5px;margin-left:6px;cursor:pointer;" +
          "visibility:hidden;font-size:11px;border-radius:2px;";
        remove.onmousedown = function (e) {
          e.preventDefault();
          e.stopPropagation();
          postSuggestion("remove", fieldname, value, function () {
            buildDropdown(input, fieldname);
          });
        };

        row.onmouseenter = function () {
          row.style.background = "#f0f0f0";
          remove.style.visibility = "visible";
        };
        row.onmouseleave = function () {
          row.style.background = "";
          remove.style.visibility = "hidden";
        };
        row.appendChild(label);
        row.appendChild(remove);
        dropdown.appendChild(row);
      });

      if (filtered.length === 0) {
        var empty = document.createElement("div");
        empty.className = "trimeta-suggest-empty";
        empty.textContent = "Aucune suggestion pour l'instant";
        empty.style.cssText =
          "padding:8px 10px;color:#999;font-style:italic;font-size:12px;";
        dropdown.appendChild(empty);
      }
      document.body.appendChild(dropdown);
    });
  }

  // Champ a suggestions auquel appartient un element, ou null.
  function fieldFor(element) {
    if (!element || element.tagName !== "INPUT" || element.type !== "text" || !element.name) {
      return null;
    }
    var fields = getFields();
    for (var i = 0; i < fields.length; i++) {
      if (new RegExp("^" + fields[i] + "(-\\d+)?$").test(element.name)) {
        return fields[i];
      }
    }
    return null;
  }

  function markInputs() {
    getFields().forEach(function (fieldname) {
      findInputs(fieldname).forEach(function (input) {
        input.setAttribute("data-trimeta-suggest", fieldname);
        input.setAttribute("autocomplete", "off");
      });
    });
  }

  // Ecoute DELEGUEE au niveau du document, et non champ par champ:
  // l'en-tete de l'echantillon remplace ses champs apres chaque
  // modification, et le formulaire de creation en ajoute (+Add). Un
  // ecouteur pose sur le champ d'origine ne voyait plus le nouveau, et le
  // menu ne s'ouvrait plus jusqu'au passage suivant d'un rebranchement.
  document.addEventListener("focusin", function (e) {
    var fieldname = fieldFor(e.target);
    if (fieldname) {
      e.target.setAttribute("autocomplete", "off");
      buildDropdown(e.target, fieldname);
    }
  });

  document.addEventListener("input", function (e) {
    var fieldname = fieldFor(e.target);
    if (fieldname) {
      buildDropdown(e.target, fieldname);
    }
  });

  // Une valeur validee (champ quitte ou Entree) devient une suggestion
  // pour tous les postes, sans attendre l'enregistrement du formulaire.
  document.addEventListener("focusout", function (e) {
    var fieldname = fieldFor(e.target);
    if (fieldname) {
      postSuggestion("add", fieldname, e.target.value);
      // Delai: laisse un clic sur une suggestion aboutir avant fermeture.
      setTimeout(function () {
        closeDropdownsNotFor(document.activeElement);
      }, 150);
    }
  });

  document.addEventListener("keydown", function (e) {
    var fieldname = fieldFor(e.target);
    if (!fieldname) {
      return;
    }
    if (e.key === "Enter") {
      postSuggestion("add", fieldname, e.target.value);
    } else if (e.key === "Escape") {
      closeAllDropdowns();
    }
  });

  document.addEventListener("click", function (e) {
    var inDropdown = e.target.closest && e.target.closest(".trimeta-suggest-dropdown");
    if (!inDropdown && !fieldFor(e.target)) {
      closeAllDropdowns();
    }
  });

  document.addEventListener("DOMContentLoaded", function () {
    // Seul effet: couper l'autocompletion native du navigateur, qui
    // masquerait le menu. Les ecouteurs, eux, sont deja delegues.
    markInputs();
    setInterval(markInputs, 2000);
    if (window.jQuery) {
      window.jQuery(document).ajaxComplete(function () { cache = {}; });
    }
  });
})();
