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
        self.assertEqual(field.widget.visible.get("add"), "edit")


def test_suite():
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    suite.addTest(loader.loadTestsFromTestCase(TestExtenderDeclaration))
    suite.addTest(loader.loadTestsFromTestCase(TestSchemaOnSample))
    return suite
