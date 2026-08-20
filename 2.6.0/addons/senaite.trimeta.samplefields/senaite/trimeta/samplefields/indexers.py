# -*- coding: utf-8 -*-
"""
Indexeurs nommes (plone.indexer) pour les champs ajoutes par l'add-on.

Un indexeur nomme est un adaptateur (objet, catalogue) -> valeur, que
Plone consulte via IndexableObjectWrapper aussi bien pour alimenter un
index que pour remplir une colonne de metadonnees. C'est le seul
mecanisme fiable pour indexer un champ schemaextender (voir catalog.py).
"""

from bika.lims.interfaces import IAnalysisRequest
from plone.indexer import indexer


def get_field_value(instance, fieldname, default=""):
    """Lit la valeur d'un champ etendu sans supposer l'existence d'un
    accesseur sur la classe.

    Renvoie `default` si le champ est absent du schema (cas d'un objet
    cree avant l'ajout du champ, ou d'un schema non encore etendu).
    """
    field = instance.getField(fieldname)
    if field is None:
        return default
    value = field.get(instance)
    if value is None:
        return default
    return value


def to_index_string(value):
    """Normalise une valeur pour un FieldIndex: toujours une chaine,
    jamais None (sinon le catalogue stocke un marqueur inutilisable)."""
    if value is None:
        return ""
    if isinstance(value, bytes):
        value = value.decode("utf-8", "replace")
    elif not isinstance(value, str):
        value = str(value)
    return value.strip()


@indexer(IAnalysisRequest)
def getSampleCode(instance):
    """Index et colonne `getSampleCode` du sample_catalog."""
    return to_index_string(get_field_value(instance, "SampleCode"))
