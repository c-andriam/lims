# -*- coding: utf-8 -*-
"""En cas d'echec annonce au navigateur, aucune creation ne reste en base."""
import transaction
from senaite.trimeta.samplefields.browser.sample_submit import atomic_submit
from senaite.trimeta.samplefields.tests.base import TrimetaTestCase


class TestAtomicSampleSubmit(TrimetaTestCase):

    def write_then_fail(self):
        self.portal._setProperty("trimeta_submit_probe", "partiel", "string")
        # Le gestionnaire amont cree lui-meme des savepoints entre objets.
        transaction.savepoint(optimistic=True)
        return {"errors": {"message": "deuxieme echantillon invalide"}}

    def test_caught_error_rolls_back_partial_writes(self):
        result = atomic_submit(self.write_then_fail)
        self.assertIn("errors", result)
        self.assertFalse(self.portal.hasProperty("trimeta_submit_probe"))

    def test_exception_rolls_back_partial_writes(self):
        def fail():
            self.write_then_fail()
            raise ValueError("echec")
        with self.assertRaises(ValueError):
            atomic_submit(fail)
        self.assertFalse(self.portal.hasProperty("trimeta_submit_probe"))

    def test_success_keeps_writes(self):
        def success():
            self.portal._setProperty("trimeta_submit_probe", "complet", "string")
            return {"success": True}
        self.assertEqual(atomic_submit(success), {"success": True})
        self.assertEqual(self.portal.getProperty("trimeta_submit_probe"), "complet")
