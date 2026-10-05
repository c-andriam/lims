# -*- coding: utf-8 -*-
"""Retour des formulaires Archetypes en cas de validation refusee."""
from bika.lims import api
from senaite.trimeta.samplefields.setuphandlers import ensure_archetypes_edit_actions


def upgrade(tool):
    ensure_archetypes_edit_actions(api.get_portal())
    return True
