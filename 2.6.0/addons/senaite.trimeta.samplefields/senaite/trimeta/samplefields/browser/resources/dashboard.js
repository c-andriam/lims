/* Tableau de bord Trimeta: entree de barre laterale et infobulles.
 *
 * Deux traitements, volontairement dans le meme fichier parce qu'ils
 * partagent la meme configuration (window.TRIMETA_DASHBOARD, posee par
 * le viewlet) :
 *
 *   1. ENTREE DE BARRE LATERALE, sur toutes les pages.
 *   2. INFOBULLES D'EN-TETE, sur la seule page du tableau de bord.
 *
 * Pourquoi du JavaScript pour la barre laterale
 * ---------------------------------------------
 * Sa construction appartient a senaite.core et n'est pas un point
 * d'extension documente. Plutot que de parier sur son gabarit -- une
 * hypothese fausse donnerait au mieux un lien invisible -- on CLONE une
 * entree existante et on n'en change que le lien, le libelle et
 * l'icone. Le clone herite donc du balisage, des classes et du style
 * exacts de SENAITE : il ne peut pas detonner, meme si le theme change.
 *
 * Tout est enveloppe de try/catch : une icone manquante est un
 * desagrement, une page qui ne s'affiche plus est un arret de travail.
 */
(function () {
  "use strict";

  var CONFIG = window.TRIMETA_DASHBOARD || {};
  var MARKER = "trimeta-dashboard-link";

  /* Marque de version. Elle sert a repondre a une question qui s'est
   * posee: "le correctif est-il charge, ou le navigateur sert-il
   * encore l'ancien fichier ?". Lisible dans la console:
   *     window.TRIMETA_DASHBOARD_VERSION
   */
  var VERSION = 3;
  window.TRIMETA_DASHBOARD_VERSION = VERSION;


  /* Trace de l'icone, dans le style trait fin des icones SENAITE:
   * un cadre, une separation horizontale, une verticale -- un tableau.
   * `currentColor` la fait suivre la couleur des autres entrees, etat
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

  function log(message, error) {
    if (window.console && window.console.debug) {
      window.console.debug("[trimeta] " + message, error || "");
    }
  }

  // ------------------------------------------------------------------
  // 1. Entree de barre laterale
  // ------------------------------------------------------------------

  /* Trouver l'ENTREE a cloner, sans rien savoir du balisage.
   *
   * Regle: on remonte depuis un lien tant que l'ancetre ne contient
   * qu'UN SEUL lien. Le dernier ancetre qui satisfait cela est l'entree
   * complete (icone + libelle); son parent est la liste des entrees.
   *
   * C'est la correction d'un vrai defaut: la premiere version cherchait
   * la barre par une liste de selecteurs, dont un tres large
   * ([class*='sidebar']). Celui-ci attrapait un conteneur EXTERNE dont
   * l'unique enfant direct etait la liste entiere -- on clonait donc
   * toute la barre, qui apparaissait en double.
   *
   * La regle du "un seul lien" ne peut pas commettre cette erreur: des
   * qu'un ancetre contient deux liens, il n'est plus une entree. */
  function findItemAndList() {
    var links = document.querySelectorAll("a[href]");
    var best = null;

    for (var i = 0; i < links.length; i++) {
      var link = links[i];
      if (!isSidebarCandidate(link)) {
        continue;
      }
      var node = link;
      while (node.parentNode &&
             node.parentNode !== document.body &&
             node.parentNode.querySelectorAll("a[href]").length === 1) {
        node = node.parentNode;
      }
      var list = node.parentNode;
      if (!list) {
        continue;
      }
      // La liste doit contenir plusieurs entrees: c'est ce qui
      // distingue une barre de navigation d'un lien isole.
      var siblings = list.querySelectorAll("a[href]").length;
      if (siblings < 2) {
        continue;
      }
      if (!best || siblings > best.siblings) {
        best = {item: node, link: link, list: list, siblings: siblings};
      }
    }
    return best;
  }

  /* Un lien de la barre laterale est etroit et colle a gauche. Le test
   * geometrique evite de confondre la barre avec le menu horizontal du
   * haut ou avec les liens de pied de page. */
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
   * On ne tente plus de charger une icone du theme: un nom inconnu
   * renvoyait une reponse que le navigateur acceptait comme image sans
   * pouvoir la dessiner, d'ou le "?" observe a l'ecran. Un trace fourni
   * par l'add-on, lui, s'affiche toujours. */
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
      // Reprend les classes de l'image pour heriter des marges.
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

    /* Garde-fou, et non simple precaution: c'est l'invariant qui
     * definit une entree de barre laterale. Une version precedente
     * clonait un conteneur portant TOUS les liens, et la barre
     * apparaissait en double. Si le noeud retenu porte plus d'un lien,
     * ce n'est pas une entree: on se rabat sur le lien seul, qui en
     * est une a coup sur. */
    var source = found.item;
    if (source.querySelectorAll &&
        source.querySelectorAll("a[href]").length > 1) {
      source = found.link;
    }

    var clone = source.cloneNode(true);
    if (clone.querySelectorAll &&
        clone.querySelectorAll("a[href]").length > 1) {
      log("entree non clonable: elle porte plusieurs liens");
      return;
    }
    clone.id = MARKER;
    // Un etat "actif" herite du clone allumerait deux entrees.
    clone.className = (clone.className || "").replace(/\bactive\b/g, "");
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
     * `apply` reinterrogerait le DOM a chacune d'elles -- des dizaines
     * de fois pour un seul changement de page. On regroupe donc les
     * rafales en un seul passage. */
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
        // lui-meme un noeud a la barre laterale, qu'il est inutile de
        // se voir notifier.
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
