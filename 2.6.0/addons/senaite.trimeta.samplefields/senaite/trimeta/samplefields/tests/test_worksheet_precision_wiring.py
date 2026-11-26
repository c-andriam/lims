# -*- coding: utf-8 -*-
"""Precision et impression raccordees aux classes natives installees."""
import unittest
from senaite.trimeta.samplefields.worksheet import views, printview
from senaite.trimeta.samplefields.tests.test_worksheet_precision import Analysis


class TestWorksheetPrecisionWiring(unittest.TestCase):
    def patch(self, owner, name, value):
        self.addCleanup(setattr, owner, name, getattr(owner, name))
        setattr(owner, name, value)

    def test_native_result_is_reformatted_without_modifying_raw_value(self):
        analysis = Analysis('0.61')
        self.patch(views.api, 'get_object', lambda brain: analysis)
        def native(view, brain, item):
            item.update(Result='0.61', formatted_result='1')
        self.patch(views.AnalysesView, '_folder_item_result', native)
        view = views.TrimetaAnalysesView.__new__(views.TrimetaAnalysesView)
        view.dmk = '.'
        row = {}
        view._folder_item_result(object(), row)
        self.assertEqual(row['formatted_result'], '0.61')
        self.assertEqual(row['Result'], '0.61')

    def test_native_permission_mask_is_not_bypassed(self):
        def forbidden(brain):
            raise AssertionError('Result object must not be read')
        self.patch(views.api, 'get_object', forbidden)
        self.patch(views.AnalysesView, '_folder_item_result',
                   lambda view, brain, item: item.update(Result=''))
        view = views.TrimetaAnalysesView.__new__(views.TrimetaAnalysesView)
        row = {}
        view._folder_item_result(object(), row)
        self.assertEqual(row, {'Result': ''})

    def print_view(self, selected):
        view = printview.TrimetaPrintView.__new__(printview.TrimetaPrintView)
        view.request = {'template': selected}
        view._TEMPLATES_LIST = [selected]
        view._worksheets = [object()]
        view._current_ws_index = 0
        view.column_template = lambda: 'COLUMN'
        view.row_template = lambda: 'ROW'
        return view

    def test_both_native_print_templates_use_the_addon_and_advance_once(self):
        for name, expected in [('sample_by_column.pt', 'COLUMN'), ('sample_by_row.pt', 'ROW')]:
            view = self.print_view('Worksheet Print Templates:' + name)
            self.assertEqual(view.renderWSTemplate(), expected)
            self.assertEqual(view._current_ws_index, 1)

    def test_third_party_template_is_delegated_to_native_renderer(self):
        self.patch(printview.PrintView, 'renderWSTemplate', lambda view: 'THIRD_PARTY')
        self.assertEqual(self.print_view('External:sample_by_row.pt').renderWSTemplate(), 'THIRD_PARTY')

    def test_print_data_has_exact_value_and_business_assignment(self):
        analysis = Analysis('2.0500')
        class Parent(object):
            def getDecimalMark(self):
                return '.'
        parent = Parent()
        parent.aq_parent = parent
        analysis.aq_parent = parent
        class Field(object):
            def get(self, context):
                return 'contact-object'
        analysis.getField = lambda name: Field()
        self.patch(printview.PrintView, '_analysis_data', lambda view, obj: {'formatted_result': '2'})
        self.patch(printview.api, 'get_title', lambda contact: 'Paul Randria')
        view = self.print_view('sample_by_row.pt')
        data = view._analysis_data(analysis)
        self.assertEqual(data['formatted_result'], '2.0500')
        self.assertEqual(data['assigned_lab_analyst'], 'Paul Randria')
        self.assertEqual(analysis.getResult(), '2.0500')


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromTestCase(TestWorksheetPrecisionWiring)
