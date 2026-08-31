# -*- coding: utf-8 -*-
"""
Colonnes "Code echantillon" et "Lot" dans la liste des Echantillons.

Les deux valeurs proviennent de colonnes de metadonnees du catalogue --
getSampleCode, cree par l'add-on, et getClientSampleID, natif. Aucune
ligne ne reveille donc son objet depuis la ZODB: la liste reste rapide
meme a plusieurs milliers d'echantillons.
"""

from senaite.app.listing.interfaces import IListingViewAdapter
from zope.interface import implementer
from zope.i18nmessageid import MessageFactory

from senaite.trimeta.samplefields.listings.base import BaseListingAdapter
from senaite.trimeta.samplefields.listings.base import insert_column_after
from senaite.trimeta.samplefields.listings.base import show_in_all_states

_ = MessageFactory("senaite.trimeta.samplefields")

SAMPLE_CODE = "SampleCode"
LOT = "Lot"


@implementer(IListingViewAdapter)
class SamplesListingAdapter(BaseListingAdapter):
    """Ajoute Code echantillon et Lot a la liste des Echantillons."""

    portal_types = ("AnalysisRequest",)

    def add_columns(self):
        columns = self.listing.columns

        # Placees juste apres l'identifiant SENAITE: c'est la que l'oeil
        # cherche une reference d'echantillon.
        insert_column_after(columns, "getId", SAMPLE_CODE, {
            "title": _(u"Sample Code"),
            "index": "getSampleCode",
            "sortable": True,
            "toggle": True,
        })
        insert_column_after(columns, SAMPLE_CODE, LOT, {
            "title": _(u"Lot"),
            "index": "getClientSampleID",
            "sortable": True,
            "toggle": True,
        })

        show_in_all_states(self.listing, SAMPLE_CODE, LOT)

    def fill_item(self, obj, item, index):
        # Colonnes de metadonnees: lecture directe sur le brain.
        item[SAMPLE_CODE] = getattr(obj, "getSampleCode", "") or ""
        item[LOT] = getattr(obj, "getClientSampleID", "") or ""
