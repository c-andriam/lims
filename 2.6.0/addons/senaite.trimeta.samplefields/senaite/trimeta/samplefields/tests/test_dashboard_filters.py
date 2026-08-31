# -*- coding: utf-8 -*-
"""
Tests des filtres du tableau de bord.

Logique pure: aucun site Plone, aucun Zope. Le convertisseur de date
est injecte, ce qui permet de verifier la construction de la requete
sans DateTime.
"""

import io
import os
import re
import unittest

from senaite.trimeta.samplefields.dashboard.columns import COLUMN_HELP
from senaite.trimeta.samplefields.dashboard.columns import DASHBOARD_ANALYSES
from senaite.trimeta.samplefields.dashboard.columns import build_columns
from senaite.trimeta.samplefields.dashboard.columns import get_column_help
from senaite.trimeta.samplefields.dashboard.columns import get_column_labels
from senaite.trimeta.samplefields.dashboard.columns import get_keyword_for
from senaite.trimeta.samplefields.dashboard.columns import get_keywords
from senaite.trimeta.samplefields.dashboard.columns import get_metadata_map
from senaite.trimeta.samplefields.dashboard.filters import ALL_FILTERS
from senaite.trimeta.samplefields.dashboard.filters import PREFIX
from senaite.trimeta.samplefields.dashboard.filters import build_query
from senaite.trimeta.samplefields.dashboard.filters import hidden_fields
from senaite.trimeta.samplefields.dashboard.filters import is_active
from senaite.trimeta.samplefields.dashboard.filters import read_filters


def fake_to_date(value, end_of_day=False):
    """Convertisseur de doublure: rend un texte reconnaissable.

    Suffit a verifier la FORME de la requete, qui est ce que ce module
    construit; la conversion reelle appartient a la vue.
    """
    if not value:
        return None
    if value == "illisible":
        return None
    return "{}{}".format(value, "T23:59:59" if end_of_day else "T00:00:00")


class TestReadFilters(unittest.TestCase):

    def test_reads_prefixed_parameters(self):
        form = {PREFIX + "lot": "LOT-1", PREFIX + "origin": "Sava"}
        self.assertEqual(read_filters(form),
                         {"lot": "LOT-1", "origin": "Sava"})

    def test_ignores_unknown_and_unprefixed(self):
        """Le prefixe evite toute collision avec les parametres de
        senaite.app.listing (pagesize, sort_on...)."""
        form = {"lot": "LOT-1", PREFIX + "inconnu": "x", "sort_on": "getId"}
        self.assertEqual(read_filters(form), {})

    def test_blank_values_are_dropped(self):
        """Une case laissee avec un espace ne doit pas produire un
        filtre qui ne trouve rien."""
        form = {PREFIX + "lot": "   ", PREFIX + "origin": ""}
        self.assertEqual(read_filters(form), {})

    def test_values_are_stripped(self):
        form = {PREFIX + "lot": "  LOT-1  "}
        self.assertEqual(read_filters(form), {"lot": "LOT-1"})

    def test_no_form_at_all(self):
        self.assertEqual(read_filters(None), {})


