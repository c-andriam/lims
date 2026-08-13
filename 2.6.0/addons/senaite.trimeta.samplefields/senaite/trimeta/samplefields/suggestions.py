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

# The 5 free-text fields that get dynamic suggestions.
SUGGESTION_FIELDS = (
    "Designation",
    "SampleCondition",
    "PackagingCondition",
    "Origin",
    "Receptionist",
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


def on_sample_added(obj, event):
    """Event subscriber: fired when a Sample (AnalysisRequest) is
    created. Reads the 5 free-text fields and remembers any non-empty
    value as a future suggestion.
    """
    try:
        for fieldname in SUGGESTION_FIELDS:
            field = obj.getField(fieldname)
            if field is None:
                continue
            value = field.get(obj)
            if value:
                add_suggestion(fieldname, value)
    except Exception:
        # Never let suggestion-tracking break sample creation.
        logger.exception(
            "### TRIMETA: erreur non bloquante lors de l'enregistrement "
            "des suggestions pour l'echantillon %s ###",
            getattr(obj, "getId", lambda: "?")(),
        )
