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

    def test_coa_uses_the_lab_logo(self):
        template = self.read(COA_TEMPLATE, mode="r")
        self.assertIn("logo-trimeta-agrofood.png", template)
        self.assertIn("senaite.trimeta.samplefields.static", template)

    def test_coa_does_not_use_the_senaite_header(self):
        """render_header ramenerait le logo SENAITE, fige dans impress."""
        self.assertNotIn("render_header", self.read(COA_TEMPLATE, mode="r"))

    def test_no_double_hyphen_inside_comments(self):
        """"--" dans un commentaire XML: le gabarit ne compile plus.

        Constate a l'ecran: "Ooops, an error occured" a la place du
        rapport, et dans le journal "The string '--' is not allowed in a
        comment". Le tiret cadratin des commentaires francais est donc
        proscrit ici.
        """
        for comment in re.findall("<!--(.*?)-->", self.read(COA_TEMPLATE, mode="r"),
                                  re.DOTALL):
            self.assertNotIn("--", comment,
                             "commentaire du COA avec un double tiret")


def test_suite():
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    for case in (TestSiteLogoFile, TestReportLogo):
        suite.addTest(loader.loadTestsFromTestCase(case))
    return suite
