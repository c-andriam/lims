# -*- coding: utf-8 -*-
"""Tests de l'export d'une Work Sheet Transposed (demande D13). Pur."""

import unittest

from senaite.trimeta.samplefields.worksheet.export import fill_export_values
from senaite.trimeta.samplefields.worksheet.export import format_due_date
from senaite.trimeta.samplefields.worksheet.export import slot_title


def transposed_rows():
    """Forme reelle de AnalysesTransposedView.folderitems: une ligne
    d'en-tete "Pos", puis une ligne par service, cellules par position."""
    header = {"column_key": "Position", "item_key": "Pos",
              "1": {"replace": {"Pos": "<html>"}},
              "2": {"replace": {"Pos": "<html>"}}}
    vanilline = {"column_key": "VANILLINE", "item_key": "Result",
                 "transposed_keys": ["1", "2"],
                 "1": {"Result": "2.05", "formatted_result": "2.05",
                       "sample": "ECH-001 (VAN-0006)"},
                 "2": {"Result": "1.90", "formatted_result": "1.90",
                       "sample": "VAN-0007"}}
    aw = {"column_key": "AW", "item_key": "Result",
          "transposed_keys": ["1"],
          "1": {"Result": "0.61", "formatted_result": "",
                "sample": "ECH-001 (VAN-0006)"}}
    return [header, vanilline, aw]


class TestFillExportValues(unittest.TestCase):

    def fill(self):
        rows = transposed_rows()
        fill_export_values(rows, ["1", "2"], lambda cell: cell["sample"])
        return rows

    def test_result_cells_export_their_result(self):
        _header, vanilline, _aw = self.fill()
        self.assertEqual(vanilline["1"]["formatted_value"], "2.05")
        self.assertEqual(vanilline["2"]["formatted_value"], "1.90")

    def test_falls_back_to_raw_result(self):
        _header, _vanilline, aw = self.fill()
        self.assertEqual(aw["1"]["formatted_value"], "0.61")

    def test_header_cells_export_the_sample(self):
        header, _vanilline, _aw = self.fill()
        self.assertEqual(header["1"]["formatted_value"], "ECH-001 (VAN-0006)")
        self.assertEqual(header["2"]["formatted_value"], "VAN-0007")

    def test_empty_slot_is_left_alone(self):
        rows = transposed_rows()
        del rows[2]["1"]
        fill_export_values(rows, ["1", "2", "3"], lambda cell: cell["sample"])
        self.assertNotIn("3", rows[0])


class TestSlotTitle(unittest.TestCase):

    def test_code_and_id(self):
        self.assertEqual(slot_title("ECH-001", "VAN-0006"), "ECH-001 (VAN-0006)")

    def test_id_alone_without_code(self):
        for code in (None, ""):
            self.assertEqual(slot_title(code, "VAN-0006"), "VAN-0006")


class TestFormatDueDate(unittest.TestCase):

    def test_due_date_is_localized(self):
        self.assertEqual(format_due_date("2026-09-20", lambda d: "20/09/2026"),
                         "20/09/2026")

    def test_no_due_date_gives_empty_cell(self):
        for value in (None, ""):
            self.assertEqual(format_due_date(value, lambda d: "jamais"), "")

    def test_localizer_returning_none_gives_empty_cell(self):
        self.assertEqual(format_due_date("2026-09-20", lambda d: None), "")


def test_suite():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for case in (TestFillExportValues, TestSlotTitle, TestFormatDueDate):
        suite.addTests(loader.loadTestsFromTestCase(case))
    return suite
