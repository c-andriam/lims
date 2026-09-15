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
        self.assertEqual(version, ("1007",))

    def test_toolbar_shows_the_trimeta_logo(self):
        from bika.lims import api
        from plone.formwidget.namedfile.converter import b64decode_file
        setup = api.get_senaite_setup()
        filename, data = b64decode_file(setup.getSiteLogo())
        self.assertEqual(filename, u"logo-trimeta-groupe-blanc.png")
        self.assertTrue(data.startswith(b"\x89PNG"))
        self.assertEqual(setup.getSiteLogoCSS(), "height:32px;")

    def test_reports_use_decimal_comma(self):
        from bika.lims import api
        setup = api.get_setup()
        self.assertEqual(setup.getField("DecimalMark").get(setup), ",")

    def test_week_starts_on_monday(self):
        from plone import api as ploneapi
        self.assertEqual(
            ploneapi.portal.get_registry_record("plone.first_weekday"), 0)

    def test_site_language_is_french(self):
        """registry.xml: francais par defaut, langue du navigateur ignoree."""
        from plone import api as ploneapi
        get = ploneapi.portal.get_registry_record
        self.assertEqual(get("plone.default_language"), "fr")
        self.assertEqual(list(get("plone.available_languages")), ["fr", "en"])
        self.assertFalse(get("plone.use_request_negotiation"))
        self.assertTrue(get("plone.use_cookie_negotiation"))
        self.assertFalse(get("plone.use_combined_language_codes"))

    def test_portal_timezone_is_madagascar(self):
        """Doit concorder avec TZ du conteneur (compose.yml)."""
        from plone import api as ploneapi
        self.assertEqual(
            ploneapi.portal.get_registry_record("plone.portal_timezone"),
            "Indian/Antananarivo")

    def test_currency_and_country_are_madagascar(self):
        from bika.lims import api
        setup = api.get_setup()
        self.assertEqual(setup.getField("Currency").get(setup), "MGA")
        self.assertEqual(setup.getField("DefaultCountry").get(setup), "MG")

    def test_lab_choice_is_kept(self):
        """Un choix explicite du laboratoire n'est pas ecrase."""
        from bika.lims import api
        from senaite.trimeta.samplefields.setuphandlers import set_lab_defaults
        setup = api.get_setup()
        field = setup.getField("Currency")
        field.set(setup, "USD")
        try:
            self.assertEqual(set_lab_defaults(), {})
            self.assertEqual(field.get(setup), "USD")
        finally:
            field.set(setup, "MGA")

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
