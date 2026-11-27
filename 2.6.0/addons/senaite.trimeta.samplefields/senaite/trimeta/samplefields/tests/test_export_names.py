# -*- coding: utf-8 -*-
"""Contrats de nommage, extensions et noms metier existants."""
import unittest

from senaite.trimeta.samplefields.export_names import export_filename


class ExportFilenameTests(unittest.TestCase):
    def test_generic_names_all_types(self):
        for extension in (".csv", ".pdf", ".xlsx", ".xls", ".xml", ".json", ".txt", ".zip"):
            self.assertEqual(export_filename("download" + extension, "Echantillons"),
                             "Echantillons" + extension)

    def test_preserve_meaningful_names(self):
        for name in ("ECH-DEMO-002.pdf", "WS-001-classique.csv",
                     "COA-20261127_123456.zip", "Report-123.pdf", "Instrument-42.xml"):
            self.assertEqual(export_filename(name, "Autre"), name)

    def test_unsafe_names_and_reserved_windows(self):
        self.assertEqual(export_filename('CON.pdf', "Autre"), "CON_.pdf")
        self.assertEqual(export_filename('download.csv', 'Reception / lot\r\n2'),
                         "Reception-lot_2.csv")
        self.assertNotIn('"', export_filename('nom";x.pdf', "Autre"))

    def test_extension_fallback_and_double_pdf(self):
        self.assertEqual(export_filename("", "Feuille-WS-001", ".pdf"), "Feuille-WS-001.pdf")
        self.assertEqual(export_filename("Default.pt.pdf.pdf", "COA-2-echantillons"),
                         "COA-2-echantillons.pdf")
        self.assertEqual(export_filename("download.XLSX", "Clients"), "Clients.xlsx")


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromTestCase(ExportFilenameTests)
