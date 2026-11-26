# -*- coding: utf-8 -*-
"""
Tests des listes deroulantes fixes.

Ce sont des fonctions pures: aucun site Plone n'est necessaire, elles
s'executent en quelques millisecondes.
"""

import unittest

from senaite.trimeta.samplefields import vocabularies as vocab


class TestTemperatureVocabulary(unittest.TestCase):
    """La temperature de reception doit rester dans 15-31 degC, borne
    metier issue du cahier des charges."""

    def test_range_bounds(self):
        keys = [k for k, _label in vocab.TEMPERATURE_VOCAB]
        self.assertEqual(keys[0], "15")
        self.assertEqual(keys[-1], "31")

    def test_no_gap_in_the_range(self):
        keys = [int(k) for k, _label in vocab.TEMPERATURE_VOCAB]
        self.assertEqual(keys, list(range(15, 32)))

    def test_labels_carry_the_unit(self):
        for _key, label in vocab.TEMPERATURE_VOCAB:
            self.assertTrue(label.endswith(u"\u00b0C"), label)


class TestCodeArticleVocabulary(unittest.TestCase):

    def test_expected_codes_are_present(self):
        keys = [k for k, _label in vocab.CODE_ARTICLE_VOCAB]
        for code in ("V-GNN", "V-GTK", "V-RAF", "V-RBF", "V-RCF",
                     "V-LLB", "AUTRES"):
            self.assertIn(code, keys)

    def test_no_duplicates(self):
        keys = [k for k, _label in vocab.CODE_ARTICLE_VOCAB]
        self.assertEqual(len(keys), len(set(keys)))

    def test_autres_is_last(self):
        """"AUTRES" doit rester en fin de liste: c'est l'option de repli,
        pas un code produit parmi d'autres."""
        keys = [k for k, _label in vocab.CODE_ARTICLE_VOCAB]
        self.assertEqual(keys[-1], "AUTRES")

    def test_dynamic_choices_keep_every_initial_code(self):
        self.assertEqual(vocab.item_code_choices(), list(vocab.CODE_ARTICLE_VOCAB))
        initial = [key for key, _label in vocab.CODE_ARTICLE_VOCAB]
        choices = [key for key, _label in vocab.item_code_choices(['V-NEW'])]
        self.assertEqual(choices[:-2], initial[:-1])
        self.assertEqual(choices[-2:], ['V-NEW', 'AUTRES'])

    def test_dynamic_choices_deduplicate_trim_and_ignore_empty_values(self):
        choices = vocab.item_code_choices(['V-GNN', 'AUTRES', ' V-NEW ', 'V-NEW', '', None])
        keys = [key for key, _label in choices]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(keys.count('V-NEW'), 1)
        self.assertNotIn('', keys)

    def test_dynamic_choices_keep_unicode_and_sort_deterministically(self):
        extras = [u'V-\u00c9CHANTILLON', 'V-Z', 'V-A']
        first = vocab.item_code_choices(extras)
        self.assertEqual(first, vocab.item_code_choices(list(reversed(extras))))
        self.assertIn((u'V-\u00c9CHANTILLON', u'V-\u00c9CHANTILLON'), first)
        self.assertEqual(first[-1], ('AUTRES', 'AUTRES'))


class TestReceptionListsFromSpecification(unittest.TestCase):
    """Condition et emballage: listes imposees par le cahier des charges."""

    def test_condition_choices(self):
        keys = [k for k, _label in vocab.SAMPLE_CONDITION_VOCAB]
        self.assertEqual(keys, ["", "Conforme", "Non conforme"])

    def test_condition_needs_an_explicit_choice(self):
        """Sans entree vide, "Conforme" serait preselectionne d'office."""
        self.assertEqual(vocab.SAMPLE_CONDITION_VOCAB[0][0], "")

    def test_packaging_choices(self):
        keys = [k for k, _label in vocab.PACKAGING_CONDITION_VOCAB]
        self.assertEqual(keys, ["Sous vide", "Sachet zip", "Kraft"])

    def test_values_already_entered_stay_valid(self):
        """Valeurs saisies en texte libre avant le passage en liste."""
        self.assertIn("Conforme", dict(vocab.SAMPLE_CONDITION_VOCAB))
        for value in ("Sous vide", "Sachet zip"):
            self.assertIn(value, dict(vocab.PACKAGING_CONDITION_VOCAB))


def test_suite():
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    suite.addTest(loader.loadTestsFromTestCase(TestTemperatureVocabulary))
    suite.addTest(loader.loadTestsFromTestCase(TestCodeArticleVocabulary))
    suite.addTest(loader.loadTestsFromTestCase(TestReceptionListsFromSpecification))
    return suite
