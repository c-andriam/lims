# -*- coding: utf-8 -*-
"""Contrat de la vue unifiee, avec une ZODB en memoire isolee du site."""
import unittest

from ZODB import DB
from ZODB.MappingStorage import MappingStorage
from transaction import TransactionManager

from bika.lims.browser.analysisrequest.add2 import ajaxAnalysisRequestAddView
from senaite.trimeta.samplefields.browser import sample_add
from senaite.trimeta.samplefields.browser import sample_submit


class Context(object):
    def translate(self, message):
        return message


class Request(dict):
    pass


class TestSampleSubmitView(unittest.TestCase):
    """Les erreurs tardives ne doivent jamais conserver un lot partiel."""

    def setUp(self):
        # Une transaction distincte evite de toucher la base des autres tests.
        self.manager = TransactionManager()
        self.database = DB(MappingStorage())
        self.connection = self.database.open(transaction_manager=self.manager)
        self.root = self.connection.root()
        self.manager.commit()
        self.addCleanup(self.database.close)
        self.addCleanup(self.connection.close)
        self.addCleanup(self.manager.abort)
        self.patch(sample_add, "transaction", self.manager)
        self.patch(sample_submit, "transaction", self.manager)
        self.view = sample_submit.TrimetaSampleSubmitView(Context(), Request())

    def patch(self, obj, name, value):
        previous = getattr(obj, name)
        self.addCleanup(setattr, obj, name, previous)
        setattr(obj, name, value)

    def write_partial(self):
        self.root["probe"] = "partial"
        self.manager.savepoint(optimistic=True)

    def test_registered_class_rejects_empty_records(self):
        with self.assertRaises(ValueError):
            self.view.create_samples([])

    def test_no_created_object_rolls_back_writes(self):
        def create_nothing(view, records):
            self.write_partial()
            return []
        self.patch(ajaxAnalysisRequestAddView, "create_samples", create_nothing)
        with self.assertRaises(ValueError):
            self.view.create_samples([{}])
        self.assertNotIn("probe", self.root)

    def test_partial_creation_rolls_back_intermediate_savepoints(self):
        def fail_creation(view, records):
            self.write_partial()
            raise ValueError("second sample failed")
        self.patch(ajaxAnalysisRequestAddView, "create_samples", fail_creation)
        with self.assertRaises(ValueError):
            self.view.create_samples([{}, {}])
        self.assertNotIn("probe", self.root)

    def test_caught_submission_error_rolls_back_writes(self):
        result = {"errors": {"message": "late failure"}}
        def submit_error(view):
            self.write_partial()
            return result
        self.patch(ajaxAnalysisRequestAddView, "ajax_submit", submit_error)
        self.assertEqual(self.view.ajax_submit(), result)
        self.assertNotIn("probe", self.root)

    def test_submission_exception_rolls_back_writes(self):
        def fail_submission(view):
            self.write_partial()
            raise RuntimeError("late exception")
        self.patch(ajaxAnalysisRequestAddView, "ajax_submit", fail_submission)
        with self.assertRaises(RuntimeError):
            self.view.ajax_submit()
        self.assertNotIn("probe", self.root)

    def test_success_preserves_created_objects_and_response(self):
        result = {"success": True, "url": "/review"}
        def create_one(view, records):
            self.root["probe"] = "complete"
            self.manager.savepoint(optimistic=True)
            return ["sample"]
        def submit_success(view):
            self.assertEqual(view.create_samples([{}]), ["sample"])
            return result
        self.patch(ajaxAnalysisRequestAddView, "create_samples", create_one)
        self.patch(ajaxAnalysisRequestAddView, "ajax_submit", submit_success)
        self.assertEqual(self.view.ajax_submit(), result)
        self.assertEqual(self.root["probe"], "complete")

    def test_native_confirmation_is_preserved(self):
        result = {"confirmation": "confirm existing sample"}
        self.patch(ajaxAnalysisRequestAddView, "ajax_submit", lambda view: result)
        self.assertEqual(self.view.ajax_submit(), result)
        self.assertNotIn("probe", self.root)


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromTestCase(TestSampleSubmitView)
