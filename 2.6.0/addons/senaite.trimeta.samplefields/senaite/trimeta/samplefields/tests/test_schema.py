# -*- coding: utf-8 -*-
"""
Tests du schema etendu du type Sample.

Ces tests protegent la reception: si un champ disparait ou change de
caractere obligatoire par accident, le formulaire de saisie change de
comportement sans prevenir. Ils sont volontairement declaratifs, pour
rester lisibles par quelqu'un qui ne connait pas Archetypes.
"""

import unittest

from senaite.trimeta.samplefields.extender import ReceptionFieldsExtender
from senaite.trimeta.samplefields.schema_modifier import DateReceivedSchemaModifier
from senaite.trimeta.samplefields.tests.base import TrimetaTestCase
from senaite.trimeta.samplefields.tests.utils import SampleFactory

# Les 15 champs de la section Reception, avec leur caractere obligatoire
# tel que specifie dans le document AMELIORATIONS SENAITE LIMS.
RECEPTION_FIELDS = (
    ("SampleCode", True),
    ("CodeArticle", True),
    ("Designation", True),
    ("ReceptionWeight", True),
    ("QuantityReceived", True),
    ("QuantityUnderAnalysis", True),
    ("TechSampleWeight", True),
    ("ReceptionTemperature", True),
    ("SampleCondition", True),
    ("PackagingCondition", True),
    ("Origin", True),
    ("SupplierCustomerDetail", True),
    ("Receptionist", True),
    ("Contract", True),
    ("EntryVoucher", True),
)

# Section Analyse: seul le numero de fiche est obligatoire.
ANALYSE_FIELDS = (
    ("AnalysisSheetNumber", True),
    ("AnalysisStart", False),
    ("AnalysisEnd", False),
    ("AnalysisPreparer", False),
    ("PodLength", False),
    ("AromaDevelopment", False),
    ("Aroma", False),
    ("Color", False),
    ("Texture", False),
)


class TestExtenderDeclaration(unittest.TestCase):
    """Verifications sur la declaration de l'extender.

    Ne necessite pas de site Plone: on inspecte la liste de champs.
    """

    def get_fields(self):
        return {f.getName(): f for f in ReceptionFieldsExtender.fields}

    def test_all_reception_fields_declared(self):
        fields = self.get_fields()
        for name, _required in RECEPTION_FIELDS:
            self.assertIn(name, fields, "Champ {} manquant".format(name))

    def test_all_analyse_fields_declared(self):
        fields = self.get_fields()
        for name, _required in ANALYSE_FIELDS:
            self.assertIn(name, fields, "Champ {} manquant".format(name))

    def test_required_flags(self):
        fields = self.get_fields()
        for name, required in RECEPTION_FIELDS + ANALYSE_FIELDS:
            self.assertEqual(
                bool(fields[name].required), required,
                "Le champ {} devrait etre {}".format(
                    name, "obligatoire" if required else "facultatif"))

    def test_schematas(self):
        """Chaque champ doit atterrir dans le bon onglet."""
        fields = self.get_fields()
        for name, _required in RECEPTION_FIELDS:
            self.assertEqual(fields[name].schemata, "Reception")
        for name, _required in ANALYSE_FIELDS:
            self.assertEqual(fields[name].schemata, "Analyse")

    def test_fields_are_visible_on_add_form(self):
        """Sans visibilite explicite, les widgets Archetypes retombent
        sur 'invisible' en mode 'add' et les champs disparaissent du
        formulaire de creation."""
        fields = self.get_fields()
        for name, _required in RECEPTION_FIELDS + ANALYSE_FIELDS:
            visible = fields[name].widget.visible
            self.assertIsInstance(
                visible, dict,
                "Le champ {} n'a pas de visibilite explicite".format(name))
            self.assertEqual(visible.get("add"), "edit")

    def test_no_duplicate_field_names(self):
        names = [f.getName() for f in ReceptionFieldsExtender.fields]
        self.assertEqual(len(names), len(set(names)),
                         "Doublon dans les noms de champs")

    def test_get_order_covers_every_field(self):
        """getOrder ne doit oublier aucun champ, sinon il sort de son
        onglet et se retrouve en bas du formulaire."""
        extender = ReceptionFieldsExtender(None)
        schematas = extender.getOrder({})
        ordered = set(schematas["Reception"]) | set(schematas["Analyse"])
        declared = {f.getName() for f in ReceptionFieldsExtender.fields}
        self.assertEqual(ordered, declared)


class TestNativeRequiredFields(unittest.TestCase):

    def test_received_date_is_required_and_visible(self):
        field = type("Field", (object,), {})()
        field.widget = type("Widget", (object,), {})()
        field.required = False
        field.mode = "r"
        DateReceivedSchemaModifier(None).fiddle({"DateReceived": field})
        self.assertTrue(field.required)
        self.assertEqual(field.mode, "rw")
        self.assertEqual(field.widget.visible["add"], "edit")


