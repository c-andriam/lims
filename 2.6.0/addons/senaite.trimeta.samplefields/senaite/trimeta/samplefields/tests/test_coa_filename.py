# -*- coding: utf-8 -*-
"""
Tests du nommage des fichiers COA (demande D10).

Logique pure: ni Zope, ni site Plone. C'est justement pour cela que le
calcul du nom vit dans `coa/filename.py` et non dans les trois vues qui
le consomment -- ces vues-la, elles, ne sont verifiables que dans le
container.

Ce qui est verifie ici est ce qui casse en clientele: un nom tronque
dans un en-tete HTTP, un fichier refuse par le poste du destinataire,
un COA qui disparait d'une archive parce qu'un homonyme l'a recouvert.
"""

import io
import os
import unittest

from senaite.trimeta.samplefields.coa.filename import FALLBACK
from senaite.trimeta.samplefields.coa.filename import MAX_LENGTH
from senaite.trimeta.samplefields.coa.filename import build_filename
from senaite.trimeta.samplefields.coa.filename import sanitize
from senaite.trimeta.samplefields.coa.filename import unique_name


class TestSanitize(unittest.TestCase):
    """Assainissement d'une valeur saisie."""

    def test_plain_code_is_left_alone(self):
        """Le cas courant ne doit rien subir."""
        self.assertEqual(sanitize(u"ECH-2024-042"), u"ECH-2024-042")

    def test_spaces_become_underscores(self):
        """senaite.core ecrit `filename=%s` SANS guillemets: un blanc y
        tronquerait le nom au premier mot."""
        self.assertEqual(sanitize(u"Vanille Bourbon 2024"),
                         u"Vanille_Bourbon_2024")

    def test_runs_of_whitespace_collapse(self):
        self.assertEqual(sanitize(u"A   B"), u"A_B")

    def test_tabs_and_newlines_are_whitespace_too(self):
        self.assertEqual(sanitize(u"A\tB\nC"), u"A_B_C")

    def test_mixed_whitespace_run_collapses_to_one_separator(self):
        self.assertEqual(sanitize(u"A \t\n B"), u"A_B")

    def test_accents_are_transliterated(self):
        """L'en-tete Content-Disposition de senaite.core n'a pas de
        forme `filename*=`: un octet non ASCII y est rendu differemment
        par chaque navigateur."""
        self.assertEqual(sanitize(u"R\xe9colte \xe9t\xe9"), u"Recolte_ete")

    def test_path_separators_become_dashes(self):
        """Une barre oblique creerait un chemin chez le destinataire."""
        self.assertEqual(sanitize(u"Lot 12/A"), u"Lot_12-A")
        self.assertEqual(sanitize(u"Lot\\12"), u"Lot-12")

    def test_control_characters_are_removed(self):
        """Les non-blancs disparaissent purement."""
        for code in (0, 7, 8, 27, 127):
            result = sanitize(u"ECH" + chr(code) + u"1")
            self.assertEqual(result, u"ECH1")

    def test_newline_and_tab_become_separators(self):
        """Un retour chariot ouvrirait une injection d'en-tete HTTP. Il
        devient separateur plutot que d'etre efface: l'effacer collerait
        deux mots ensemble."""
        for code in (9, 10, 13):
            result = sanitize(u"ECH" + chr(code) + u"1")
            self.assertEqual(result, u"ECH_1")

    def test_header_injection_attempt(self):
        """Le scenario complet, tel qu'il arriverait par le formulaire."""
        evil = u"ECH-1\r\nSet-Cookie: a=b"
        result = sanitize(evil)
        self.assertNotIn(u"\r", result)
        self.assertNotIn(u"\n", result)
        self.assertEqual(result, u"ECH-1_Set-Cookie-a=b")

    def test_windows_illegal_characters(self):
        self.assertEqual(sanitize(u'A:B*C?D"E<F>G|H'), u"A-B-C-D-E-F-G-H")

    def test_leading_dot_is_stripped(self):
        """`.ECH-1.pdf` serait un fichier cache sous Unix."""
        self.assertEqual(sanitize(u".ECH-1"), u"ECH-1")

    def test_trailing_dot_and_space_are_stripped(self):
        """Windows refuse un nom finissant par un point ou un blanc."""
        self.assertEqual(sanitize(u"ECH-1. "), u"ECH-1")

    def test_repeated_separators_collapse(self):
        self.assertEqual(sanitize(u"ECH---1"), u"ECH-1")
        self.assertEqual(sanitize(u"ECH___1"), u"ECH_1")

    def test_windows_reserved_names_get_a_suffix(self):
        """`CON.pdf` ne peut pas etre cree sous Windows."""
        self.assertEqual(sanitize(u"CON"), u"CON_")
        self.assertEqual(sanitize(u"con"), u"con_")
        self.assertEqual(sanitize(u"LPT1"), u"LPT1_")

    def test_name_merely_containing_a_reserved_word_is_untouched(self):
        self.assertEqual(sanitize(u"CONTRAT-1"), u"CONTRAT-1")

    def test_length_is_capped(self):
        result = sanitize(u"A" * 400)
        self.assertEqual(len(result), MAX_LENGTH)

    def test_truncation_does_not_leave_a_trailing_separator(self):
        result = sanitize(u"A" * (MAX_LENGTH - 1) + u"-BBB")
        self.assertFalse(result.endswith(u"-"))

    def test_empty_falls_back(self):
        self.assertEqual(sanitize(u""), FALLBACK)
        self.assertEqual(sanitize(None), FALLBACK)
        self.assertEqual(sanitize(u"   "), FALLBACK)

    def test_value_made_only_of_junk_falls_back(self):
        """Un code qui ne laisse rien apres nettoyage doit tout de meme
        donner un nom."""
        self.assertEqual(sanitize(u"///"), FALLBACK)
        self.assertEqual(sanitize(u"..."), FALLBACK)

    def test_fallback_is_overridable(self):
        """build_filename() s'en sert pour distinguer 'vide' de
        'inexploitable'."""
        self.assertEqual(sanitize(u"", fallback=u""), u"")

    def test_bytes_are_accepted(self):
        """Sur Python 2, une valeur venue du formulaire peut etre des
        octets."""
        self.assertEqual(sanitize(b"ECH-1"), u"ECH-1")


