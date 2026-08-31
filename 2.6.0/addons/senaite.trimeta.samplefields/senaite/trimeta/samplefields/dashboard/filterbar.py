# -*- coding: utf-8 -*-
"""
Rendu de la barre de filtres du tableau de bord.

Pourquoi ce module est separe de la vue
---------------------------------------
La premiere version dessinait le formulaire depuis `DashboardView.__call__`,
en le prefixant au rendu du listing. Deux defauts, tous deux constates a
l'ecran:

1. `senaite.app.listing` REUTILISE la meme vue pour ses requetes AJAX
   (pagination, tri, recherche). Prefixer le rendu collait donc du HTML
   devant une reponse JSON, et le navigateur repondait
   "JSON.parse: unexpected character at line 1 column 1". Le tableau
   restait vide.

2. `__call__` rend la page COMPLETE, chrome SENAITE compris. Le
   formulaire atterrissait donc avant `<html>`, c'est-a-dire au-dessus
   de la barre de navigation, hors de la zone de contenu.

Le formulaire est donc rendu par un viewlet (voir viewlets.py), qui le
place dans la zone de contenu sans jamais toucher au rendu de la vue.
La reponse AJAX reste intacte, et l'apparence est celle de n'importe
quelle page SENAITE.

Le formulaire reste un `<form method="get">` sans JavaScript: une
recherche est partageable par copie de l'URL, et rien ne peut se
desynchroniser entre ce qu'affiche le formulaire et ce que montre le
tableau.
"""

import logging

from bika.lims import api
from senaite.core.catalog import CLIENT_CATALOG
from senaite.core.catalog import SAMPLE_CATALOG
from senaite.core.catalog import SETUP_CATALOG
from senaite.core.i18n import translate as t
from zope.i18nmessageid import MessageFactory

from senaite.trimeta.samplefields.compat import to_text
from senaite.trimeta.samplefields.dashboard import filters as flt

_ = MessageFactory("senaite.trimeta.samplefields")

logger = logging.getLogger("senaite.trimeta.samplefields")

try:                                   # Python 2
    from cgi import escape as _escape
except ImportError:                    # Python 3
    from html import escape as _escape


def escape(value):
    """Echappe une valeur pour l'insertion dans du HTML, guillemets compris."""
    return _escape(to_text(value), True)


# Mise en forme de la page.
#
# Ces regles ne sont PAS globales malgre leur apparence: le viewlet qui
# les emet ne s'affiche que sur le tableau de bord, elles ne sont donc
# chargees nulle part ailleurs.
#
# Le probleme qu'elles corrigent: vingt colonnes dont les en-tetes se
# repliaient sur deux ou trois lignes, alignes chacun a une hauteur
# differente. Les libelles ont d'abord ete raccourcis (voir columns.py);
# ces regles font le reste.
STYLE = u"""<style>
/* En-tetes: une seule ligne, alignes sur la meme base. */
.senaite-table thead th,
#content table thead th,
table thead th {
  vertical-align: bottom;
  white-space: nowrap;
  font-size: .78rem;
  line-height: 1.2;
  padding: .45rem .55rem;
}

/* Cellules: un peu plus compactes, et une largeur bornee pour qu'un
   nom de client a rallonge ne pousse pas tout le tableau. */
#content table tbody td,
table tbody td {
  font-size: .82rem;
  padding: .35rem .55rem;
  vertical-align: middle;
  max-width: 16rem;
}

/* Vingt colonnes ne tiennent pas dans une page: on defile
   horizontalement plutot que de deborder.

   Volontairement PAS sur #content: y poser overflow-x creerait un
   contexte de formatage qui rognerait le menu de selection des
   colonnes. Si aucun de ces conteneurs n'existe, on ne change
   simplement rien -- aucun risque de regression. */
.senaite-listing,
.listing-container,
.table-responsive {
  overflow-x: auto;
}

/* Barre de filtres: les champs alignes sur leur base, quelle que soit
   la hauteur de leur etiquette. */
.trimeta-dashboard-filters .form-row {
  align-items: flex-end;
}
.trimeta-dashboard-filters label {
  margin-bottom: .15rem;
}
</style>"""


