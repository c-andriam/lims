# -*- coding: utf-8 -*-
"""La creation d'un lot d'echantillons doit etre atomique."""
import logging
import transaction
from bika.lims.browser.analysisrequest.add2 import ajaxAnalysisRequestAddView

logger = logging.getLogger("senaite.trimeta.samplefields")


def atomic_submit(submit):
    """Le gestionnaire amont capture les erreurs: annule alors ses ecritures.

    Sans rollback, Zope valide la transaction puisque l'exception a ete
    capturee par ajax_submit. Un premier echantillon peut rester cree
    alors que le navigateur annonce l'echec du lot.
    """
    checkpoint = transaction.savepoint(optimistic=True)
    try:
        result = submit()
    except Exception:
        checkpoint.rollback()
        logger.exception("Creation des echantillons annulee")
        raise
    if isinstance(result, dict) and result.get("errors"):
        checkpoint.rollback()
        logger.warning("Creation des echantillons annulee: validation ou erreur")
    return result


class TrimetaSampleSubmitView(ajaxAnalysisRequestAddView):
    """Garde la validation native et annule tout le lot en cas d'echec."""

    def ajax_submit(self):
        return atomic_submit(super(TrimetaSampleSubmitView, self).ajax_submit)
