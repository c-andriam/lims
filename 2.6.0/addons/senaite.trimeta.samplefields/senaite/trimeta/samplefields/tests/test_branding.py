# -*- coding: utf-8 -*-
"""Logo de l'application: le fichier embarque est exploitable.

Test pur: verifie le fichier lui-meme. La pose dans le Setup est couverte
par test_setup.py (site Plone requis).
"""

import os
import struct
import unittest

PACKAGE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO = os.path.join(PACKAGE, "setup_data", "logo-trimeta-groupe-blanc.png")


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


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestSiteLogoFile))
    return suite
