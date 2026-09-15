# -*- coding: utf-8 -*-
"""
Telechargement unitaire d'un COA, nomme par le Code echantillon.

Surcharge de `bika.lims.browser.publish.downloadview.DownloadView`,
enregistree sur notre couche (voir interfaces.py). La vue amont est
laissee intacte; on ne redefinit que ce qui change.

Deux differences avec l'amont
-----------------------------
1. Le nom vient du Code echantillon, via `filename.get_report_filename`.

2. L'en-tete `Content-Disposition` entoure le nom de GUILLEMETS.
   L'amont ecrit:

       "inline; filename=%s" % filename

   Cette forme non entouree convenait tant que le nom etait un Sample
   ID (`W-0031`, jamais d'espace). Le Code echantillon, lui, est du
   texte libre: `Vanille Bourbon 2024` y serait tronque au premier
   blanc par la RFC 6266, et le navigateur enregistrerait un fichier
   nomme `Vanille`. `sanitize()` remplace deja les blancs, mais les
   guillemets sont la seconde barriere -- celle qui tient meme si
   `sanitize()` evolue.
"""

import logging

from bika.lims.browser.publish.downloadview import DownloadView

from senaite.trimeta.samplefields.coa import filename as fn

logger = logging.getLogger("senaite.trimeta.samplefields")


class TrimetaDownloadView(DownloadView):
    """Telechargement d'un COA nomme par le Code echantillon."""

    def get_report_filename(self, report):
        return fn.get_report_filename(report)

    def download(self, data, filename, content_type="application/pdf"):
        """Comme l'amont, mais avec un nom de fichier entre guillemets."""
        response = self.request.response
        response.setHeader(
            "Content-Disposition",
            'inline; filename="{}"'.format(filename))
        response.setHeader("Content-Type", content_type)
        response.setHeader("Content-Length", len(data))
        response.setHeader("Cache-Control", "no-store")
        response.setHeader("Pragma", "no-cache")
        response.write(data)
