# -*- coding: utf-8 -*-
"""
Telechargement groupe de COA, nommes par le Code echantillon.

Surcharge de
`bika.lims.browser.workflow.client.WorkflowActionDownloadReportsAdapter`,
declenchee par le bouton "Telecharger" de la liste des rapports. Un seul
rapport selectionne donne un PDF; plusieurs donnent une archive ZIP.

Ici, contrairement aux deux autres surcharges, on ne peut pas se
contenter de redefinir une methode: l'amont fabrique le nom EN LIGNE
dans `__call__`. On reprend donc la boucle, en gardant telles quelles
`get_pdf()` et `download()` heritees.

Trois corrections en passant
----------------------------
**1. L'objet persistant n'est plus modifie.** L'amont ecrit
`pdf.filename = ...` sur l'objet `Pdf` lu depuis la ZODB, pour le relire
juste apres. Ecrire dans un objet persistant pour s'en servir comme
variable locale salit la transaction sans aucun besoin. On tient ici une
liste de couples (nom, donnees).

**2. Les noms de l'archive sont rendus uniques.** Le Code echantillon
n'est soumis a aucune contrainte d'unicite dans SENAITE. Deux rapports
d'une meme selection peuvent donc porter le meme nom, et
`zipfile.writestr()` accepterait les deux entrees sans rien dire: la
plupart des extracteurs n'en montreraient qu'une, et un COA
disparaitrait en silence. Voir `filename.unique_name()`.

**3. Le nom de fichier est entre guillemets** dans l'en-tete
`Content-Disposition`, comme dans coa/download.py et pour la meme
raison: un nom contenant un blanc serait tronque par la RFC 6266.

A ne pas confondre avec la demande D11
--------------------------------------
D11 decrit "5 fichiers aux noms differents mais au meme contenu". Ce
n'est pas ce code: c'est le choix d'un gabarit `Multi...` a la
publication, qui produit un PDF unique contenant les cinq echantillons,
ensuite rattache a chacun d'eux. Voir docs/lot1-parametrage.md.
"""

import logging
import tempfile
import zipfile

from bika.lims import _
from bika.lims import api
from bika.lims.browser.workflow.client import (
    WorkflowActionDownloadReportsAdapter)
from DateTime import DateTime

from senaite.trimeta.samplefields.coa import filename as fn

logger = logging.getLogger("senaite.trimeta.samplefields")


class TrimetaDownloadReportsAdapter(WorkflowActionDownloadReportsAdapter):
    """Telechargement groupe dont les fichiers portent le Code
    echantillon."""

    def __call__(self, action, uids):
        # (nom de fichier, donnees) -- l'objet Pdf de la ZODB n'est pas
        # modifie, contrairement a l'amont.
        entries = []
        taken = set()

        for uid in uids:
            try:
                report = api.get_object_by_uid(uid)
            except Exception:
                logger.exception("Rapport %r introuvable", uid)
                continue

            pdf = self.get_pdf(report)
            if pdf is None:
                self.add_status_message(
                    _("Could not load PDF for sample {}".format(
                        self.describe(report))), "warning")
                continue

            name = fn.unique_name(fn.get_report_filename(report), taken)
            entries.append((name, pdf.data))

        if not entries:
            # L'amont tomberait ici sur un IndexError (pdfs[0]) ou
            # produirait une archive vide. On le dit, et on revient.
            self.add_status_message(
                _("No report could be downloaded"), "warning")
            return self.redirect(
                redirect_url=self.request.get_header("referer"))

        if len(entries) == 1:
            name, data = entries[0]
            return self.download(data, name, type="application/pdf")

        with self.create_archive(entries) as archive:
            timestamp = DateTime().strftime("%Y%m%d_%H%M%S")
            archive_name = "COA-{}.zip".format(timestamp)
            data = archive.file.read()
            return self.download(data, archive_name, type="application/zip")

    def describe(self, report):
        """Identifiant lisible d'un rapport, pour un message d'erreur.

        Le Code echantillon si on l'a, le Sample ID sinon: c'est ce que
        l'operateur cherchera dans sa liste.
        """
        try:
            sample = report.getAnalysisRequest()
            return fn.get_sample_code(sample) or api.get_id(sample)
        except Exception:
            return api.get_id(report)

    def create_archive(self, entries):
        """Archive ZIP a partir de couples (nom, donnees).

        Signature volontairement differente de celle de l'amont, qui
        attend des objets porteurs de `.filename` et `.data`: passer une
        liste de couples a la methode heritee produirait une archive
        muette et fausse. Un nom different rend l'incompatibilite
        visible a la lecture.
        """
        archive = tempfile.NamedTemporaryFile(suffix=".zip")
        with zipfile.ZipFile(archive.name, "w", zipfile.ZIP_DEFLATED) as zf:
            for name, data in entries:
                zf.writestr(name, data)
        return archive

    def download(self, data, filename, type="application/zip"):
        """Comme l'amont, mais avec un nom de fichier entre guillemets."""
        response = self.request.response
        response.setHeader(
            "Content-Disposition",
            'attachment; filename="{}"'.format(filename))
        response.setHeader("Content-Type", "{}; charset=utf-8".format(type))
        response.setHeader("Content-Length", len(data))
        response.setHeader("Cache-Control", "no-store")
        response.setHeader("Pragma", "no-cache")
        response.write(data)
