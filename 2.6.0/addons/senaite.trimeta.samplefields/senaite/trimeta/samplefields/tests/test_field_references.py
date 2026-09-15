# -*- coding: utf-8 -*-
"""
Tout nom de champ cite en chaine existe bien dans un extender.

Le probleme
-----------
Les champs du Sample sont declares une fois, dans extender.py et
qualitydata/extender.py. Mais ils sont DESIGNES PAR LEUR NOM, sous
forme de chaine, dans au moins cinq autres endroits:

    suggestions.SUGGESTION_FIELDS       memorisation des valeurs libres
    indexers.get_field_value(..., "X")  alimentation du catalogue
    coa/filename.SAMPLE_CODE_FIELD      nom du fichier COA
    listings/base.get_sample_code       colonne Code echantillon
    COA-Trimeta.pt  model/X             contenu du certificat

Aucun de ces liens n'est verifie par l'interpreteur. Renommer un champ
dans l'extender, ou faire une faute de frappe dans l'une de ces
chaines, ne leve rien du tout:

- la suggestion ne se memorise plus, et l'operateur retape son numero
  de lot a chaque echantillon;
- la colonne de catalogue se remplit de chaines vides;
- une ligne du certificat d'analyse sort blanche.

Ce dernier cas est le plus grave: le COA est un document qualite remis
au client. Une ligne vide y passe inapercue jusqu'a ce que quelqu'un la
cherche.

Ce que fait ce module
---------------------
Il lit la liste reelle des champs declares par les deux extenders et
verifie que chaque chaine citee ailleurs y correspond.

Complement de test_catalog_wiring.py, qui verrouille l'autre bout de la
chaine: du nom d'index jusqu'a la colonne du tableau de bord.
"""

import io
import os
import re
import unittest

from senaite.trimeta.samplefields.coa import filename as coa_filename
from senaite.trimeta.samplefields.extender import ReceptionFieldsExtender
from senaite.trimeta.samplefields.qualitydata.extender import get_all_fields
from senaite.trimeta.samplefields.suggestions import SUGGESTION_FIELDS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def our_field_names():
    """Noms de tous les champs ajoutes au Sample par l'add-on."""
    names = set(f.getName() for f in ReceptionFieldsExtender.fields)
    names.update(f.getName() for f in get_all_fields())
    return names


# Identifiants qui doivent rester uniques par echantillon. Les proposer
# en suggestion encouragerait la reutilisation accidentelle d'une
# reference unique -- deux echantillons portant le meme code, et toute
# la tracabilite qui s'effondre. L'exclusion est une DECISION, pas un
# oubli: ce module la protege d'un ajout distrait.
MUST_NOT_BE_SUGGESTED = ("SampleCode", "AnalysisSheetNumber",
                         "EntryVoucher")

# Ce que le gabarit COA lit sur le SuperModel sans que cela vienne de
# notre extender: champs natifs de l'AnalysisRequest et attributs de
# l'objet. Releves sur senaite.core v2.6.0 et sur le gabarit natif
# Default.pt, dont COA-Trimeta.pt reprend la structure.
NATIVE_MODEL_NAMES = frozenset([
    "getId",
    "absolute_url",
    "SampleType",
    "Specification",
    "DateReceived",
    "Client",
    "ClientSampleID",
])


class TestFieldNamesAreReal(unittest.TestCase):

    def setUp(self):
        self.fields = our_field_names()

    def test_the_test_is_not_vacuous(self):
        """Un controle de coherence qui ne lit plus rien passe au vert
        sans rien verifier."""
        self.assertGreaterEqual(len(self.fields), 60)
        self.assertGreaterEqual(len(SUGGESTION_FIELDS), 10)

    def test_every_suggested_field_exists(self):
        """Une suggestion posee sur un champ inexistant ne memorise
        jamais rien. Le cahier des charges demande explicitement le
        rajout memorise sur les lots de solvants."""
        for name in SUGGESTION_FIELDS:
            self.assertIn(
                name, self.fields,
                "SUGGESTION_FIELDS cite '%s', qui n'est declare par "
                "aucun extender" % name)

    def test_unique_identifiers_are_never_suggested(self):
        """Decision documentee dans suggestions.py, protegee ici."""
        for name in MUST_NOT_BE_SUGGESTED:
            self.assertIn(
                name, self.fields,
                "'%s' n'existe plus: mettre a jour "
                "MUST_NOT_BE_SUGGESTED" % name)
            self.assertNotIn(
                name, SUGGESTION_FIELDS,
                "'%s' doit rester unique par echantillon: le proposer "
                "en suggestion encouragerait la reutilisation "
                "accidentelle d'une reference unique" % name)

    def test_every_field_read_by_an_indexer_exists(self):
        """Un indexeur lisant un champ absent remplit sa colonne de
        chaines vides, sans erreur."""
        source = io.open(os.path.join(ROOT, "indexers.py"),
                         encoding="utf-8").read()
        read = re.findall(r'get_field_value\(instance,\s*"(\w+)"', source)
        self.assertGreaterEqual(len(read), 8)
        for name in read:
            # SampleType est natif: il n'est pas ajoute par nous, mais
            # lu par getTrimetaSampleTypeUID.
            if name == "SampleType":
                continue
            self.assertIn(
                name, self.fields,
                "indexers.py lit le champ '%s', qui n'est declare par "
                "aucun extender" % name)

    def test_the_coa_filename_field_exists(self):
        self.assertIn(coa_filename.SAMPLE_CODE_FIELD, self.fields)

    def test_the_listing_reads_an_existing_field(self):
        """listings/base.get_sample_code cite le nom en dur."""
        source = io.open(os.path.join(ROOT, "listings", "base.py"),
                         encoding="utf-8").read()
        read = re.findall(r'getField\("(\w+)"\)', source)
        self.assertGreaterEqual(len(read), 1)
        for name in read:
            self.assertIn(
                name, self.fields,
                "listings/base.py lit le champ '%s', inexistant" % name)


