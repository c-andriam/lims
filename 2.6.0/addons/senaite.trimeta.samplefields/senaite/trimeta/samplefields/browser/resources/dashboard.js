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

  // Conteneurs possibles de la barre laterale, du plus precis au plus
  // large. On s'arrete au premier qui contient au moins un lien.
  var SIDEBAR_SELECTORS = [
    "#sidebar",
    "nav#sidebar",
    ".sidebar",
    "#portal-sidebar",
    "[class*='sidebar']"
  ];

  // Icone de repli, dans le style trait fin des icones SENAITE.
  // Utilisee seulement si aucune icone du theme ne repond.
  var FALLBACK_SVG =
    '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" ' +
    'viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
    'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">' +
    '<rect x="3" y="3" width="18" height="18" rx="2"/>' +
    '<line x1="3" y1="9" x2="21" y2="9"/>' +
    '<line x1="9" y1="9" x2="9" y2="21"/>' +
    "</svg>";

  function log(message, error) {
    if (window.console && window.console.debug) {
      window.console.debug("[trimeta] " + message, error || "");
    }
  }

  // ------------------------------------------------------------------
  // 1. Entree de barre laterale
  // ------------------------------------------------------------------

  function findSidebar() {
    for (var i = 0; i < SIDEBAR_SELECTORS.length; i++) {
      var nodes = document.querySelectorAll(SIDEBAR_SELECTORS[i]);
      for (var j = 0; j < nodes.length; j++) {
        if (nodes[j].querySelector("a[href]")) {
          return nodes[j];
        }
      }
    }
    return null;
  }

  /* Entree a cloner: la DERNIERE de la barre, pour que la nouvelle
   * vienne se poser a la suite sans s'intercaler au milieu. */
  function findTemplateItem(sidebar) {
    var links = sidebar.querySelectorAll("a[href]");
    if (!links.length) {
      return null;
    }
    var link = links[links.length - 1];
    // On remonte au bloc qui porte l'entree entiere (icone + libelle),
    // sans jamais depasser la barre elle-meme.
    var node = link;
    while (node.parentNode && node.parentNode !== sidebar) {
      node = node.parentNode;
    }
    return node;
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

    // Les libelles textuels de la barre sont remplaces; l'icone, elle,
    // est un element et n'est pas touchee ici.
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

  /* Essaie les icones du theme l'une apres l'autre; garde celle du
   * clone si aucune ne repond, et l'icone de repli si le clone n'en
   * avait pas. */
  function setIcon(link) {
    var holder = link.querySelector("img, svg");
    var candidates = CONFIG.icons || [];

    function useFallback() {
      if (holder) {
        return;                       // l'icone du clone fait l'affaire
      }
      var span = document.createElement("span");
      span.innerHTML = FALLBACK_SVG;
      link.insertBefore(span, link.firstChild);
    }

    function tryNext(index) {
      if (index >= candidates.length) {
        useFallback();
        return;
      }
      var url = CONFIG.iconBase + candidates[index];
      var probe = new Image();
      probe.onload = function () {
        try {
          if (holder && holder.tagName.toLowerCase() === "img") {
            holder.setAttribute("src", url);
          } else if (holder) {
            var img = document.createElement("img");
            img.setAttribute("src", url);
            img.setAttribute("alt", "");
            // Reprend la taille rendue de l'icone remplacee, pour
            // rester aligne sur les autres entrees.
            img.style.width = holder.clientWidth
              ? holder.clientWidth + "px" : "24px";
            holder.parentNode.replaceChild(img, holder);
          } else {
            var solo = document.createElement("img");
            solo.setAttribute("src", url);
            solo.setAttribute("alt", "");
            link.insertBefore(solo, link.firstChild);
          }
        } catch (error) {
          log("icone non posee", error);
          useFallback();
        }
      };
      probe.onerror = function () {
        tryNext(index + 1);
      };
      probe.src = url;
    }

    tryNext(0);
  }

  function addSidebarEntry() {
    if (!CONFIG.url || document.getElementById(MARKER)) {
      return;
    }
    var sidebar = findSidebar();
    if (!sidebar) {
      return;                          // barre absente sur cette page
    }
    var template = findTemplateItem(sidebar);
    if (!template) {
      return;
    }

    var clone = template.cloneNode(true);
    clone.id = MARKER;
    // Un etat "actif" herite du clone donnerait deux entrees allumees.
    clone.className = (clone.className || "").replace(/\bactive\b/g, "");

    var link = setLabel(clone, CONFIG.label || "Dashboard");
    if (!link) {
      return;
    }
    setIcon(link);
    sidebar.appendChild(clone);
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
