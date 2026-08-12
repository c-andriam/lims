// senaite.trimeta.samplefields - ajustements formulaire Add Sample
//
// 1. Separateur visuel discret au-dessus de la section "Reception".
// 2. Correctif fiable pour l'affichage inline des erreurs "champ
//    requis" sur les widgets complexes (Client, Contact, Sample Type,
//    Date Sampled). Le mecanisme natif de SENAITE cherche le
//    conteneur ".field" via field.parent("div.field"), ce qui echoue
//    silencieusement pour les widgets ou l'id du champ est deja
//    porte par l'element ".field" lui-meme (ex: ArchetypesReferenceWidget).
//    On reintercepte la reponse AJAX du formulaire pour reappliquer
//    l'affichage avec .closest(".field"), qui couvre les deux cas
//    sans rien casser pour les champs deja fonctionnels.
(function () {
  "use strict";

  function insertSeparator() {
    var target = document.querySelector('tr[fieldName="SampleCode-0"]') ||
                 document.querySelector('tr[fieldName="SampleCode"]');
    if (!target) {
      return false;
    }
    if (document.getElementById("trimeta-reception-separator")) {
      return true;
    }

    var row = document.createElement("tr");
    row.id = "trimeta-reception-separator";
    row.innerHTML =
      '<td colspan="10" style="' +
      'background:#f7f7f7;' +
      'border-top:2px solid #ddd;' +
      'padding:4px 8px;' +
      'font-size:11px;' +
      'font-weight:600;' +
      'text-transform:uppercase;' +
      'letter-spacing:0.03em;' +
      'color:#888;">' +
      "Reception" +
      "</td>";

    target.parentNode.insertBefore(row, target);
    return true;
  }

  function tryInsert(retries) {
    if (insertSeparator()) {
      return;
    }
    if (retries <= 0) {
      return;
    }
    setTimeout(function () {
      tryInsert(retries - 1);
    }, 300);
  }

  function ensureErrorBox(container) {
    var box = container.find("> div.fieldErrorBox");
    if (box.length === 0) {
      box = window.jQuery(
        '<div class="fieldErrorBox"></div>'
      ).appendTo(container);
    }
    return box;
  }

  function findFieldElement($, fieldname) {
    // Differents widgets SENAITE exposent l'id du champ sous des
    // formats variables. On essaie plusieurs strategies dans l'ordre
    // et on prend la premiere qui matche.
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
      // .closest() couvre a la fois le cas ou l'element porte deja
      // la classe "field" et celui ou elle est portee par un ancetre.
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

  function tryInit(retries) {
    var sepDone = insertSeparator();
    var jqReady = !!window.jQuery;
    if (jqReady) {
      watchAjaxSubmit();
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
  });
})();
