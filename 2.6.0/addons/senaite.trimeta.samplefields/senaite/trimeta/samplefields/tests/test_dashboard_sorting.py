# -*- coding: utf-8 -*-
"""Ordre global des echantillons, independant des pages et des reprises."""
import unittest

from senaite.trimeta.samplefields.dashboard.sorting import sort_sample_types
from senaite.trimeta.samplefields.dashboard.sorting import sort_vanillin
from senaite.trimeta.samplefields.dashboard.results import group_by_sample
from senaite.trimeta.samplefields.tests.test_dashboard import FakeBrain


class SampleBrain(object):
    def __init__(self, sample_id, title=""):
        self.getId = sample_id
        self.UID = sample_id
        self.getSampleTypeTitle = title

    def getObject(self):
        raise AssertionError("Le tri ne doit pas reveiller les objets")


def ids(brains):
    return [brain.getId for brain in brains]


class TestDashboardSorting(unittest.TestCase):
    def setUp(self):
        self.brains = [SampleBrain("S3"), SampleBrain("S1"), SampleBrain("S2")]

    def test_numeric_order_instead_of_lexical_order(self):
        results = {'S1': {'VAN': '10'}, 'S2': {'VAN': '2,5'}, 'S3': {'VAN': '0'}}
        self.assertEqual(ids(sort_vanillin(self.brains, results, ['VAN'])), ['S3', 'S2', 'S1'])
        self.assertEqual(ids(sort_vanillin(self.brains, results, ['VAN'], True)), ['S1', 'S2', 'S3'])

    def test_unusable_results_stay_last_in_both_directions(self):
        brains = [SampleBrain('S%d' % i) for i in range(7)]
        results = dict(('S%d' % i, {'VAN': value}) for i, value in enumerate(
            ['<0.5', '', 'nan', 'inf', 'NA', '2', '10']))
        self.assertEqual(ids(sort_vanillin(brains, results, ['VAN'])),
                         ['S5', 'S6', 'S0', 'S1', 'S2', 'S3', 'S4'])
        self.assertEqual(ids(sort_vanillin(brains, results, ['VAN'], True)),
                         ['S6', 'S5', 'S0', 'S1', 'S2', 'S3', 'S4'])

    def test_equal_values_have_stable_identifiers(self):
        results = dict((key, {'VAN': '2'}) for key in ('S1', 'S2', 'S3'))
        for descending in (False, True):
            for brains in (self.brains, list(reversed(self.brains))):
                self.assertEqual(ids(sort_vanillin(brains, results, ['VAN'], descending)),
                                 ['S1', 'S2', 'S3'])

    def test_sort_uses_latest_non_empty_retest_and_keyword_priority(self):
        results = group_by_sample([
            FakeBrain('S1', 'VAN', '2', 1), FakeBrain('S1', 'VAN', '10', 2),
            FakeBrain('S1', 'VAN', '', 3), FakeBrain('S1', 'ALIAS', '0', 4),
            FakeBrain('S2', 'ALIAS', '3', 2)])
        self.assertEqual(ids(sort_vanillin(self.brains, results, ['VAN', 'ALIAS'])),
                         ['S2', 'S1', 'S3'])

    def test_pagination_must_slice_the_globally_sorted_selection(self):
        results = {'S1': {'VAN': '10'}, 'S2': {'VAN': '2'}, 'S3': {'VAN': '5'}}
        ordered = sort_vanillin(self.brains, results, ['VAN'])
        self.assertEqual(ids(ordered[:2]), ['S2', 'S3'])
        self.assertEqual(ids(ordered[2:]), ['S1'])

    def test_sample_types_ignore_case_and_accents_and_keep_empty_last(self):
        brains = [SampleBrain('S1', u'Vanille'), SampleBrain('S2', u''),
                  SampleBrain('S3', u'\u00c9xtrait'), SampleBrain('S4', u'extrait')]
        self.assertEqual(ids(sort_sample_types(brains)), ['S3', 'S4', 'S1', 'S2'])
        self.assertEqual(ids(sort_sample_types(brains, True)), ['S1', 'S3', 'S4', 'S2'])

    def test_empty_selection(self):
        self.assertEqual(sort_vanillin([], {}, ['VAN']), [])
        self.assertEqual(sort_sample_types([]), [])

    def test_non_latin_type_names_are_not_treated_as_missing(self):
        brains = [SampleBrain('S1', ''), SampleBrain('S2', u'\u9999\u8349'),
                  SampleBrain('S3', 'Vanille')]
        self.assertEqual(ids(sort_sample_types(brains, True)), ['S2', 'S3', 'S1'])


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromTestCase(TestDashboardSorting)
