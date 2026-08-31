# -*- coding: utf-8 -*-
"""
Tests du tableau de bord (lot 5).

Ce fichier ne couvre que de la logique pure: la lecture des resultats
d'analyse et le filtre de plage. Aucun site Plone n'est necessaire, un
catalogue de doublure suffit -- ce qui rend ces tests executables par
`make test-pure` sur n'importe quel poste.
"""

import unittest

from senaite.trimeta.samplefields.dashboard.results import fetch_results
from senaite.trimeta.samplefields.dashboard.results import group_by_sample
from senaite.trimeta.samplefields.dashboard.results import in_range
from senaite.trimeta.samplefields.dashboard.results import sample_ids_in_range
from senaite.trimeta.samplefields.dashboard.results import to_number
from senaite.trimeta.samplefields.tests.test_listings import capture_logs


class FakeBrain(object):
    """Brain de l'analysis_catalog, reduit aux colonnes reellement lues."""

    def __init__(self, request_id, keyword, result="", captured=None):
        self.getRequestID = request_id
        self.getKeyword = keyword
        self.getResult = result
        self.getResultCaptureDate = captured


class FakeCatalog(object):
    """Catalogue de doublure: filtre une liste de brains sur la requete.

    Reproduit le seul comportement dont depend le code teste -- une
    valeur de requete peut etre une chaine ou une liste, auquel cas
    c'est un OU. Enregistre les requetes recues, ce qui permet de
    verifier qu'on interroge bien le catalogue une seule fois.
    """

    def __init__(self, brains):
        self.brains = brains
        self.queries = []

    def __call__(self, query):
        self.queries.append(query)

        def matches(brain):
            for index, expected in query.items():
                value = getattr(brain, index, None)
                if isinstance(expected, (list, tuple, set)):
                    if value not in expected:
                        return False
                elif value != expected:
                    return False
            return True

        return [b for b in self.brains if matches(b)]


class ExplodingCatalog(object):
    """Catalogue qui leve, pour verifier qu'on n'emporte pas la page."""

    def __call__(self, query):
        raise RuntimeError("catalogue indisponible")


class TestToNumber(unittest.TestCase):

    def test_plain_numbers(self):
        self.assertEqual(to_number("12.5"), 12.5)
        self.assertEqual(to_number(3), 3.0)

    def test_decimal_comma_is_accepted(self):
        """Saisie courante sur un poste francophone."""
        self.assertEqual(to_number("12,5"), 12.5)

    def test_surrounding_whitespace(self):
        self.assertEqual(to_number("  2.0  "), 2.0)

    def test_empty_is_none(self):
        for value in (None, "", "   "):
            self.assertIsNone(to_number(value))

    def test_text_is_none(self):
        self.assertIsNone(to_number("conforme"))

    def test_detection_limits_are_not_numbers(self):
        """"<0.5" n'est pas 0.5. Le traiter comme tel le ferait entrer
        dans un intervalle auquel il n'appartient peut-etre pas, sans
        que personne ne le voie."""
        self.assertIsNone(to_number("<0.5"))
        self.assertIsNone(to_number(">100"))


class TestInRange(unittest.TestCase):

    def test_between_two_bounds(self):
        self.assertTrue(in_range("5", 1, 10))
        self.assertFalse(in_range("15", 1, 10))
        self.assertFalse(in_range("0.5", 1, 10))

    def test_bounds_are_inclusive(self):
        self.assertTrue(in_range("1", 1, 10))
        self.assertTrue(in_range("10", 1, 10))

    def test_only_a_lower_bound(self):
        self.assertTrue(in_range("50", minimum=10))
        self.assertFalse(in_range("5", minimum=10))

    def test_only_an_upper_bound(self):
        self.assertTrue(in_range("5", maximum=10))
        self.assertFalse(in_range("50", maximum=10))

    def test_uncomparable_values_are_out(self):
        for value in ("", None, "conforme", "<0.5"):
            self.assertFalse(in_range(value, 1, 10))


class TestGroupBySample(unittest.TestCase):

    def test_groups_by_sample_then_keyword(self):
        brains = [
            FakeBrain("VAN-0001", "VAN", "2.1"),
            FakeBrain("VAN-0001", "TH", "18.4"),
            FakeBrain("VAN-0002", "VAN", "1.8"),
        ]
        self.assertEqual(group_by_sample(brains), {
            "VAN-0001": {"VAN": "2.1", "TH": "18.4"},
            "VAN-0002": {"VAN": "1.8"},
        })

    def test_unwanted_keywords_are_dropped(self):
        brains = [
            FakeBrain("VAN-0001", "VAN", "2.1"),
            FakeBrain("VAN-0001", "AUTRE", "9"),
        ]
        grouped = group_by_sample(brains, keywords=["VAN"])
        self.assertEqual(grouped, {"VAN-0001": {"VAN": "2.1"}})

    def test_rows_without_identifier_are_ignored(self):
        """Un brain incomplet ne doit pas creer une ligne fantome."""
        brains = [
            FakeBrain("", "VAN", "2.1"),
            FakeBrain("VAN-0001", "", "2.1"),
        ]
        self.assertEqual(group_by_sample(brains), {})

    def test_a_filled_result_beats_an_empty_one(self):
        """Cas d'une reprise: la premiere analyse est annulee sans
        resultat, la seconde en porte un."""
        brains = [
            FakeBrain("VAN-0001", "VAN", "2.1"),
            FakeBrain("VAN-0001", "VAN", ""),
        ]
        self.assertEqual(group_by_sample(brains),
                         {"VAN-0001": {"VAN": "2.1"}})

    def test_the_most_recent_result_wins(self):
        brains = [
            FakeBrain("VAN-0001", "VAN", "2.1", captured=100),
            FakeBrain("VAN-0001", "VAN", "2.4", captured=200),
        ]
        self.assertEqual(group_by_sample(brains),
                         {"VAN-0001": {"VAN": "2.4"}})

    def test_the_most_recent_wins_whatever_the_order(self):
        brains = [
            FakeBrain("VAN-0001", "VAN", "2.4", captured=200),
            FakeBrain("VAN-0001", "VAN", "2.1", captured=100),
        ]
        self.assertEqual(group_by_sample(brains),
                         {"VAN-0001": {"VAN": "2.4"}})

    def test_missing_dates_keep_the_last_seen(self):
        brains = [
            FakeBrain("VAN-0001", "VAN", "2.1"),
            FakeBrain("VAN-0001", "VAN", "2.4"),
        ]
        self.assertEqual(group_by_sample(brains),
                         {"VAN-0001": {"VAN": "2.4"}})


