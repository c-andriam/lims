# -*- coding: utf-8 -*-
"""
Vocabularies for the Reception section fields.

Designation et Origin sont en texte libre, avec suggestions partagees
(voir suggestions.py). Received By est une reference vers les contacts
du laboratoire.

Listes fixes: temperature de reception (15-31 degC), condition de
l'echantillon et etat de l'emballage. Les codes article initiaux sont
completes par les nouveaux codes memorises apres sauvegarde.
"""

from zope.i18nmessageid import MessageFactory
from senaite.trimeta.samplefields.compat import to_text

_ = MessageFactory("senaite.trimeta.samplefields")

# Reception Temperature: fixed integer range 15-31 degC
TEMPERATURE_VOCAB = tuple(
    (str(i), u"{} \u00b0C".format(i)) for i in range(15, 32)
)

# Code article: codes produit initiaux (remplace l'ancien champ
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


def item_code_choices(remembered=()):
    """Codes livres puis codes memorises, sans doublon, AUTRES en dernier."""
    known = set(key for key, _label in CODE_ARTICLE_VOCAB)
    extras = set(to_text(value).strip() for value in remembered or ())
    extras = sorted((value for value in extras if value and value not in known),
                    key=lambda value: (value.lower(), value))
    return (list(CODE_ARTICLE_VOCAB[:-1]) + [(value, value) for value in extras]
            + list(CODE_ARTICLE_VOCAB[-1:]))

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
