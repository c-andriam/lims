# -*- coding: utf-8 -*-
"""Cree le calcul variable sans recalculer les analyses historiques."""
from bika.lims import api
from senaite.trimeta.samplefields.defaults import setup_repetitions


def upgrade(tool):
    setup_repetitions(api.get_portal())
    return True
