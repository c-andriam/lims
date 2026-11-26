# -*- coding: utf-8 -*-
"""La creation d'un lot d'echantillons doit etre atomique."""
import logging
import re
import transaction
from senaite.trimeta.samplefields.browser.sample_add import SampleAddView
from senaite.trimeta.samplefields.compat import to_text

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


class TrimetaSampleSubmitView(SampleAddView):
    """Refuse les creations vides et annule tout le lot en cas d'echec."""

    def ajax_submit(self):
        def submit():
            self.normalize_item_codes()
            return super(TrimetaSampleSubmitView, self).ajax_submit()
        return atomic_submit(submit)

    def normalize_item_codes(self):
        """Le controle obligatoire doit lire la valeur, pas le choix Autre."""
        form = getattr(self.request, "form", self.request)
        keys = [key for key in form if re.match(r"^CodeArticle-\d+$", key)]
        if not keys:
            return
        sample = self.get_ar()
        field = sample.getField("CodeArticle")
        for key in keys:
            try:
                value, _options = field.widget.process_form(
                    sample, field, {"CodeArticle": form[key] or ""})
            except IndexError:
                value = ""
            form[key] = to_text(value).strip()
