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
from plone import api as ploneapi
from senaite.core.api import catalog as capi

from senaite.trimeta.samplefields.catalog import CATALOGS

logger = logging.getLogger("senaite.trimeta.samplefields")

PROFILE_ID = "profile-senaite.trimeta.samplefields:default"

# Nombre d'objets reindexes entre deux savepoints. Evite de faire
# gonfler la memoire sur une base de plusieurs milliers d'echantillons.
SAVEPOINT_EVERY = 100

# Gabarit COA du lot 4 (coa/templates/reports/COA-Trimeta.pt), tel qu'il
# apparait dans la liste que retourne senaite.impress.template.
# TemplateFinder -- prefixe par le "name" donne a notre <plone:static>
# dans coa/configure.zcml.
COA_TEMPLATE = u"senaite.trimeta.samplefields:COA-Trimeta.pt"

# Cle du registre Plone ou senaite.impress stocke la liste des gabarits
# *actifs*, proposes dans le selecteur de l'ecran de publication.
#
# Cette liste n'est PAS recalculee a chaque affichage: c'est une valeur
# enregistree une fois, au moment ou le profil senaite.impress:default a
# ete applique la premiere fois sur le site. Ajouter notre gabarit au
# repertoire de ressources (coa/configure.zcml) le rend *decouvrable*
# (visible dans Configuration > Impress > Available Templates) mais ne
# l'ajoute pas tout seul a cette liste enregistree -- constate sur
# l'instance de demonstration: le gabarit natif Default.pt s'affichait
# dans le selecteur, pas le notre, tant que ce qui suit n'existait pas.
IMPRESS_TEMPLATES_RECORD = "senaite.impress.templates"

# Gabarit preselectionne dans l'ecran de publication. La valeur d'usine
# est un gabarit Multi: publier plusieurs echantillons produit alors un
# seul PDF, rattache a chacun d'eux (demande D11 du document).
IMPRESS_DEFAULT_RECORD = "senaite.impress.default_template"
IMPRESS_FACTORY_DEFAULT = u"senaite.impress:MultiDefault.pt"

# Valeurs par defaut du laboratoire dans Configuration > Setup, onglet
# Accounting: {champ: (valeur voulue, valeurs d'usine remplacables)}.
#
# Seules les valeurs d'usine sont remplacees: un choix fait ensuite par
# le laboratoire dans l'ecran de configuration est conserve.
LAB_SETUP_DEFAULTS = {
    "Currency": ("MGA", ("", "EUR")),       # Ariary malgache (ISO 4217)
    "DefaultCountry": ("MG", ("",)),        # Madagascar (ISO 3166 alpha-2)
}


def post_install(portal_setup):
    """Post-installation du profil `default`."""
    logger.info("senaite.trimeta.samplefields: post_install")
    portal = api.get_portal()
    added = setup_catalogs(portal)
    if added:
        # Seuls les catalogues reellement modifies sont reconstruits.
        for catalog_id, indexes in added.items():
            reindex_catalog(catalog_id, indexes)
    register_coa_template()
    set_coa_as_default_template()
    set_lab_defaults()
    logger.info("senaite.trimeta.samplefields: post_install termine")


def set_lab_defaults():
    """Devise et pays du laboratoire dans le Setup SENAITE.

    Idempotent. Une valeur absente du vocabulaire du champ (version de
    SENAITE differente) n'est pas ecrite: elle est journalisee, plutot
    que d'enregistrer une valeur que l'ecran ne saurait pas afficher.

    :returns: {champ: (ancienne valeur, nouvelle valeur)} des changements
    """
    setup = api.get_setup()
    changes = {}
    for name, (wanted, factory_values) in sorted(LAB_SETUP_DEFAULTS.items()):
        field = setup.getField(name)
        if field is None:
            logger.warning("Setup: champ %s introuvable", name)
            continue
        current = field.get(setup) or ""
        if current == wanted:
            continue
        if current not in factory_values:
            logger.info("Setup: %s=%r conserve (choix du laboratoire)",
                        name, current)
            continue
        allowed = field.Vocabulary(setup).keys()
        if wanted not in allowed:
            logger.warning("Setup: %r absent du vocabulaire de %s",
                           wanted, name)
            continue
        field.set(setup, wanted)
        changes[name] = (current, wanted)
        logger.info("Setup: %s %r -> %r", name, current, wanted)
    return changes


