# -*- coding: utf-8 -*-
"""Impression native avec valeurs stockees et affectations explicites."""
import logging
from bika.lims import api
from bika.lims.browser.worksheet.views.printview import PrintView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope.i18nmessageid import MessageFactory

from senaite.trimeta.samplefields.analysts import FIELD
from senaite.trimeta.samplefields.indexers import get_field_value
from senaite.trimeta.samplefields.worksheet.export import worksheet_result

_ = MessageFactory("senaite.trimeta.samplefields")
logger = logging.getLogger("senaite.trimeta.samplefields")


class TrimetaPrintView(PrintView):
    column_template = ViewPageTemplateFile("templates/sample_by_column.pt")
    row_template = ViewPageTemplateFile("templates/sample_by_row.pt")
    worksheet_analyst_label = _(u"Worksheet analyst")
    assigned_analyst_label = _(u"Assigned analyst")
    sample_code_label = _(u"Sample Code")

    def _analysis_data(self, analysis):
        data = super(TrimetaPrintView, self)._analysis_data(analysis)
        decimalmark = analysis.aq_parent.aq_parent.getDecimalMark()
        data["formatted_result"] = worksheet_result(
            analysis, data["formatted_result"], decimalmark)
        field = analysis.getField(FIELD)
        contact = field.get(analysis) if field is not None else None
        if field is None:
            data["assigned_lab_analyst"] = ""
        elif contact is None:
            data["assigned_lab_analyst"] = _(u"Not assigned")
        else:
            data["assigned_lab_analyst"] = api.get_title(contact)
        return data

    def _sample_data(self, sample):
        data = super(TrimetaPrintView, self)._sample_data(sample)
        data["sample_code"] = get_field_value(sample, "SampleCode") if sample else ""
        return data

    def renderWSTemplate(self):
        selected = self.request.get("template", self._TEMPLATES_LIST[0])
        templates = {"sample_by_column.pt": self.column_template,
                     "sample_by_row.pt": self.row_template}
        parts = selected.split(":")
        # Les modeles tiers continuent d'utiliser le moteur natif.
        if len(parts) > 2 or (len(parts) == 2 and parts[0] != "Worksheet Print Templates"):
            return super(TrimetaPrintView, self).renderWSTemplate()
        template = templates.get(parts[-1])
        if template is None:
            return super(TrimetaPrintView, self).renderWSTemplate()
        try:
            return template()
        except Exception:
            logger.exception("Impression de la Work Sheet impossible")
            raise
        finally:
            if self._current_ws_index < len(self._worksheets):
                self._current_ws_index += 1
