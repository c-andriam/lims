# -*- coding: utf-8 -*-
"""
Pieces jointes d'un envoi de COA, nommees par le Code echantillon.

Surcharge de `bika.lims.browser.publish.emailview.EmailView`,
enregistree sur notre couche pour les deux contextes ou l'amont la
declare: le Client et l'echantillon.

Les noms sont uniques parmi les COA selectionnes, y compris sans casse.
Le meme nom est expose dans l'ecran et dans la piece jointe MIME.
La lecture du PDF est partagee avec les telechargements. Le reste --
destinataires, corps du message, controle de taille, journal d'envoi --
reste celui de SENAITE.

C'est le point le plus visible des trois pour le laboratoire: c'est le
nom que le client final lit dans sa boite aux lettres.
"""

import logging

from bika.lims.browser.publish.emailview import EmailView
from bika.lims import api

from senaite.trimeta.samplefields.coa import filename as fn
from senaite.trimeta.samplefields.coa.pdf import get_pdf

logger = logging.getLogger("senaite.trimeta.samplefields")


class TrimetaEmailView(EmailView):
    """Ecran d'envoi dont les pieces jointes portent le Code
    echantillon."""

    def get_report_filename(self, report):
        filenames = getattr(self, "_trimeta_report_filenames", None)
        if filenames is None:
            filenames = {}
            taken = set()
            for selected in self.reports:
                name = fn.unique_name(fn.get_report_filename(selected), taken)
                filenames[api.get_uid(selected)] = name
            self._trimeta_report_filenames = filenames
        return filenames.get(api.get_uid(report), fn.get_report_filename(report))

    def get_pdf(self, report):
        return get_pdf(report)
