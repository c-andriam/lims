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

from senaite.trimeta.samplefields import indexers
from senaite.trimeta.samplefields.indexers import to_contact_title
from senaite.trimeta.samplefields.indexers import to_index_date
from senaite.trimeta.samplefields.indexers import to_index_string
from senaite.trimeta.samplefields.indexers import to_reference_uid
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
        """Sur Python 2, un str() naif sur du texte accentue leverait
        UnicodeEncodeError et rendrait l'echantillon non indexable."""
        self.assertEqual(to_index_string(u"Réception"), u"Réception")

    def test_result_is_always_text(self):
        """Jamais d'octets en retour: le catalogue melangerait alors des
        types et le tri deviendrait incoherent."""
        from senaite.trimeta.samplefields.compat import text_type
        for value in (None, b"ECH-1", u"ECH-2", 42, u"Réception"):
            self.assertIsInstance(to_index_string(value), text_type)

    def test_utf8_bytes_are_decoded(self):
        self.assertEqual(to_index_string(u"Réception".encode("utf-8")),
                         u"Réception")


class TestIndexDateNormalisation(unittest.TestCase):
    """Fonction pure, testable sans site Plone."""

    def test_none_stays_none(self):
        self.assertIsNone(to_index_date(None))

    def test_empty_string_becomes_none(self):
        """Un champ date vide rendu comme chaine vide -- ce que fait
        Archetypes -- ne doit pas atterrir tel quel dans la colonne: le
        listing tenterait de le formater comme une date."""
        self.assertIsNone(to_index_date(""))

    def test_a_date_is_passed_through_untouched(self):
        """On ne convertit pas en texte: le formatage appartient au
        listing, qui seul connait la langue du compte."""
        marker = object()
        self.assertIs(to_index_date(marker), marker)


class FakeContact(object):
    """Doublure d'un LabContact: juste de quoi repondre a get_title."""

    def __init__(self, title, uid=""):
        self.title = title
        self.uid = uid


class FakeAPI(object):
    """Doublure de bika.lims.api, limitee a ce que lit to_contact_title.

    Injectee a la place du vrai module dans les tests ci-dessous: la
    fonction se teste ainsi a l'identique sur le poste et dans le
    container, sans site Plone d'un cote ni contact reel de l'autre.
    """

    def __init__(self, uids=None):
        self.uids = uids or {}

    def get_object_by_uid(self, uid):
        if uid in self.uids:
            return self.uids[uid]
        raise LookupError(uid)

    def get_uid(self, obj):
        if not isinstance(obj, FakeContact):
            raise TypeError(obj)
        return obj.uid

    def get_title(self, obj):
        # Le vrai api.get_title leve sur ce qui n'est pas un contenu.
        # La doublure fait pareil, sinon to_contact_title paraitrait
        # plus robuste qu'il ne l'est.
        if not isinstance(obj, FakeContact):
            raise TypeError(obj)
        return obj.title


