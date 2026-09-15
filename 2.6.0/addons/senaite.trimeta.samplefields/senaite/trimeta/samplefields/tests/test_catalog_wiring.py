# -*- coding: utf-8 -*-
"""
Coherence du cablage catalogue.

Le probleme
-----------
Exposer une valeur au catalogue demande QUATRE declarations qui doivent
s'accorder, reparties dans trois fichiers:

    catalog.py       le nom de l'index ou de la colonne
    indexers.py      la fonction decoree @indexer qui porte ce nom
    configure.zcml   <adapter name="..." factory=".indexers...." />
    dashboard/       la colonne qui lira la valeur sur le brain

En oublier une, ou faire une faute de frappe dans l'une, ne leve
AUCUNE erreur. Plone ne trouve pas l'adaptateur nomme, l'index reste
vide, la colonne du tableau de bord reste blanche -- et rien, nulle
part, n'explique pourquoi. C'est le piege le plus couteux de cet
add-on: il coute une session de deboguage a chaque fois, et il est
invisible a la relecture.

Ce que fait ce module
---------------------
Il relit les trois fichiers et verifie qu'ils disent la meme chose. Une
faute de frappe devient une erreur de test au lieu d'une colonne vide
en production.

Le cas particulier des colonnes natives
---------------------------------------
Le tableau de bord lit aussi des colonnes que senaite.core fournit
deja (getClientSampleID, getDateReceived...). Elles n'ont rien a faire
dans notre catalog.py -- les recreer serait au mieux inutile, au pire
une collision avec une version future de SENAITE.

Elles sont donc listees explicitement plus bas. Cette liste n'est pas
une redite: c'est l'inventaire de ce sur quoi l'add-on PARIE cote
amont. Ajouter une colonne au tableau de bord sans la declarer ni ici
ni dans catalog.py fait echouer le test, ce qui oblige a trancher --
est-elle native, ou faut-il la creer ?
"""

import os
import re
import unittest
import xml.etree.ElementTree as ET

from senaite.trimeta.samplefields import catalog
from senaite.trimeta.samplefields import indexers
from senaite.trimeta.samplefields.dashboard import columns as cols

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ZOPE_NS = "{http://namespaces.zope.org/zope}"

# Colonnes de metadonnees fournies par senaite.core sur le
# sample_catalog, verifiees sur l'instance avec `make dashboard-info`.
NATIVE_COLUMNS = frozenset([
    "getClientSampleID",     # le "Lot" du cahier des charges
    "getClientTitle",
    "getSampleTypeTitle",
    "getDateReceived",
    "getDateVerified",
])

# Index fournis par senaite.core sur le sample_catalog.
#
# getSampleTypeTitle et getSampleTypeUID n'y figurent PAS: ce sont des
# colonnes, pas des index -- d'ou notre getTrimetaSampleTypeUID. Voir
# le commentaire de catalog.py.
NATIVE_INDEXES = frozenset([
    "getClientSampleID",
    "getClientTitle",
    "getClientUID",
    "getDateReceived",
    "getDateVerified",
    "getId",
])


def read_zcml_adapters():
    """{nom de l'adaptateur: suffixe de la factory} du configure.zcml.

    Ne retient que les adaptateurs nommes pointant sur .indexers: ce
    sont les seuls que ce module a vocation a verifier.
    """
    tree = ET.parse(os.path.join(ROOT, "configure.zcml"))
    found = {}
    for element in tree.getroot().iter(ZOPE_NS + "adapter"):
        name = element.get("name")
        factory = element.get("factory") or ""
        if not name or not factory.startswith(".indexers."):
            continue
        found[name] = factory[len(".indexers."):]
    return found


def declared_indexer_names():
    """Noms devant exister en indexeur: nos index et nos colonnes."""
    names = set()
    for _catalog_id, indexes, columns in catalog.CATALOGS:
        for index_id, _index_type, _attrs in indexes:
            names.add(index_id)
        names.update(columns)
    return names


