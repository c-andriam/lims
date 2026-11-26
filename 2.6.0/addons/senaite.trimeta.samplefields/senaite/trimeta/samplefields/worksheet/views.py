# -*- coding: utf-8 -*-
"""Vues de saisie des resultats d'une Work Sheet.

Enregistrees dans worksheet/configure.zcml pour ISenaiteTrimetaLayer,
elles remplacent analyses_classic_view et analyses_transposed_view de
senaite.core.
"""

import logging

from bika.lims import api
from bika.lims import senaiteMessageFactory as _
from bika.lims.browser.worksheet.views import AnalysesTransposedView
from bika.lims.browser.worksheet.views import AnalysesView
from bika.lims.interfaces import IRoutineAnalysis

from senaite.trimeta.samplefields.indexers import get_field_value
from senaite.trimeta.samplefields.worksheet.export import fill_export_values
from senaite.trimeta.samplefields.worksheet.export import format_due_date
from senaite.trimeta.samplefields.worksheet.export import slot_title
from senaite.trimeta.samplefields.worksheet.export import worksheet_result

logger = logging.getLogger("senaite.trimeta.samplefields")


def sample_title(analysis):
    """`CODE (ID)` de l'echantillon d'une analyse de routine, sinon None."""
    if not IRoutineAnalysis.providedBy(analysis):
        return None
    sample = analysis.getRequest()
    return slot_title(get_field_value(sample, "SampleCode"),
                      api.get_id(sample))


class SampleCodeSlotHeaderMixin(object):
    """Tete de position: `CODE (ID)` au lieu de l'ID seul.

    Le document demande de "remplacer ou ajouter" l'ID par le code: on
    ajoute, le lien vers l'echantillon reste porte par l'ID.
    """

    def _folder_item_result(self, analysis_brain, item):
        super(SampleCodeSlotHeaderMixin, self)._folder_item_result(analysis_brain, item)
        # Le core n'ajoute formatted_result que si ViewResults est autorise
        # et qu'un resultat existe. Ne jamais contourner ce controle.
        if "formatted_result" not in item:
            return
        try:
            analysis = api.get_object(analysis_brain)
            item["formatted_result"] = worksheet_result(
                analysis, item["formatted_result"], self.dmk)
        except Exception:
            logger.exception("Presentation du resultat de Work Sheet impossible")

    def get_slot_header_data(self, obj):
        data = super(SampleCodeSlotHeaderMixin, self).get_slot_header_data(obj)
        title = sample_title(obj)
        if title:
            # copie: la methode parente est memoisee
            data = dict(data, item_title=title)
        return data

    def folderitem(self, obj, item, index):
        item = super(SampleCodeSlotHeaderMixin, self).folderitem(
            obj, item, index)
        # senaite.core (worksheet/views/analyses.py) ecrase l'echeance par
        # ulocalized_time(analyse) au lieu de getDueDate(): colonne toujours
        # vide dans la Work Sheet, remplie dans la liste de l'echantillon.
        try:
            due_date = api.get_object(obj).getDueDate()
            item["DueDate"] = format_due_date(
                due_date, lambda d: self.ulocalized_time(d, long_format=0))
        except Exception:
            logger.exception("Echeance de l'analyse %s illisible",
                             item.get("uid"))
        return item


class TrimetaAnalysesView(SampleCodeSlotHeaderMixin, AnalysesView):
    """Mise en page classique."""


class TrimetaAnalysesTransposedView(SampleCodeSlotHeaderMixin,
                                    AnalysesTransposedView):
    """Mise en page Transposed, exportable en CSV."""

    def folderitems(self):
        rows = super(TrimetaAnalysesTransposedView, self).folderitems()
        try:
            slots = list(self.get_slots())
            # Le core conserve les colonnes classiques dans self.columns.
            # React les ajoute a l'export meme hors de l'etat de revue.
            keys = ["column_key"] + slots
            for key, definition in self.columns.items():
                # Les metadonnees Result restent necessaires aux cellules
                # React, meme quand Result n'est pas une colonne externe.
                definition["toggle"] = key in keys
            self.columns["column_key"]["title"] = _(u"Analysis")
            for slot in slots:
                self.columns[slot]["title"] = u"Position {}".format(slot)
            fill_export_values(rows, slots, self.cell_sample_label)
        except Exception:
            # Un export incomplet vaut mieux qu'une grille qui ne s'affiche plus
            logger.exception("Valeurs d'export Transposed impossibles")
        return rows

    def cell_sample_label(self, cell):
        obj = api.get_object(cell.get("obj"), default=None)
        return (obj is not None and sample_title(obj)) or u""
