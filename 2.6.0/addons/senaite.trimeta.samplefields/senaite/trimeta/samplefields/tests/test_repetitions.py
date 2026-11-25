# -*- coding: utf-8 -*-
"""Moyenne variable et refus des series incompletes ou non numeriques."""
import unittest

from senaite.trimeta.samplefields.repetitions import average_interims
from senaite.trimeta.samplefields.repetitions import normalize_values
from senaite.trimeta.samplefields.repetitions import is_repetition_calculation
from senaite.trimeta.samplefields import defaults, repetitions


def interims(values):
    return [{"keyword": "R{}".format(index), "value": value}
            for index, value in enumerate(values, 1)]


class TestVariableRepetitions(unittest.TestCase):
    def test_two_three_four_five_and_twenty_repetitions(self):
        for count in (2, 3, 4, 5, 20):
            values = list(range(1, count + 1))
            self.assertEqual(average_interims(interims(values)), (count + 1) / 2.0)

    def test_zero_and_negative_numbers_count_as_measurements(self):
        self.assertEqual(average_interims(interims([0, -2, 2, 4])), 1.0)

    def test_decimal_comma_and_exponent(self):
        self.assertAlmostEqual(average_interims(interims([" 2,2 ", "2e0"])), 2.1)

    def test_no_implicit_zero_or_partial_average(self):
        for values in ([], [2], [2, ""], [2, " "], [2, None], [2, "<3"],
                       [2, "NaN"], [2, "inf"], [2, "1e999"], [2, "abc"]):
            self.assertEqual(average_interims(interims(values)), "NA")

    def test_missing_repetition_keyword_is_not_ignored(self):
        self.assertEqual(average_interims([
            {"keyword": "R1", "value": "2"},
            {"keyword": "R3", "value": "4"}]), "NA")

    def test_duplicate_repetition_keyword_is_rejected(self):
        self.assertEqual(average_interims(interims([2, 4]) + [
            {"keyword": "R2", "value": "6"}]), "NA")

    def test_unrelated_interims_do_not_change_mean(self):
        fields = interims([2, 4]) + [{"keyword": "MASS", "value": "100"}]
        self.assertEqual(average_interims(fields), 3.0)

    def test_large_finite_measurements_do_not_overflow_sum(self):
        self.assertEqual(average_interims(interims(["1e308", "1e308"])), 1e308)

    def test_form_rejects_invalid_series_before_writes(self):
        for values in ([2], [2, ""], [2, "nan"], [2, "__import__('os')"], "2;4"):
            with self.assertRaises(ValueError):
                normalize_values(values)

    def calculation(self, count=3):
        class Calculation(object):
            trimeta_variable_repetitions = False

            def Title(self):
                return u"Moyenne de {} repetitions".format(count)

            def getFormula(self):
                return self.formula

            def getInterimFields(self):
                return self.fields

            def getPythonImports(self):
                return self.imports
        calculation = Calculation()
        calculation.formula = defaults.build_formula(count)
        calculation.fields = defaults.build_interims(count)
        calculation.imports = [{"module": "math", "function": "ceil"},
                               {"module": "math", "function": "floor"}]
        return calculation

    def test_original_calculations_can_use_variable_form(self):
        for count in (2, 3):
            calculation = self.calculation(count)
            self.assertTrue(is_repetition_calculation(calculation))
            for field in calculation.fields:
                del field['hidden']
                del field['wide']
            self.assertTrue(is_repetition_calculation(calculation))

    def test_custom_formula_fields_and_imports_are_preserved(self):
        calculation = self.calculation()
        calculation.formula += ' * 100'
        self.assertFalse(is_repetition_calculation(calculation))
        calculation = self.calculation()
        calculation.fields[0]['value'] = '1'
        self.assertFalse(is_repetition_calculation(calculation))
        calculation = self.calculation()
        calculation.imports.append({'module': 'math', 'function': 'sqrt'})
        self.assertFalse(is_repetition_calculation(calculation))

    def test_dynamic_calculation_changed_by_lab_is_preserved(self):
        calculation = self.calculation()
        calculation.trimeta_variable_repetitions = True
        calculation.formula = repetitions.FORMULA
        calculation.imports = repetitions.IMPORTS
        self.assertTrue(is_repetition_calculation(calculation))
        calculation.formula += ' * 100'
        self.assertFalse(is_repetition_calculation(calculation))


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromTestCase(TestVariableRepetitions)
