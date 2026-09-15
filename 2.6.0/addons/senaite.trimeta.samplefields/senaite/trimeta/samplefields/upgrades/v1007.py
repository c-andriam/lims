# -*- coding: utf-8 -*-
"""
Etape de mise a jour 1006 -> 1007 (logo de l'application).

Pose le logo Trimeta Group (version blanche) dans la barre d'outils, si
aucun logo n'est defini dans Configuration > Apparence.
"""

import logging

from senaite.trimeta.samplefields.setuphandlers import set_site_logo

logger = logging.getLogger("senaite.trimeta.samplefields")

VERSION = "1007"


def upgrade(tool):
    """:param tool: portal_setup, fourni par GenericSetup."""
    logger.info("Upgrade Trimeta -> %s : demarrage", VERSION)
    set_site_logo()
    logger.info("Upgrade Trimeta -> %s : termine", VERSION)
    return True
