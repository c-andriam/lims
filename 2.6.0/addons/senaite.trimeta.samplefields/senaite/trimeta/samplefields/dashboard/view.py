# -*- coding: utf-8 -*-
"""
Vue du tableau de bord Trimeta.

    /senaite/trimeta-dashboard

Assemblage
----------
Cette vue ne rend QUE le listing. La barre de filtres est dessinee par
un viewlet (dashboard/viewlets.py), qui la place dans la zone de
contenu.

Cette separation n'est pas cosmetique. Une premiere version prefixait
le formulaire au rendu de `__call__`, avec deux consequences visibles a
l'ecran:

- `senaite.app.listing` REUTILISE la meme vue pour ses requetes AJAX;
  le HTML se retrouvait donc devant la reponse JSON, et le navigateur
  affichait "JSON.parse: unexpected character at line 1 column 1" --
  le tableau restait vide;
- `__call__` rend la page COMPLETE, chrome compris: le formulaire
  atterrissait au-dessus de la barre de navigation SENAITE.

La vue reste donc un `ListingView` ordinaire, avec sa pagination, son
tri, sa bascule de colonnes et son export.

La pagination et le tri passent par AJAX. Les criteres du formulaire
sont donc poses en champs caches (`additional_hidden_fields`), sans
quoi la page 2 d'un resultat filtre afficherait tout le catalogue.

Securite
--------
Aucun controle d'acces specifique n'est ajoute, et c'est voulu: le
sample_catalog filtre deja par `allowedRolesAndUsers`. Un contact
client qui ouvrirait cette page n'y verrait que ses propres
echantillons.
"""

import logging

from bika.lims import api
from DateTime import DateTime
from senaite.app.listing import ListingView
from senaite.core.catalog import ANALYSIS_CATALOG
from senaite.core.catalog import SAMPLE_CATALOG
from senaite.core.i18n import translate as t
from zope.i18nmessageid import MessageFactory

from senaite.trimeta.samplefields.compat import to_text
from senaite.trimeta.samplefields.dashboard import columns as cols
from senaite.trimeta.samplefields.dashboard import filters as flt
from senaite.trimeta.samplefields.dashboard.results import fetch_results
from senaite.trimeta.samplefields.dashboard.results import sample_ids_in_range

_ = MessageFactory("senaite.trimeta.samplefields")

logger = logging.getLogger("senaite.trimeta.samplefields")

# Valeur impossible, utilisee quand un filtre ne selectionne AUCUN
# echantillon. Une liste vide dans une requete ZCatalog est ambigue --
# selon l'index elle peut etre ignoree, et le tableau afficherait alors
# tout le catalogue au lieu de rien. Un identifiant qui n'existe pas
# leve l'ambiguite.
NO_MATCH = "__trimeta_aucun_resultat__"


