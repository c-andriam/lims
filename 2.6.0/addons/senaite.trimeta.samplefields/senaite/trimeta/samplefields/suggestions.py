# -*- coding: utf-8 -*-
"""
Shared, persistent suggestion storage for the free-text Reception
fields (Designation, Sample Condition, Packaging Condition, Origin,
Received By).

Every value a user types and successfully validates on a new sample
is automatically remembered here, and offered as an autocomplete
suggestion to every user/workstation afterwards (until manually
removed).

Storage: a nested OOBTree kept as an annotation on the Plone site
root, so it is shared across all users and persists in the ZODB
(no separate database needed).
"""

import logging

from BTrees.OOBTree import OOBTree
from zope.annotation.interfaces import IAnnotations

logger = logging.getLogger("senaite.trimeta.samplefields")

STORAGE_KEY = "senaite.trimeta.samplefields.suggestions"

# The free-text fields that get dynamic suggestions. "Receptionist"
# was removed: it is now a reference field pointing to existing
# LabContacts, not a free-text suggestion field.
#
# Deliberately EXCLUDED: SampleCode, AnalysisSheetNumber, EntryVoucher.
# These must stay unique per record; surfacing old values as
# suggestions would risk encouraging accidental duplicate reuse of
# a unique identifier.
SUGGESTION_FIELDS = (
    # Section Reception / Analyse
    "Designation",
    "SampleCondition",
    "PackagingCondition",
    "Origin",
    "SupplierCustomerDetail",
    "Contract",
    "Aroma",
    "Color",
    "Texture",
    "AromaDevelopment",
    # Section Assurance Qualite. Le cahier des charges demande
    # explicitement un "rajout memorise" sur les lots de solvants: un
    # meme lot sert a des dizaines d'echantillons, le retaper a chaque
    # fois serait une source d'erreur de saisie.
    "EthanolLot",
    "AcetonitrileLot",
    "HPLCWaterLot",
    "IsopropanolLot",
    "ColumnSerialNumber",
    "LampSerialNumber",
)


def _get_portal():
    from bika.lims import api
    return api.get_portal()


def get_storage():
    """Return the root OOBTree, creating it if needed."""
    portal = _get_portal()
    annotations = IAnnotations(portal)
    if annotations.get(STORAGE_KEY) is None:
        annotations[STORAGE_KEY] = OOBTree()
    return annotations[STORAGE_KEY]


def _get_field_bucket(storage, fieldname):
    if storage.get(fieldname) is None:
        storage[fieldname] = OOBTree()
    return storage[fieldname]


def add_suggestion(fieldname, value):
    """Remember a value as a future suggestion for this field."""
    if fieldname not in SUGGESTION_FIELDS:
        return
    value = (value or u"").strip()
    if not value:
        return
    storage = get_storage()
    bucket = _get_field_bucket(storage, fieldname)
    # OOBTree used as an ordered set: value -> True
    bucket[value] = True


def remove_suggestion(fieldname, value):
    """Remove a suggestion (e.g. via the small 'x' button in the UI)."""
    if fieldname not in SUGGESTION_FIELDS:
        return
    storage = get_storage()
    bucket = _get_field_bucket(storage, fieldname)
    if value in bucket:
        del bucket[value]


def list_suggestions(fieldname):
    """Return the sorted list of suggestions for a field."""
    if fieldname not in SUGGESTION_FIELDS:
        return []
    storage = get_storage()
    bucket = _get_field_bucket(storage, fieldname)
    return sorted(bucket.keys(), key=lambda s: s.lower())


def remember_field_values(obj):
    """Parcourt les champs a suggestion et memorise les valeurs saisies.

    Ne leve jamais: memoriser une suggestion est un confort de saisie,
    pas une donnee metier. Une panne du magasin ne doit ni empecher la
    creation d'un echantillon, ni faire echouer un enregistrement.

    :returns: la liste des champs effectivement memorises.
    """
    remembered = []
    try:
        for fieldname in SUGGESTION_FIELDS:
            field = obj.getField(fieldname)
            if field is None:
                # Champ absent du schema: l'objet a ete cree avant
                # l'ajout du champ, ou le schema n'est pas etendu.
                continue
            value = field.get(obj)
            if value:
                add_suggestion(fieldname, value)
                remembered.append(fieldname)
    except Exception:
        logger.exception(
            "Enregistrement des suggestions impossible pour "
            "l'echantillon %s",
            getattr(obj, "getId", lambda: "?")(),
        )
        return remembered

    if remembered:
        logger.debug("Suggestions enregistrees pour %s: %s",
                     getattr(obj, "getId", lambda: "?")(),
                     ", ".join(remembered))
    return remembered


def on_sample_added(obj, event):
    """Creation d'un echantillon: memorise les champs de reception."""
    remember_field_values(obj)


def on_sample_modified(obj, event):
    """Modification d'un echantillon: memorise les champs saisis apres
    coup.

    Indispensable pour la section Assurance Qualite: les lots de
    solvants et les numeros de serie sont renseignes une fois l'analyse
    faite, donc bien apres la creation de l'echantillon. Sans cet
    abonne, le "rajout memorise" demande sur ces champs ne se
    declencherait jamais.
    """
    remember_field_values(obj)