def register_coa_template():
    """Ajoute le gabarit COA Trimeta a la liste des gabarits actifs.

    Idempotent: relire, ajouter seulement si absent, reecrire. N'efface
    jamais les gabarits deja choisis par le laboratoire.
    """
    try:
        templates = list(api.get_registry_record(
            IMPRESS_TEMPLATES_RECORD, default=[]) or [])
    except Exception:
        logger.warning(
            "senaite.trimeta.samplefields: registre %r introuvable "
            "(senaite.impress absent ou pas encore installe?) -- "
            "gabarit COA Trimeta non enregistre.",
            IMPRESS_TEMPLATES_RECORD)
        return
    if COA_TEMPLATE in templates:
        logger.info("Gabarit %s deja dans %s", COA_TEMPLATE,
                    IMPRESS_TEMPLATES_RECORD)
        return
    templates.append(COA_TEMPLATE)
    ploneapi.portal.set_registry_record(IMPRESS_TEMPLATES_RECORD, templates)
    logger.info("Gabarit %s ajoute a %s", COA_TEMPLATE,
                IMPRESS_TEMPLATES_RECORD)


def set_coa_as_default_template():
    """Preselectionne le gabarit COA Trimeta, s'il n'y a pas eu de choix.

    Ne remplace que la valeur d'usine: un gabarit par defaut choisi par
    le laboratoire dans Configuration > Impress est conserve.
    """
    current = api.get_registry_record(IMPRESS_DEFAULT_RECORD, default=None)
    if current not in (None, u"", IMPRESS_FACTORY_DEFAULT):
        logger.info("Gabarit par defaut %s conserve", current)
        return
    ploneapi.portal.set_registry_record(IMPRESS_DEFAULT_RECORD, COA_TEMPLATE)
    logger.info("Gabarit par defaut: %s -> %s", current, COA_TEMPLATE)


def unregister_coa_template():
    """Retire le gabarit COA Trimeta de la liste des gabarits actifs."""
    if api.get_registry_record(IMPRESS_DEFAULT_RECORD,
                               default=None) == COA_TEMPLATE:
        ploneapi.portal.set_registry_record(IMPRESS_DEFAULT_RECORD,
                                            IMPRESS_FACTORY_DEFAULT)
    try:
        templates = list(api.get_registry_record(
            IMPRESS_TEMPLATES_RECORD, default=[]) or [])
    except Exception:
        return
    if COA_TEMPLATE not in templates:
        return
    templates.remove(COA_TEMPLATE)
    ploneapi.portal.set_registry_record(IMPRESS_TEMPLATES_RECORD, templates)
    logger.info("Gabarit %s retire de %s", COA_TEMPLATE,
                IMPRESS_TEMPLATES_RECORD)


def post_uninstall(portal_setup):
    """Post-desinstallation: on retire index et colonnes.

    Les valeurs des champs restent stockees sur les echantillons; seule
    la vue catalogue disparait. Rien n'est perdu si l'add-on est
    reinstalle plus tard.
    """
    logger.info("senaite.trimeta.samplefields: post_uninstall")
    unregister_coa_template()
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

    Le dict ne retourne QUE des noms d'INDEX reels: c'est la liste passee
    telle quelle a `catalog_object(idxs=...)` dans reindex_catalog(), et
    Zope leve un KeyError si on lui donne un nom qui n'existe que comme
    colonne de metadonnees (`Catalog.getIndex()` cherche dans
    `self.indexes`, pas dans les colonnes). Une colonne fraichement
    ajoutee est tout de meme reindexee: `update_metadata=True` rafraichit
    TOUTES les colonnes d'un objet quel que soit le contenu de `idxs`,
    donc il suffit de declencher reindex_catalog() sur ce catalogue --
    inutile, et dangereux, d'y glisser le nom de la colonne.
    """
    created = {}
    for catalog_id, indexes, columns in CATALOGS:
        catalog = capi.get_catalog(catalog_id)
        existing_indexes = capi.get_indexes(catalog)
        existing_columns = capi.get_columns(catalog)

        new_indexes = []
        touched = False
        for index_id, index_type, indexed_attrs in indexes:
            if index_id in existing_indexes:
                logger.info("Index %s deja present dans %s",
                            index_id, catalog_id)
                continue
            capi.add_index(catalog, index_id, index_type,
                           indexed_attrs=indexed_attrs)
            new_indexes.append(index_id)
            touched = True
            logger.info("Index %s cree dans %s", index_id, catalog_id)

        for column in columns:
            if column in existing_columns:
                logger.info("Colonne %s deja presente dans %s",
                            column, catalog_id)
                continue
            capi.add_column(catalog, column)
            touched = True
            logger.info("Colonne %s creee dans %s", column, catalog_id)

        if touched:
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
