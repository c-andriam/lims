# -*- coding: utf-8 -*-
"""
Installation du profil GenericSetup de l'add-on.

Appele par le post_handler declare dans configure.zcml. Deux
responsabilites:

1. creer les index et colonnes de catalogue declares dans catalog.py;
2. reindexer les echantillons deja saisis, sans quoi un index
   fraichement cree reste vide pour l'historique.

Toutes les operations sont idempotentes: reinstaller le profil ne
duplique rien et ne casse rien.
"""

import logging

import transaction
from bika.lims import api
from senaite.core.api import catalog as capi

from senaite.trimeta.samplefields.catalog import CATALOGS

logger = logging.getLogger("senaite.trimeta.samplefields")

PROFILE_ID = "profile-senaite.trimeta.samplefields:default"

# Nombre d'objets reindexes entre deux savepoints. Evite de faire
# gonfler la memoire sur une base de plusieurs milliers d'echantillons.
SAVEPOINT_EVERY = 100


def post_install(portal_setup):
    """Post-installation du profil `default`."""
    logger.info("senaite.trimeta.samplefields: post_install")
    portal = api.get_portal()
    added = setup_catalogs(portal)
    if added:
        # Seuls les catalogues reellement modifies sont reconstruits.
        for catalog_id, indexes in added.items():
            reindex_catalog(catalog_id, indexes)
    logger.info("senaite.trimeta.samplefields: post_install termine")


def post_uninstall(portal_setup):
    """Post-desinstallation: on retire index et colonnes.

    Les valeurs des champs restent stockees sur les echantillons; seule
    la vue catalogue disparait. Rien n'est perdu si l'add-on est
    reinstalle plus tard.
    """
    logger.info("senaite.trimeta.samplefields: post_uninstall")
    for catalog_id, indexes, columns in CATALOGS:
        catalog = capi.get_catalog(catalog_id)
        for index_id, _index_type, _attrs in indexes:
            if index_id in capi.get_indexes(catalog):
                capi.del_index(catalog, index_id)
        for column in columns:
            if column in capi.get_columns(catalog):
                capi.del_column(catalog, column)


def setup_catalogs(portal):
    """Cree les index et colonnes manquants.

    :returns: dict {catalog_id: [index_ids reellement crees]}
    """
    created = {}
    for catalog_id, indexes, columns in CATALOGS:
        catalog = capi.get_catalog(catalog_id)
        existing_indexes = capi.get_indexes(catalog)
        existing_columns = capi.get_columns(catalog)

        new_indexes = []
        for index_id, index_type, indexed_attrs in indexes:
            if index_id in existing_indexes:
                logger.info("Index %s deja present dans %s",
                            index_id, catalog_id)
                continue
            capi.add_index(catalog, index_id, index_type,
                           indexed_attrs=indexed_attrs)
            new_indexes.append(index_id)
            logger.info("Index %s cree dans %s", index_id, catalog_id)

        for column in columns:
            if column in existing_columns:
                logger.info("Colonne %s deja presente dans %s",
                            column, catalog_id)
                continue
            capi.add_column(catalog, column)
            # Une colonne ajoutee doit etre alimentee, meme si l'index
            # correspondant existait deja.
            if column not in new_indexes:
                new_indexes.append(column)
            logger.info("Colonne %s creee dans %s", column, catalog_id)

        if new_indexes:
            created[catalog_id] = new_indexes
    return created


def reindex_catalog(catalog_id, indexes):
    """Reindexe tous les objets d'un catalogue pour les index donnes.

    On passe par catalog_object() plutot que par reindex_index() afin de
    mettre a jour l'index ET les colonnes de metadonnees en une seule
    passe.
    """
    catalog = capi.get_catalog(catalog_id)
    brains = catalog({})
    total = len(brains)
    logger.info("Reindexation de %s objets dans %s pour %r",
                total, catalog_id, indexes)

    for num, brain in enumerate(brains):
        obj = api.get_object(brain, default=None)
        if obj is None:
            continue
        catalog.catalog_object(obj, idxs=indexes, update_metadata=True)
        if num and num % SAVEPOINT_EVERY == 0:
            transaction.savepoint(optimistic=True)
            logger.info("  ... %s/%s", num, total)

    logger.info("Reindexation de %s terminee (%s objets)",
                catalog_id, total)
