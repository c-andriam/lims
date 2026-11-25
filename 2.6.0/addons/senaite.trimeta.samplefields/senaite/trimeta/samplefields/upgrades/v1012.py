# -*- coding: utf-8 -*-
"""Contacts analystes et deux historiques d'equipement."""
from bika.lims import api
from senaite.trimeta.samplefields.analysts import migrate_assignments
from senaite.trimeta.samplefields.equipment_history import setup_history_actions


def upgrade(tool):
    portal = api.get_portal()
    setup_history_actions(portal)
    migrate_assignments(portal)
    return True
