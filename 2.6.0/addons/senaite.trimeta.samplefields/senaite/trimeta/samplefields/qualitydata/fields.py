# -*- coding: utf-8 -*-
"""
Fabriques de champs pour la section Assurance Qualite.

Le cahier des charges decrit 41 champs qui se ramenent a cinq formes
seulement. Plutot que 41 blocs copies-colles -- ou une faute de frappe
passe inapercue et ou changer une regle commune demande 41 corrections
-- chaque forme est ici une fonction.

Toutes les fabriques posent les memes invariants:

- `required=False` : le cahier des charges impose que tous les champs de
  cette section soient facultatifs;
- `schemata=SCHEMATA` : ils atterrissent tous dans le meme onglet;
- `visible=QA_VISIBLE` : visibles en consultation et modification, mais
  masques a la creation de l'echantillon, puisqu'ils sont renseignes
  apres l'analyse.
"""

from AccessControl import ClassSecurityInfo
from Products.Archetypes.public import SelectionWidget
from Products.Archetypes.public import StringWidget
from Products.Archetypes.public import TextAreaWidget
from Products.Archetypes.public import TextField
from archetypes.schemaextender.field import ExtensionField
from bika.lims.browser.widgets import DateTimeWidget
from senaite.core.browser.widgets.referencewidget import ReferenceWidget
from senaite.core.catalog import CONTACT_CATALOG
from zope.i18nmessageid import MessageFactory

from senaite.trimeta.samplefields.extender import ExtDateTimeField
from senaite.trimeta.samplefields.extender import ExtStringField
from senaite.trimeta.samplefields.extender import ExtUIDReferenceField
from senaite.trimeta.samplefields.qualitydata import vocabularies as vocab

_ = MessageFactory("senaite.trimeta.samplefields")

# Onglet unique de la section.
SCHEMATA = "AssuranceQualite"

# Masque a la creation, visible ensuite. Voir le docstring du module.
QA_VISIBLE = {
    "edit": "visible",
    "view": "visible",
    "add": "invisible",
}


class ExtTextField(ExtensionField, TextField):
    """Champ texte multiligne extensible."""
    security = ClassSecurityInfo()


def date_field(name, label):
    """(3) Une date, sans heure.

    L'heure n'apporte rien ici: ce sont des dates d'operation et de
    verification, pas des horodatages de tracabilite.
    """
    return ExtDateTimeField(
        name,
        required=False,
        mode="rw",
        schemata=SCHEMATA,
        widget=DateTimeWidget(
            label=label,
            show_time=False,
            visible=QA_VISIBLE,
            render_own_label=True,
        ),
    )


def operator_field(name, label, description=None):
    """(4) Un operateur, choisi parmi les contacts du laboratoire.

    Meme mecanisme que le champ "Received By" de la section Reception:
    une reference vers un LabContact existant, pas du texte libre. Les
    operateurs restent ainsi une donnee unique, modifiable en un seul
    endroit.
    """
    return ExtUIDReferenceField(
        name,
        required=False,
        schemata=SCHEMATA,
        allowed_types=("LabContact",),
        mode="rw",
        widget=ReferenceWidget(
            visible=QA_VISIBLE,
            label=label,
            description=description or u"",
            render_own_label=True,
            ui_item="Title",
            catalog=CONTACT_CATALOG,
            query={
                "portal_type": "LabContact",
                "is_active": True,
                "sort_on": "sortable_title",
                "sort_order": "ascending",
            },
            columns=[
                {"name": "Title", "label": _(u"Name")},
            ],
        ),
    )


def conformity_field(name, label):
    """(1) Conformite: OK ou NOK.

    La valeur vide est proposee volontairement en premier: le champ est
    facultatif, et laisser "OK" par defaut ferait passer pour verifie ce
    qui ne l'a pas ete.
    """
    return ExtStringField(
        name,
        required=False,
        vocabulary=vocab.as_displaylist(vocab.CONFORMITY_VOCAB),
        schemata=SCHEMATA,
        widget=SelectionWidget(
            visible=QA_VISIBLE,
            format="select",
            label=label,
        ),
    )


def count_field(name, label):
    """(2) Nombre d'analyses ou d'extractions: 1, 2 ou 3."""
    return ExtStringField(
        name,
        required=False,
        vocabulary=vocab.as_displaylist(vocab.COUNT_VOCAB),
        schemata=SCHEMATA,
        widget=SelectionWidget(
            visible=QA_VISIBLE,
            format="select",
            label=label,
        ),
    )


def choice_field(name, label, vocabulary):
    """(5) Choix dans une liste fixe quelconque."""
    return ExtStringField(
        name,
        required=False,
        vocabulary=vocab.as_displaylist(vocabulary),
        schemata=SCHEMATA,
        widget=SelectionWidget(
            visible=QA_VISIBLE,
            format="select",
            label=label,
        ),
    )


def text_field(name, label, description=None):
    """Texte court libre (numero de lot, numero de serie).

    Les champs crees ici peuvent etre inscrits dans SUGGESTION_FIELDS
    pour beneficier du "rajout memorise" demande sur les lots de
    solvants.
    """
    return ExtStringField(
        name,
        required=False,
        searchable=True,
        schemata=SCHEMATA,
        widget=StringWidget(
            visible=QA_VISIBLE,
            label=label,
            description=description or u"",
        ),
    )


def remarks_field(name, label, description=None):
    """Texte long libre (remarques, actions correctives)."""
    return ExtTextField(
        name,
        required=False,
        default_content_type="text/plain",
        allowable_content_types=("text/plain",),
        default_output_type="text/plain",
        schemata=SCHEMATA,
        widget=TextAreaWidget(
            visible=QA_VISIBLE,
            label=label,
            description=description or u"",
            rows=4,
        ),
    )
