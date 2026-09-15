# -*- coding: utf-8 -*-
"""Traductions: priorite des catalogues, lecture des .po, .mo a jour.

Tests purs: ni Zope ni SENAITE.
"""

import gettext
import io
import os
import unittest

from senaite.trimeta.samplefields import i18n


class TestPrioritizeCatalogs(unittest.TestCase):

    PREFIX = "/src/trimeta/locales"

    def test_ours_first_relative_order_kept(self):
        names = ["/eggs/core/locales/fr/senaite.core.mo",
                 "/src/trimeta/locales/fr/LC_MESSAGES/a.mo",
                 "test",
                 "/src/trimeta/locales/fr/LC_MESSAGES/b.mo"]
        self.assertEqual(i18n.prioritize_catalogs(names, self.PREFIX), [
            "/src/trimeta/locales/fr/LC_MESSAGES/a.mo",
            "/src/trimeta/locales/fr/LC_MESSAGES/b.mo",
            "/eggs/core/locales/fr/senaite.core.mo",
            "test"])

    def test_similar_prefix_is_not_ours(self):
        """/src/trimeta/locales-old n'est pas /src/trimeta/locales."""
        names = ["/eggs/core.mo", "/src/trimeta/locales-old/fr/x.mo"]
        self.assertEqual(i18n.prioritize_catalogs(names, self.PREFIX), names)

    def test_nothing_ours_leaves_the_order(self):
        names = ["/eggs/a.mo", "/eggs/b.mo"]
        self.assertEqual(i18n.prioritize_catalogs(names, self.PREFIX), names)


class TestParsePo(unittest.TestCase):

    def test_entries_multiline_and_escapes(self):
        text = (u'msgid ""\nmsgstr ""\n"Content-Type: text/plain; charset=UTF-8\\n"\n\n'
                u'msgid "Save"\nmsgstr "Enregistrer"\n\n'
                u'msgid "long"\nmsgstr ""\n"premi\u00e8re "\n"ligne \\"cit\u00e9e\\""\n')
        messages = i18n.parse_po(text)
        self.assertEqual(messages[u"Save"], u"Enregistrer")
        self.assertEqual(messages[u"long"], u'premi\u00e8re ligne "cit\u00e9e"')
        self.assertIn(u"charset=UTF-8", messages[u""])

    def test_fuzzy_and_untranslated_are_ignored(self):
        text = (u'#, fuzzy\nmsgid "A"\nmsgstr "a"\n\n'
                u'msgid "B"\nmsgstr ""\n')
        self.assertEqual(i18n.parse_po(text), {})

    def test_context(self):
        text = u'msgctxt "menu"\nmsgid "File"\nmsgstr "Fichier"\n'
        self.assertEqual(i18n.parse_po(text), {u"menu\x04File": u"Fichier"})

    def test_mo_round_trip(self):
        messages = {u"": u"Content-Type: text/plain; charset=UTF-8\n",
                    u"Batch": u"S\u00e9rie", u"Save": u"Enregistrer"}
        catalog = gettext.GNUTranslations(io.BytesIO(i18n.build_mo(messages)))
        self.assertEqual(catalog.gettext(u"Batch"), u"S\u00e9rie")
        self.assertEqual(catalog.gettext(u"Save"), u"Enregistrer")


class TestShippedCatalogs(unittest.TestCase):
    """Chaque .mo livre doit correspondre a son .po.

    Zope ne lit que les .mo: une traduction ajoutee au .po sans
    recompilation (make i18n) n'apparaitrait jamais a l'ecran.
    """

    def iter_po(self):
        for root, _dirs, files in os.walk(i18n.LOCALES_DIR):
            for name in sorted(files):
                if name.endswith(".po"):
                    yield os.path.join(root, name)

    def test_every_mo_matches_its_po(self):
        found = 0
        for po_path in self.iter_po():
            found += 1
            mo_path = po_path[:-3] + ".mo"
            self.assertTrue(os.path.exists(mo_path), "absent: %s" % mo_path)
            with io.open(po_path, encoding="utf-8") as po_file:
                expected = i18n.parse_po(po_file.read())
            with open(mo_path, "rb") as mo_file:
                catalog = gettext.GNUTranslations(mo_file)._catalog
            for msgid, msgstr in expected.items():
                if msgid:
                    self.assertEqual(catalog.get(msgid), msgstr,
                                     "%s: %s (make i18n)" % (os.path.basename(po_path), msgid))
        self.assertGreaterEqual(found, 4)

    def core_catalog(self):
        path = os.path.join(i18n.LOCALES_DIR, "fr", "LC_MESSAGES", "senaite.core.po")
        with io.open(path, encoding="utf-8") as po_file:
            return i18n.parse_po(po_file.read())

    def test_dates_are_day_first(self):
        messages = self.core_catalog()
        self.assertEqual(messages[u"date_format_short"], u"${d}/${m}/${Y}")
        self.assertEqual(messages[u"date_format_long"], u"${d}/${m}/${Y} ${H}:${M}")

    def test_batch_is_not_called_lot(self):
        """"Lot" est le lot du client: une serie SENAITE ne doit pas s'y confondre."""
        messages = self.core_catalog()
        for msgid in (u"Batch", u"label_sample_batch"):
            self.assertNotEqual(messages[msgid], u"Lot")

    def test_placeholders_are_kept(self):
        """Une variable ${...} perdue a la traduction casse l'affichage."""
        import re
        for po_path in self.iter_po():
            with io.open(po_path, encoding="utf-8") as po_file:
                for msgid, msgstr in i18n.parse_po(po_file.read()).items():
                    if not msgid or msgid.startswith(u"date_format") or msgid == u"time_format":
                        continue
                    self.assertEqual(sorted(re.findall(u"\\$\\{\\w+\\}", msgid)),
                                     sorted(re.findall(u"\\$\\{\\w+\\}", msgstr)), msgid)


def test_suite():
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    for case in (TestPrioritizeCatalogs, TestParsePo, TestShippedCatalogs):
        suite.addTest(loader.loadTestsFromTestCase(case))
    return suite