class TestBuildQuery(unittest.TestCase):

    def test_simple_filters_map_to_indexes(self):
        query = build_query({
            "lot": "LOT-1",
            "client": "uid-client",
            "sample_type": "uid-type",
            "origin": "Sava",
        })
        self.assertEqual(query, {
            "getClientSampleID": "LOT-1",
            "getClientUID": "uid-client",
            "getTrimetaSampleTypeUID": "uid-type",
            "getOrigin": "Sava",
        })

    def test_empty_filters_give_an_empty_query(self):
        """Aucun critere ne doit rien restreindre du tout."""
        self.assertEqual(build_query({}), {})
        self.assertEqual(build_query(None), {})

    def test_both_dates_give_a_min_max_range(self):
        query = build_query({"date_from": "2026-01-01",
                             "date_to": "2026-01-31"},
                            to_date=fake_to_date)
        self.assertEqual(query["getDateReceived"], {
            "query": ["2026-01-01T00:00:00", "2026-01-31T23:59:59"],
            "range": "min:max",
        })

    def test_upper_bound_covers_the_whole_day(self):
        """Sans cela, "jusqu'au 31" exclurait tout ce qui a ete recu ce
        jour-la apres minuit, c'est-a-dire tout."""
        query = build_query({"date_to": "2026-01-31"}, to_date=fake_to_date)
        self.assertEqual(query["getDateReceived"], {
            "query": "2026-01-31T23:59:59",
            "range": "max",
        })

    def test_lower_bound_only(self):
        query = build_query({"date_from": "2026-01-01"}, to_date=fake_to_date)
        self.assertEqual(query["getDateReceived"], {
            "query": "2026-01-01T00:00:00",
            "range": "min",
        })

    def test_an_unreadable_date_is_ignored(self):
        """Une date mal saisie desactive ce critere, elle ne doit pas
        produire une requete invalide."""
        query = build_query({"date_from": "illisible"}, to_date=fake_to_date)
        self.assertNotIn("getDateReceived", query)

    def test_without_a_converter_dates_are_skipped(self):
        query = build_query({"date_from": "2026-01-01"})
        self.assertEqual(query, {})

    def test_the_vanillin_range_is_not_a_catalog_query(self):
        """getResult n'est qu'une colonne de metadonnees: la plage se
        resout ailleurs (results.sample_ids_in_range)."""
        query = build_query({"van_min": "2", "van_max": "5"},
                            to_date=fake_to_date)
        self.assertEqual(query, {})


class TestHiddenFields(unittest.TestCase):

    def test_only_active_filters_are_carried(self):
        fields = hidden_fields({"lot": "LOT-1", "origin": ""})
        self.assertEqual(fields, [{"name": PREFIX + "lot", "value": "LOT-1"}])

    def test_every_filter_can_be_carried(self):
        """La pagination passe par AJAX: un critere absent de ces champs
        serait perdu des la page 2."""
        filters = dict([(name, "x") for name in ALL_FILTERS])
        names = [f["name"] for f in hidden_fields(filters)]
        self.assertEqual(len(names), len(ALL_FILTERS))
        for name in ALL_FILTERS:
            self.assertIn(PREFIX + name, names)

    def test_nothing_to_carry(self):
        self.assertEqual(hidden_fields({}), [])


class TestIsActive(unittest.TestCase):

    def test_detects_an_active_filter(self):
        self.assertTrue(is_active({"lot": "LOT-1"}))
        self.assertFalse(is_active({}))


class TestColumns(unittest.TestCase):

    def test_the_document_asks_for_twenty_columns(self):
        self.assertEqual(len(build_columns()), 20)

    def test_column_order_follows_the_document(self):
        keys = list(build_columns().keys())
        self.assertEqual(keys[:5],
                         ["SampleCode", "Lot", "Client", "SampleType",
                          "Origin"])
        self.assertEqual(keys[-3:],
                         ["HPLCOperator", "MoistureOperator",
                          "WaterActivityOperator"])

    def test_every_column_has_a_title(self):
        for key, definition in build_columns().items():
            self.assertTrue(definition.get("title"),
                            "colonne sans intitule: %s" % key)

    def test_only_indexed_columns_are_sortable(self):
        """Un en-tete cliquable qui ne trie rien est pire qu'un en-tete
        inerte: l'utilisateur croit que le tri a eu lieu."""
        for key, definition in build_columns().items():
            if definition.get("sortable"):
                self.assertIn("index", definition,
                              "colonne triable sans index: %s" % key)

    def test_analysis_columns_are_never_sortable(self):
        """Un resultat d'analyse ne vit pas dans le sample_catalog."""
        columns = build_columns()
        for column_id, _keyword, _label in DASHBOARD_ANALYSES:
            self.assertFalse(columns[column_id].get("sortable"))

    def test_seven_analysis_columns(self):
        self.assertEqual(len(DASHBOARD_ANALYSES), 7)
        self.assertEqual(len(get_keywords()), 7)

    def test_keywords_are_unique(self):
        """Deux colonnes partageant un mot-cle afficheraient la meme
        valeur, sans que rien ne le signale."""
        keywords = get_keywords()
        self.assertEqual(len(keywords), len(set(keywords)))

    def test_keyword_lookup(self):
        self.assertEqual(get_keyword_for("Vanillin"), "VANILLINE")
        self.assertIsNone(get_keyword_for("Inconnue"))

    def test_metadata_map_covers_every_catalog_column(self):
        mapping = get_metadata_map()
        analysis_ids = [c for c, _k, _l in DASHBOARD_ANALYSES]
        for key in build_columns():
            if key in analysis_ids:
                continue
            self.assertIn(key, mapping,
                          "colonne sans attribut de brain: %s" % key)


