# -*- coding: utf-8 -*-
"""Resultats du COA sans arrondi supplementaire et avec repli natif."""
import unittest
from senaite.trimeta.samplefields.coa.reportview import CoaValidationMixin
from senaite.trimeta.samplefields.tests.test_worksheet_precision import Analysis


class Model(object):
    decimal_mark = ','

    def get_formatted_result(self, analysis):
        return 'NATIVE'


class Wrapper(object):
    def __init__(self, value, kind='numeric', operand=''):
        self.instance = Analysis(value,kind,operand)


class TestCoaResultPrecision(unittest.TestCase):
    def test_decimal_digits_and_recorded_trailing_zeros_are_kept(self):
        view = CoaValidationMixin()
        for value, expected in [('27.9','27,9'),('0.61','0,61'),('2.0500','2,0500'),('0','0')]:
            self.assertEqual(view.get_coa_result(Model(),Wrapper(value)),expected)

    def test_detection_limit_is_preserved_and_escaped_for_html(self):
        self.assertEqual(CoaValidationMixin().get_coa_result(Model(),Wrapper('0.61',operand='<')),'&lt;0,61')

    def test_scientific_notation_is_kept(self):
        self.assertEqual(CoaValidationMixin().get_coa_result(Model(),Wrapper('1.20e-5')),'1,20e-5')

    def test_text_choices_and_absent_results_keep_native_formatting(self):
        view = CoaValidationMixin()
        for value, kind in [('1','select'),('NA','numeric'),('','numeric')]:
            self.assertEqual(view.get_coa_result(Model(),Wrapper(value,kind)),'NATIVE')
        wrapper = Wrapper('1')
        wrapper.instance.getResultOptions = lambda: [{'ResultValue':'1','ResultText':'Conforme'}]
        self.assertEqual(view.get_coa_result(Model(),wrapper),'NATIVE')


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromTestCase(TestCoaResultPrecision)
