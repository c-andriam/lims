# -*- coding: utf-8 -*-
"""
Tests des adaptateurs de listing.

L'essentiel est testable sans site Plone: la discrimination (est-ce que
cet adaptateur s'applique a ce listing ?) et l'insertion ordonnee des
colonnes sont de la logique pure, sur des objets factices.

C'est volontaire. Ces adaptateurs s'executent sur TOUS les listings de
l'application: une discrimination trop large ajouterait une colonne
vide sur des ecrans qui n'ont rien a voir, et une erreur non rattrapee
empecherait le listing de s'afficher.
"""

import logging
import unittest
from collections import OrderedDict
from contextlib import contextmanager

from senaite.trimeta.samplefields.listings.base import BaseListingAdapter
from senaite.trimeta.samplefields.listings.base import insert_column_after
from senaite.trimeta.samplefields.listings.base import show_in_all_states
from senaite.trimeta.samplefields.listings.reports import (
    ReportsListingAdapter)
from senaite.trimeta.samplefields.listings.samples import (
    SamplesListingAdapter)
from senaite.trimeta.samplefields.listings.worksheets import (
    WorksheetAnalysesAdapter)


class FakeListing(object):
    """Vue de listing minimale, suffisante pour before_render."""

    def __init__(self, portal_type=None, columns=None, review_states=None):
        self.contentFilter = {}
        if portal_type is not None:
            self.contentFilter["portal_type"] = portal_type
        self.columns = OrderedDict(columns or [])
        self.review_states = review_states or []


@contextmanager
def capture_logs(name, level=logging.ERROR):
    """Capture les enregistrements d'un logger, sur Python 2 comme 3.

    unittest.assertLogs n'existe qu'a partir de Python 3.4, et le
    container SENAITE deploye tourne en Python 2.7.

    Capturer sert deux buts: verifier que l'incident est bien trace, et
    eviter que la pile d'appels ne s'affiche au milieu d'une execution
    de tests reussie.
    """
    logger = logging.getLogger(name)
    records = []

    class _Collector(logging.Handler):
        def emit(self, record):
            records.append(record)

    handler = _Collector()
    previous_level = logger.level
    previous_propagate = logger.propagate
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
    try:
        yield records
    finally:
        logger.removeHandler(handler)
        logger.setLevel(previous_level)
        logger.propagate = previous_propagate


class FakeBrain(object):
    """Brain de catalogue minimal."""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class TestInsertColumnAfter(unittest.TestCase):

    def make_columns(self):
        return OrderedDict([
            ("getId", {}),
            ("Client", {}),
            ("State", {}),
        ])

    def test_inserts_at_the_right_place(self):
        columns = self.make_columns()
        insert_column_after(columns, "getId", "SampleCode", {"title": "x"})
        self.assertEqual(list(columns.keys()),
                         ["getId", "SampleCode", "Client", "State"])

    def test_preserves_the_other_definitions(self):
        columns = self.make_columns()
        columns["Client"] = {"title": "Client"}
        insert_column_after(columns, "getId", "SampleCode", {"title": "x"})
        self.assertEqual(columns["Client"], {"title": "Client"})

    def test_appends_when_anchor_is_missing(self):
        """Une colonne d'ancrage absente ne doit pas faire perdre la
        nouvelle colonne."""
        columns = self.make_columns()
        insert_column_after(columns, "Inexistant", "SampleCode", {})
        self.assertIn("SampleCode", columns)
        self.assertEqual(list(columns.keys())[-1], "SampleCode")

    def test_is_idempotent(self):
        columns = self.make_columns()
        insert_column_after(columns, "getId", "SampleCode", {"title": "a"})
        insert_column_after(columns, "getId", "SampleCode", {"title": "b"})
        self.assertEqual(list(columns.keys()).count("SampleCode"), 1)
        self.assertEqual(columns["SampleCode"]["title"], "a")


