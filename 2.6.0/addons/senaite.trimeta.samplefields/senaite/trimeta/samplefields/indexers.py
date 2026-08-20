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

from senaite.trimeta.samplefields.compat import to_text


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
    """Normalise une valeur pour un FieldIndex: toujours du texte,
    jamais None (sinon le catalogue stocke un marqueur inutilisable).

    Passe par compat.to_text: sur Python 2, `str(u"Réception")` leverait
    UnicodeEncodeError et rendrait l'echantillon non indexable.
    """
    return to_text(value).strip()


@indexer(IAnalysisRequest)
def getSampleCode(instance):
    """Index et colonne `getSampleCode` du sample_catalog."""
    return to_index_string(get_field_value(instance, "SampleCode"))
