# -*- coding: utf-8 -*-
"""
Pieces jointes d'un envoi de COA, nommees par le Code echantillon.

Surcharge de `bika.lims.browser.publish.emailview.EmailView`,
enregistree sur notre couche pour les deux contextes ou l'amont la
declare: le Client et l'echantillon.

Une seule methode change: `get_report_filename()`, consommee par la
propriete `email_attachments`. Tout le reste de l'ecran d'envoi --
destinataires, corps du message, controle de taille, journal d'envoi --
reste celui de SENAITE.

C'est le point le plus visible des trois pour le laboratoire: c'est le
nom que le client final lit dans sa boite aux lettres.
"""

import logging

from bika.lims.browser.publish.emailview import EmailView

from senaite.trimeta.samplefields.coa import filename as fn

logger = logging.getLogger("senaite.trimeta.samplefields")


class TrimetaEmailView(EmailView):
    """Ecran d'envoi dont les pieces jointes portent le Code
    echantillon."""

    def get_report_filename(self, report):
        return fn.get_report_filename(report)
