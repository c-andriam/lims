# -*- coding: utf-8 -*-
"""
Etape de mise a jour 1003 -> 1004 (lot 4, COA).

1. Pose la couche ISenaiteTrimetaLayer (browserlayer.xml). C'est elle
   qui active nos vues download_pdf / email et l'action download_reports,
   qui nomment les PDF d'apres le Code echantillon.
2. Ajoute le gabarit COA Trimeta a la liste des gabarits actifs de
   senaite.impress. Un site installe en 1003 n'est jamais repasse par
   post_install, qui s'en charge pour une installation neuve.
"""

import logging

from senaite.trimeta.samplefields.setuphandlers import PROFILE_ID
from senaite.trimeta.samplefields.setuphandlers import register_coa_template

logger = logging.getLogger("senaite.trimeta.samplefields")

VERSION = "1004"


def upgrade(tool):
    """:param tool: portal_setup, fourni par GenericSetup."""
    logger.info("Upgrade Trimeta -> %s : demarrage", VERSION)
    tool.runImportStepFromProfile(PROFILE_ID, "browserlayer")
    register_coa_template()
    logger.info("Upgrade Trimeta -> %s : termine", VERSION)
    return True
