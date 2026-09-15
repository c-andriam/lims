# -*- coding: utf-8 -*-
"""
Listes deroulantes de la section Assurance Qualite.

Les libelles numerotes (1) a (5) du cahier des charges correspondent
aux quatre vocabulaires ci-dessous plus le champ date:

    (1) Choix entre OK ou NOK          -> CONFORMITY_VOCAB
    (2) Choix entre 1, 2 ou 3          -> COUNT_VOCAB
    (3) Date                           -> champ date, pas de vocabulaire
    (4) Choix operateur (Contact labo) -> reference LabContact
    (5) Mail, papier, COA, Tableau     -> TRANSMISSION_VOCAB
"""

from zope.i18nmessageid import MessageFactory

_ = MessageFactory("senaite.trimeta.samplefields")

# Premiere entree des listes: les champs sont facultatifs, il faut pouvoir
# ne rien choisir, mais une ligne blanche ressemble a une erreur.
NOT_SPECIFIED = ("", u"— Non renseigné —")

# (1) Conformite
CONFORMITY_VOCAB = (
    NOT_SPECIFIED,
    ("OK", u"OK"),
    ("NOK", u"NOK"),
)

# (2) Nombre d'analyses / d'extractions
COUNT_VOCAB = (
    NOT_SPECIFIED,
    ("1", u"1"),
    ("2", u"2"),
    ("3", u"3"),
)

# (5) Mode de transmission des resultats
TRANSMISSION_VOCAB = (
    NOT_SPECIFIED,
    ("mail", u"Mail"),
    ("paper", u"Papier"),
    ("coa", u"COA"),
    ("table", u"Tableau"),
)


def as_displaylist(vocab_tuple):
    """Convertit un tuple de vocabulaire en DisplayList Archetypes."""
    from Products.Archetypes.public import DisplayList
    return DisplayList(list(vocab_tuple))
