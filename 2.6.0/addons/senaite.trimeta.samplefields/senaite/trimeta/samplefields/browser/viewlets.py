# -*- coding: utf-8 -*-
"""
Viewlet injectant, uniquement sur la page de creation d'echantillon
(ar_add) :
1. Le script JS du separateur visuel "Reception".
2. Une regle CSS qui masque le bandeau d'erreur recapitulatif natif
   de SENAITE (.portalMessage.alert-danger dans #viewlet-above-content),
   de facon garantie et independante du timing de chargement JS.
   Cette regle est volontairement scopee a cette seule page : le
   bandeau reste actif partout ailleurs dans l'application.
"""

from plone.app.layout.viewlets import ViewletBase
import logging

logger = logging.getLogger("senaite.trimeta.samplefields")


SCRIPT_TAG = (
    '<script type="text/javascript" '
    'id="trimeta-samplefields-script" '
    'data-portal-url="%s" '
    'src="%s/++resource++senaite.trimeta.samplefields.static/'
    'reception_separator.js"></script>'
)

STYLE_TAG = (
    "<style>"
    "#viewlet-above-content .portalMessage.alert-danger { "
    "display: none !important; "
    "}"
    "</style>"
)


class ReceptionSeparatorViewlet(ViewletBase):
    """Injecte le JS + CSS uniquement sur les formulaires d'ajout
    d'echantillon.

    La detection par nom de vue (__parent__.__name__) s'est averee peu
    fiable sur cette page AJAX particuliere ; on se base donc plutot
    sur l'URL de la requete, qui contient toujours '/ar_add' pour ce
    formulaire (que ce soit via un client, un batch ou le dossier
    racine des echantillons).
    """

    def render(self):
        request_url = self.request.get("ACTUAL_URL", "") or \
            self.request.get("URL", "")
        if "/ar_add" not in request_url:
            return ""
        portal_url = self.portal_state.portal_url()
        return STYLE_TAG + (SCRIPT_TAG % (portal_url, portal_url))
