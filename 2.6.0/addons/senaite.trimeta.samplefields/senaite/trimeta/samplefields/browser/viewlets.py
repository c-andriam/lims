# -*- coding: utf-8 -*-
"""
Viewlets injectant les ressources statiques de l'add-on.

Deux viewlets distincts, parce que les deux pages n'ont ni les memes
besoins ni le meme rendu:

- ReceptionSeparatorViewlet, sur le formulaire d'ajout d'echantillon:
  separateurs Reception/Analyse, autocompletion des champs libres,
  clavier numerique, et masquage du bandeau d'erreur recapitulatif.

- QualitySectionsViewlet, sur les formulaires de modification: intitules
  des 7 sous-sections de l'onglet Assurance Qualite. Ces champs sont
  masques a la creation, donc inutiles sur ar_add.
"""

import json
import logging

from plone.app.layout.viewlets import ViewletBase
from zope.i18n import translate

from senaite.trimeta.samplefields.qualitydata.extender import (
    get_section_map)

logger = logging.getLogger("senaite.trimeta.samplefields")

RESOURCE_BASE = "++resource++senaite.trimeta.samplefields.static"

SCRIPT_TAG = (
    '<script type="text/javascript" '
    'id="trimeta-samplefields-script" '
    'data-portal-url="{portal_url}" '
    'src="{portal_url}/{resources}/reception_separator.js"></script>'
)

QA_SCRIPT_TAG = (
    '<script type="text/javascript">'
    'window.TRIMETA_QA_SECTIONS = {sections};'
    '</script>'
    '<script type="text/javascript" '
    'id="trimeta-qa-sections-script" '
    'src="{portal_url}/{resources}/quality_sections.js"></script>'
)

# Masque le bandeau d'erreur recapitulatif natif de SENAITE sur la seule
# page de creation. En CSS plutot qu'en JS: garanti, et independant du
# moment ou le script se charge.
STYLE_TAG = (
    "<style>"
    "#viewlet-above-content .portalMessage.alert-danger { "
    "display: none !important; "
    "}"
    "</style>"
)

# Pages de modification, selon le rendu (Archetypes ou vue SENAITE).
EDIT_URL_MARKERS = ("/base_edit", "/edit", "/atct_edit")


class TrimetaViewletBase(ViewletBase):
    """Outillage commun aux viewlets de l'add-on."""

    def get_request_url(self):
        return self.request.get("ACTUAL_URL", "") or \
            self.request.get("URL", "")

    def get_portal_url(self):
        return self.portal_state.portal_url()


class ReceptionSeparatorViewlet(TrimetaViewletBase):
    """Ressources du formulaire de creation d'echantillon.

    La detection par nom de vue (__parent__.__name__) s'est averee peu
    fiable sur cette page AJAX; on se base sur l'URL de la requete, qui
    contient toujours '/ar_add' pour ce formulaire, qu'on y arrive par
    un client, un batch ou le dossier racine des echantillons.
    """

    def render(self):
        if "/ar_add" not in self.get_request_url():
            return ""
        return STYLE_TAG + SCRIPT_TAG.format(
            portal_url=self.get_portal_url(),
            resources=RESOURCE_BASE,
        )


class QualitySectionsViewlet(TrimetaViewletBase):
    """Intitules des sous-sections Assurance Qualite.

    Les sous-sections sont definies une seule fois cote Python; elles
    sont serialisees ici pour le JavaScript. Ajouter un champ a une
    sous-section suffit donc a le voir apparaitre du bon cote du bon
    intitule.
    """

    def is_edit_page(self):
        url = self.get_request_url()
        return any(marker in url for marker in EDIT_URL_MARKERS)

    def get_sections_json(self):
        sections = []
        for section_id, title, fieldnames in get_section_map():
            sections.append({
                "id": section_id,
                "title": translate(title, context=self.request),
                "fields": fieldnames,
            })
        return json.dumps(sections)

    def render(self):
        if not self.is_edit_page():
            return ""
        return QA_SCRIPT_TAG.format(
            portal_url=self.get_portal_url(),
            resources=RESOURCE_BASE,
            sections=self.get_sections_json(),
        )
