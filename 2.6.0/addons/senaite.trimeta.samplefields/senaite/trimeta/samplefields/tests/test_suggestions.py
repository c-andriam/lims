# -*- coding: utf-8 -*-
"""
Tests du magasin de suggestions partagees.

Regle metier a proteger: les identifiants uniques (code echantillon,
numero de fiche, bon d'entree) ne doivent JAMAIS etre proposes en
suggestion. Les reproposer inviterait a reutiliser par megarde un
identifiant deja attribue.
"""

import unittest

from senaite.trimeta.samplefields import suggestions
from senaite.trimeta.samplefields.tests.base import TrimetaTestCase
from senaite.trimeta.samplefields.tests.utils import SampleFactory

# Champs qui ne doivent jamais alimenter les suggestions.
UNIQUE_FIELDS = ("SampleCode", "AnalysisSheetNumber", "EntryVoucher")


class TestSuggestionStorage(TrimetaTestCase):

    def test_add_then_list(self):
        suggestions.add_suggestion("Origin", "Sambava")
        self.assertIn("Sambava", suggestions.list_suggestions("Origin"))

    def test_listing_is_sorted_case_insensitively(self):
        for value in ("antalaha", "Sambava", "Bemanevika"):
            suggestions.add_suggestion("Origin", value)
        listed = suggestions.list_suggestions("Origin")
        self.assertEqual(listed, sorted(listed, key=lambda s: s.lower()))

    def test_duplicates_are_collapsed(self):
        suggestions.add_suggestion("Origin", "Antalaha")
        suggestions.add_suggestion("Origin", "Antalaha")
        listed = suggestions.list_suggestions("Origin")
        self.assertEqual(listed.count("Antalaha"), 1)

    def test_whitespace_is_trimmed(self):
        suggestions.add_suggestion("Origin", "  Vohemar  ")
        self.assertIn("Vohemar", suggestions.list_suggestions("Origin"))

    def test_empty_value_is_ignored(self):
        before = list(suggestions.list_suggestions("Origin"))
        suggestions.add_suggestion("Origin", "   ")
        suggestions.add_suggestion("Origin", "")
        suggestions.add_suggestion("Origin", None)
        self.assertEqual(suggestions.list_suggestions("Origin"), before)

    def test_remove(self):
        suggestions.add_suggestion("Color", "Brun fonce")
        suggestions.remove_suggestion("Color", "Brun fonce")
        self.assertNotIn("Brun fonce",
                         suggestions.list_suggestions("Color"))

    def test_removing_an_absent_value_is_harmless(self):
        suggestions.remove_suggestion("Color", "jamais ajoute")

    def test_unique_fields_are_never_stored(self):
        for fieldname in UNIQUE_FIELDS:
            self.assertNotIn(fieldname, suggestions.SUGGESTION_FIELDS)
            suggestions.add_suggestion(fieldname, "ECH-0001")
            self.assertEqual(suggestions.list_suggestions(fieldname), [])

    def test_storage_is_shared_across_calls(self):
        """Le magasin vit sur la racine du site: deux appels successifs
        doivent voir la meme donnee, quel que soit l'utilisateur."""
        suggestions.add_suggestion("Aroma", "Boise")
        first = suggestions.get_storage()
        second = suggestions.get_storage()
        self.assertIs(first, second)


class TestSuggestionsOnSampleCreation(TrimetaTestCase):

    def setUp(self):
        super(TestSuggestionsOnSampleCreation, self).setUp()
        self.factory = SampleFactory(self.portal, self.request)

    def test_created_sample_feeds_the_suggestions(self):
        self.factory.create(
            SampleCode="ECH-0100",
            Designation="Gousses fendues",
            Origin="Andapa",
            Color="Brun rouge",
        )
        self.assertIn("Gousses fendues",
                      suggestions.list_suggestions("Designation"))
        self.assertIn("Andapa", suggestions.list_suggestions("Origin"))
        self.assertIn("Brun rouge", suggestions.list_suggestions("Color"))

    def test_sample_code_is_not_remembered(self):
        self.factory.create(SampleCode="ECH-0101")
        self.assertEqual(suggestions.list_suggestions("SampleCode"), [])

    def test_creation_survives_a_broken_suggestion_store(self):
        """L'enregistrement des suggestions ne doit jamais empecher la
        creation d'un echantillon: c'est un confort de saisie, pas une
        donnee metier."""
        original = suggestions.add_suggestion

        def boom(*args, **kwargs):
            raise RuntimeError("magasin indisponible")

        suggestions.add_suggestion = boom
        try:
            sample = self.factory.create(SampleCode="ECH-0102",
                                         Origin="Maroantsetra")
            self.assertIsNotNone(sample)
        finally:
            suggestions.add_suggestion = original


def test_suite():
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    suite.addTest(loader.loadTestsFromTestCase(TestSuggestionStorage))
    suite.addTest(
        loader.loadTestsFromTestCase(TestSuggestionsOnSampleCreation))
    return suite