class TestSchemaOnSample(TrimetaTestCase):
    """Verifications sur un echantillon reellement cree."""

    def setUp(self):
        super(TestSchemaOnSample, self).setUp()
        self.factory = SampleFactory(self.portal, self.request)

    def test_fields_are_present_on_sample(self):
        sample = self.factory.create()
        for name, _required in RECEPTION_FIELDS + ANALYSE_FIELDS:
            self.assertIsNotNone(
                sample.getField(name),
                "Champ {} absent du schema de l'echantillon".format(name))

    def test_required_flags_on_real_schema(self):
        sample = self.factory.create()
        for name, required in RECEPTION_FIELDS + ANALYSE_FIELDS:
            self.assertEqual(bool(sample.getField(name).required), required,
                             "Obligation incorrecte: {}".format(name))
        self.assertTrue(sample.getField("DateReceived").required)

    def test_values_are_stored_and_read_back(self):
        sample = self.factory.create(
            SampleCode="ECH-0001",
            Designation="Gousses de vanille noire",
            Origin="Sambava",
        )
        self.assertEqual(
            sample.getField("SampleCode").get(sample), "ECH-0001")
        self.assertEqual(
            sample.getField("Designation").get(sample),
            "Gousses de vanille noire")
        self.assertEqual(
            sample.getField("Origin").get(sample), "Sambava")

    def test_date_received_is_writable(self):
        """Le modificateur de schema doit rendre DateReceived saisissable
        manuellement, sinon la correction d'une reception enregistree en
        retard est impossible."""
        sample = self.factory.create()
        field = sample.getField("DateReceived")
        self.assertEqual(field.mode, "rw")
        self.assertTrue(field.required)
        self.assertEqual(field.widget.visible.get("add"), "edit")
        self.assertEqual(field.widget.visible.get("edit"), "visible")

    def test_empty_received_date_is_rejected(self):
        sample = self.factory.create()
        field = sample.getField("DateReceived")
        errors = {}
        self.assertTrue(field.validate(None, sample, errors=errors,
                                       REQUEST=self.request))
        self.assertIn("DateReceived", errors)

    def test_received_date_is_saved_without_changing_sampled_date(self):
        from DateTime import DateTime
        sampled = DateTime("2026/09/30 10:00:00 GMT+3")
        received = DateTime("2026/10/01 11:30:00 GMT+3")
        sample = self.factory.create(DateSampled=sampled,
                                     DateReceived=received)
        self.assertEqual(sample.getDateReceived(), received)
        self.assertEqual(sample.getDateSampled(), sampled)

    def test_create_form_rejects_missing_received_date(self):
        from senaite.trimeta.samplefields.browser.sample_submit import (
            TrimetaSampleSubmitView)
        sample = self.factory.create()
        view = TrimetaSampleSubmitView(self.factory.client, self.request)
        before = self.factory.client.objectIds()
        view.check_confirmation = lambda: None
        view.get_ar = lambda: sample
        view.get_records = lambda: [{"SampleCode": "DATE-OBLIGATOIRE"}]
        view.create_samples = lambda records: self.fail(
            "La creation ne doit pas etre appelee sans date de reception")
        result = view.ajax_submit()
        self.assertIn("DateReceived-0", result["errors"]["fielderrors"])
        self.assertEqual(self.factory.client.objectIds(), before)

    def test_received_date_rejects_future_and_before_sampling(self):
        from DateTime import DateTime
        sampled = DateTime() - 2
        sample = self.factory.create(DateSampled=sampled)
        field = sample.getField("DateReceived")
        self.assertTrue(field.validate(sampled - 1, sample,
                                       REQUEST=self.request))
        self.assertTrue(field.validate(DateTime() + 1, sample,
                                       REQUEST=self.request))
        self.assertFalse(field.validate(sampled + 1, sample,
                                        REQUEST=self.request))
        self.assertTrue(field.checkPermission("w", sample))

    def test_parent_client_is_not_validated_as_missing_edit_input(self):
        sample = self.factory.create()
        field = sample.getField("Client")
        self.assertTrue(field.required)
        self.assertEqual(field.widget.visible.get("add"), "edit")
        self.assertEqual(field.widget.visible.get("edit"), "invisible")
        self.assertIsNotNone(sample.getClient())


def test_suite():
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    suite.addTest(loader.loadTestsFromTestCase(TestExtenderDeclaration))
    suite.addTest(loader.loadTestsFromTestCase(TestNativeRequiredFields))
    suite.addTest(loader.loadTestsFromTestCase(TestSchemaOnSample))
    return suite
