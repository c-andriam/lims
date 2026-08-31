# -*- coding: utf-8 -*-
"""
Etape de mise a jour 1002 -> 1003.

Introduit l'index `getTrimetaSampleTypeUID`, qui porte le filtre
"Type d'echantillon" du tableau de bord.

Pourquoi un index a nous: senaite.core expose le type d'echantillon en
COLONNES du sample_catalog (getSampleTypeTitle, getSampleTypeUID) mais
n'en fait pas des index, et AnalysisRequest ne definit aucun accesseur
getSampleTypeUID. Voir le commentaire dans catalog.py.

Comme les precedentes, l'etape delegue a setuphandlers: le comportement
d'une mise a jour et celui d'une installation neuve restent
rigoureusement identiques.

Elle reindexe les echantillons existants. Sans cela le filtre ne
trouverait que les echantillons saisis apres la mise a jour.
"""

import logging

from bika.lims import api

from senaite.trimeta.samplefields.setuphandlers import reindex_catalog
from senaite.trimeta.samplefields.setuphandlers import setup_catalogs

logger = logging.getLogger("senaite.trimeta.samplefields")

VERSION = "1003"


def upgrade(tool):
    """:param tool: portal_setup, fourni par GenericSetup."""
    logger.info("Upgrade Trimeta -> %s : demarrage", VERSION)
    portal = api.get_portal()

    added = setup_catalogs(portal)
    for catalog_id, indexes in added.items():
        reindex_catalog(catalog_id, indexes)

    if not added:
        logger.info("Aucun index a creer, catalogue deja a jour")

    logger.info("Upgrade Trimeta -> %s : termine", VERSION)
    return True