class FilterBar(object):
    """Dessine le formulaire de recherche du tableau de bord."""

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.filters = flt.read_filters(request.form)

    # -- vocabulaires ---------------------------------------------------

    def get_options(self, catalog_id, portal_type):
        """[(uid, intitule)] tries, pour une liste deroulante.

        N'utilise que `UID` et `Title`: ce sont des colonnes de
        metadonnees de TOUS les catalogues senaite (BASE_COLUMNS), donc
        les seules sur lesquelles on puisse compter sans verifier
        catalogue par catalogue.

        Le tri se fait en Python: `sortable_title` n'est pas garanti
        present partout.
        """
        try:
            brains = api.search({"portal_type": portal_type,
                                 "is_active": True}, catalog_id)
            options = [(b.UID, to_text(b.Title)) for b in brains]
            return sorted(options, key=lambda pair: pair[1].lower())
        except Exception:
            logger.exception("Liste %s indisponible", portal_type)
            return []

    def get_origin_options(self):
        """Provenances reellement saisies, lues dans l'index.

        Il n'existe pas de liste de reference pour ce champ: les choix
        proposes sont donc les valeurs deja rencontrees.
        """
        try:
            catalog = api.get_tool(SAMPLE_CATALOG)
            values = catalog.uniqueValuesFor("getOrigin")
            return [(v, v) for v in sorted([to_text(x) for x in values if x])]
        except Exception:
            logger.exception("Provenances indisponibles")
            return []

    # -- briques de formulaire -------------------------------------------

    def text_input(self, name, label, input_type="text"):
        return (
            u'<div class="col-6 col-md-3 col-lg-2 mb-2">'
            u'<label class="small text-muted mb-1" for="{id}">{label}</label>'
            u'<input class="form-control form-control-sm" type="{type}" '
            u'id="{id}" name="{id}" value="{value}"/>'
            u'</div>'
        ).format(id=flt.PREFIX + name,
                 label=escape(label),
                 value=escape(self.filters.get(name, "")),
                 type=input_type)

    def select_input(self, name, label, options):
        current = to_text(self.filters.get(name, ""))
        rendered = [u'<option value=""></option>']
        for value, text in options:
            selected = u' selected="selected"' \
                if to_text(value) == current else u''
            rendered.append(u'<option value="{v}"{s}>{t}</option>'.format(
                v=escape(value), s=selected, t=escape(text)))
        return (
            u'<div class="col-6 col-md-3 col-lg-2 mb-2">'
            u'<label class="small text-muted mb-1" for="{id}">{label}</label>'
            u'<select class="form-control form-control-sm" '
            u'id="{id}" name="{id}">{options}</select>'
            u'</div>'
        ).format(id=flt.PREFIX + name,
                 label=escape(label),
                 options=u"".join(rendered))

    # -- rendu ------------------------------------------------------------

    def get_action_url(self):
        return u"{}/trimeta-dashboard".format(api.get_url(self.context))

    def render(self):
        try:
            fields = [
                self.text_input("date_from", t(_(u"Received from")), "date"),
                self.text_input("date_to", t(_(u"Received to")), "date"),
                self.text_input("lot", t(_(u"Lot"))),
                self.select_input(
                    "client", t(_(u"Client")),
                    self.get_options(CLIENT_CATALOG, "Client")),
                self.select_input(
                    "sample_type", t(_(u"Sample Type")),
                    self.get_options(SETUP_CATALOG, "SampleType")),
                self.select_input("origin", t(_(u"Origin")),
                                  self.get_origin_options()),
                self.text_input("van_min", t(_(u"Vanillin min")), "number"),
                self.text_input("van_max", t(_(u"Vanillin max")), "number"),
            ]

            reset = u""
            if flt.is_active(self.filters):
                reset = (
                    u'<a class="btn btn-sm btn-outline-secondary ml-2" '
                    u'href="{url}">{label}</a>'
                ).format(url=escape(self.get_action_url()),
                         label=escape(t(_(u"Reset"))))

            return STYLE + (
                u'<form method="get" action="{url}" '
                u'class="trimeta-dashboard-filters card mb-3">'
                u'<div class="card-body py-2">'
                u'<div class="form-row">{fields}</div>'
                u'<div class="form-row"><div class="col-12">'
                u'<button type="submit" class="btn btn-sm btn-primary">'
                u'{search}</button>{reset}'
                u'</div></div>'
                u'</div></form>'
            ).format(url=escape(self.get_action_url()),
                     fields=u"".join(fields),
                     search=escape(t(_(u"Search"))),
                     reset=reset)
        except Exception:
            # Mieux vaut un tableau sans barre de filtres qu'aucun
            # tableau du tout.
            logger.exception("Barre de filtres non rendue")
            return u""