class TestContactTitleResolution(unittest.TestCase):
    """Fonction pure: bika.lims.api est remplace le temps du test."""

    def setUp(self):
        self.marie = FakeContact(u"Marie Rakoto", "uid-marie")
        self.jean = FakeContact(u"Jean Dupont", "uid-jean")
        self._real_api = indexers.api
        indexers.api = FakeAPI({
            "uid-marie": self.marie,
            "uid-jean": self.jean,
        })

    def tearDown(self):
        indexers.api = self._real_api

    def test_empty_value_gives_empty_string(self):
        for value in (None, u"", [], ()):
            self.assertEqual(to_contact_title(value), u"")

    def test_uid_is_resolved_to_the_contact_title(self):
        self.assertEqual(to_contact_title("uid-marie"), u"Marie Rakoto")

    def test_object_is_accepted_directly(self):
        """UIDReferenceField rend tantot l'UID, tantot l'objet, selon la
        version de SENAITE. Les deux doivent marcher."""
        self.assertEqual(to_contact_title(self.marie), u"Marie Rakoto")

    def test_unresolvable_uid_gives_empty_string(self):
        """Contact supprime, UID obsolete: la colonne reste vide plutot
        que d'afficher un UID brut, et surtout l'indexation de tout
        l'echantillon ne doit pas echouer pour autant."""
        self.assertEqual(to_contact_title("uid-inconnu"), u"")

    def test_a_list_is_joined(self):
        """Le cas d'un champ multiValued, comme AnalysisPreparer."""
        self.assertEqual(
            to_contact_title(["uid-marie", "uid-jean"]),
            u"Marie Rakoto, Jean Dupont")

    def test_unresolvable_entries_are_dropped_from_a_list(self):
        self.assertEqual(
            to_contact_title(["uid-marie", "uid-inconnu"]),
            u"Marie Rakoto")

    def test_result_is_always_text(self):
        from senaite.trimeta.samplefields.compat import text_type
        for value in (None, "uid-marie", "uid-inconnu", ["uid-jean"]):
            self.assertIsInstance(to_contact_title(value), text_type)


class TestReferenceUid(unittest.TestCase):
    """Fonction pure: bika.lims.api est remplace le temps du test."""

    def setUp(self):
        self.vanille = FakeContact(u"Vanille verte", "uid-type")
        self._real_api = indexers.api
        indexers.api = FakeAPI({"uid-type": self.vanille})

    def tearDown(self):
        indexers.api = self._real_api

    def test_empty_value_gives_empty_string(self):
        for value in (None, u"", [], ()):
            self.assertEqual(to_reference_uid(value), u"")

    def test_an_object_is_resolved_to_its_uid(self):
        self.assertEqual(to_reference_uid(self.vanille), u"uid-type")

    def test_a_uid_is_returned_as_is(self):
        """L'accesseur rend parfois deja l'UID: rien a resoudre."""
        self.assertEqual(to_reference_uid("uid-type"), u"uid-type")

    def test_a_list_keeps_the_first_entry(self):
        self.assertEqual(to_reference_uid([self.vanille]), u"uid-type")

    def test_an_unreadable_value_gives_empty_string(self):
        """Ne jamais lever: l'indexation de tout l'echantillon en
        dependrait, pour un seul champ."""
        self.assertEqual(to_reference_uid(object()), u"")

    def test_result_is_always_text(self):
        from senaite.trimeta.samplefields.compat import text_type
        for value in (None, "uid-type", self.vanille, object()):
            self.assertIsInstance(to_reference_uid(value), text_type)


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


