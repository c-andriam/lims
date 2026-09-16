# -*- coding: utf-8 -*-
"""
Colonne "Code echantillon" dans la liste des rapports d'analyse.

Ecran vise: la liste des COA d'un client (reports_listing). Une ligne y
est un ARReport, qui pointe vers l'echantillon dont il rend compte.
"""

from bika.lims import api

from senaite.trimeta.samplefields.compat import string_types
from senaite.app.listing.interfaces import IListingViewAdapter
from zope.i18nmessageid import MessageFactory
from zope.interface import implementer

from senaite.trimeta.samplefields.listings.base import BaseListingAdapter
from senaite.trimeta.samplefields.listings.base import insert_column_after
from senaite.trimeta.samplefields.listings.base import show_in_all_states

_ = MessageFactory("senaite.trimeta.samplefields")

SAMPLE_CODE = "SampleCode"
LOT = "Lot"

# Colonnes natives retouchees pour l'export CSV.
INFO = "Info"
PRIMARY_SAMPLE = "AnalysisRequest"
PDF = "PDF"

# Colonne native "Batch" (lot de travail), traduite "Lot" en francais:
# elle faisait croire que le Lot de l'echantillon etait vide.
NATIVE_BATCH = "Batch"


@implementer(IListingViewAdapter)
class ReportsListingAdapter(BaseListingAdapter):
    """Ajoute Code echantillon et Lot a la liste des rapports."""

    portal_types = ("ARReport",)

    def add_columns(self):
        columns = self.listing.columns
        insert_column_after(columns, "AnalysisRequest", SAMPLE_CODE, {
            "title": _(u"Sample Code"),
            "sortable": False,
            "toggle": True,
        })
        insert_column_after(columns, SAMPLE_CODE, LOT, {
            "title": _(u"Lot"),
            "sortable": False,
            "toggle": True,
        })
        if NATIVE_BATCH in columns:
            # masquee par defaut, toujours activable dans le menu des colonnes
            columns[NATIVE_BATCH]["toggle"] = False
        if INFO in columns:
            # La valeur de cette colonne EST du HTML (icone d'information):
            # l'export CSV la recopiait telle quelle, en premiere colonne.
            # L'export ne retient que les colonnes AFFICHEES: masquee par
            # defaut, elle sort du fichier et reste activable dans le menu
            # des colonnes.
            columns[INFO]["toggle"] = False
        show_in_all_states(self.listing, SAMPLE_CODE, LOT)

    def get_sample_uid(self, report):
        """UID de l'echantillon dont le rapport rend compte."""
        uid = getattr(report, "getAnalysisRequestUID", None)
        if isinstance(uid, string_types) and uid:
            return uid
        try:
            obj = api.get_object(report)
            sample = obj.getAnalysisRequest()
        except Exception:
            return None
        return api.get_uid(sample) if sample else None

    def fill_export_values(self, item, sample):
        """Valeurs texte des colonnes qui n'existent qu'en HTML.

        senaite.core ne renseigne que `item["replace"]` pour l'echantillon
        primaire et le lien PDF. A l'ecran on voit un lien; l'export CSV,
        lui, lit `item[cle]` et ramenait donc des colonnes vides.

        L'affichage ne change pas: `replace` reste prioritaire. Aucune
        adresse n'est inventee -- sans lien de telechargement (rapport sans
        fichier), la cellule reste vide.
        """
        replace = item.get("replace") or {}
        if not item.get(PRIMARY_SAMPLE) and sample is not None:
            item[PRIMARY_SAMPLE] = sample.getId()
        if not item.get(PDF):
            url = item.get("url")
            item[PDF] = "{}/download_pdf".format(url) \
                if url and replace.get(PDF) else ""

    def fill_item(self, obj, item, index):
        sample = self.get_cached_sample(self.get_sample_uid(obj))
        item[SAMPLE_CODE] = self.get_sample_code(sample)
        item[LOT] = (sample.getClientSampleID() or "") if sample else ""
        self.fill_export_values(item, sample)