class TestShowInAllStates(unittest.TestCase):

    def test_column_added_to_every_filter(self):
        listing = FakeListing(review_states=[
            {"id": "default", "columns": ["getId"]},
            {"id": "received", "columns": ["getId", "State"]},
        ])
        show_in_all_states(listing, "SampleCode")
        for state in listing.review_states:
            self.assertIn("SampleCode", state["columns"])

    def test_no_duplicate(self):
        listing = FakeListing(review_states=[
            {"id": "default", "columns": ["getId", "SampleCode"]},
        ])
        show_in_all_states(listing, "SampleCode")
        self.assertEqual(
            listing.review_states[0]["columns"].count("SampleCode"), 1)

    def test_filters_without_columns_are_left_alone(self):
        """Un filtre sans cle "columns" herite des colonnes par defaut:
        lui en imposer une liste le figerait."""
        listing = FakeListing(review_states=[{"id": "all"}])
        show_in_all_states(listing, "SampleCode")
        self.assertNotIn("columns", listing.review_states[0])


class TestDiscrimination(unittest.TestCase):
    """Chaque adaptateur ne doit agir que sur son propre ecran."""

    def applies(self, adapter_class, portal_type):
        listing = FakeListing(portal_type=portal_type)
        return adapter_class(listing, None).applies()

    def test_samples_adapter_scope(self):
        self.assertTrue(
            self.applies(SamplesListingAdapter, "AnalysisRequest"))
        self.assertFalse(self.applies(SamplesListingAdapter, "Analysis"))
        self.assertFalse(self.applies(SamplesListingAdapter, "ARReport"))
        self.assertFalse(self.applies(SamplesListingAdapter, "Client"))

    def test_worksheet_adapter_scope(self):
        self.assertTrue(
            self.applies(WorksheetAnalysesAdapter, "Analysis"))
        self.assertTrue(
            self.applies(WorksheetAnalysesAdapter, "DuplicateAnalysis"))
        self.assertFalse(
            self.applies(WorksheetAnalysesAdapter, "AnalysisRequest"))

    def test_reports_adapter_scope(self):
        self.assertTrue(self.applies(ReportsListingAdapter, "ARReport"))
        self.assertFalse(
            self.applies(ReportsListingAdapter, "AnalysisRequest"))

    def test_listing_without_portal_type_is_skipped(self):
        """Certains listings ne filtrent pas par type: ne rien supposer
        plutot que d'ajouter une colonne au hasard."""
        listing = FakeListing()
        self.assertFalse(SamplesListingAdapter(listing, None).applies())

    def test_portal_type_as_a_list(self):
        listing = FakeListing(portal_type=["AnalysisRequest", "Batch"])
        self.assertTrue(SamplesListingAdapter(listing, None).applies())


class TestSamplesColumns(unittest.TestCase):

    def make_listing(self):
        return FakeListing(
            portal_type="AnalysisRequest",
            columns=[("getId", {}), ("Client", {})],
            review_states=[{"id": "default", "columns": ["getId"]}],
        )

    def test_columns_are_added_in_order(self):
        listing = self.make_listing()
        SamplesListingAdapter(listing, None).before_render()
        self.assertEqual(list(listing.columns.keys()),
                         ["getId", "SampleCode", "Lot", "Client"])

    def test_columns_are_sortable_on_a_real_index(self):
        """Une colonne declaree triable sans index derriere produit un
        tri qui ne trie rien."""
        listing = self.make_listing()
        SamplesListingAdapter(listing, None).before_render()
        self.assertEqual(listing.columns["SampleCode"]["index"],
                         "getSampleCode")
        self.assertEqual(listing.columns["Lot"]["index"],
                         "getClientSampleID")

    def test_columns_visible_in_every_filter(self):
        listing = self.make_listing()
        SamplesListingAdapter(listing, None).before_render()
        columns = listing.review_states[0]["columns"]
        self.assertIn("SampleCode", columns)
        self.assertIn("Lot", columns)

    def test_values_come_from_catalog_metadata(self):
        """Pas de reveil d'objet: les deux valeurs sont lues sur le
        brain, sinon la liste devient lente."""
        listing = self.make_listing()
        adapter = SamplesListingAdapter(listing, None)
        adapter.before_render()
        brain = FakeBrain(getSampleCode="ECH-0007",
                          getClientSampleID="LOT-42")
        item = adapter.folder_item(brain, {}, 0)
        self.assertEqual(item["SampleCode"], "ECH-0007")
        self.assertEqual(item["Lot"], "LOT-42")

    def test_missing_metadata_gives_empty_cells(self):
        listing = self.make_listing()
        adapter = SamplesListingAdapter(listing, None)
        adapter.before_render()
        item = adapter.folder_item(FakeBrain(), {}, 0)
        self.assertEqual(item["SampleCode"], "")
        self.assertEqual(item["Lot"], "")

    def test_none_metadata_gives_empty_cells(self):
        listing = self.make_listing()
        adapter = SamplesListingAdapter(listing, None)
        adapter.before_render()
        brain = FakeBrain(getSampleCode=None, getClientSampleID=None)
        item = adapter.folder_item(brain, {}, 0)
        self.assertEqual(item["SampleCode"], "")
        self.assertEqual(item["Lot"], "")


