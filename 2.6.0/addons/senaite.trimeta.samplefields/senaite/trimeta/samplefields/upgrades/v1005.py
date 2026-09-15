# -*- coding: utf-8 -*-
"""
Etape de mise a jour 1004 -> 1005 (parametrage, langue et fuseau).

Importe profiles/default/registry.xml: francais comme langue par
defaut, langues proposees francais et anglais, langue du navigateur
ignoree, fuseau horaire du portail Indian/Antananarivo. Un site deja
installe en 1004 ne relit jamais ce fichier sans cette etape.

Pose aussi la devise (MGA) et le pays (Madagascar) du Setup SENAITE, si
ce sont encore les valeurs d'usine.
"""

import logging

from senaite.trimeta.samplefields.setuphandlers import PROFILE_ID
from senaite.trimeta.samplefields.setuphandlers import set_lab_defaults

logger = logging.getLogger("senaite.trimeta.samplefields")

VERSION = "1005"


def upgrade(tool):
    """:param tool: portal_setup, fourni par GenericSetup."""
    logger.info("Upgrade Trimeta -> %s : demarrage", VERSION)
    tool.runImportStepFromProfile(PROFILE_ID, "plone.app.registry")
    set_lab_defaults()
    logger.info("Upgrade Trimeta -> %s : termine", VERSION)
    return True
