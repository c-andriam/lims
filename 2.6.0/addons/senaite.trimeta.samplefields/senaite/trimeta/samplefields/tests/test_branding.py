# -*- coding: utf-8 -*-
"""Logo de l'application: le fichier embarque est exploitable.

Test pur: verifie le fichier lui-meme. La pose dans le Setup est couverte
par test_setup.py (site Plone requis).
"""

import os
import re
import struct
import unittest

PACKAGE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO = os.path.join(PACKAGE, "setup_data", "logo-trimeta-groupe-blanc.png")
REPORT_LOGO = os.path.join(PACKAGE, "browser", "resources",
                           "logo-trimeta-agrofood.png")
COA_TEMPLATE = os.path.join(PACKAGE, "coa", "templates", "reports",
                            "COA-Trimeta.pt")
HEADER_TEMPLATE = os.path.join(PACKAGE, "coa", "templates", "header.pt")


class TestSiteLogoFile(unittest.TestCase):

    def read_header(self):
        with open(LOGO, "rb") as logo_file:
            return logo_file.read(24)

    def test_logo_is_shipped(self):
        self.assertTrue(os.path.isfile(LOGO), LOGO)

    def test_logo_is_a_png(self):
        """PNG, pas WebP: la chaine d'images Python 2 ne garantit pas le WebP."""
        self.assertEqual(self.read_header()[:8], b"\x89PNG\r\n\x1a\n")

    def test_logo_dimensions(self):
        """Version 180 x 92 de l'image fournie par le groupe."""
        width, height = struct.unpack(">II", self.read_header()[16:24])
        self.assertEqual((width, height), (180, 92))


class TestReportLogo(unittest.TestCase):
    """Logo du laboratoire sur le COA, a la place du logo SENAITE."""

    def read(self, path, mode="rb", size=None):
        with open(path, mode) as handle:
            return handle.read(size) if size else handle.read()

    def test_logo_is_shipped_as_a_web_resource(self):
        """Le PDF charge l'image par son adresse: elle doit etre servie."""
        self.assertTrue(os.path.isfile(REPORT_LOGO), REPORT_LOGO)

    def test_logo_is_a_png(self):
        self.assertEqual(self.read(REPORT_LOGO, size=8), b"\x89PNG\r\n\x1a\n")

    def test_logo_is_cropped_to_its_content(self):
        """Recadre sur l'encre: l'original avait 53px de vide en haut et
        54px en bas sur 150px, et ressortait illisible une fois mis a
        l'echelle dans l'en-tete du rapport."""
        header = self.read(REPORT_LOGO, size=24)
        self.assertEqual(struct.unpack(">II", header[16:24]), (126, 43))

    def test_header_uses_the_lab_logo(self):
        """L'en-tete de l'add-on sert a TOUS les gabarits de rapport."""
        header = self.read(HEADER_TEMPLATE, mode="r")
        self.assertIn("logo-trimeta-agrofood.png", header)
        self.assertIn("senaite.trimeta.samplefields.static", header)
        self.assertNotIn("senaite.svg", header)

    def test_coa_renders_the_standard_header(self):
        """Pas de duplication: le COA appelle l'en-tete de la vue."""
        self.assertIn("render_header", self.read(COA_TEMPLATE, mode="r"))

    def test_sections_may_break_across_pages(self):
        """Sans cette regle, une section entiere saute a la page suivante.

        La feuille de style des rapports pose "div.row { page-break-inside:
        avoid }". Nos tableaux sont longs: le COA sortait sur 3 pages, la
        premiere presque vide. La regle du gabarit, posee apres et plus
        specifique, autorise la coupure de nos sections, en gardant les
        lignes de tableau entieres.
        """
        template = self.read(COA_TEMPLATE, mode="r")
        self.assertIn("page-break-inside: auto", template)
        # Les sections de senaite.impress comptent autant que les notres:
        # le tableau des resultats, insecable, basculait entier a la page
        # suivante et laissait un blanc en bas de la premiere.
        for section in ("section-summary", "section-sample-information",
                        "section-organoleptic", "section-results",
                        "section-signatures", "section-discreeter"):
            self.assertIn(section, template)
        # Une ligne de tableau reste entiere, un titre ne finit pas la page
        self.assertIn("page-break-inside: avoid", template)
        self.assertIn("page-break-after: avoid", template)

    def test_sections_are_separate_blocks(self):
        """Une section par bloc: chacune se place a la suite."""
        template = self.read(COA_TEMPLATE, mode="r")
        blocks = re.split('<div class="row', template)[1:]
        self.assertGreaterEqual(len(blocks), 3, "sections du COA non separees")

    def test_no_double_hyphen_inside_comments(self):
        """"--" dans un commentaire XML: le gabarit ne compile plus.

        Constate a l'ecran: "Ooops, an error occured" a la place du
        rapport, et dans le journal "The string '--' is not allowed in a
        comment". Le tiret cadratin des commentaires francais est donc
        proscrit ici.
        """
        for path in (COA_TEMPLATE, HEADER_TEMPLATE):
            for comment in re.findall("<!--(.*?)-->", self.read(path, mode="r"),
                                      re.DOTALL):
                self.assertNotIn("--", comment,
                                 "%s: commentaire avec un double tiret"
                                 % os.path.basename(path))


def test_suite():
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    for case in (TestSiteLogoFile, TestReportLogo):
        suite.addTest(loader.loadTestsFromTestCase(case))
    return suite
