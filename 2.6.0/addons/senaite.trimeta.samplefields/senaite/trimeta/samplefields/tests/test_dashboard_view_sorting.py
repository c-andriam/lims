# -*- coding: utf-8 -*-
"""Raccordement du tri global a search() et _fetch_brains() natifs.

Execution avec bin/zopepy -m unittest, sans site Plone.
"""
import unittest

from senaite.core.catalog import SAMPLE_CATALOG
from senaite.trimeta.samplefields.dashboard import columns, view
from senaite.trimeta.samplefields.tests.test_dashboard import FakeBrain, FakeCatalog
from senaite.trimeta.samplefields.tests.test_dashboard_sorting import SampleBrain, ids


class Request(dict):
    @property
    def form(self):
        return self


class SampleCatalog(object):
    def __init__(self, brains):
        self.brains = brains
        self.queries = []

    def indexes(self):
        return ['created', 'getDateReceived', 'getDateVerified']

    def __call__(self, query):
        self.queries.append(query)
        return self.brains


class TestDashboardViewSorting(unittest.TestCase):
    def setUp(self):
        self.samples = SampleCatalog([
            SampleBrain('S1', 'Vanille'), SampleBrain('S2', 'Extrait'),
            SampleBrain('S3', '')])
        self.analyses = FakeCatalog([
            FakeBrain('S1', 'VAN', '1', 1), FakeBrain('S1', 'VAN', '10', 2),
            FakeBrain('S2', 'VAN', '2', 1), FakeBrain('S3', 'VAN', '5', 1)])
        previous = view.api.get_tool
        self.addCleanup(setattr, view.api, 'get_tool', previous)
        view.api.get_tool = lambda name: self.samples if name == SAMPLE_CATALOG else self.analyses
        self.view = view.DashboardView.__new__(view.DashboardView)
        self.view.request = Request()
        self.view.form_id = 'trimeta_dashboard'
        self.view.catalog = SAMPLE_CATALOG
        self.view.contentFilter = {'sort_on': 'created', 'sort_order': 'ascending'}
        self.view.review_states = [{'id':'default', 'contentFilter':{}}]
        self.view.default_review_state = 'default'
        self.view.pagesize = 2
        self.view._column_keywords = {'Vanillin':['VAN']}

    def select_sort(self, criterion, direction='ascending'):
        self.view.request['trimeta_dashboard_sort_on'] = criterion
        self.view.request['trimeta_dashboard_sort_order'] = direction

    def test_vanillin_sort_happens_before_native_pagination(self):
        self.select_sort(columns.VANILLIN_SORT)
        self.assertEqual(ids(self.view._fetch_brains(0)), ['S2', 'S3'])
        self.assertEqual(ids(self.view._fetch_brains(2)), ['S1'])
        self.assertEqual(self.view.total, 3)
        for query in self.analyses.queries:
            self.assertEqual(query['getRequestID'], ['S1', 'S2', 'S3'])
        self.assertEqual(self.samples.queries[0]['sort_on'], 'created')

    def test_descending_sort_uses_the_latest_result(self):
        self.select_sort(columns.VANILLIN_SORT, 'descending')
        self.assertEqual(ids(self.view._fetch_brains(0)), ['S1', 'S3'])
        self.assertEqual(ids(self.view._fetch_brains(2)), ['S2'])

    def test_sample_type_sort_keeps_empty_types_last_in_both_directions(self):
        for direction, expected in [('ascending', ['S2', 'S1', 'S3']),
                                    ('descending', ['S1', 'S2', 'S3'])]:
            self.select_sort(columns.SAMPLE_TYPE_SORT, direction)
            self.assertEqual(ids(self.view.search()), expected)
        self.assertEqual(self.analyses.queries, [])

    def test_manual_criteria_never_go_to_the_catalog_as_sort_indexes(self):
        for criterion in columns.MANUAL_SORTS:
            self.select_sort(criterion)
            query = self.view.get_catalog_query()
            self.assertEqual(query['sort_on'], 'created')
            self.assertEqual(self.view.manual_sort_on, criterion)

    def test_validation_sort_preserves_all_pages_and_total(self):
        for brain, state, date in zip(self.samples.brains,
                                      ['sample_received', 'published', 'verified'],
                                      [99, 2, 1]):
            brain.review_state = state
            brain.getDateVerified = date
        self.select_sort(columns.VALIDATION_SORT)
        self.assertEqual(ids(self.view._fetch_brains(0)), ['S3', 'S2'])
        self.assertEqual(ids(self.view._fetch_brains(2)), ['S1'])
        self.assertEqual(self.view.total, 3)
        self.assertEqual(self.samples.queries[0]['sort_on'], 'created')
        self.assertEqual(self.analyses.queries, [])

    def test_received_date_sort_preserves_missing_dates(self):
        self.samples.brains[0].getDateReceived = None
        self.samples.brains[1].getDateReceived = 2
        self.samples.brains[2].getDateReceived = 1
        self.select_sort(columns.DATE_RECEIVED_SORT, 'descending')
        self.assertEqual(ids(self.view._fetch_brains(0)), ['S2', 'S3'])
        self.assertEqual(ids(self.view._fetch_brains(2)), ['S1'])
        self.assertEqual(self.view.total, 3)


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromTestCase(TestDashboardViewSorting)