class TestCatalogWiring(unittest.TestCase):
    """catalog.py, indexers.py et configure.zcml disent la meme chose."""

    def setUp(self):
        self.adapters = read_zcml_adapters()
        self.declared = declared_indexer_names()

    def test_the_test_is_not_vacuous(self):
        """Garde-fou. Un test de coherence qui ne lit plus rien passe au
        vert sans rien verifier: c'est pire qu'une absence de test,
        parce qu'il inspire confiance."""
        self.assertGreaterEqual(len(self.declared), 8)
        self.assertGreaterEqual(len(self.adapters), 8)

    def test_every_declared_name_has_an_indexer(self):
        """Sans fonction @indexer, l'index reste vide en silence."""
        for name in sorted(self.declared):
            function = getattr(indexers, name, None)
            self.assertIsNotNone(
                function,
                "'%s' est declare dans catalog.py mais aucune fonction "
                "de ce nom n'existe dans indexers.py" % name)

    def test_every_declared_name_is_registered_in_zcml(self):
        """Sans <adapter name=...>, Plone ne trouve jamais l'indexeur."""
        for name in sorted(self.declared):
            self.assertIn(
                name, self.adapters,
                "'%s' est declare dans catalog.py mais n'a pas de "
                "<adapter name=\"%s\" /> dans configure.zcml" % (name, name))

    def test_adapter_name_matches_its_factory(self):
        """`name` et `factory` doivent porter le meme nom.

        `<adapter name="getOrigin" factory=".indexers.getSampleCode" />`
        ne leve rien: Plone enregistre simplement le mauvais indexeur,
        et la colonne affiche la valeur d'un autre champ. Une faute
        plus sournoise qu'une colonne vide, parce qu'elle donne une
        valeur -- fausse.
        """
        for name, factory in sorted(self.adapters.items()):
            self.assertEqual(
                name, factory,
                "l'adaptateur '%s' pointe sur .indexers.%s: le nom et la "
                "factory doivent coincider" % (name, factory))

    def test_no_adapter_without_a_declaration(self):
        """Un indexeur enregistre mais absent de catalog.py alimente un
        index qui n'existe pas: travail fait a chaque sauvegarde
        d'echantillon, pour rien."""
        for name in sorted(self.adapters):
            self.assertIn(
                name, self.declared,
                "'%s' est enregistre dans configure.zcml mais n'est "
                "declare ni en index ni en colonne dans catalog.py"
                % name)

    def test_indexers_module_exposes_nothing_unregistered(self):
        """Une fonction @indexer oubliee en cours de route ne sert a
        rien: elle n'est appelee que si elle est enregistree."""
        pattern = re.compile(r"^def (get\w+)\(instance\)", re.M)
        source = open(os.path.join(ROOT, "indexers.py")).read()
        for name in pattern.findall(source):
            self.assertIn(
                name, self.adapters,
                "indexers.%s existe mais n'est enregistre nulle part "
                "dans configure.zcml" % name)


class TestDashboardWiring(unittest.TestCase):
    """Le tableau de bord ne lit que des colonnes qui existent."""

    def setUp(self):
        self.declared = declared_indexer_names()

    def test_every_dashboard_column_reads_an_existing_metadata_column(self):
        """Une colonne du tableau qui lit un attribut inexistant sur le
        brain reste blanche, sans la moindre erreur."""
        for key, attr in sorted(cols.get_metadata_map().items()):
            self.assertTrue(
                attr in self.declared or attr in NATIVE_COLUMNS,
                "la colonne '%s' du tableau de bord lit '%s', qui n'est "
                "ni declare dans catalog.py ni connu comme colonne "
                "native. Soit il faut le creer, soit l'ajouter a "
                "NATIVE_COLUMNS apres l'avoir vu dans "
                "`make dashboard-info`." % (key, attr))

    def test_every_sortable_column_really_has_an_index(self):
        """Un en-tete cliquable qui ne trie rien est pire qu'un en-tete
        inerte: l'utilisateur croit que le tri a eu lieu et lit le
        tableau de travers."""
        our_indexes = set()
        for _catalog_id, indexes, _columns in catalog.CATALOGS:
            for index_id, _index_type, _attrs in indexes:
                our_indexes.add(index_id)

        for key, definition in cols.build_columns().items():
            if not definition.get("sortable"):
                continue
            index = definition.get("index")
            self.assertIsNotNone(
                index,
                "la colonne '%s' est declaree triable sans index" % key)
            self.assertTrue(
                index in our_indexes or index in NATIVE_INDEXES,
                "la colonne '%s' trie sur '%s', qui n'est un index ni "
                "chez nous ni chez senaite.core" % (key, index))

    def test_unsortable_columns_declare_it(self):
        """senaite.app.listing rend l'en-tete cliquable par defaut."""
        for key, definition in cols.build_columns().items():
            self.assertIn(
                "sortable", definition,
                "la colonne '%s' ne dit pas si elle est triable" % key)

    def test_every_column_has_a_tooltip(self):
        """Vingt en-tetes courts ne tiennent que si le sens complet est
        rendu au survol."""
        help_map = cols.get_column_help()
        for key in cols.build_columns():
            self.assertIn(
                key, help_map,
                "la colonne '%s' n'a pas d'infobulle dans COLUMN_HELP"
                % key)


def test_suite():
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    for case in (TestCatalogWiring, TestDashboardWiring):
        suite.addTest(loader.loadTestsFromTestCase(case))
    return suite
