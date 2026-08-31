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

import logging

from plone.app.layout.viewlets import ViewletBase

from senaite.trimeta.samplefields.dashboard.filterbar import FilterBar

logger = logging.getLogger("senaite.trimeta.samplefields")

# Fragment d'URL identifiant la page du tableau de bord.
DASHBOARD_MARKER = "trimeta-dashboard"


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
