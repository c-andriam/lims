# -*- coding: utf-8 -*-
"""
Tests de l'indexation du Code echantillon.

Le piege que ces tests couvrent: un champ ajoute par schemaextender n'a
pas d'accesseur sur la classe AnalysisRequest. Un index ZCatalog naif
resterait donc vide en silence, et la colonne du listing afficherait des
cases blanches sans qu'aucune erreur ne soit levee.
"""

import unittest

from senaite.core.api import catalog as capi
from senaite.core.catalog import SAMPLE_CATALOG

from senaite.trimeta.samplefields.indexers import to_index_string
from senaite.trimeta.samplefields.tests.base import TrimetaTestCase
from senaite.trimeta.samplefields.tests.utils import SampleFactory


class TestIndexStringNormalisation(unittest.TestCase):
    """Fonction pure, testable sans site Plone."""

    def test_none_becomes_empty_string(self):
        self.assertEqual(to_index_string(None), "")

    def test_bytes_are_decoded(self):
        self.assertEqual(to_index_string(b"ECH-001"), "ECH-001")

    def test_surrounding_whitespace_is_stripped(self):
        self.assertEqual(to_index_string("  ECH-001  "), "ECH-001")

    def test_non_string_is_coerced(self):
        self.assertEqual(to_index_string(42), "42")

    def test_accents_survive(self):
        self.assertEqual(to_index_string(u"Réception"), u"Réception")


class TestSampleCodeIndex(TrimetaTestCase):

    def setUp(self):
        super(TestSampleCodeIndex, self).setUp()
        self.factory = SampleFactory(self.portal, self.request)
        self.catalog = capi.get_catalog(SAMPLE_CATALOG)

    def test_sample_is_findable_by_code(self):
        sample = self.factory.create(SampleCode="ECH-0042")
        brains = self.catalog(getSampleCode="ECH-0042")
        self.assertEqual(len(brains), 1)
        self.assertEqual(brains[0].UID, sample.UID())

    def test_metadata_column_is_populated(self):
        """La colonne doit etre lisible depuis le brain, sans reveiller
        l'objet: c'est ce qui rend le listing rapide."""
        self.factory.create(SampleCode="ECH-0043")
        brains = self.catalog(getSampleCode="ECH-0043")
        self.assertEqual(len(brains), 1)
        self.assertEqual(brains[0].getSampleCode, "ECH-0043")

    def test_empty_code_is_indexed_as_empty_string(self):
        """Un code absent ne doit pas faire echouer l'indexation."""
        sample = self.factory.create()
        brains = self.catalog(UID=sample.UID())
        self.assertEqual(len(brains), 1)
        self.assertEqual(brains[0].getSampleCode, "")

    def test_index_follows_edits(self):
        sample = self.factory.create(SampleCode="AVANT")
        sample.getField("SampleCode").set(sample, "APRES")
        sample.reindexObject()

        self.assertEqual(len(self.catalog(getSampleCode="AVANT")), 0)
        brains = self.catalog(getSampleCode="APRES")
        self.assertEqual(len(brains), 1)
        self.assertEqual(brains[0].getSampleCode, "APRES")

    def test_lot_uses_the_native_client_sample_id(self):
        """Decision d'architecture: le "Lot" du cahier des charges est le
        champ natif ClientSampleID, deja indexe par senaite.core. Ce test
        documente ce choix et alerte s'il cesse d'etre vrai."""
        indexes = capi.get_indexes(self.catalog)
        columns = capi.get_columns(self.catalog)
        self.assertIn("getClientSampleID", indexes)
        self.assertIn("getClientSampleID", columns)

        sample = self.factory.create(ClientSampleID="LOT-2026-07")
        brains = self.catalog(getClientSampleID="LOT-2026-07")
        self.assertEqual(len(brains), 1)
        self.assertEqual(brains[0].UID, sample.UID())


def test_suite():
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    suite.addTest(loader.loadTestsFromTestCase(TestIndexStringNormalisation))
    suite.addTest(loader.loadTestsFromTestCase(TestSampleCodeIndex))
    return suite