class TestBuildFilename(unittest.TestCase):
    """Arbitrage entre Code echantillon et Sample ID."""

    def test_sample_code_wins(self):
        self.assertEqual(build_filename(u"ECH-042", u"W-0031"),
                         u"ECH-042.pdf")

    def test_empty_code_falls_back_to_sample_id(self):
        """C'est la demande D10 lue a l'envers: un echantillon saisi
        avant l'ajout du champ garde l'ancien nom plutot que rien."""
        self.assertEqual(build_filename(u"", u"W-0031"), u"W-0031.pdf")
        self.assertEqual(build_filename(None, u"W-0031"), u"W-0031.pdf")

    def test_unusable_code_falls_back_to_sample_id(self):
        self.assertEqual(build_filename(u"///", u"W-0031"), u"W-0031.pdf")

    def test_both_empty_gives_the_last_resort_name(self):
        self.assertEqual(build_filename(u"", u""),
                         u"{}.pdf".format(FALLBACK))

    def test_sample_id_is_sanitized_too(self):
        self.assertEqual(build_filename(u"", u"W 0031"), u"W_0031.pdf")

    def test_extension_is_overridable(self):
        self.assertEqual(build_filename(u"ECH-1", u"W-1", u".zip"),
                         u"ECH-1.zip")


class TestUniqueName(unittest.TestCase):
    """Desambiguisation des noms dans une archive ZIP."""

    def test_first_name_is_kept(self):
        taken = set()
        self.assertEqual(unique_name(u"ECH-1.pdf", taken), u"ECH-1.pdf")

    def test_duplicate_gets_a_suffix_before_the_extension(self):
        """zipfile accepte deux entrees homonymes sans rien dire, et la
        plupart des extracteurs n'en montrent qu'une."""
        taken = set()
        self.assertEqual(unique_name(u"ECH-1.pdf", taken), u"ECH-1.pdf")
        self.assertEqual(unique_name(u"ECH-1.pdf", taken), u"ECH-1-2.pdf")
        self.assertEqual(unique_name(u"ECH-1.pdf", taken), u"ECH-1-3.pdf")

    def test_comparison_ignores_case(self):
        """Le destinataire peut extraire sur un systeme de fichiers qui
        ne distingue pas la casse."""
        taken = set()
        unique_name(u"ECH-1.pdf", taken)
        self.assertEqual(unique_name(u"ech-1.pdf", taken), u"ech-1-2.pdf")

    def test_name_without_extension(self):
        taken = set()
        unique_name(u"ECH-1", taken)
        self.assertEqual(unique_name(u"ECH-1", taken), u"ECH-1-2")

    def test_distinct_names_are_untouched(self):
        taken = set()
        self.assertEqual(unique_name(u"A.pdf", taken), u"A.pdf")
        self.assertEqual(unique_name(u"B.pdf", taken), u"B.pdf")

    def test_suffix_does_not_collide_with_an_existing_name(self):
        """Si `ECH-1-2.pdf` existe deja par lui-meme, le doublon de
        `ECH-1.pdf` doit passer au suivant."""
        taken = set()
        unique_name(u"ECH-1.pdf", taken)
        unique_name(u"ECH-1-2.pdf", taken)
        self.assertEqual(unique_name(u"ECH-1.pdf", taken), u"ECH-1-3.pdf")


class TestSources(unittest.TestCase):
    """Hygiene des sources du module coa/."""

    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def read(self, *parts):
        path = os.path.join(self.ROOT, *parts)
        return io.open(path, encoding="utf-8").read()

    def test_no_control_characters_in_sources(self):
        """Un caractere de controle ecrit litteralement dans une
        expression reguliere s'est deja glisse dans ce depot
        (dashboard.js, un vrai 0x08). Illisible a l'oeil, silencieux a
        l'execution -- et ici, ce serait la protection contre
        l'injection d'en-tete qui sauterait."""
        for name in ("filename.py", "download.py", "email.py",
                     "workflow.py"):
            source = self.read("coa", name)
            for code in (0, 7, 8, 11, 12, 27, 127):
                self.assertNotIn(
                    chr(code), source,
                    "caractere de controle %d present dans coa/%s"
                    % (code, name))

    def test_sources_are_ascii(self):
        """Convention du depot: pas d'accents dans les sources Python,
        l'encodage du container n'etant pas garanti."""
        for name in ("filename.py", "download.py", "email.py",
                     "workflow.py"):
            source = self.read("coa", name)
            try:
                source.encode("ascii")
            except UnicodeEncodeError as exc:
                self.fail("caractere non ASCII dans coa/%s: %s"
                          % (name, exc))


def test_suite():
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    for case in (TestSanitize, TestBuildFilename, TestUniqueName,
                 TestSources):
        suite.addTest(loader.loadTestsFromTestCase(case))
    return suite
