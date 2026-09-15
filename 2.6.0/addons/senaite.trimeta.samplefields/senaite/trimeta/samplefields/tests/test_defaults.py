# -*- coding: utf-8 -*-
"""
Configuration livree en code (defaults.py).

Ne sont testees ici que les parties PURES: la forme des formules et des
champs de saisie. La creation effective des objets dans l'instance
demande un vrai site et releve de `make test`.

Le point le plus important de ce module est
`test_no_default_value_on_repetitions`. Il protege une decision dont
l'enjeu n'est pas visible en lisant le code: pre-remplir les cases de
repetition a 0 ferait passer une moyenne fausse pour un resultat
valide.
"""

import unittest

from senaite.trimeta.samplefields import defaults


class TestRepetitionFormulas(unittest.TestCase):

    def test_formula_for_three_repetitions(self):
        self.assertEqual(defaults.build_formula(3),
                         "([R1] + [R2] + [R3]) / 3")

    def test_formula_for_two_repetitions(self):
        self.assertEqual(defaults.build_formula(2), "([R1] + [R2]) / 2")

    def test_formula_uses_the_markers_senaite_expects(self):
        """SENAITE substitue les marqueurs [Xxx] de la formule. Une
        autre notation ne serait jamais remplacee, et la formule
        partirait telle quelle a l'evaluation."""
        formula = defaults.build_formula(3)
        for num in (1, 2, 3):
            self.assertIn("[R{}]".format(num), formula)

    def test_every_declared_calculation_builds(self):
        for count, title in defaults.CALCULATIONS:
            self.assertTrue(title)
            self.assertEqual(len(defaults.build_interims(count)), count)

    def test_default_calculation_is_declared(self):
        """Le calcul rattache par defaut doit exister dans CALCULATIONS,
        sinon setup_repetitions ne rattache rien."""
        declared = [count for count, _title in defaults.CALCULATIONS]
        self.assertIn(defaults.DEFAULT_REPETITIONS, declared)


class TestRepetitionInterims(unittest.TestCase):

    def setUp(self):
        self.interims = defaults.build_interims(3)

    def test_keywords_match_the_formula(self):
        keywords = [i["keyword"] for i in self.interims]
        self.assertEqual(keywords, ["R1", "R2", "R3"])

    def test_no_default_value_on_repetitions(self):
        """Les cases de repetition doivent rester VIDES.

        C'est la decision centrale de D9, et elle tient a une seule
        ligne de senaite.core (AbstractAnalysis.calculateResult):

            # skip unset values
            if interim_value == "":
                continue

        Un champ vide n'entre pas dans le mapping, son marqueur survit
        dans la formule, le formatage leve un KeyError, et SENAITE pose
        le resultat "NA". Une repetition oubliee est donc VISIBLE.

        Y mettre 0 par defaut inverserait exactement cela: trois cases
        pre-remplies dont deux seulement sont corrigees donneraient une
        moyenne calculee sur un zero fantome -- un nombre plausible,
        faux, et que rien ne signale. C'est le seul scenario qui
        pourrait envoyer un resultat errone a un client.
        """
        for interim in self.interims:
            self.assertEqual(
                interim["value"], "",
                "la repetition %s a une valeur par defaut: une "
                "repetition non saisie serait comptee comme un zero"
                % interim["keyword"])

    def test_repetitions_are_not_reported(self):
        """Le rapport publie porte la moyenne, pas les mesures
        intermediaires."""
        for interim in self.interims:
            self.assertFalse(interim["report"])

    def test_declares_every_subfield_senaite_expects(self):
        """InterimFieldsField declare ses sous-champs; en omettre un
        laisse SENAITE lire une cle absente."""
        expected = ("keyword", "title", "value", "choices", "result_type",
                    "allow_empty", "unit", "report", "hidden", "wide")
        for interim in self.interims:
            for key in expected:
                self.assertIn(key, interim)


class TestPublishingDefaults(unittest.TestCase):

    def test_our_coa_template_is_not_a_multi_template(self):
        """Tout l'objet de D11.

        senaite.impress donne la totalite des echantillons selectionnes
        a un gabarit dont le nom commence ou finit par "Multi". Le
        notre ne doit surtout pas en etre un, sans quoi on retablirait
        precisement le symptome qu'on corrige.
        """
        name = defaults.COA_TEMPLATE.split(":")[-1]
        self.assertFalse(name.startswith("Multi"))
        self.assertFalse(name.replace(".pt", "").endswith("Multi"))

    def test_the_replaced_templates_are_all_multi(self):
        """On ne remplace que des gabarits multi-echantillons: c'est ce
        qui rend le remplacement sur."""
        for template in defaults.MULTI_TEMPLATES:
            self.assertIn("Multi", template)

    def test_our_template_is_never_in_the_replaced_list(self):
        self.assertNotIn(defaults.COA_TEMPLATE, defaults.MULTI_TEMPLATES)


class TestKeywordsAreShared(unittest.TestCase):

    def test_repetitions_target_the_dashboard_keywords(self):
        """Une seule source de verite pour les mots-cles de services.

        Si les calculs visaient leur propre liste, confirmer les
        mots-cles aupres du laboratoire faudrait le faire deux fois --
        et la seconde serait oubliee.
        """
        from senaite.trimeta.samplefields.dashboard import columns
        self.assertEqual(defaults.get_keywords(), columns.get_keywords())
        self.assertEqual(len(defaults.get_keywords()), 7)


def test_suite():
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    for case in (TestRepetitionFormulas, TestRepetitionInterims,
                 TestPublishingDefaults, TestKeywordsAreShared):
        suite.addTest(loader.loadTestsFromTestCase(case))
    return suite
