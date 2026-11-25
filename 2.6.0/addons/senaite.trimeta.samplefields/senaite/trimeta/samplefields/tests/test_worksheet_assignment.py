# -*- coding: utf-8 -*-
"""Affectation sur les deux dispositions natives de Work Sheet."""
import unittest
from collections import OrderedDict

from senaite.app.listing.interfaces import ITransposedListingView
from zope.interface import alsoProvides
from senaite.trimeta.samplefields import analysts
from senaite.trimeta.samplefields.listings import analysts as listing


class Listing(object):
    def __init__(self, query):
        self.contentFilter = query
        self.columns = OrderedDict([('Result', {})])
        self.review_states = [{'columns': ['Result']}]
        self.request = {}


class Field(object):
    def get(self, context):
        return context.contact


class Analysis(object):
    contact = None

    def getField(self, name):
        return Field()

    def absolute_url(self):
        return 'http://localhost/sample/analysis'


class Contact(object):
    title = u'Paul <Randria>'


class TestWorksheetAssignment(unittest.TestCase):
    def setUp(self):
        for owner, name, value in [
                (listing.api, 'get_object', lambda obj: obj),
                (listing.api, 'get_title', lambda obj: obj.title),
                (analysts, 'can_assign', lambda obj: True),
                (listing, 't', lambda text, **kw: text)]:
            self.addCleanup(setattr, owner, name, getattr(owner, name))
            setattr(owner, name, value)

    def test_worksheet_filter_without_portal_type_is_recognized(self):
        view = Listing({'getWorksheetUID': 'worksheet-uid'})
        adapter = listing.AssignedAnalystAdapter(view, None)
        self.assertTrue(adapter.applies())
        adapter.before_render()
        self.assertIn(analysts.FIELD, view.columns)
        self.assertIn(analysts.FIELD, view.review_states[0]['columns'])

    def test_sample_analyses_still_match_but_unrelated_listings_do_not(self):
        for query, expected in [({'portal_type': 'Analysis'}, True),
                                ({'portal_type': 'Client'}, False), ({}, False)]:
            self.assertEqual(listing.AssignedAnalystAdapter(Listing(query), None).applies(), expected)

    def test_transposed_view_keeps_position_columns(self):
        view = Listing({'getWorksheetUID': 'worksheet-uid'})
        alsoProvides(view, ITransposedListingView)
        listing.AssignedAnalystAdapter(view, None).before_render()
        self.assertNotIn(analysts.FIELD, view.columns)

    def test_transposed_cell_keeps_result_and_existing_annotations(self):
        view = Listing({'getWorksheetUID': 'worksheet-uid'})
        alsoProvides(view, ITransposedListingView)
        obj = Analysis()
        obj.contact = Contact()
        row = {'Result': '0.61', 'formatted_result': '0.61',
               'after': {'Result': '<span>native</span>'}}
        listing.AssignedAnalystAdapter(view, None).fill_item(obj, row, 0)
        self.assertEqual(row['Result'], '0.61')
        self.assertEqual(row['formatted_result'], '0.61')
        self.assertTrue(row['after']['Result'].startswith('<span>native</span>'))
        self.assertIn('Paul &lt;Randria&gt;', row['after']['Result'])
        self.assertIn('/trimeta-assign-analyst', row['after']['Result'])
        self.assertEqual(row[analysts.FIELD], Contact.title)

    def test_read_only_analysis_has_no_assignment_link(self):
        analysts.can_assign = lambda obj: False
        obj = Analysis()
        obj.contact = Contact()
        row = {}
        listing.AssignedAnalystAdapter(Listing({}), None).fill_item(obj, row, 0)
        self.assertNotIn('<a', row['replace'][analysts.FIELD])

    def test_control_without_assignment_field_is_unchanged(self):
        obj = Analysis()
        obj.getField = lambda name: None
        row = {'Result': 'OK'}
        listing.AssignedAnalystAdapter(Listing({}), None).fill_item(obj, row, 0)
        self.assertEqual(row, {'Result': 'OK'})


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromTestCase(TestWorksheetAssignment)
