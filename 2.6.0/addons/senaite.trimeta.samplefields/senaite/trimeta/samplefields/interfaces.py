# -*- coding: utf-8 -*-
"""Interfaces de l'add-on."""

from bika.lims.interfaces import IBikaLIMS


class ISenaiteTrimetaLayer(IBikaLIMS):
    """Couche navigateur posee par profiles/default/browserlayer.xml.

    Elle etend IBikaLIMS: une vue enregistree pour cette couche passe
    devant la vue du meme nom enregistree par senaite.core pour IBikaLIMS.
    """
