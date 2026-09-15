# -*- coding: utf-8 -*-
"""Tests du nom des PDF de COA (lot 4). Logique pure."""

import unittest

from senaite.trimeta.samplefields.coa.filename import build_coa_filename
from senaite.trimeta.samplefields.coa.filename import unique_filename


class TestBuildCoaFilename(unittest.TestCase):

    def test_uses_sample_code(self):
        self.assertEqual(build_coa_filename("ECH-DEMO-001", "VAN-0005"),
                         "ECH-DEMO-001.pdf")

    def test_falls_back_to_sample_id_when_code_is_empty(self):
        for code in (None, "", "   "):
            self.assertEqual(build_coa_filename(code, "VAN-0005"),
                             "VAN-0005.pdf")

    def test_replaces_unsafe_characters(self):
        self.assertEqual(build_coa_filename("ECH 001/A;b", "VAN-0005"),
                         "ECH_001_A_b.pdf")

    def test_neutralises_header_injection(self):
        self.assertEqual(
            build_coa_filename('ECH"\r\nX-Evil: 1', "VAN-0005"),
            "ECH_X-Evil_1.pdf")

    def test_code_made_only_of_unsafe_characters_falls_back(self):
        self.assertEqual(build_coa_filename("///", "VAN-0005"),
                         "VAN-0005.pdf")

    def test_keeps_inner_dots_strips_leading_ones(self):
        self.assertEqual(build_coa_filename("ECH.2026.001", "VAN-0005"),
                         "ECH.2026.001.pdf")
        self.assertEqual(build_coa_filename("..ECH", "VAN-0005"),
                         "ECH.pdf")


class TestUniqueFilename(unittest.TestCase):

    def test_free_name_is_kept_and_recorded(self):
        taken = set()
        self.assertEqual(unique_filename("ECH-001.pdf", taken), "ECH-001.pdf")
        self.assertEqual(taken, {"ECH-001.pdf"})

    def test_collisions_get_numbered_suffixes(self):
        taken = set()
        names = [unique_filename("ECH-001.pdf", taken) for _ in range(3)]
        self.assertEqual(names,
                         ["ECH-001.pdf", "ECH-001-2.pdf", "ECH-001-3.pdf"])

    def test_suffix_skips_names_already_taken(self):
        taken = {"ECH-001.pdf", "ECH-001-2.pdf"}
        self.assertEqual(unique_filename("ECH-001.pdf", taken),
                         "ECH-001-3.pdf")


def test_suite():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for case in (TestBuildCoaFilename, TestUniqueFilename):
        suite.addTests(loader.loadTestsFromTestCase(case))
    return suite
