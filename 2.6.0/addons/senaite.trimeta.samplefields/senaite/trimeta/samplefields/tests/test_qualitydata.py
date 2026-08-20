# -*- coding: utf-8 -*-
"""
Tests de la section Assurance Qualite.

Deux regles metier sont protegees ici, parce que les enfreindre serait
silencieux et grave:

1. TOUS les champs de la section sont facultatifs. Un champ passe
   obligatoire par megarde bloquerait la reception d'echantillons.
2. Aucun champ n'apparait sur le formulaire de creation. Ces donnees
   sont produites apres l'analyse; les afficher a la reception
   allongerait le formulaire de 41 lignes vides.
"""

import unittest

from senaite.trimeta.samplefields.qualitydata import extender as qa
from senaite.trimeta.samplefields.qualitydata.fields import QA_VISIBLE
from senaite.trimeta.samplefields.qualitydata.fields import SCHEMATA
from senaite.trimeta.samplefields.suggestions import SUGGESTION_FIELDS
from senaite.trimeta.samplefields.tests.base import TrimetaTestCase
from senaite.trimeta.samplefields.tests.utils import SampleFactory

# Nombre de champs attendu par sous-section, d'apres le cahier des
# charges. Un ecart signale un champ ajoute ou perdu.
EXPECTED_SECTION_SIZES = {
    "extraction": 3,
    "hplc": 4,
    "desiccator": 3,
    "awmeter": 3,
    "instruments": 16,   # 8 appareils x (date + conformite)
    "consumables": 7,
    "validation": 5,
}

EXPECTED_TOTAL = sum(EXPECTED_SECTION_SIZES.values())

# Lots de consommables: le cahier des charges demande un "rajout
# memorise" sur ces champs.
REMEMBERED_CONSUMABLES = (
    "EthanolLot",
    "AcetonitrileLot",
    "HPLCWaterLot",
    "IsopropanolLot",
)


class TestQualityDataDeclaration(unittest.TestCase):
    """Inspection de la declaration; aucun site Plone necessaire."""

    def test_total_field_count(self):
        self.assertEqual(len(qa.get_all_fields()), EXPECTED_TOTAL)

    def test_section_sizes(self):
        sizes = {sid: len(fields) for sid, _t, fields in qa.SECTIONS}
        self.assertEqual(sizes, EXPECTED_SECTION_SIZES)

    def test_every_field_is_optional(self):
        for field in qa.get_all_fields():
            self.assertFalse(
                field.required,
                "Le champ {} ne doit pas etre obligatoire".format(
                    field.getName()))

    def test_no_field_on_the_add_form(self):
        for field in qa.get_all_fields():
            self.assertEqual(
                field.widget.visible.get("add"), "invisible",
                "Le champ {} ne doit pas apparaitre a la creation".format(
                    field.getName()))

    def test_every_field_is_visible_afterwards(self):
        for field in qa.get_all_fields():
            self.assertEqual(field.widget.visible.get("edit"), "visible")
            self.assertEqual(field.widget.visible.get("view"), "visible")

    def test_all_fields_share_the_schemata(self):
        for field in qa.get_all_fields():
            self.assertEqual(field.schemata, SCHEMATA)

    def test_no_duplicate_names(self):
        names = [f.getName() for f in qa.get_all_fields()]
        self.assertEqual(len(names), len(set(names)))

    def test_no_clash_with_reception_fields(self):
        """Un meme nom dans deux extenders ecraserait silencieusement le
        champ declare en premier."""
        from senaite.trimeta.samplefields.extender import (
            ReceptionFieldsExtender)
        reception = {f.getName() for f in ReceptionFieldsExtender.fields}
        quality = {f.getName() for f in qa.get_all_fields()}
        self.assertEqual(reception & quality, set())

    def test_instrument_checks_come_in_pairs(self):
        names = [f.getName() for f in qa.instrument_check_fields()]
        for prefix, _label in qa.INSTRUMENT_CHECKS:
            self.assertIn("{}CheckDate".format(prefix), names)
            self.assertIn("{}Conformity".format(prefix), names)

    def test_section_map_matches_declaration(self):
        """La carte transmise au JavaScript doit refleter exactement les
        champs declares, sinon un intitule se retrouve devant le mauvais
        groupe."""
        mapped = []
        for _sid, _title, fieldnames in qa.get_section_map():
            mapped.extend(fieldnames)
        declared = [f.getName() for f in qa.get_all_fields()]
        self.assertEqual(mapped, declared)

    def test_get_order_covers_every_field(self):
        extender = qa.QualityDataExtender(None)
        schematas = extender.getOrder({})
        self.assertEqual(
            set(schematas[SCHEMATA]),
            {f.getName() for f in qa.get_all_fields()})

    def test_get_order_leaves_other_schematas_alone(self):
        extender = qa.QualityDataExtender(None)
        schematas = extender.getOrder({"Reception": ["SampleCode"]})
        self.assertEqual(schematas["Reception"], ["SampleCode"])

    def test_qa_fields_are_hidden_on_add(self):
        self.assertEqual(QA_VISIBLE.get("add"), "invisible")

    def test_consumable_lots_are_remembered(self):
        for name in REMEMBERED_CONSUMABLES:
            self.assertIn(name, SUGGESTION_FIELDS)


