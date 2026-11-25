# -*- coding: utf-8 -*-
"""Affectation metier d'un contact du laboratoire a chaque analyse."""
import hashlib
import json
import logging

from bika.lims import api
from senaite.trimeta.samplefields.compat import to_text

FIELD = "AssignedLabAnalyst"
EDIT_STATES = ("registered", "unassigned", "assigned")
logger = logging.getLogger("senaite.trimeta.samplefields")


def lab_contacts(active_only=True):
    from senaite.core.catalog import CONTACT_CATALOG
    query = {"portal_type": "LabContact"}
    if active_only:
        query["is_active"] = True
    contacts = [api.get_object(b) for b in api.search(query, CONTACT_CATALOG)]
    return sorted(contacts, key=lambda c: (to_text(api.get_title(c)).lower(), api.get_uid(c)))


def unique_user_contacts(contacts):
    """Aucune deduction si plusieurs contacts partagent un compte."""
    grouped = {}
    for contact in contacts:
        username = contact.getUsername()
        if username:
            grouped.setdefault(username, []).append(contact)
    return dict((username, values[0]) for username, values in grouped.items() if len(values) == 1)


def can_assign(analysis):
    from bika.lims.api.security import check_permission
    from senaite.core.permissions import FieldEditAnalysisConditions
    if getattr(analysis, "portal_type", "") != "Analysis":
        return False
    sample = analysis.getRequest()
    return (sample is not None and api.is_active(sample)
            and api.get_workflow_status_of(analysis) in EDIT_STATES
            and check_permission(FieldEditAnalysisConditions, analysis))


def revision(analysis):
    field = analysis.getField(FIELD)
    data = [field.getRaw(analysis) or "", analysis.getAnalyst(),
            api.get_workflow_status_of(analysis)]
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode("utf-8")).hexdigest()


def migrate_assignments(portal):
    """Reprend seulement les liens historiques de compte non ambigus."""
    from senaite.core.catalog import ANALYSIS_CATALOG
    contacts = unique_user_contacts(lab_contacts(active_only=False))
    updated = 0
    for brain in api.search({"portal_type": "Analysis"}, ANALYSIS_CATALOG):
        analysis = api.get_object(brain)
        field = analysis.getField(FIELD)
        if (field is None or field.getRaw(analysis)
                or getattr(analysis, "_trimeta_assigned_analyst_set", False)):
            continue
        contact = contacts.get(analysis.getAnalyst())
        if contact is None:
            continue
        field.set(analysis, api.get_uid(contact), _trimeta_migration_=True)
        updated += 1
    logger.info("Affectations de contacts reprises: %s", updated)
    return updated
