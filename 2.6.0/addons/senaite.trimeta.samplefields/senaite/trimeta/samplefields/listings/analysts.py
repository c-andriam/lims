# -*- coding: utf-8 -*-
"""Analyste affecte par analyse dans les echantillons et Work Sheets."""
from xml.sax.saxutils import escape, quoteattr
from bika.lims import api
from senaite.app.listing.interfaces import IListingViewAdapter
from zope.interface import implementer
from zope.i18nmessageid import MessageFactory
from senaite.core.i18n import translate as t
from senaite.trimeta.samplefields import analysts
from senaite.trimeta.samplefields.compat import to_text
from senaite.trimeta.samplefields.listings.base import BaseListingAdapter, insert_column_after, show_in_all_states

_ = MessageFactory("senaite.trimeta.samplefields")


@implementer(IListingViewAdapter)
class AssignedAnalystAdapter(BaseListingAdapter):
    portal_types = ("Analysis",)

    def add_columns(self):
        insert_column_after(self.listing.columns, "Analyst", analysts.FIELD, {
            "title": _(u"Assigned laboratory analyst"), "sortable":False})
        show_in_all_states(self.listing, analysts.FIELD)

    def fill_item(self, obj, item, index):
        analysis = api.get_object(obj)
        field = analysis.getField(analysts.FIELD)
        if field is None:
            return
        contact = field.get(analysis)
        title = api.get_title(contact) if contact is not None else ""
        item[analysts.FIELD] = title
        rendered = escape(to_text(title))
        if analysts.can_assign(analysis):
            url = analysis.absolute_url() + "/trimeta-assign-analyst"
            label = escape(to_text(t(_(u"Assign"), context=self.listing.request)))
            rendered += ' <a class="btn btn-sm btn-outline-secondary" href={}>{}</a>'.format(quoteattr(url),label)
        item.setdefault("replace", {})[analysts.FIELD] = rendered
