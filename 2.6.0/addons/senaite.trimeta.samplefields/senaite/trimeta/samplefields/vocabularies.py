# -*- coding: utf-8 -*-
"""
Vocabularies for the Reception section fields.

Designation et Origin sont en texte libre, avec suggestions partagees
(voir suggestions.py). Received By est une reference vers les contacts
du laboratoire.

Listes fixes: temperature de reception (15-31 degC), code article, et
les deux listes imposees par le cahier des charges -- condition de
l'echantillon et etat de l'emballage.
"""

from zope.i18nmessageid import MessageFactory

_ = MessageFactory("senaite.trimeta.samplefields")

# Reception Temperature: fixed integer range 15-31 degC
TEMPERATURE_VOCAB = tuple(
    (str(i), u"{} \u00b0C".format(i)) for i in range(15, 32)
)

# Code article: liste fixe de codes produit (remplace l'ancien champ
# "Reference de l'echantillon", juge redondant).
CODE_ARTICLE_VOCAB = (
    ("V-GNN", "V-GNN"),
    ("V-GTK", "V-GTK"),
    ("V-RAF", "V-RAF"),
    ("V-RBF", "V-RBF"),
    ("V-RCF", "V-RCF"),
    ("V-LLB", "V-LLB"),
    ("AUTRES", "AUTRES"),
)

# Condition de l'echantillon (cahier des charges: "conforme - non
# conforme", champ obligatoire). Les valeurs enregistrees sont les
# libelles eux-memes: les echantillons deja saisis ("Conforme") restent
# valides sans migration. L'entree vide oblige a un choix explicite: sans
# elle, "Conforme" serait preselectionne sans que personne l'ait decide.
SAMPLE_CONDITION_VOCAB = (
    ("", u"— Choisir —"),
    ("Conforme", u"Conforme"),
    ("Non conforme", u"Non conforme"),
)

# Etat de l'emballage (cahier des charges: "sous vide, sachet zip, kraft,
# autres"). "Autres" est le choix "Autre..." du widget SelectOtherWidget
# de senaite.core, qui ouvre une saisie libre.
PACKAGING_CONDITION_VOCAB = (
    ("Sous vide", u"Sous vide"),
    ("Sachet zip", u"Sachet zip"),
    ("Kraft", u"Kraft"),
)


def as_displaylist(vocab_tuple):
    """Convert a vocabulary tuple into an Archetypes DisplayList."""
    from Products.Archetypes.public import DisplayList
    return DisplayList(list(vocab_tuple))
