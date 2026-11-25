# -*- coding: utf-8 -*-
"""Saisie native des repetitions d'une analyse avant verification."""
import hashlib
import json
import logging

import transaction
from AccessControl import Unauthorized
from bika.lims import api
from bika.lims.api.security import check_permission
from plone.protect import CheckAuthenticator
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent
from senaite.core.permissions import EditFieldResults, EditResults
from senaite.core.permissions import FieldEditAnalysisResult

from senaite.trimeta.samplefields.defaults import build_interims
from senaite.trimeta.samplefields.defaults import setup_dynamic_calculation
from senaite.trimeta.samplefields.repetitions import KEYWORD
from senaite.trimeta.samplefields.repetitions import is_repetition_calculation
from senaite.trimeta.samplefields.repetitions import normalize_values

logger = logging.getLogger("senaite.trimeta.samplefields")


def can_edit(analysis, request):
    """Permissions natives et verrouillage explicite apres soumission."""
    if getattr(analysis, "portal_type", None) != "Analysis":
        return False
    sample = analysis.getRequest()
    if sample is None or api.get_workflow_status_of(analysis) not in (
            "unassigned", "assigned"):
        return False
    if not is_repetition_calculation(analysis.getCalculation()):
        return False
    permission = EditFieldResults if analysis.getPointOfCapture() == "field" else EditResults
    return (api.is_active(sample) and check_permission(permission, analysis)
            and check_permission(FieldEditAnalysisResult, analysis))


def revision(analysis):
    """Refuse l'ecrasement d'une saisie modifiee dans un autre onglet."""
    calculation = analysis.getCalculation()
    values = [analysis.getInterimFields(), analysis.getResult(),
              api.get_uid(calculation), api.get_workflow_status_of(analysis)]
    payload = json.dumps(values, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class RepetitionsView(BrowserView):
    index = ViewPageTemplateFile("templates/repetitions.pt")

    def __call__(self):
        if not can_edit(self.context, self.request):
            raise Unauthorized(u"Cette analyse ne permet pas la saisie de repetitions.")
        self.error = u""
        self.saved = False
        self.token = revision(self.context)
        self.values = [field.get("value", "")
                       for field in self.context.getInterimFields()
                       if KEYWORD.match(field.get("keyword", ""))]
        if not self.values:
            self.values = ["", ""]
        if self.request.get("REQUEST_METHOD") == "POST":
            CheckAuthenticator(self.request)
            values = self.request.form.get("repetitions", [])
            self.values = values if isinstance(values, list) else [values]
            try:
                self.save()
                self.saved = True
            except ValueError as error:
                self.error = str(error)
                self.token = self.request.form.get("revision", "")
            except Exception:
                self.error = u"Enregistrement impossible. Aucune valeur n'a ete modifiee."
                self.token = self.request.form.get("revision", "")
        if self.saved:
            self.token = revision(self.context)
        return self.index()

    def save(self):
        if self.request.form.get("revision") != revision(self.context):
            raise ValueError(u"L'analyse a change. Rechargez la page avant de saisir a nouveau.")
        values = normalize_values(self.values)
        checkpoint = transaction.savepoint(optimistic=True)
        try:
            calculation = setup_dynamic_calculation(api.get_portal())
            if calculation is None:
                raise ValueError(u"Le calcul de moyenne est indisponible.")
            fields = build_interims(len(values))
            for field, value in zip(fields, values):
                field["value"] = value
            others = [dict(field) for field in self.context.getInterimFields()
                      if not KEYWORD.match(field.get("keyword", ""))]
            self.context.setCalculation(calculation)
            self.context.setInterimFields(others + fields)
            self.context.setDetectionLimitOperand("")
            self.context.calculateResult(override=True)
            self.context.reindexObject()
            notify(ObjectModifiedEvent(self.context))
            self.values = values
        except Exception:
            checkpoint.rollback()
            logger.exception("Enregistrement des repetitions annule")
            raise

    def back_url(self):
        return self.context.getRequest().absolute_url()
