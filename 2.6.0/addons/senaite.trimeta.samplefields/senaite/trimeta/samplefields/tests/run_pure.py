# -*- coding: utf-8 -*-
"""Execute les tests qui n'ont besoin ni de Zope ni de SENAITE.

    python senaite/trimeta/samplefields/tests/run_pure.py
    make test-pure          (depuis 2.6.0/)

Une bonne partie de l'add-on est de la logique pure: la declaration des
champs, les vocabulaires, la normalisation d'index, l'insertion ordonnee
de colonnes, la discrimination des adaptateurs de listing. Ce harnais
remplace les quelques symboles SENAITE importes par des doublures, ce
qui permet de verifier cette logique en une fraction de seconde, sur
n'importe quel poste, sans monter de container.

CE HARNAIS NE REMPLACE PAS `make test`.

Il ne prouve pas que l'add-on fonctionne dans SENAITE: les doublures
sont des approximations. Les tests d'installation du profil, de
catalogue, de schema sur un echantillon reel et de suggestions ont
besoin d'un vrai site et ne tournent que dans le container.

Si une doublure derive de la realite, l'import echoue bruyamment plutot
que de laisser passer un test faux: c'est pour cela qu'elles sont
volontairement minimales.
"""
import importlib.util
import os
import sys
import types
import unittest

