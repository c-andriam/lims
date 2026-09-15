# -*- coding: utf-8 -*-
"""
Etape de mise a jour 1003 -> 1004.

Active la couche de navigateur `ITrimetaLayer`, qui porte les
surcharges de nommage des fichiers COA (demande D10).

Pourquoi une etape est necessaire
---------------------------------
`profiles/default/browserlayer.xml` n'est lu qu'a l'installation du
profil. Une instance ou l'add-on est deja installe ne le rejouerait
jamais: la couche resterait inactive, les surcharges ne seraient jamais
retenues par le registre d'adaptateurs, et les COA continueraient de
porter le Sample ID -- sans la moindre erreur pour l'expliquer.

Contrairement aux etapes 1001 a 1003, celle-ci ne touche a aucun index
et ne reindexe rien: elle est instantanee, quel que soit le nombre
d'echantillons.
"""

import logging

logger = logging.getLogger("senaite.trimeta.samplefields")

VERSION = "1004"
PROFILE_ID = "profile-senaite.trimeta.samplefields:default"
STEP = "browserlayer"


def upgrade(tool):
    """:param tool: portal_setup, fourni par GenericSetup."""
    logger.info("Upgrade Trimeta -> %s : demarrage", VERSION)

    # `tool` EST le portal_setup pour un upgradeStep, mais GenericSetup
    # passe parfois l'outil parent selon le point d'appel. On ne fait
    # pas de suppositions.
    setup = getattr(tool, "portal_setup", tool)
    setup.runImportStepFromProfile(PROFILE_ID, STEP)

    logger.info(
        "Couche ITrimetaLayer activee: les COA sont desormais nommes "
        "par le Code echantillon.")
    logger.info("Upgrade Trimeta -> %s : termine", VERSION)
    return True
