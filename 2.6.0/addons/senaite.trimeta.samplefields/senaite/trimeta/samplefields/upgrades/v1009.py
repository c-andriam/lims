# -*- coding: utf-8 -*-
"""Rattachement des repetitions aux services reconnus du laboratoire."""
from bika.lims import api
from senaite.trimeta.samplefields.defaults import setup_repetitions


def upgrade(tool):
    setup_repetitions(api.get_portal())
    return True