class TestWorksheetColumn(unittest.TestCase):

    def test_column_is_added_but_id_is_kept(self):
        """Le cahier des charges dit "remplacer ou ajouter": on ajoute,
        pour ne pas perdre le lien de navigation vers l'echantillon."""
        listing = FakeListing(
            portal_type="Analysis",
            columns=[("getId", {}), ("Result", {})],
        )
        WorksheetAnalysesAdapter(listing, None).before_render()
        self.assertIn("getId", listing.columns)
        self.assertEqual(list(listing.columns.keys()),
                         ["getId", "SampleCode", "Result"])

    def test_column_is_not_sortable(self):
        """Aucun index de code echantillon n'existe sur le catalogue des
        analyses: annoncer un tri serait mentir a l'utilisateur."""
        listing = FakeListing(portal_type="Analysis",
                              columns=[("getId", {})])
        WorksheetAnalysesAdapter(listing, None).before_render()
        self.assertFalse(listing.columns["SampleCode"]["sortable"])


class TestFailureIsolation(unittest.TestCase):
    """Un adaptateur cassé ne doit jamais empêcher un listing de
    s'afficher: mieux vaut une colonne vide qu'un écran d'erreur."""

    class BrokenAdapter(BaseListingAdapter):
        portal_types = ("AnalysisRequest",)

        def add_columns(self):
            raise RuntimeError("colonnes cassees")

        def fill_item(self, obj, item, index):
            raise RuntimeError("remplissage casse")

    # Avaler une erreur en silence serait pire que la laisser passer:
    # la colonne disparaitrait sans que personne ne sache pourquoi. On
    # verifie donc les deux moities du contrat -- le listing survit ET
    # l'incident est trace.
    LOGGER = "senaite.trimeta.samplefields"

    def test_before_render_swallows_errors(self):
        listing = FakeListing(portal_type="AnalysisRequest")
        with capture_logs(self.LOGGER) as records:
            self.BrokenAdapter(listing, None).before_render()
        self.assertEqual(len(records), 1)
        self.assertIn("colonnes cassees", str(records[0].exc_info[1]))

    def test_folder_item_returns_the_item_unchanged(self):
        listing = FakeListing(portal_type="AnalysisRequest")
        adapter = self.BrokenAdapter(listing, None)
        with capture_logs(self.LOGGER) as records:
            item = adapter.folder_item(FakeBrain(), {"existing": 1}, 0)
        self.assertEqual(item, {"existing": 1})
        self.assertEqual(len(records), 1)
        self.assertIn("remplissage casse", str(records[0].exc_info[1]))


def test_suite():
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    for case in (TestInsertColumnAfter, TestShowInAllStates,
                 TestDiscrimination, TestSamplesColumns,
                 TestWorksheetColumn, TestFailureIsolation):
        suite.addTest(loader.loadTestsFromTestCase(case))
    return suite
