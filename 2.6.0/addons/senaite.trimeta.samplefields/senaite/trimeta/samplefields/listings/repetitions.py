# -*- coding: utf-8 -*-
"""Acces a la saisie variable depuis l'echantillon et la feuille de travail."""
from xml.sax.saxutils import quoteattr

from bika.lims import api
from senaite.app.listing.interfaces import IListingViewAdapter
from zope.interface import implementer

from senaite.trimeta.samplefields.listings.base import BaseListingAdapter
from senaite.trimeta.samplefields.listings.base import insert_column_after
from senaite.trimeta.samplefields.listings.base import show_in_all_states


@implementer(IListingViewAdapter)
class RepetitionsListingAdapter(BaseListingAdapter):
    portal_types = ("Analysis",)

    def add_columns(self):
        insert_column_after(self.listing.columns, "Result", "TrimetaRepetitions", {
            "title": u"Repetitions", "sortable": False})
        show_in_all_states(self.listing, "TrimetaRepetitions")

    def fill_item(self, obj, item, index):
        from senaite.trimeta.samplefields.browser.repetitions import can_edit
        analysis = api.get_object(obj)
        if not can_edit(analysis, self.listing.request):
            return
        url = analysis.absolute_url() + "/trimeta-repetitions"
        item.setdefault("replace", {})["TrimetaRepetitions"] = (
            '<a class="btn btn-sm btn-outline-secondary" href={}>'
            'Saisir les repetitions</a>'.format(quoteattr(url)))
