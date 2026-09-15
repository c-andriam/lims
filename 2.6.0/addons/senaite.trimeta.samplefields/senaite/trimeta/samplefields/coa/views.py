# -*- coding: utf-8 -*-
"""Les trois points ou senaite.core nomme un PDF de COA `<ID>.pdf`.

Enregistres dans coa/configure.zcml pour ISenaiteTrimetaLayer, ils
remplacent ceux de senaite.core sans toucher a son code.
"""

from bika.lims import _
from bika.lims import api
from bika.lims.browser.publish.downloadview import DownloadView
from bika.lims.browser.publish.emailview import EmailView
from bika.lims.browser.workflow.client import \
    WorkflowActionDownloadReportsAdapter
from DateTime import DateTime

from senaite.trimeta.samplefields.coa.filename import get_report_filename
from senaite.trimeta.samplefields.coa.filename import unique_filename


class TrimetaDownloadView(DownloadView):
    """Liste des rapports > clic sur un PDF."""

    def get_report_filename(self, report):
        return get_report_filename(report)


class TrimetaEmailView(EmailView):
    """Pieces jointes de l'envoi des resultats par e-mail."""

    def get_report_filename(self, report):
        return get_report_filename(report)


class TrimetaDownloadReportsAdapter(WorkflowActionDownloadReportsAdapter):
    """Liste des rapports > action groupee "Download".

    Le parent construit le nom en ligne dans __call__: on le recopie a
    l'identique, seule la ligne `pdf.filename = ...` change.
    """

    def __call__(self, action, uids):
        reports = map(api.get_object_by_uid, uids)

        pdfs = []
        taken = set()

        for report in reports:
            pdf = self.get_pdf(report)
            if pdf is None:
                sample_id = api.get_id(report.getAnalysisRequest())
                self.add_status_message(
                    _("Could not load PDF for sample {}"
                      .format(sample_id)), "warning")
                continue
            pdf.filename = unique_filename(get_report_filename(report), taken)
            pdfs.append(pdf)

        if len(pdfs) == 1:
            pdf = pdfs[0]
            return self.download(pdf.data, pdf.filename,
                                 type="application/pdf")

        with self.create_archive(pdfs) as archive:
            timestamp = DateTime().strftime("%Y%m%d_%H%M%S")
            archive_name = "Reports-{}.zip".format(timestamp)
            data = archive.file.read()
            return self.download(data, archive_name, type="application/zip")
