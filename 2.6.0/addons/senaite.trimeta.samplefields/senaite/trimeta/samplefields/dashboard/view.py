# -*- coding: utf-8 -*-
"""
Vue du tableau de bord Trimeta.

    /senaite/trimeta-dashboard

Assemblage
----------
La page est une barre de filtres suivie d'un listing senaite standard.
Plutot que de remplacer le gabarit de `ListingView` -- dont l'assemblage
interne peut changer d'une version 2.x a l'autre -- on prefixe
simplement son rendu par le formulaire. La vue reste donc un
`ListingView` ordinaire, avec sa pagination, son tri, son bascule de
colonnes et son export.

Le formulaire est un `<form method="get">` sans JavaScript: cliquer sur
"Rechercher" recharge la page avec les criteres dans l'URL. Une
recherche est ainsi partageable par copie du lien, et rien ne peut se
desynchroniser entre ce qu'affiche le formulaire et ce que montre le
tableau.

La pagination et le tri, eux, passent par AJAX. Les criteres sont donc
aussi poses en champs caches (`additional_hidden_fields`), sans quoi la
page 2 d'un resultat filtre afficherait tout le catalogue.

Securite
--------
Aucun controle d'acces specifique n'est ajoute, et c'est voulu: le
sample_catalog filtre deja par `allowedRolesAndUsers`. Un contact
client qui ouvrirait cette page n'y verrait que ses propres
echantillons.
"""

import collections
import logging

from bika.lims import api
from DateTime import DateTime
from senaite.app.listing import ListingView
from senaite.core.catalog import ANALYSIS_CATALOG
from senaite.core.catalog import CLIENT_CATALOG
from senaite.core.catalog import SAMPLE_CATALOG
from senaite.core.catalog import SETUP_CATALOG
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

try:                                   # Python 2
    from cgi import escape as _escape

    def escape(value):
        return _escape(to_text(value), True)
except ImportError:                    # Python 3
    from html import escape as _escape

    def escape(value):
        return _escape(to_text(value), True)


