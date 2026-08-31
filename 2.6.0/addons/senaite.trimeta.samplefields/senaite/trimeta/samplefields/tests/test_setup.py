# -*- coding: utf-8 -*-
"""
Tests d'installation: le profil GenericSetup s'installe, cree ce qu'il
doit creer, et sa desinstallation nettoie derriere elle.

C'est le filet de securite du lot 0: si ces tests passent, l'add-on est
deployable sans intervention manuelle sur le catalogue.
"""

import unittest

from plone.app.testing import applyProfile
from senaite.core.api import catalog as capi

from senaite.trimeta.samplefields.catalog import CATALOGS
from senaite.trimeta.samplefields.tests.base import TrimetaTestCase

PROFILE = "senaite.trimeta.samplefields:default"
UNINSTALL_PROFILE = "senaite.trimeta.samplefields:uninstall"


class TestProfileInstallation(TrimetaTestCase):

    def test_profile_is_registered(self):
        setup_tool = self.portal.portal_setup
        profiles = [p["id"] for p in setup_tool.listProfileInfo()]
        self.assertIn(PROFILE, profiles)

    def test_profile_version(self):
        """La version installee doit correspondre a metadata.xml.

        Un ecart signifie qu'une etape de mise a jour n'a pas ete jouee.
        """
        setup_tool = self.portal.portal_setup
        version = setup_tool.getLastVersionForProfile(PROFILE)
        self.assertEqual(version, ("1001",))

    def test_indexes_are_created(self):
        for catalog_id, indexes, _columns in CATALOGS:
            catalog = capi.get_catalog(catalog_id)
            existing = capi.get_indexes(catalog)
            for index_id, _index_type, _attrs in indexes:
                self.assertIn(
                    index_id, existing,
                    "Index {} absent de {}".format(index_id, catalog_id))

    def test_columns_are_created(self):
        for catalog_id, _indexes, columns in CATALOGS:
            catalog = capi.get_catalog(catalog_id)
            existing = capi.get_columns(catalog)
            for column in columns:
                self.assertIn(
                    column, existing,
                    "Colonne {} absente de {}".format(column, catalog_id))

    def test_index_type_is_correct(self):
        """Un FieldIndex declare ne doit pas se retrouver en KeywordIndex:
        le tri et les requetes d'egalite ne se comporteraient pas pareil.
        """
        for catalog_id, indexes, _columns in CATALOGS:
            catalog = capi.get_catalog(catalog_id)
            for index_id, index_type, _attrs in indexes:
                index = capi.get_index(catalog, index_id)
                self.assertEqual(index.meta_type, index_type)

    def test_install_is_idempotent(self):
        """Reinstaller le profil ne doit ni dupliquer ni supprimer."""
        catalog_id, indexes, columns = CATALOGS[0]
        catalog = capi.get_catalog(catalog_id)
        before_indexes = sorted(capi.get_indexes(catalog))
        before_columns = sorted(capi.get_columns(catalog))

        applyProfile(self.portal, PROFILE)

        self.assertEqual(sorted(capi.get_indexes(catalog)), before_indexes)
        self.assertEqual(sorted(capi.get_columns(catalog)), before_columns)


class TestProfileUninstallation(TrimetaTestCase):

    def tearDown(self):
        # Les tests suivants doivent retrouver un site installe.
        applyProfile(self.portal, PROFILE)
        super(TestProfileUninstallation, self).tearDown()

    def test_uninstall_removes_indexes_and_columns(self):
        applyProfile(self.portal, UNINSTALL_PROFILE)
        for catalog_id, indexes, columns in CATALOGS:
            catalog = capi.get_catalog(catalog_id)
            for index_id, _index_type, _attrs in indexes:
                self.assertNotIn(index_id, capi.get_indexes(catalog))
            for column in columns:
                self.assertNotIn(column, capi.get_columns(catalog))


def test_suite():
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    suite.addTest(loader.loadTestsFromTestCase(TestProfileInstallation))
    suite.addTest(loader.loadTestsFromTestCase(TestProfileUninstallation))
    return suite
