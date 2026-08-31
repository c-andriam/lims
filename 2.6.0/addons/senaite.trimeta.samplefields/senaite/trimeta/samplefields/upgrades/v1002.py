# -*- coding: utf-8 -*-
"""
Etape de mise a jour 1001 -> 1002.

Introduit les index et colonnes dont le tableau de bord du lot 5 a
besoin: la Provenance (index, car elle sert de filtre), le poids a la
reception, les dates de debut et de fin d'analyse, et les trois
operateurs HPLC / humidite / activite de l'eau.

Comme pour la 1001, l'etape delegue a setuphandlers: le comportement
d'une mise a jour et celui d'une installation neuve restent ainsi
rigoureusement identiques, et il n'y a qu'un seul endroit ou se tromper.

Cette etape reindexe les echantillons existants. Sur une base fournie
c'est long -- comptez de l'ordre de la minute pour quelques milliers
d'echantillons -- mais c'est indispensable: un index fraichement cree
reste vide pour tout l'historique, et le tableau de bord n'afficherait
alors des valeurs que pour les echantillons saisis apres la mise a jour.
"""

import logging

from bika.lims import api

from senaite.trimeta.samplefields.setuphandlers import reindex_catalog
from senaite.trimeta.samplefields.setuphandlers import setup_catalogs

logger = logging.getLogger("senaite.trimeta.samplefields")

VERSION = "1002"


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
