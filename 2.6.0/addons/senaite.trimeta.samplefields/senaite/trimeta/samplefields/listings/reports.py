# -*- coding: utf-8 -*-
"""
Colonne "Code echantillon" dans la liste des rapports d'analyse.

Ecran vise: la liste des COA d'un client (reports_listing). Une ligne y
est un ARReport, qui pointe vers l'echantillon dont il rend compte.
"""

from bika.lims import api
from senaite.app.listing.interfaces import IListingViewAdapter
from zope.i18nmessageid import MessageFactory
from zope.interface import implementer

from senaite.trimeta.samplefields.listings.base import BaseListingAdapter
from senaite.trimeta.samplefields.listings.base import insert_column_after
from senaite.trimeta.samplefields.listings.base import show_in_all_states

_ = MessageFactory("senaite.trimeta.samplefields")

SAMPLE_CODE = "SampleCode"


@implementer(IListingViewAdapter)
class ReportsListingAdapter(BaseListingAdapter):
    """Ajoute le Code echantillon a la liste des rapports."""

    portal_types = ("ARReport",)

    def add_columns(self):
        insert_column_after(self.listing.columns, "Title", SAMPLE_CODE, {
            "title": _(u"Sample Code"),
            "sortable": False,
            "toggle": True,
        })
        show_in_all_states(self.listing, SAMPLE_CODE)

    def get_sample_uid(self, report):
        """UID de l'echantillon dont le rapport rend compte."""
        uid = getattr(report, "getAnalysisRequestUID", None)
        if isinstance(uid, str) and uid:
            return uid
        try:
            obj = api.get_object(report)
            sample = obj.getAnalysisRequest()
        except Exception:
            return None
        return api.get_uid(sample) if sample else None

    def fill_item(self, obj, item, index):
        sample = self.get_cached_sample(self.get_sample_uid(obj))
        item[SAMPLE_CODE] = self.get_sample_code(sample)