class TestDashboardColumns(TrimetaTestCase):
    """Colonnes alimentant le tableau de bord (lot 5).

    Ce qui est verifie ici n'est pas l'affichage mais la seule chose qui
    puisse casser en silence: qu'un champ schemaextender arrive bien
    jusqu'a la colonne de metadonnees. Une colonne qui reste vide ne
    leve aucune erreur -- elle produit juste un tableau de bord inutile.
    """

    def setUp(self):
        super(TestDashboardColumns, self).setUp()
        self.factory = SampleFactory(self.portal, self.request)
        self.catalog = capi.get_catalog(SAMPLE_CATALOG)

    def get_brain(self, sample):
        brains = self.catalog(UID=sample.UID())
        self.assertEqual(len(brains), 1)
        return brains[0]

    def set_and_reindex(self, sample, **values):
        """Renseigne des champs apres coup, comme le fait le laboratoire.

        Les champs Assurance Qualite sont invisibles a la creation: ils
        ne peuvent pas etre passes a create_analysisrequest.
        """
        for name, value in values.items():
            field = sample.getField(name)
            self.assertIsNotNone(
                field, "Champ {} absent du schema".format(name))
            field.set(sample, value)
        sample.reindexObject()

    def test_declared_columns_exist_after_install(self):
        """Le profil doit avoir cree les huit colonnes."""
        from senaite.trimeta.samplefields.catalog import SAMPLE_COLUMNS
        columns = capi.get_columns(self.catalog)
        for column in SAMPLE_COLUMNS:
            self.assertIn(column, columns)

    def test_origin_is_indexed_and_searchable(self):
        """La Provenance est le seul champ du tableau de bord a etre un
        index: c'est lui qui porte le filtre."""
        self.assertIn("getOrigin", capi.get_indexes(self.catalog))

        sample = self.factory.create()
        self.set_and_reindex(sample, Origin=u"Sava")

        brains = self.catalog(getOrigin=u"Sava")
        self.assertEqual(len(brains), 1)
        self.assertEqual(brains[0].UID, sample.UID())
        self.assertEqual(brains[0].getOrigin, u"Sava")

    def test_sample_type_is_indexed_by_uid(self):
        """Filtre "Type d'echantillon" du tableau de bord.

        L'UID plutot que l'intitule: renommer un type d'echantillon ne
        doit pas casser un filtre enregistre."""
        from bika.lims import api
        self.assertIn("getTrimetaSampleTypeUID",
                      capi.get_indexes(self.catalog))

        sample = self.factory.create()
        uid = api.get_uid(self.factory.sampletype)

        brains = self.catalog(getTrimetaSampleTypeUID=uid)
        self.assertIn(sample.UID(), [b.UID for b in brains])

    def test_reception_weight_keeps_its_decimals(self):
        """Une pesee arrondie serait une perte de donnee analytique."""
        sample = self.factory.create()
        self.set_and_reindex(sample, ReceptionWeight="12.50")
        self.assertEqual(self.get_brain(sample).getReceptionWeight, "12.50")

    def test_analysis_dates_are_stored_as_dates(self):
        """La colonne garde un objet date, pas du texte: c'est le
        listing qui formate selon la langue du compte."""
        from DateTime import DateTime
        start = DateTime("2026/07/01 08:00:00")
        end = DateTime("2026/07/03 17:30:00")

        sample = self.factory.create()
        self.set_and_reindex(sample, AnalysisStart=start, AnalysisEnd=end)

        brain = self.get_brain(sample)
        self.assertEqual(DateTime(brain.getAnalysisStart), start)
        self.assertEqual(DateTime(brain.getAnalysisEnd), end)

    def test_empty_analysis_dates_are_none(self):
        """Un champ non renseigne ne doit pas se confondre avec une date
        au 1er janvier 1970 dans le tableau."""
        sample = self.factory.create()
        brain = self.get_brain(sample)
        self.assertFalse(brain.getAnalysisStart)
        self.assertFalse(brain.getAnalysisEnd)

    def test_operator_column_holds_the_contact_name(self):
        """La reference stockee est un UID; la colonne doit porter le nom
        lisible, sinon le tableau de bord affiche des identifiants."""
        from bika.lims import api
        from senaite.trimeta.samplefields.tests.utils import create_labcontact

        contact = create_labcontact(self.portal, "Marie", "Rakoto")
        sample = self.factory.create()
        self.set_and_reindex(sample, HPLCOperator=api.get_uid(contact))

        title = self.get_brain(sample).getHPLCOperator
        self.assertIn(u"Rakoto", title)

    def test_missing_operator_gives_empty_string(self):
        sample = self.factory.create()
        brain = self.get_brain(sample)
        self.assertEqual(brain.getMoistureOperator, u"")
        self.assertEqual(brain.getWaterActivityOperator, u"")


def test_suite():
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    suite.addTest(loader.loadTestsFromTestCase(TestIndexStringNormalisation))
    suite.addTest(loader.loadTestsFromTestCase(TestIndexDateNormalisation))
    suite.addTest(loader.loadTestsFromTestCase(TestContactTitleResolution))
    suite.addTest(loader.loadTestsFromTestCase(TestReferenceUid))
    suite.addTest(loader.loadTestsFromTestCase(TestSampleCodeIndex))
    suite.addTest(loader.loadTestsFromTestCase(TestDashboardColumns))
    return suite
