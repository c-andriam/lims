/* Tableau de bord Trimeta: entree de barre laterale et infobulles.
 *
 * Deux traitements, dans le meme fichier parce qu'ils partagent la meme
 * configuration (window.TRIMETA_DASHBOARD, posee par le viewlet) :
 *
 *   1. ENTREE DE BARRE LATERALE, sur toutes les pages.
 *   2. INFOBULLES D'EN-TETE, sur la seule page du tableau de bord.
 *
 * Pourquoi du JavaScript pour la barre laterale
 * ---------------------------------------------
 * Sa construction appartient a senaite.core et n'est pas un point
 * d'extension documente. Plutot que de parier sur son gabarit, on CLONE
 * une entree existante et on n'en change que le lien, le libelle et
 * l'icone. Le clone herite du balisage, des classes et du style exacts
 * de SENAITE : il ne peut pas detonner, meme si le theme change.
 *
 * Tout est enveloppe de try/catch : une icone manquante est un
 * desagrement, une page qui ne s'affiche plus est un arret de travail.
 */
(function () {
  "use strict";

  var CONFIG = window.TRIMETA_DASHBOARD || {};
  var MARKER = "trimeta-dashboard-link";

  /* Marque de version, pour repondre depuis la console a la question
   * "le correctif est-il charge, ou le navigateur sert-il encore
   * l'ancien fichier ?" :
   *     window.TRIMETA_DASHBOARD_VERSION
   * Doit rester en accord avec SCRIPT_VERSION dans viewlets.py, qui la
   * reporte en parametre d'URL. Un test verifie cette concordance.
   */
  var VERSION = 4;
  window.TRIMETA_DASHBOARD_VERSION = VERSION;

  /* Dimensions maximales d'une entree de barre laterale.
   *
   * C'est la contrainte qui manquait, et son absence a produit deux
   * defauts successifs a l'ecran: d'abord la barre entiere clonee,
   * puis la PAGE entiere. La cause etait la meme dans les deux cas --
   * une remontee dans l'arbre que rien n'arretait.
   *
   * Une entree de navigation est petite. On le dit, plutot que de
   * l'esperer. */
  var MAX_ITEM_WIDTH = 300;
  var MAX_ITEM_HEIGHT = 120;

  /* Elements qu'une entree de navigation ne contient jamais. Test
   * complementaire du precedent: il aurait suffi a lui seul a rejeter
   * le bloc de page clone par erreur, qui portait un titre, un
   * formulaire et un tableau. */
  var FOREIGN_TO_AN_ENTRY = "table, form, h1, h2, input, select";

  // Nombre minimal d'entrees pour qu'une liste soit une barre de
  // navigation. Ecarte le pied de page et les liens isoles.
  var MIN_ENTRIES = 3;

  /* Trace de l'icone, dans le style trait fin des icones SENAITE:
   * un cadre, une separation horizontale, une verticale -- un tableau.
   * `currentColor` la fait suivre la couleur des autres entrees, etats
   * survole et actif compris. */
  var ICON_PATHS =
    '<rect x="3" y="3" width="18" height="18" rx="2"/>' +
    '<line x1="3" y1="9" x2="21" y2="9"/>' +
    '<line x1="9" y1="9" x2="9" y2="21"/>';

  function svgWithSize(size) {
    return '<svg xmlns="http://www.w3.org/2000/svg" width="' + size +
      '" height="' + size + '" viewBox="0 0 24 24" fill="none" ' +
      'stroke="currentColor" stroke-width="1.5" stroke-linecap="round" ' +
      'stroke-linejoin="round">' + ICON_PATHS + "</svg>";
  }

  function log(message, detail) {
    if (window.console && window.console.debug) {
      window.console.debug("[trimeta] " + message, detail || "");
    }
  }

  // ------------------------------------------------------------------
  // 1. Entree de barre laterale
  // ------------------------------------------------------------------

  /* Un lien de barre laterale est visible, etroit et colle a gauche,
   * sous le bandeau superieur. Ecarte le menu horizontal du haut et la
   * plupart des liens de pied de page. */
  function isSidebarCandidate(link) {
    try {
      var box = link.getBoundingClientRect();
      if (!box.width || !box.height) {
        return false;                    // masque
      }
      return box.left < 260 && box.top > 40;
    } catch (error) {
      return false;
    }
  }

  function isSmallEnough(node) {
    try {
      var box = node.getBoundingClientRect();
      return box.width <= MAX_ITEM_WIDTH && box.height <= MAX_ITEM_HEIGHT;
    } catch (error) {
      return false;
    }
  }

  function looksLikeEntry(node) {
    if (!node || !node.querySelector) {
      return false;
    }
    return !node.querySelector(FOREIGN_TO_AN_ENTRY);
  }

  /* L'entree complete: le plus grand ancetre du lien qui reste UNE
   * entree. Trois conditions, chacune necessaire:
   *
   *   - il ne porte qu'un seul lien (au-dela, c'est une liste);
   *   - il reste petit (au-dela, c'est une region de page);
   *   - il ne contient ni titre, ni formulaire, ni tableau.
   *
   * La premiere seule ne suffisait pas: une region ne contenant qu'un
   * lien la satisfait, et c'est ainsi que le contenu entier de la page
   * s'est retrouve clone. */
  function climbToEntry(link) {
    var node = link;
    while (node.parentNode &&
           node.parentNode !== document.body &&
           node.parentNode.querySelectorAll("a[href]").length === 1 &&
           isSmallEnough(node.parentNode) &&
           looksLikeEntry(node.parentNode)) {
      node = node.parentNode;
    }
    return node;
  }

  function countEntries(list) {
    var links = list.querySelectorAll("a[href]");
    var count = 0;
    for (var i = 0; i < links.length; i++) {
      if (isSidebarCandidate(links[i])) {
        count++;
      }
    }
    return count;
  }

  /* La liste retenue est celle qui porte le plus d'entrees repondant
   * aux criteres de la barre laterale. */
  function findItemAndList() {
    var links = document.querySelectorAll("a[href]");
    var best = null;

    for (var i = 0; i < links.length; i++) {
      var link = links[i];
      if (!isSidebarCandidate(link)) {
        continue;
      }
      var item = climbToEntry(link);
      var list = item.parentNode;
      if (!list || !list.querySelectorAll) {
        continue;
      }
      var entries = countEntries(list);
      if (entries < MIN_ENTRIES) {
        continue;
      }
      if (!best || entries > best.entries) {
        best = {item: item, link: link, list: list, entries: entries};
      }
    }
    return best;
  }

  function setLabel(clone, label) {
    var link = clone.matches && clone.matches("a[href]")
      ? clone : clone.querySelector("a[href]");
    if (!link) {
      return null;
    }
    link.setAttribute("href", CONFIG.url);
    link.setAttribute("title", label);
    link.setAttribute("aria-label", label);

    // Les libelles textuels sont remplaces; l'icone est un element et
    // n'est pas concernee ici.
    var walker = document.createTreeWalker(
      link, NodeFilter.SHOW_TEXT, null, false);
    var replaced = false;
    var node;
    while ((node = walker.nextNode())) {
      if (node.nodeValue && node.nodeValue.trim()) {
        node.nodeValue = replaced ? "" : label;
        replaced = true;
      }
    }
    return link;
  }

  /* Icone: on remplace le CONTENU de celle du clone, en gardant son
   * element et donc ses classes, sa taille et sa couleur. C'est ce qui
   * garantit l'alignement avec les autres entrees.
   *
   * On ne tente pas de charger une icone du theme: un nom inconnu
   * renvoyait une reponse que le navigateur acceptait comme image sans
   * pouvoir la dessiner, d'ou le "?" observe a l'ecran. */
  function setIcon(link) {
    var holder = link.querySelector("svg");
    if (holder) {
      holder.setAttribute("viewBox", "0 0 24 24");
      holder.setAttribute("fill", "none");
      holder.setAttribute("stroke", "currentColor");
      holder.setAttribute("stroke-width", "1.5");
      holder.innerHTML = ICON_PATHS;
      return;
    }

    var img = link.querySelector("img");
    if (img) {
      var span = document.createElement("span");
      span.innerHTML = svgWithSize(img.clientWidth || 24);
      span.className = img.className || "";
      img.parentNode.replaceChild(span, img);
      return;
    }

    var solo = document.createElement("span");
    solo.innerHTML = svgWithSize(24);
    link.insertBefore(solo, link.firstChild);
  }

  function addSidebarEntry() {
    if (!CONFIG.url || document.getElementById(MARKER)) {
      return;
    }
    var found = findItemAndList();
    if (!found) {
      return;                            // pas de barre sur cette page
    }

    /* Repli: si le noeud retenu n'a pas l'allure d'une entree, on prend
     * le lien seul, qui en est une a coup sur. */
    var source = found.item;
    if (!isSmallEnough(source) || !looksLikeEntry(source) ||
        source.querySelectorAll("a[href]").length > 1) {
      source = found.link;
    }

    var clone = source.cloneNode(true);

    /* Derniere barriere, avant insertion. Les deux defauts observes --
     * barre dupliquee, puis page dupliquee -- auraient ete arretes
     * ici. */
    if (clone.querySelectorAll &&
        (clone.querySelectorAll("a[href]").length > 1 ||
         clone.querySelector(FOREIGN_TO_AN_ENTRY))) {
      log("entree non clonable: le noeud retenu n'est pas une entree");
      return;
    }

    clone.id = MARKER;
    // Un etat "actif" herite du clone allumerait deux entrees.
    clone.className = (clone.className || "").replace(/(^|\s)active(\s|$)/g, " ");
    if (clone.removeAttribute) {
      clone.removeAttribute("aria-current");
    }

    var link = setLabel(clone, CONFIG.label || "Dashboard");
    if (!link) {
      return;
    }
    setIcon(link);
    found.list.appendChild(clone);
  }

  // ------------------------------------------------------------------
  // 2. Infobulles d'en-tete
  // ------------------------------------------------------------------

  /* Les en-tetes sont courts par necessite; le sens complet est rendu
   * au survol, par un attribut `title` natif -- aucune dependance a une
   * bibliotheque, et lisible aussi par un lecteur d'ecran.
   *
   * L'appariement se fait sur le TEXTE affiche: le viewlet fournit la
   * table {intitule court: intitule complet}, les deux issus du meme
   * catalogue de traduction au meme instant. */
  function addHeaderTooltips() {
    var help = CONFIG.help;
    if (!help) {
      return;
    }
    var headers = document.querySelectorAll("thead th");
    for (var i = 0; i < headers.length; i++) {
      var th = headers[i];
      var text = (th.textContent || "").trim();
      // Le tri ajoute une fleche au libelle: on la retire.
      text = text.replace(/[▲▼↑↓]/g, "").trim();
      var full = help[text];
      if (full && full !== text && th.getAttribute("title") !== full) {
        th.setAttribute("title", full);
        th.style.cursor = "help";
      }
    }
  }

  // ------------------------------------------------------------------
  // Application, et re-application apres les rendus AJAX
  // ------------------------------------------------------------------

  function apply() {
    try {
      addSidebarEntry();
    } catch (error) {
      log("entree de barre laterale non ajoutee", error);
    }
    try {
      addHeaderTooltips();
    } catch (error) {
      log("infobulles non posees", error);
    }
  }

  function start() {
    apply();

    /* senaite.app.listing redessine son tableau en AJAX: les attributs
     * poses sur les anciens en-tetes disparaissent avec eux.
     *
     * Une page React emet beaucoup de mutations. Sans temporisation,
     * `apply` reinterrogerait le DOM a chacune d'elles. On regroupe
     * donc les rafales en un seul passage. */
    if (!window.MutationObserver) {
      return;
    }
    var pending = null;
    var observer = new MutationObserver(function () {
      if (pending) {
        return;
      }
      pending = window.setTimeout(function () {
        pending = null;
        // On suspend l'observation le temps d'agir: `apply` ajoute
        // lui-meme un noeud, qu'il est inutile de se voir notifier.
        observer.disconnect();
        apply();
        observer.observe(document.body, {childList: true, subtree: true});
      }, 150);
    });
    observer.observe(document.body, {childList: true, subtree: true});
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();