class TestCoaTemplateFields(unittest.TestCase):
    """Le certificat d'analyse ne lit que des champs qui existent."""

    def setUp(self):
        self.fields = our_field_names()
        path = os.path.join(ROOT, "coa", "templates", "reports",
                            "COA-Trimeta.pt")
        self.template = io.open(path, encoding="utf-8").read()

    def collect(self):
        """Noms lus sur le SuperModel dans le gabarit.

        Deux ecritures cohabitent dans un gabarit TAL, et le cahier des
        charges en utilise les deux:

            model/Designation            chemin TAL
            model.AnalysisStart          expression python:
        """
        names = set(re.findall(r"model/(\w+)", self.template))
        names.update(re.findall(r"model\.(\w+)", self.template))
        # Accesseurs natifs appeles comme methodes: hors de notre
        # perimetre, ils appartiennent a l'AnalysisRequest.
        return set(n for n in names if not n.startswith("get"))

    def test_the_test_is_not_vacuous(self):
        self.assertGreaterEqual(len(self.collect()), 10)

    def test_every_field_read_by_the_coa_exists(self):
        """Une ligne du COA lisant un champ inexistant sort BLANCHE.

        `tal:content="model/Designation|nothing"` : le `|nothing` evite
        l'erreur, donc rien ne signale la faute. Sur un document
        qualite remis au client, c'est le pire des deux mondes -- le
        rapport part, incomplet, et personne ne le voit.
        """
        for name in sorted(self.collect()):
            self.assertTrue(
                name in self.fields or name in NATIVE_MODEL_NAMES,
                "COA-Trimeta.pt lit 'model/%s', qui n'est ni un champ "
                "de l'add-on ni un nom natif connu. Soit c'est une "
                "faute de frappe, soit il faut l'ajouter a "
                "NATIVE_MODEL_NAMES apres l'avoir verifie sur "
                "l'instance." % name)

    def test_the_document_requested_fields_are_all_present(self):
        """Les champs que le cahier des charges demande d'ajouter au
        COA, section par section. Les retirer par megarde ferait
        regresser la demande D5 sans qu'aucun autre test ne bronche."""
        required = (
            "ReceptionWeight",      # Sample weight
            "AnalysisStart",        # Start of Analyses
            "AnalysisEnd",          # End of Analyses
            "FinalValidator",       # Validated by
            "AnalysisSheetNumber",  # Report reference
            "ReceptionTemperature",
            "Designation",
            "Texture",
            "Color",
            "Aroma",
        )
        present = self.collect()
        for name in required:
            self.assertIn(
                name, present,
                "le cahier des charges demande '%s' sur le COA: il a "
                "disparu du gabarit" % name)

    def test_published_by_carries_no_mailto(self):
        """Demande explicite du cahier des charges: supprimer l'adresse
        mail du rapport.

        On retire les commentaires XML avant de chercher: le gabarit
        explique justement en commentaire pourquoi le lien a ete
        enleve, et cette explication doit pouvoir y rester.
        """
        markup = re.sub(r"<!--.*?-->", "", self.template, flags=re.S)
        self.assertNotIn("mailto", markup.lower())


def test_suite():
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    for case in (TestFieldNamesAreReal, TestCoaTemplateFields):
        suite.addTest(loader.loadTestsFromTestCase(case))
    return suite
