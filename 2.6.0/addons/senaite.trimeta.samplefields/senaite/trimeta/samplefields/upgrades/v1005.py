# -*- coding: utf-8 -*-
"""
Etape de mise a jour 1004 -> 1005.

Pose la configuration que l'add-on livre desormais en code plutot que
de la laisser a l'operateur (voir defaults.py):

- D11 : le gabarit de publication par defaut devient le COA Trimeta,
  unitaire. senaite.impress livre `MultiDefault.pt`, un gabarit
  multi-echantillons qui recoit TOUS les echantillons selectionnes --
  d'ou les fichiers distincts au contenu identique decrits dans le
  cahier des charges. Ce n'etait donc ni un defaut du logiciel ni une
  fausse manipulation: c'etait le reglage d'usine.

- D9 : creation des calculs de moyenne sur repetitions et rattachement
  aux services d'analyse qui n'en portent pas deja un.

- D7 : attribution du role Analyst aux comptes deja lies a un contact
  du laboratoire. La creation des comptes reste manuelle: elle exige un
  mot de passe.

Comme les precedentes, l'etape delegue a setuphandlers, pour que le
comportement d'une mise a jour et celui d'une installation neuve
restent rigoureusement identiques.

Elle est idempotente et prudente: aucun reglage deliberement pose par
le laboratoire n'est ecrase. La rejouer ne coute rien.
"""

import logging

from bika.lims import api

from senaite.trimeta.samplefields.setuphandlers import apply_defaults

logger = logging.getLogger("senaite.trimeta.samplefields")

VERSION = "1005"


def upgrade(tool):
    """:param tool: portal_setup, fourni par GenericSetup."""
    logger.info("Upgrade Trimeta -> %s : demarrage", VERSION)
    apply_defaults(api.get_portal())
    logger.info("Upgrade Trimeta -> %s : termine", VERSION)
    return True
