// Les preferences natives omettent les nouvelles colonnes du serveur.
// Completer la configuration avant l'initialisation de la grille React.
(function (root) {
  "use strict";
  function migrate(storage, key) {
    try {
      var config = JSON.parse(storage.getItem(key));
      if (!Array.isArray(config) || !config.length) { return false; }
      if (!config.every(function (entry) {
        return entry && typeof entry.key === "string";
      })) { return false; }
      if (config.some(function (entry) {
        return entry.key === "AssignedLabAnalyst";
      })) { return false; }
      config.push({key: "AssignedLabAnalyst", toggle: true});
      storage.setItem(key, JSON.stringify(config));
      return true;
    } catch (error) { return false; }
  }
  if (typeof module !== "undefined" && module.exports) { module.exports = migrate; }
  if (!root.document) { return; }
  var script = root.document.currentScript;
  var key = script && script.getAttribute("data-storage-key");
  if (key) {
    try { migrate(root.localStorage, key); } catch (error) { /* Stockage desactive. */ }
  }
}(typeof window !== "undefined" ? window : this));
