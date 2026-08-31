# -*- coding: utf-8 -*-
"""
senaite.trimeta.samplefields

Add-on SENAITE pour Trimeta Group. Ajoute au type Sample les champs
des sections Reception et Analyse, un magasin de suggestions partagees
pour les champs libres, et les index de catalogue permettant de les
afficher, trier et rechercher dans les listings.
"""

import logging

PRODUCT_NAME = "senaite.trimeta.samplefields"
PROFILE_ID = "profile-{}:default".format(PRODUCT_NAME)

logger = logging.getLogger(PRODUCT_NAME)

# Le patch date_received_patch (DateReceived modifiable manuellement)
# doit etre applique au chargement du module, avant que le workflow ne
# soit sollicite.
#
# NOTE: le monkey patch ajax_submit (limitation a un seul message
# d'erreur a la fois) a ete retire sur demande. Le comportement natif
# (un message par champ obligatoire manquant) est conserve. Seul le
# bandeau recapitulatif en haut de page est supprime, via le JS
# reception_separator.js (voir browser/viewlets.py).
import senaite.trimeta.samplefields.patches  # noqa: E402


def initialize(context):
    """Initialiseur Zope 2, requis meme si vide."""
    logger.info("%s initialise", PRODUCT_NAME)