# Racine du paquet: le repertoire parent de tests/
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def make_module(name, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


# --------------------------------------------------------------------
# Doublures
# --------------------------------------------------------------------

class StubWidget(object):
    def __init__(self, **kwargs):
        self.label = kwargs.get("label")
        self.description = kwargs.get("description")
        self.visible = kwargs.get("visible")
        self.__dict__.update(kwargs)


class StubField(object):
    """Reproduit le contrat Archetypes utilise par les tests."""

    def __init__(self, name, **kwargs):
        self._name = name
        self.required = kwargs.get("required", False)
        self.schemata = kwargs.get("schemata", "default")
        self.widget = kwargs.get("widget")
        self.vocabulary = kwargs.get("vocabulary")
        self.mode = kwargs.get("mode", "rw")
        self.__dict__.update(
            {k: v for k, v in kwargs.items()
             if k not in ("required", "schemata", "widget", "vocabulary",
                          "mode")})

    def getName(self):
        return self._name


def install_stubs():
    def implementer(*interfaces):
        return lambda cls: cls

    class Interface(object):
        pass

    def adapts(*interfaces):
        return None

    def indexer(*interfaces):
        return lambda fn: fn

    def MessageFactory(domain):
        def factory(text, **kwargs):
            return text
        return factory

    zope = make_module("zope")
    zope.interface = make_module("zope.interface",
                                 implementer=implementer,
                                 Interface=Interface)
    zope.component = make_module("zope.component", adapts=adapts)
    zope.i18nmessageid = make_module("zope.i18nmessageid",
                                     MessageFactory=MessageFactory)

    make_module("AccessControl", ClassSecurityInfo=lambda: None)

    products = make_module("Products")
    archetypes = make_module("Products.Archetypes")
    products.Archetypes = archetypes
    archetypes.public = make_module(
        "Products.Archetypes.public",
        StringField=StubField,
        FixedPointField=StubField,
        TextField=StubField,
        SelectionWidget=StubWidget,
        StringWidget=StubWidget,
        DecimalWidget=StubWidget,
        TextAreaWidget=StubWidget,
        DisplayList=lambda items: list(items),
    )

    at_ext = make_module("archetypes")
    at_ext.schemaextender = make_module("archetypes.schemaextender")
    # ExtensionField doit etre une classe distincte d'object, sinon
    # `class X(ExtensionField, StubField)` n'a pas de MRO coherent.
    class StubExtensionField(object):
        pass

    make_module("archetypes.schemaextender.field",
                ExtensionField=StubExtensionField)
    make_module("archetypes.schemaextender.interfaces",
                IOrderableSchemaExtender=Interface,
                ISchemaModifier=Interface)

    class FakeAPI(object):
        @staticmethod
        def get_object(obj):
            return obj

        @staticmethod
        def get_uid(obj):
            return getattr(obj, "uid", None)

        @staticmethod
        def get_object_by_uid(uid):
            raise LookupError(uid)

    bika = make_module("bika")
    bika.lims = make_module("bika.lims", api=FakeAPI())
    make_module("bika.lims.interfaces", IAnalysisRequest=Interface)
    make_module("bika.lims.browser")
    make_module("bika.lims.browser.fields", UIDReferenceField=StubField)
    make_module("bika.lims.browser.widgets", DateTimeWidget=StubWidget)

    senaite = make_module("senaite")
    senaite.app = make_module("senaite.app")
    senaite.app.listing = make_module("senaite.app.listing")
    make_module("senaite.app.listing.interfaces",
                IListingViewAdapter=Interface,
                IListingView=Interface)

    senaite.core = make_module("senaite.core")
    senaite.core.__path__ = []
    make_module("senaite.core.api")
    make_module("senaite.core.api.catalog",
                get_catalog=lambda name: None,
                get_indexes=lambda cat: [],
                get_columns=lambda cat: [],
                get_index=lambda cat, idx: None,
                add_index=lambda *a, **k: True,
                add_column=lambda *a, **k: True)
    make_module("senaite.core.catalog",
                CONTACT_CATALOG="contact_catalog",
                SAMPLE_CATALOG="sample_catalog")
    make_module("senaite.core.browser")
    make_module("senaite.core.browser.fields")
    make_module("senaite.core.browser.fields.datetime",
                DateTimeField=StubField)
    make_module("senaite.core.browser.widgets")
    make_module("senaite.core.browser.widgets.referencewidget",
                ReferenceWidget=StubWidget)

    make_module("plone")
    make_module("plone.indexer", indexer=indexer)


def install_package_shims():
    trimeta = make_module("senaite.trimeta")
    sys.modules["senaite"].trimeta = trimeta
    samplefields = make_module("senaite.trimeta.samplefields",
                               PRODUCT_NAME="senaite.trimeta.samplefields")
    samplefields.__path__ = [ROOT]
    trimeta.samplefields = samplefields
    # Les modules de test importent tests.base et tests.utils, qui
    # exigent un site Plone. On les remplace par des coquilles: seules
    # les classes de test PURES sont executees ici.
    tests = make_module("senaite.trimeta.samplefields.tests")
    tests.__path__ = [os.path.join(ROOT, "tests")]
    samplefields.tests = tests
    make_module("senaite.trimeta.samplefields.tests.base",
                TrimetaTestCase=unittest.TestCase)
    make_module("senaite.trimeta.samplefields.tests.utils",
                SampleFactory=object)

    for sub in ("listings", "qualitydata", "dashboard"):
        module = make_module(
            "senaite.trimeta.samplefields.{}".format(sub))
        module.__path__ = [os.path.join(ROOT, sub)]
        setattr(samplefields, sub, module)


def load(dotted, relpath):
    path = os.path.join(ROOT, relpath)
    spec = importlib.util.spec_from_file_location(dotted, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[dotted] = module
    spec.loader.exec_module(module)
    parent_name, _, leaf = dotted.rpartition(".")
    if parent_name in sys.modules:
        setattr(sys.modules[parent_name], leaf, module)
    return module


P = "senaite.trimeta.samplefields."

MODULES = [
    (P + "vocabularies", "vocabularies.py"),
    (P + "indexers", "indexers.py"),
    (P + "extender", "extender.py"),
    (P + "qualitydata.vocabularies", "qualitydata/vocabularies.py"),
    (P + "qualitydata.fields", "qualitydata/fields.py"),
    (P + "qualitydata.extender", "qualitydata/extender.py"),
    (P + "listings.base", "listings/base.py"),
    (P + "listings.samples", "listings/samples.py"),
    (P + "listings.worksheets", "listings/worksheets.py"),
    (P + "listings.reports", "listings/reports.py"),
    (P + "dashboard.results", "dashboard/results.py"),
    (P + "dashboard.filters", "dashboard/filters.py"),
    (P + "dashboard.columns", "dashboard/columns.py"),
]

# (fichier de test, classes qui n'ont pas besoin d'un site Plone)
PURE_CASES = [
    ("test_vocabularies.py",
     ["TestTemperatureVocabulary", "TestCodeArticleVocabulary"]),
    ("test_indexers.py", ["TestIndexStringNormalisation",
                          "TestIndexDateNormalisation",
                          "TestContactTitleResolution",
                          "TestReferenceUid"]),
    ("test_schema.py", ["TestExtenderDeclaration"]),
    ("test_qualitydata.py", ["TestQualityDataDeclaration"]),
    ("test_listings.py", None),   # tout le fichier est pur
    ("test_dashboard.py", None),  # idem
    ("test_dashboard_filters.py", None),
]


def load_test_module(filename):
    path = os.path.join(ROOT, "tests", filename)
    name = "trimeta_" + filename[:-3]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    install_stubs()
    install_package_shims()

    for dotted, relpath in MODULES:
        load(dotted, relpath)

    # suggestions.py a besoin de BTrees, absent hors Zope. Seule la
    # constante SUGGESTION_FIELDS est lue par les tests: on
    # l'extrait du source plutot que d'importer le module.
    import re
    src = open(os.path.join(ROOT, "suggestions.py"),
               encoding="utf-8").read()
    block = re.search(r"SUGGESTION_FIELDS = \((.*?)\)", src, re.S).group(1)
    fields = tuple(re.findall(r'"([^"]+)"', block))
    make_module(P + "suggestions", SUGGESTION_FIELDS=fields)

    # schema_modifier: idem, seule HIDDEN_NATIVE_FIELDS est lue.
    load(P + "schema_modifier", "schema_modifier.py")

    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    for filename, classnames in PURE_CASES:
        module = load_test_module(filename)
        if classnames is None:
            suite.addTest(module.test_suite())
            continue
        for classname in classnames:
            suite.addTest(
                loader.loadTestsFromTestCase(getattr(module, classname)))

    result = unittest.TextTestRunner(verbosity=1).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
