# -*- coding: utf-8 -*-
"""
Etape de mise a jour 1000 -> 1001.

Introduit l'index et la colonne `getSampleCode` dans le sample_catalog,
et reindexe les echantillons deja saisis.

L'etape delegue a setuphandlers pour ne pas dupliquer la logique: le
comportement d'une mise a jour et celui d'une installation neuve
restent ainsi rigoureusement identiques.
"""

import logging

from bika.lims import api

from senaite.trimeta.samplefields.setuphandlers import reindex_catalog
from senaite.trimeta.samplefields.setuphandlers import setup_catalogs

logger = logging.getLogger("senaite.trimeta.samplefields")

VERSION = "1001"


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