class DashboardView(ListingView):
    """Tableau de bord: 20 colonnes, 6 filtres, un bouton de recherche."""

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

        # Le tableau de bord est une vue de consultation: ni cases a
        # cocher, ni boutons de transition. Les afficher laisserait
        # croire qu'on peut agir sur les echantillons depuis ici.
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

        # Rempli une fois par page rendue, dans folderitems().
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
        liste d'identifiants, passee ensuite au sample_catalog via
        `getId`, qui lui est indexe.
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

    # -- vocabulaires du formulaire -------------------------------------

    def get_options(self, catalog_id, portal_type):
        """[(uid, intitule)] tries, pour une liste deroulante.

        N'utilise que `UID` et `Title`, qui sont des colonnes de
        metadonnees de TOUS les catalogues senaite (BASE_COLUMNS). Le
        tri se fait en Python: `sortable_title` n'est pas garanti
        present sur chaque catalogue.
        """
        try:
            brains = api.search({"portal_type": portal_type,
                                 "is_active": True}, catalog_id)
            options = [(b.UID, to_text(b.Title)) for b in brains]
            return sorted(options, key=lambda pair: pair[1].lower())
        except Exception:
            logger.exception("Liste %s indisponible", portal_type)
            return []

    def get_client_options(self):
        return self.get_options(CLIENT_CATALOG, "Client")

    def get_sample_type_options(self):
        return self.get_options(SETUP_CATALOG, "SampleType")

    def get_origin_options(self):
        """Provenances reellement saisies, lues dans l'index.

        Pas de liste de reference pour ce champ: la liste des choix est
        donc celle des valeurs deja rencontrees.
        """
        try:
            catalog = api.get_tool(SAMPLE_CATALOG)
            values = catalog.uniqueValuesFor("getOrigin")
            return sorted([to_text(v) for v in values if v])
        except Exception:
            logger.exception("Provenances indisponibles")
            return []

    # -- rendu -----------------------------------------------------------

    def __call__(self):
        """Barre de filtres, puis le listing standard."""
        listing = super(DashboardView, self).__call__()
        return self.render_filter_bar() + listing

    def text_input(self, name, label, value, input_type="text"):
        return (
            u'<div class="col-md-2 mb-2">'
            u'<label class="small mb-1" for="{id}">{label}</label>'
            u'<input class="form-control form-control-sm" type="{type}" '
            u'id="{id}" name="{id}" value="{value}"/>'
            u'</div>'
        ).format(id=flt.PREFIX + name, label=escape(label),
                 value=escape(value), type=input_type)

    def select_input(self, name, label, value, options):
        rendered = [u'<option value=""></option>']
        for option_value, option_label in options:
            selected = u' selected="selected"' \
                if to_text(option_value) == to_text(value) else u''
            rendered.append(
                u'<option value="{v}"{s}>{l}</option>'.format(
                    v=escape(option_value), s=selected,
                    l=escape(option_label)))
        return (
            u'<div class="col-md-2 mb-2">'
            u'<label class="small mb-1" for="{id}">{label}</label>'
            u'<select class="form-control form-control-sm" '
            u'id="{id}" name="{id}">{options}</select>'
            u'</div>'
        ).format(id=flt.PREFIX + name, label=escape(label),
                 options=u"".join(rendered))

    def render_filter_bar(self):
        """Le formulaire de recherche, dessine au-dessus du tableau."""
        try:
            get = self.filters.get
            origins = [(o, o) for o in self.get_origin_options()]

            fields = [
                self.text_input("date_from", t(_(u"Received from")),
                                get("date_from", ""), "date"),
                self.text_input("date_to", t(_(u"Received to")),
                                get("date_to", ""), "date"),
                self.text_input("lot", t(_(u"Lot")), get("lot", "")),
                self.select_input("client", t(_(u"Client")),
                                  get("client", ""),
                                  self.get_client_options()),
                self.select_input("sample_type", t(_(u"Sample Type")),
                                  get("sample_type", ""),
                                  self.get_sample_type_options()),
                self.select_input("origin", t(_(u"Origin")),
                                  get("origin", ""), origins),
                self.text_input("van_min", t(_(u"Vanillin min")),
                                get("van_min", ""), "number"),
                self.text_input("van_max", t(_(u"Vanillin max")),
                                get("van_max", ""), "number"),
            ]

            reset = u""
            if flt.is_active(self.filters):
                reset = (
                    u'<a class="btn btn-sm btn-outline-secondary ml-2" '
                    u'href="{url}">{label}</a>'
                ).format(url=escape(self.get_dashboard_url()),
                         label=escape(t(_(u"Reset"))))

            return (
                u'<form method="get" action="{url}" '
                u'class="trimeta-dashboard-filters card card-body mb-3">'
                u'<div class="row">{fields}</div>'
                u'<div class="row"><div class="col-md-12">'
                u'<button type="submit" class="btn btn-sm btn-primary">'
                u'{search}</button>{reset}'
                u'</div></div>'
                u'</form>'
            ).format(url=escape(self.get_dashboard_url()),
                     fields=u"".join(fields),
                     search=escape(t(_(u"Search"))),
                     reset=reset)
        except Exception:
            # Mieux vaut un tableau sans barre de filtres qu'aucun
            # tableau du tout.
            logger.exception("Barre de filtres non rendue")
            return u""

    def get_dashboard_url(self):
        return "{}/trimeta-dashboard".format(api.get_url(self.context))

    # -- remplissage des lignes -------------------------------------------

    def folderitems(self):
        """Ajoute les resultats d'analyse, en une requete pour la page."""
        self._page_ids = []
        items = super(DashboardView, self).folderitems()

        keywords = cols.get_keywords()
        self._results = fetch_results(
            api.get_tool(ANALYSIS_CATALOG), self._page_ids, keywords)

        for item in items:
            per_sample = self._results.get(item.get("_trimeta_id"), {})
            for column_id, keyword, _label in cols.DASHBOARD_ANALYSES:
                item[column_id] = per_sample.get(keyword, "")

        self.warn_about_empty_columns()
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
                value = getattr(obj, attr, "")
                item[key] = self.format_value(value)
        except Exception:
            logger.exception("Ligne %s incomplete", index)
        return item

    def format_value(self, value):
        """Texte affichable, en respectant la langue du compte pour les
        dates."""
        if not value:
            return ""
        if isinstance(value, DateTime):
            return self.ulocalized_time(value, long_format=1)
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
