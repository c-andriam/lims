# -*- coding: utf-8 -*-
"""Precision de travail sans arrondi supplementaire ni changement de donnees."""
import unittest
from senaite.trimeta.samplefields.worksheet.export import stored_numeric_result, worksheet_result


class Analysis(object):
    def __init__(self, value, kind="numeric", operand=""):
        self.value, self.kind, self.operand = value, kind, operand

    def getResult(self):
        return self.value

    def getResultType(self):
        return self.kind

    def getDetectionLimitOperand(self):
        return self.operand


class TestWorksheetPrecision(unittest.TestCase):
    def test_recorded_values_are_not_rounded(self):
        for value in ("27.9", "0.61", "2.05", "2.0500", "0", "-0.003", "1.234567890123456789"):
            self.assertEqual(worksheet_result(Analysis(value), 'rounded'), value)

    def test_scientific_notation_is_not_converted_to_a_float(self):
        self.assertEqual(stored_numeric_result('1.200e-12'), '1.200e-12')

    def test_detection_limit_operand_is_preserved(self):
        self.assertEqual(worksheet_result(Analysis('0.61', operand='<'), '1'), '<0.61')
        self.assertEqual(stored_numeric_result('> 2.050', '>'), '>2.050')
        self.assertEqual(stored_numeric_result('<=0.01'), '<=0.01')

    def test_client_decimal_mark_is_respected(self):
        self.assertEqual(stored_numeric_result('0.610', decimalmark=','), '0,610')
        self.assertEqual(stored_numeric_result('0,610'), '0.610')

    def test_empty_text_and_nonfinite_values_keep_native_format(self):
        for value in ('', None, 'NA', 'ND', 'NaN', 'inf', '1,234.5'):
            self.assertEqual(worksheet_result(Analysis(value), 'native'), 'native')

    def test_select_and_text_results_keep_native_labels(self):
        for kind in ('select', 'multiselect', 'string'):
            self.assertEqual(worksheet_result(Analysis('1', kind), 'Conforme'), 'Conforme')

    def test_result_is_never_written(self):
        analysis = Analysis('2.0500')
        worksheet_result(analysis, '2')
        self.assertEqual(analysis.getResult(), '2.0500')

    def test_numeric_choice_codes_keep_their_native_label(self):
        analysis = Analysis('1')
        analysis.getResultOptions = lambda: [{'ResultValue': '1', 'ResultText': 'Conforme'}]
        self.assertEqual(worksheet_result(analysis, 'Conforme'), 'Conforme')


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromTestCase(TestWorksheetPrecision)