class TestFetchResults(unittest.TestCase):

    def setUp(self):
        self.catalog = FakeCatalog([
            FakeBrain("VAN-0001", "VAN", "2.1"),
            FakeBrain("VAN-0001", "TH", "18.4"),
            FakeBrain("VAN-0002", "VAN", "1.8"),
            FakeBrain("VAN-0003", "VAN", "9.9"),
        ])

    def test_one_single_query_for_the_whole_page(self):
        """C'est tout l'interet: le cout ne depend pas du nombre de
        lignes affichees."""
        fetch_results(self.catalog, ["VAN-0001", "VAN-0002"], ["VAN", "TH"])
        self.assertEqual(len(self.catalog.queries), 1)

    def test_query_uses_indexed_columns_only(self):
        fetch_results(self.catalog, ["VAN-0001"], ["VAN"])
        query = self.catalog.queries[0]
        self.assertEqual(sorted(query.keys()), ["getKeyword", "getRequestID"])

    def test_only_the_requested_samples_come_back(self):
        results = fetch_results(self.catalog, ["VAN-0001"], ["VAN", "TH"])
        self.assertEqual(results, {"VAN-0001": {"VAN": "2.1", "TH": "18.4"}})

    def test_empty_arguments_do_not_query_at_all(self):
        self.assertEqual(fetch_results(self.catalog, [], ["VAN"]), {})
        self.assertEqual(fetch_results(self.catalog, ["VAN-0001"], []), {})
        self.assertEqual(self.catalog.queries, [])

    def test_an_unknown_keyword_gives_no_column_not_an_error(self):
        """Un service pas encore cree dans l'instance."""
        self.assertEqual(fetch_results(self.catalog, ["VAN-0001"], ["XXX"]), {})

    def test_a_failing_catalog_does_not_break_the_page(self):
        """Mieux vaut des colonnes de resultats vides qu'un tableau de
        bord qui ne s'affiche plus.

        L'incident doit tout de meme etre journalise: une panne muette
        se traduirait par des colonnes vides que personne ne saurait
        expliquer."""
        with capture_logs("senaite.trimeta.samplefields") as records:
            self.assertEqual(
                fetch_results(ExplodingCatalog(), ["VAN-0001"], ["VAN"]), {})
        self.assertEqual(len(records), 1)


class TestSampleIdsInRange(unittest.TestCase):

    def setUp(self):
        self.catalog = FakeCatalog([
            FakeBrain("VAN-0001", "VAN", "2.1"),
            FakeBrain("VAN-0002", "VAN", "1.2"),
            FakeBrain("VAN-0003", "VAN", "5.0"),
            FakeBrain("VAN-0004", "VAN", "<0.5"),
            FakeBrain("VAN-0005", "VAN", ""),
            FakeBrain("VAN-0009", "TH", "18.4"),
        ])

    def test_no_bound_means_no_filtering(self):
        """None, pas une liste vide: "pas de filtre" et "aucun resultat"
        ne doivent pas se confondre."""
        self.assertIsNone(sample_ids_in_range(self.catalog, "VAN"))
        self.assertEqual(self.catalog.queries, [])

    def test_between_two_bounds(self):
        self.assertEqual(
            sample_ids_in_range(self.catalog, "VAN", 2, 6),
            ["VAN-0001", "VAN-0003"])

    def test_lower_bound_only(self):
        self.assertEqual(
            sample_ids_in_range(self.catalog, "VAN", minimum=5),
            ["VAN-0003"])

    def test_no_match_gives_an_empty_list(self):
        self.assertEqual(sample_ids_in_range(self.catalog, "VAN", 100, 200), [])

    def test_only_the_asked_keyword_is_queried(self):
        sample_ids_in_range(self.catalog, "VAN", 1, 100)
        self.assertEqual(self.catalog.queries, [{"getKeyword": "VAN"}])

    def test_uncomparable_results_are_left_out(self):
        """"<0.5" et une case vide ne peuvent pas etre situes dans un
        intervalle: ils en sortent."""
        found = sample_ids_in_range(self.catalog, "VAN", 0, 1000)
        self.assertNotIn("VAN-0004", found)
        self.assertNotIn("VAN-0005", found)

    def test_a_failing_catalog_disables_the_filter(self):
        """Plutot afficher tout le tableau qu'une page d'erreur."""
        with capture_logs("senaite.trimeta.samplefields") as records:
            self.assertIsNone(
                sample_ids_in_range(ExplodingCatalog(), "VAN", 1, 2))
        self.assertEqual(len(records), 1)


def test_suite():
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    for case in (TestToNumber, TestInRange, TestGroupBySample,
                 TestFetchResults, TestSampleIdsInRange):
        suite.addTest(loader.loadTestsFromTestCase(case))
    return suite
