# -*- coding: utf-8 -*-
"""L'export transpose suit les positions, sans colonnes classiques vides."""
import unittest
from collections import OrderedDict
from senaite.trimeta.samplefields.worksheet import views


class TestTransposedExportColumns(unittest.TestCase):
    def test_only_active_slots_are_exposed_to_native_export(self):
        rows = [{'item_key': 'Result', 'column_key': 'VAN',
                 '1': {'formatted_result': '2.05'},
                 '4': {'formatted_result': '0.61'}},
                {'item_key': 'Pos', '1': {}, '4': {}}]
        parent = views.AnalysesTransposedView
        original = parent.folderitems
        self.addCleanup(setattr, parent, 'folderitems', original)
        parent.folderitems = lambda instance: rows
        view = views.TrimetaAnalysesTransposedView.__new__(views.TrimetaAnalysesTransposedView)
        view.get_slots = lambda: ['1', '4']
        view.cell_sample_label = lambda cell: 'SAMPLE-CODE'
        view.columns = OrderedDict((key, {'title': ''}) for key in
                                   ['Pos', 'Result', 'SampleCode', 'column_key', '1', '4'])
        result = view.folderitems()
        self.assertEqual([key for key, col in view.columns.items() if col.get('toggle')],
                         ['column_key', '1', '4'])
        self.assertIn('Result', view.columns)
        self.assertFalse(view.columns['Result']['toggle'])
        self.assertEqual(view.columns['1']['title'], 'Position 1')
        self.assertEqual(view.columns['4']['title'], 'Position 4')
        self.assertEqual(result[0]['1']['formatted_value'], '2.05')
        self.assertEqual(result[0]['4']['formatted_value'], '0.61')
        self.assertEqual(result[1]['1']['formatted_value'], 'SAMPLE-CODE')


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromTestCase(TestTransposedExportColumns)