class TestQualityDataOnSample(TrimetaTestCase):

    def setUp(self):
        super(TestQualityDataOnSample, self).setUp()
        self.factory = SampleFactory(self.portal, self.request)

    def test_fields_exist_on_sample(self):
        sample = self.factory.create()
        for field in qa.get_all_fields():
            self.assertIsNotNone(
                sample.getField(field.getName()),
                "Champ {} absent du schema".format(field.getName()))

    def test_reception_fields_still_exist(self):
        """Deux extenders sur le meme type: verifier que le second n'a
        pas evince le premier."""
        sample = self.factory.create()
        self.assertIsNotNone(sample.getField("SampleCode"))
        self.assertIsNotNone(sample.getField("AnalysisSheetNumber"))
        self.assertIsNotNone(sample.getField("ExtractionDate"))

    def test_values_round_trip(self):
        sample = self.factory.create()
        sample.getField("EthanolLot").set(sample, "ETH-2026-014")
        sample.getField("HPLCBlankCheck").set(sample, "OK")
        sample.getField("ExtractionCount").set(sample, "2")

        self.assertEqual(
            sample.getField("EthanolLot").get(sample), "ETH-2026-014")
        self.assertEqual(
            sample.getField("HPLCBlankCheck").get(sample), "OK")
        self.assertEqual(
            sample.getField("ExtractionCount").get(sample), "2")

    def test_sample_creation_needs_no_quality_data(self):
        """La reception ne doit jamais dependre de donnees produites
        apres l'analyse."""
        sample = self.factory.create(SampleCode="ECH-0200")
        self.assertIsNotNone(sample)
        self.assertFalse(sample.getField("ExtractionDate").get(sample))


class TestNativeFieldRetouches(TrimetaTestCase):
    """Retouches sur les champs natifs (schema_modifier)."""

    def setUp(self):
        super(TestNativeFieldRetouches, self).setUp()
        self.factory = SampleFactory(self.portal, self.request)
        self.sample = self.factory.create()

    def test_client_sample_id_is_labelled_lot(self):
        from zope.i18n import translate
        field = self.sample.getField("ClientSampleID")
        label = translate(field.widget.label, target_language="en")
        self.assertEqual(label, "Lot")

    def test_client_sample_id_stays_usable(self):
        """Le champ porte le Lot: il doit rester visible et saisissable
        partout, y compris a la creation."""
        field = self.sample.getField("ClientSampleID")
        self.assertEqual(field.widget.visible.get("add"), "edit")
        self.assertEqual(field.widget.visible.get("edit"), "visible")

    def test_redundant_field_is_hidden(self):
        from senaite.trimeta.samplefields.schema_modifier import (
            HIDDEN_NATIVE_FIELDS)
        for name in HIDDEN_NATIVE_FIELDS:
            field = self.sample.getField(name)
            if field is None:
                continue
            self.assertEqual(field.widget.visible.get("add"), "invisible")
            self.assertFalse(field.required)

    def test_client_sample_id_is_never_hidden(self):
        from senaite.trimeta.samplefields.schema_modifier import (
            HIDDEN_NATIVE_FIELDS)
        self.assertNotIn("ClientSampleID", HIDDEN_NATIVE_FIELDS)


def test_suite():
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    suite.addTest(loader.loadTestsFromTestCase(TestQualityDataDeclaration))
    suite.addTest(loader.loadTestsFromTestCase(TestQualityDataOnSample))
    suite.addTest(loader.loadTestsFromTestCase(TestNativeFieldRetouches))
    return suite
