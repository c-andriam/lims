import logging

PRODUCT_NAME = "senaite.trimeta.samplefields"
logger = logging.getLogger(PRODUCT_NAME)
logger.warning("### TRIMETA SAMPLEFIELDS - MODULE IMPORTE ###")

# NOTE: le monkey patch ajax_submit (limitation a un seul message
# d'erreur a la fois) a ete retire sur demande. Le comportement natif
# (un message par champ obligatoire manquant) est conserve. Seul le
# bandeau recapitulatif en haut de page est supprime, via le JS
# reception_separator.js (voir browser/viewlets.py).


def initialize(context):
    """Zope 2 style initializer, requis meme si vide."""
    logger.warning("### TRIMETA SAMPLEFIELDS - INITIALIZE APPELE ###")
    pass