class TestColumnHelp(unittest.TestCase):
    """Infobulles: chaque en-tete court doit avoir sa version longue."""

    def test_every_column_has_help(self):
        """Un en-tete abrege sans infobulle serait une perte seche: le
        sens complet n'existerait plus nulle part dans l'interface."""
        help_texts = get_column_help()
        for key in build_columns():
            self.assertIn(key, help_texts,
                          "colonne sans infobulle: %s" % key)

    def test_help_covers_exactly_the_columns(self):
        """Une entree d'aide orpheline signale une colonne supprimee
        dont l'infobulle a survecu."""
        self.assertEqual(sorted(dict(COLUMN_HELP).keys()),
                         sorted(build_columns().keys()))

    def test_labels_cover_exactly_the_columns(self):
        self.assertEqual(sorted(get_column_labels().keys()),
                         sorted(build_columns().keys()))


class TestScriptVersion(unittest.TestCase):
    """La version du script existe a DEUX endroits, et doit concorder.

    Le viewlet la reporte en parametre d'URL (`dashboard.js?v=N`) pour
    forcer le navigateur a recharger le fichier apres une modification;
    le script la publie dans `window.TRIMETA_DASHBOARD_VERSION` pour
    qu'on puisse verifier depuis la console ce qui tourne reellement.

    Si les deux divergent, l'invalidation du cache cesse d'etre fiable
    -- en silence, et c'est exactement le genre de panne qui fait
    croire qu'un correctif deploye n'a pas fonctionne.
    """

    def setUp(self):
        self.root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def read(self, *parts):
        path = os.path.join(self.root, *parts)
        self.assertTrue(os.path.exists(path), "fichier absent: %s" % path)
        return io.open(path, encoding="utf-8").read()

    def test_versions_match(self):
        script = self.read("browser", "resources", "dashboard.js")
        viewlet = self.read("dashboard", "viewlets.py")

        in_js = re.search(r"var VERSION = (\d+);", script)
        in_py = re.search(r"SCRIPT_VERSION = (\d+)", viewlet)

        self.assertIsNotNone(in_js, "VERSION introuvable dans dashboard.js")
        self.assertIsNotNone(
            in_py, "SCRIPT_VERSION introuvable dans viewlets.py")
        self.assertEqual(
            in_js.group(1), in_py.group(1),
            "dashboard.js annonce la version %s, le viewlet sert la %s: "
            "le cache du navigateur ne sera plus invalide correctement."
            % (in_js.group(1), in_py.group(1)))

    def test_script_carries_no_control_characters(self):
        """Une limite de mot d'expression reguliere, ecrite par megarde comme un
        vrai caractere backspace s'est deja glisse dans ce fichier. Il
        ne se voit pas a la lecture."""
        script = self.read("browser", "resources", "dashboard.js")
        for code in (7, 8, 11, 12, 27):
            self.assertNotIn(
                chr(code), script,
                "caractere de controle %d present dans dashboard.js" % code)


def test_suite():
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    for case in (TestReadFilters, TestBuildQuery, TestHiddenFields,
                 TestIsActive, TestColumns, TestColumnHelp,
                 TestScriptVersion):
        suite.addTest(loader.loadTestsFromTestCase(case))
    return suite
