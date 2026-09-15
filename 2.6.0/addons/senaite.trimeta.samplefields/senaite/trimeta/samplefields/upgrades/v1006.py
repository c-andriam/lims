# -*- coding: utf-8 -*-
"""
Etape de mise a jour 1005 -> 1006 (parametres de base).

- virgule decimale sur les rapports (COA), si le point d'usine est encore
  en place;
- lundi comme premier jour de la semaine, si rien n'a ete choisi.

Les deux fonctions sont idempotentes et ne remplacent jamais un choix du
laboratoire.
"""

import logging

from senaite.trimeta.samplefields.setuphandlers import set_first_weekday
from senaite.trimeta.samplefields.setuphandlers import set_lab_defaults

logger = logging.getLogger("senaite.trimeta.samplefields")

VERSION = "1006"


def upgrade(tool):
    """:param tool: portal_setup, fourni par GenericSetup."""
    logger.info("Upgrade Trimeta -> %s : demarrage", VERSION)
    set_lab_defaults()
    set_first_weekday()
    logger.info("Upgrade Trimeta -> %s : termine", VERSION)
    return True
