# -*- coding: utf-8 -*-
"""
Monkey patch de bika.lims.workflow.analysisrequest.events.after_receive

Objectif: ne plus ecraser systematiquement DateReceived avec l'heure
systeme actuelle au moment du clic sur "Receive". Si le personnel a
deja saisi manuellement une date de reception (pour corriger un
retard de manipulation du logiciel), cette valeur est preservee.

Ce comportement aligne DateReceived sur la logique deja appliquee
nativement par SENAITE a DateSampled dans after_sample() (meme
fichier source), qui ne definit la date que si elle est vide.

Copie fidele de la fonction originale (senaite.core 2.6.0), avec
uniquement l'ajout d'une verification "if not already set" avant
d'appeler setDateReceived().
"""

import logging

from bika.lims.interfaces import IReceived
from bika.lims.workflow.analysisrequest import do_action_to_analyses
from DateTime import DateTime
from zope.interface import alsoProvides

logger = logging.getLogger("senaite.trimeta.samplefields")


def patched_after_receive(analysis_request):
    """Version patchee: ne definit DateReceived que si elle est vide,
    pour permettre une saisie manuelle prealable.
    """
    alsoProvides(analysis_request, IReceived)

    # --- SEULE MODIFICATION PAR RAPPORT A L'ORIGINAL ---
    # L'original faisait : analysis_request.setDateReceived(DateTime())
    # sans condition, ecrasant toute date deja saisie manuellement.
    if not analysis_request.getDateReceived():
        analysis_request.setDateReceived(DateTime())
    # --- FIN DE LA MODIFICATION ---

    do_action_to_analyses(analysis_request, "initialize")


def apply_patch():
    from bika.lims.workflow.analysisrequest import events
    events.after_receive = patched_after_receive
    logger.warning(
        "### TRIMETA: patch applique sur after_receive "
        "(DateReceived preservee si deja saisie manuellement) ###"
    )
