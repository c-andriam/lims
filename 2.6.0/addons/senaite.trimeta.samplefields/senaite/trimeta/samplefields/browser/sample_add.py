# -*- coding: utf-8 -*-
"""Creation atomique, sans confirmation trompeuse pour un formulaire vide."""

import transaction

from bika.lims.browser.analysisrequest.add2 import ajaxAnalysisRequestAddView
from zope.i18nmessageid import MessageFactory

_ = MessageFactory("senaite.trimeta.samplefields")


class SampleAddView(ajaxAnalysisRequestAddView):
    """Conserve la validation native et la transaction geree par Zope."""

    def create_samples(self, records):
        # Le core intercepte les exceptions et renvoie du JSON: sans retour
        # au savepoint, une creation partielle pourrait alors etre commitee.
        if not records:
            raise ValueError(self.context.translate(_(
                u"No sample was saved. Complete the required fields "
                u"and select the analyses before saving.")))
        checkpoint = transaction.savepoint(optimistic=True)
        try:
            samples = super(SampleAddView, self).create_samples(records)
            if not samples:
                raise ValueError(self.context.translate(_(
                    u"No sample was saved. Check the entered values.")))
            return samples
        except Exception:
            checkpoint.rollback()
            raise
