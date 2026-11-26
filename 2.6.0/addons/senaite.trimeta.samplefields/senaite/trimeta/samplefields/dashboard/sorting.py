# -*- coding: utf-8 -*-
"""Tris globaux sur les metadonnees, avant la pagination du listing."""
import unicodedata

from senaite.trimeta.samplefields.compat import to_text
from senaite.trimeta.samplefields.dashboard.results import pick_result
from senaite.trimeta.samplefields.dashboard.results import to_number
from senaite.trimeta.samplefields.coa.validation import VALIDATED_STATES


def stable_id(brain):
    """Departage les egalites sans reveiller un objet ZODB."""
    return (to_text(getattr(brain, "getId", "")),
            to_text(getattr(brain, "UID", "")))


def sort_values(brains, value_for, descending=False):
    """Valeurs absentes en dernier dans les deux sens; egalites stables."""
    present, missing = [], []
    for brain in sorted(brains, key=stable_id):
        value = value_for(brain)
        if value is None:
            missing.append(brain)
        else:
            present.append((value, brain))
    present.sort(key=lambda entry: entry[0], reverse=descending)
    return [brain for _value, brain in present] + missing


def sort_sample_types(brains, descending=False):
    def value_for(brain):
        text = to_text(getattr(brain, "getSampleTypeTitle", "")).strip().lower()
        text = unicodedata.normalize("NFKD", text)
        value = u"".join(c for c in text if not unicodedata.combining(c))
        return value or None
    return sort_values(brains, value_for, descending)


def current_validation_date(brain):
    """Une ancienne validation n'est pas la validation d'un etat provisoire."""
    if getattr(brain, "review_state", "") not in VALIDATED_STATES:
        return None
    return getattr(brain, "getDateVerified", None) or None


def sort_validation_dates(brains, descending=False):
    return sort_values(brains, current_validation_date, descending)


def sort_received_dates(brains, descending=False):
    return sort_values(brains, lambda brain: getattr(
        brain, "getDateReceived", None) or None, descending)


def sort_vanillin(brains, results, keywords, descending=False):
    def value_for(brain):
        sample_id = to_text(getattr(brain, "getId", ""))
        value = pick_result(results.get(sample_id, {}), keywords)
        return to_number(value)
    return sort_values(brains, value_for, descending)