class DashboardView(ListingView):
    """Tableau de bord: 20 colonnes, filtrables et exportables."""

    def __init__(self, context, request):
        super(DashboardView, self).__init__(context, request)

        self.catalog = SAMPLE_CATALOG
        self.contentFilter = {
            "isRootAncestor": True,      # pas les partitions
            "sort_on": "getDateReceived",
            "sort_order": "descending",
        }

        self.title = t(_(u"Dashboard"))
        self.description = ""
        self.form_id = "trimeta_dashboard"

        # Vue de consultation: ni cases a cocher, ni boutons de
        # transition. Les afficher laisserait croire qu'on peut agir
        # sur les echantillons depuis ici.
        self.show_select_column = False
        self.show_select_all_checkbox = False
        self.show_workflow_action_buttons = False
        self.show_column_toggles = True
        self.show_search = True
        self.pagesize = 50

        self.columns = cols.build_columns()
        self.review_states = [{
            "id": "default",
            "title": t(_(u"All")),
            "contentFilter": {},
            "transitions": [],
            "custom_transitions": [],
            "columns": list(self.columns.keys()),
        }]

        self.filters = flt.read_filters(request.form)
        self.additional_hidden_fields = flt.hidden_fields(self.filters)
        self.apply_filters()

        # Identifiants de la page en cours, remplis par folderitem() et
        # consommes par folderitems() pour la requete groupee.
        self._page_ids = []
        self._results = {}

    # -- filtres --------------------------------------------------------

    def to_date(self, value, end_of_day=False):
        """Convertit une date de formulaire, ou None si elle est illisible.

        Une date mal saisie doit desactiver ce critere, pas faire tomber
        la page.
        """
        text = to_text(value).strip()
        if not text:
            return None
        if end_of_day:
            text = "{} 23:59:59".format(text)
        try:
            return DateTime(text)
        except Exception:
            logger.debug("Date de filtre illisible: %r", value)
            return None

    def apply_filters(self):
        """Traduit les criteres du formulaire en requete catalogue."""
        try:
            self.contentFilter.update(
                flt.build_query(self.filters, to_date=self.to_date))
            self.apply_result_range()
        except Exception:
            # Un filtre qui echoue doit rendre le tableau non filtre,
            # pas une page d'erreur.
            logger.exception("Application des filtres impossible")

    def apply_result_range(self):
        """Filtre de plage sur la vanilline.

        Il ne peut pas s'exprimer en requete catalogue -- `getResult`
        n'est qu'une colonne de metadonnees -- et il doit pourtant
        s'appliquer AVANT la pagination, sinon le nombre de pages
        annonce serait faux. D'ou cette resolution prealable en une
        liste d'identifiants, passee au sample_catalog via `getId`, qui
        lui est indexe.
        """
        minimum = self.filters.get("van_min")
        maximum = self.filters.get("van_max")
        if not minimum and not maximum:
            return

        keyword = cols.get_keyword_for(cols.VANILLIN_COLUMN)
        matching = sample_ids_in_range(
            api.get_tool(ANALYSIS_CATALOG), keyword, minimum, maximum)

        if matching is None:
            return
        self.contentFilter["getId"] = matching or [NO_MATCH]

    # -- remplissage des lignes -------------------------------------------

    def folderitems(self):
        """Ajoute les resultats d'analyse, en une requete pour la page."""
        self._page_ids = []
        items = super(DashboardView, self).folderitems()

        try:
            keywords = cols.get_keywords()
            self._results = fetch_results(
                api.get_tool(ANALYSIS_CATALOG), self._page_ids, keywords)

            for item in items:
                per_sample = self._results.get(item.get("_trimeta_id"), {})
                for column_id, keyword, _label in cols.DASHBOARD_ANALYSES:
                    item[column_id] = per_sample.get(keyword, "")

            self.warn_about_empty_columns()
        except Exception:
            # Des colonnes de resultats vides restent lisibles; une
            # page d'erreur, non.
            logger.exception("Resultats d'analyse non rapportes")

        return items

    def folderitem(self, obj, item, index):
        """Colonnes issues du catalogue, lues sur le brain.

        Aucun `api.get_object` ici: c'est ce qui permet a un tableau de
        plusieurs centaines de lignes de rester utilisable.
        """
        item = super(DashboardView, self).folderitem(obj, item, index)
        try:
            sample_id = getattr(obj, "getId", "") or ""
            item["_trimeta_id"] = sample_id
            self._page_ids.append(sample_id)

            for key, attr in cols.get_metadata_map().items():
                item[key] = self.format_value(getattr(obj, attr, ""))
        except Exception:
            logger.exception("Ligne %s incomplete", index)
        return item

    def format_value(self, value):
        """Texte affichable.

        Les dates passent par `to_str_date`, fourni par ListingView:
        c'est lui qui applique le format attendu par le listing, plutot
        qu'une conversion maison qui figerait la langue.
        """
        if not value:
            return ""
        if isinstance(value, DateTime):
            try:
                return self.to_str_date(value)
            except Exception:
                return to_text(value.strftime("%Y-%m-%d"))
        return to_text(value)

    def warn_about_empty_columns(self):
        """Journalise les mots-cles qui ne ramenent jamais rien.

        Une faute de frappe dans DASHBOARD_ANALYSES ne provoque aucune
        erreur -- juste une colonne vide, que personne ne saurait
        expliquer. Cette trace donne la reponse dans les logs.
        """
        if not self._page_ids or not self._results:
            return
        seen = set()
        for per_sample in self._results.values():
            seen.update(per_sample.keys())
        missing = [k for k in cols.get_keywords() if k not in seen]
        if missing:
            logger.info(
                "Tableau de bord: aucun resultat pour les mots-cles %s. "
                "Verifier la colonne Keyword dans Configuration > "
                "Analyses, et DASHBOARD_ANALYSES dans dashboard/"
                "columns.py.", ", ".join(missing))
