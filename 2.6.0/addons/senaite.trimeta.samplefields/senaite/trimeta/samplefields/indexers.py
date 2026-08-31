# -*- coding: utf-8 -*-
"""
Indexeurs nommes (plone.indexer) pour les champs ajoutes par l'add-on.

Un indexeur nomme est un adaptateur (objet, catalogue) -> valeur, que
Plone consulte via IndexableObjectWrapper aussi bien pour alimenter un
index que pour remplir une colonne de metadonnees. C'est le seul
mecanisme fiable pour indexer un champ schemaextender (voir catalog.py).

Trois formes de valeur seulement
--------------------------------
Les huit champs exposes au catalogue se ramenent a trois normalisations,
chacune ecrite une fois:

- `to_index_string`  texte, jamais None (codes, provenances, poids);
- `to_index_date`    la date telle quelle, ou None si vide;
- `to_contact_title` l'intitule d'un LabContact reference.

Les fonctions decorees par `@indexer` restent ecrites une par une: leur
nom EST l'identifiant de l'index, et chacune doit etre enregistree
nommement dans configure.zcml. Les generer masquerait ce lien.
"""

import logging

from bika.lims import api
from bika.lims.interfaces import IAnalysisRequest
from plone.indexer import indexer

from senaite.trimeta.samplefields.compat import string_types
from senaite.trimeta.samplefields.compat import to_text

logger = logging.getLogger("senaite.trimeta.samplefields")


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


def to_index_date(value):
    """Normalise une date pour une colonne de metadonnees.

    On renvoie l'objet date tel quel plutot qu'une chaine: c'est le
    listing qui doit decider du format d'affichage, selon la langue du
    compte. Une date convertie en texte ici serait figee en anglais et
    impossible a trier correctement.

    Une valeur vide donne None, pas la chaine vide: un champ date non
    renseigne et un champ date au 1er janvier 1970 ne doivent pas se
    confondre dans le tableau.
    """
    if not value:
        return None
    return value


def to_contact_title(value):
    """Intitule du ou des LabContact references par un champ.

    `UIDReferenceField` ne rend pas toujours la meme forme selon les
    versions de SENAITE et selon que le champ est multiValued: tantot
    l'objet, tantot son UID, tantot une liste des deux. On accepte donc
    les trois plutot que de parier sur l'une.

    Une reference qui ne se resout pas -- contact supprime, UID
    obsolete -- donne une chaine vide. Afficher l'UID brut dans une
    colonne "Operateur" serait du bruit illisible, et lever ferait
    perdre l'indexation de tout l'echantillon pour un seul champ.
    """
    if not value:
        return u""

    if isinstance(value, (list, tuple)):
        titles = [to_contact_title(item) for item in value]
        return u", ".join([title for title in titles if title])

    if isinstance(value, string_types):
        try:
            value = api.get_object_by_uid(value)
        except Exception:
            logger.debug("Reference de contact non resolue: %r", value)
            return u""

    try:
        return to_text(api.get_title(value)).strip()
    except Exception:
        logger.debug("Titre illisible sur %r", value)
        return u""


def to_reference_uid(value):
    """UID de l'objet reference par un champ, quelle que soit la forme.

    Meme prudence que to_contact_title: UIDReferenceField et les
    accesseurs Archetypes rendent tantot l'objet, tantot son UID,
    tantot une liste. Une reference morte donne une chaine vide plutot
    que de faire echouer l'indexation de tout l'echantillon.
    """
    if not value:
        return u""

    if isinstance(value, (list, tuple)):
        value = value[0] if value else None
        if not value:
            return u""

    if isinstance(value, string_types):
        # Deja un UID: rien a resoudre.
        return to_text(value).strip()

    try:
        return to_text(api.get_uid(value)).strip()
    except Exception:
        logger.debug("UID illisible sur %r", value)
        return u""


# ---------------------------------------------------------------------
# Section Reception / Analyse
# ---------------------------------------------------------------------

@indexer(IAnalysisRequest)
def getSampleCode(instance):
    """Index et colonne `getSampleCode` du sample_catalog."""
    return to_index_string(get_field_value(instance, "SampleCode"))


@indexer(IAnalysisRequest)
def getOrigin(instance):
    """Index et colonne `getOrigin` -- filtre Provenance du tableau."""
    return to_index_string(get_field_value(instance, "Origin"))


@indexer(IAnalysisRequest)
def getTrimetaSampleTypeUID(instance):
    """Index `getTrimetaSampleTypeUID` -- filtre Type d'echantillon.

    Le champ SampleType est natif, mais il n'est pas indexe dans le
    sample_catalog et AnalysisRequest n'expose pas d'accesseur
    getSampleTypeUID (voir catalog.py). On lit donc le champ
    directement et on en tire l'UID.
    """
    return to_reference_uid(get_field_value(instance, "SampleType", None))


@indexer(IAnalysisRequest)
def getReceptionWeight(instance):
    """Colonne `getReceptionWeight`.

    Le champ est un FixedPointField: sa valeur est deja une chaine
    decimale ("12.50"). On la garde telle quelle plutot que de la
    convertir en nombre, pour ne pas perdre les decimales
    significatives d'une pesee.
    """
    return to_index_string(get_field_value(instance, "ReceptionWeight"))


@indexer(IAnalysisRequest)
def getAnalysisStart(instance):
    """Colonne `getAnalysisStart` -- debut d'analyse."""
    return to_index_date(get_field_value(instance, "AnalysisStart", None))


@indexer(IAnalysisRequest)
def getAnalysisEnd(instance):
    """Colonne `getAnalysisEnd` -- fin d'analyse."""
    return to_index_date(get_field_value(instance, "AnalysisEnd", None))


# ---------------------------------------------------------------------
# Section Assurance Qualite: les trois operateurs du tableau de bord
# ---------------------------------------------------------------------

@indexer(IAnalysisRequest)
def getHPLCOperator(instance):
    """Colonne `getHPLCOperator` -- operateur du dosage HPLC."""
    return to_contact_title(get_field_value(instance, "HPLCOperator", None))


@indexer(IAnalysisRequest)
def getMoistureOperator(instance):
    """Colonne `getMoistureOperator` -- operateur du taux d'humidite."""
    return to_contact_title(
        get_field_value(instance, "MoistureOperator", None))


@indexer(IAnalysisRequest)
def getWaterActivityOperator(instance):
    """Colonne `getWaterActivityOperator` -- operateur de l'activite de
    l'eau."""
    return to_contact_title(
        get_field_value(instance, "WaterActivityOperator", None))
