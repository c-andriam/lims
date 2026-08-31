# -*- coding: utf-8 -*-
"""
Placement de la barre de filtres dans la page.

Pourquoi un viewlet
-------------------
Le formulaire doit apparaitre DANS la zone de contenu, au-dessus du
tableau, et surtout ne jamais toucher au rendu de la vue elle-meme:
`senaite.app.listing` reutilise la vue pour ses requetes AJAX, et tout
ce qu'on ajouterait a son rendu corromprait la reponse JSON.

Un viewlet resout les deux d'un coup: il est rendu par le gabarit de
page, donc au bon endroit et uniquement pour une vraie page HTML.

Detection de la page
--------------------
On se base sur l'URL de la requete, comme les viewlets de la section
Assurance Qualite. Le nom de la vue (`__parent__.__name__`) s'est
avere peu fiable sur les pages qui font des appels AJAX -- ce qui est
precisement le cas ici.
"""

import json
import logging

from plone.app.layout.viewlets import ViewletBase
from senaite.core.i18n import translate as t
from zope.i18nmessageid import MessageFactory

from senaite.trimeta.samplefields.dashboard import columns as cols
from senaite.trimeta.samplefields.dashboard.filterbar import FilterBar

_ = MessageFactory("senaite.trimeta.samplefields")

logger = logging.getLogger("senaite.trimeta.samplefields")

# Fragment d'URL identifiant la page du tableau de bord.
DASHBOARD_MARKER = "trimeta-dashboard"

RESOURCE_BASE = "++resource++senaite.trimeta.samplefields.static"

SCRIPT_TAG = (
    u'<script type="text/javascript">'
    u'window.TRIMETA_DASHBOARD = {config};'
    u'</script>'
    u'<script type="text/javascript" '
    u'id="trimeta-dashboard-script" '
    u'src="{portal_url}/{resources}/dashboard.js"></script>'
)


class DashboardScriptViewlet(ViewletBase):
    """Entree de barre laterale et infobulles d'en-tete.

    Rendu sur TOUTES les pages, contrairement au viewlet de la barre de
    filtres: le raccourci vers le tableau de bord doit etre disponible
    partout, pas seulement une fois qu'on y est deja.

    Le script lui-meme decide de ce qu'il applique: l'entree de barre
    laterale toujours, les infobulles seulement s'il trouve un tableau.
    """

    def get_portal_url(self):
        return self.portal_state.portal_url()

    def get_dashboard_url(self):
        return "{}/trimeta-dashboard".format(self.get_portal_url())

    def get_help_map(self):
        """{intitule court affiche: intitule complet}.

        L'appariement cote JavaScript se fait sur le texte rendu. Les
        deux faces viennent donc du meme catalogue de traduction, lu au
        meme instant: elles ne peuvent pas diverger.
        """
        labels = cols.get_column_labels()
        help_texts = cols.get_column_help()
        mapping = {}
        for key, short in labels.items():
            full = help_texts.get(key)
            if not full:
                continue
            short_text = t(short, context=self.request)
            full_text = t(full, context=self.request)
            if short_text and full_text and short_text != full_text:
                mapping[short_text] = full_text
        return mapping

    def get_config_json(self):
        return json.dumps({
            "url": self.get_dashboard_url(),
            "label": t(_(u"Dashboard"), context=self.request),
            "help": self.get_help_map(),
        })

    def render(self):
        try:
            return SCRIPT_TAG.format(
                config=self.get_config_json(),
                portal_url=self.get_portal_url(),
                resources=RESOURCE_BASE,
            )
        except Exception:
            logger.exception("Script du tableau de bord non injecte")
            return ""


class DashboardFiltersViewlet(ViewletBase):
    """Barre de filtres, au-dessus du tableau."""

    def get_request_url(self):
        return self.request.get("ACTUAL_URL", "") or \
            self.request.get("URL", "")

    def is_dashboard(self):
        """Vrai sur la page du tableau de bord, et nulle part ailleurs.

        Le test exclut les sous-chemins AJAX (`.../ajax_folderitems`):
        ils ne rendent pas de page, mais mieux vaut ne pas dependre de
        cette hypothese.
        """
        url = self.get_request_url()
        if DASHBOARD_MARKER not in url:
            return False
        return url.rstrip("/").endswith(DASHBOARD_MARKER)

    def render(self):
        if not self.is_dashboard():
            return ""
        try:
            return FilterBar(self.context, self.request).render()
        except Exception:
            # Une page sans barre de filtres reste utilisable; une page
            # qui ne s'affiche plus, non.
            logger.exception("Viewlet du tableau de bord non rendu")
            return ""
