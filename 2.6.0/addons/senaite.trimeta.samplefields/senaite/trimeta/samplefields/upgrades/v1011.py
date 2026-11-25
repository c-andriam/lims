# -*- coding: utf-8 -*-
"""Expose les limites de detection au tableau sans ouvrir les analyses."""
from bika.lims import api
from senaite.trimeta.samplefields.setuphandlers import setup_catalogs, reindex_catalog


def upgrade(tool):
    for catalog_id, indexes in setup_catalogs(api.get_portal()).items():
        reindex_catalog(catalog_id, indexes)
    return True
