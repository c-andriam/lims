// SENAITE 2.6 retire la virgule, le signe et l'exposant des champs AT.
// Conserver la saisie: le serveur reste responsable de sa validation.
(function (root) {
  "use strict";
  function normalizeDecimal(value) {
    // Un seul separateur decimal. Une saisie ambigue doit etre refusee
    // par le serveur, jamais convertie en une valeur plausible et fausse.
    if (value.indexOf(".") === -1 && (value.match(/,/g) || []).length === 1) {
      return value.replace(",", ".");
    }
    return value;
  }
  if (typeof module !== "undefined" && module.exports) {
    module.exports = normalizeDecimal;
  }
  if (!root.document) { return; }
  function isDecimal(input) {
    return input && input.tagName === "INPUT" && input.type === "text" &&
      (input.closest(".ArchetypesDecimalWidget") || /:float(?:$|\b)/.test(input.name));
  }
  root.document.addEventListener("input", function (event) {
    if (!isDecimal(event.target)) { return; }
    var input = event.target;
    var value = normalizeDecimal(input.value);
    if (input.value !== value) {
      var start = input.selectionStart;
      var end = input.selectionEnd;
      input.value = value;
      input.setSelectionRange(start, end);
    }
    input.setAttribute("inputmode", "decimal");
  }, true);
  root.document.addEventListener("keyup", function (event) {
    if (isDecimal(event.target)) {
      // Bloque uniquement le filtre keyup destructeur delegue sur body.
      // Les evenements input/change/blur et la validation AT restent actifs.
      event.stopPropagation();
    }
  }, true);
})(typeof window === "undefined" ? {} : window);
