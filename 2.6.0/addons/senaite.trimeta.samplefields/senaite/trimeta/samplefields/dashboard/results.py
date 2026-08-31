# -*- coding: utf-8 -*-
"""
Recuperation des resultats d'analyse pour le tableau de bord.

Pourquoi une requete a part
---------------------------
Les sept colonnes de resultats du tableau de bord (Vanilline,
Gluco-vanilline, AC Vanillique, PHB, AC PHB, TH, AW) ne sont pas des
champs de l'echantillon: ce sont des objets `Analysis` rattaches a lui.
Elles ne peuvent donc pas venir du sample_catalog, et il n'y a rien a
ajouter de ce cote.

Elles sont lues dans l'analysis_catalog, en UNE requete pour toute la
page affichee, et uniquement dans des elements qui y existent deja:

    getRequestID   identifiant de l'echantillon parent   index + colonne
    getKeyword     mot-cle du service                    index + colonne
    getResult      resultat saisi                        colonne
    getResultCaptureDate  date de saisie du resultat     index + colonne

Aucun objet n'est reveille depuis la ZODB: le cout est d'une requete
catalogue par affichage, quel que soit le nombre de lignes.

L'alternative aurait ete de denormaliser les resultats dans le
sample_catalog au moment de l'indexation. Plus rapide encore a
l'affichage, mais il aurait fallu reindexer l'echantillon a chaque
saisie de resultat -- un etat duplique a tenir coherent, donc une
source de valeurs fausses en silence.

Pourquoi le mot-cle et pas l'intitule
-------------------------------------
Un service peut etre renomme dans l'interface; son mot-cle (Keyword)
est la cle stable. Un mot-cle qui ne correspond a aucun service donne
une colonne vide, jamais une erreur.

Le cas des resultats censures
-----------------------------
SENAITE enregistre les limites de detection sous la forme "<0.5" ou
">100". Ces valeurs ne sont pas des nombres et ne sont donc PAS
comparables: `to_number` renvoie None, et le filtre de plage les
ecarte. C'est volontaire. Traiter "<0.5" comme 0.5 le ferait entrer
dans un intervalle auquel il n'appartient peut-etre pas, et personne
ne le verrait.
"""

import logging

from senaite.trimeta.samplefields.compat import to_text

logger = logging.getLogger("senaite.trimeta.samplefields")


def to_number(value):
    """Convertit un resultat en nombre comparable, ou None.

    Accepte la virgule decimale, saisie courante sur un poste
    francophone. Renvoie None pour tout ce qui n'est pas un nombre
    simple: chaine vide, texte, et limites de detection ("<0.5").
    """
    if value is None:
        return None
    text = to_text(value).strip().replace(",", ".")
    if not text:
        return None
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def in_range(value, minimum=None, maximum=None):
    """Le resultat tombe-t-il dans l'intervalle [minimum, maximum] ?

    Les deux bornes sont facultatives et independantes: renseigner la
    seule borne basse donne "au moins X". Une valeur non comparable
    (vide, texte, limite de detection) est hors intervalle des qu'une
    borne est posee.
    """
    number = to_number(value)
    if number is None:
        return False
    low = to_number(minimum)
    high = to_number(maximum)
    if low is not None and number < low:
        return False
    if high is not None and number > high:
        return False
    return True


def _is_better(candidate, current):
    """Des deux analyses, laquelle doit alimenter la case du tableau ?

    Un echantillon peut porter plusieurs analyses pour un meme mot-cle
    -- une reprise (retest) apres un premier resultat. La regle:

    1. un resultat renseigne l'emporte toujours sur une case vide;
    2. entre deux resultats renseignes, le plus recemment saisi gagne;
    3. a defaut de date exploitable, le dernier rencontre gagne.

    `candidate` et `current` sont des couples (resultat, date de saisie).
    """
    new_result, new_date = candidate
    old_result, old_date = current

    if bool(new_result) != bool(old_result):
        return bool(new_result)

    if new_date is None or old_date is None:
        # Sans date des deux cotes, on ne peut pas trancher sur la
        # fraicheur: on garde le dernier vu, ce qui suit l'ordre de tri
        # rendu par le catalogue.
        return True

    try:
        return new_date >= old_date
    except TypeError:
        # Types de date incomparables (Python 3 refuse ce que Python 2
        # acceptait). On ne devine pas: dernier vu.
        return True


def group_by_sample(brains, keywords=None):
    """Range des brains d'analyses en {identifiant echantillon: {mot-cle: resultat}}.

    :param brains: brains de l'analysis_catalog
    :param keywords: mots-cles a retenir; None les prend tous
    """
    wanted = set(keywords) if keywords else None
    best = {}

    for brain in brains:
        sample_id = to_text(getattr(brain, "getRequestID", "")).strip()
        keyword = to_text(getattr(brain, "getKeyword", "")).strip()
        if not sample_id or not keyword:
            continue
        if wanted is not None and keyword not in wanted:
            continue

        candidate = (
            to_text(getattr(brain, "getResult", "")).strip(),
            getattr(brain, "getResultCaptureDate", None),
        )
        key = (sample_id, keyword)
        current = best.get(key)
        if current is None or _is_better(candidate, current):
            best[key] = candidate

    grouped = {}
    for (sample_id, keyword), (result, _date) in best.items():
        grouped.setdefault(sample_id, {})[keyword] = result
    return grouped


def fetch_results(catalog, sample_ids, keywords):
    """Resultats des `keywords` pour les `sample_ids`, en une requete.

    :param catalog: l'analysis_catalog
    :param sample_ids: identifiants des echantillons de la page affichee
    :param keywords: mots-cles des services a ramener
    :returns: {identifiant echantillon: {mot-cle: resultat}}

    Renvoie un dictionnaire vide plutot que de lever: une colonne de
    resultats absente est un desagrement, un tableau de bord qui ne
    s'affiche plus est un arret de travail.
    """
    sample_ids = [s for s in (sample_ids or []) if s]
    keywords = [k for k in (keywords or []) if k]
    if not sample_ids or not keywords:
        return {}

    try:
        brains = catalog({
            "getRequestID": sample_ids,
            "getKeyword": keywords,
        })
        return group_by_sample(brains, keywords)
    except Exception:
        logger.exception(
            "Lecture des resultats impossible pour %s echantillon(s)",
            len(sample_ids))
        return {}


def sample_ids_in_range(catalog, keyword, minimum=None, maximum=None):
    """Identifiants des echantillons dont le resultat `keyword` est dans
    l'intervalle.

    Sert au filtre de plage du tableau de bord. Il doit s'appliquer
    AVANT la pagination -- sinon le nombre de pages annonce serait faux
    -- d'ou cette requete prealable sur l'analysis_catalog, dont on
    ressort une liste d'identifiants passee ensuite au sample_catalog.

    La requete ne porte que sur le mot-cle, qui est indexe; le tri
    numerique se fait en Python, `getResult` n'etant qu'une colonne de
    metadonnees. Le volume reste celui des analyses d'un seul service.

    :returns: liste d'identifiants, ou None si aucune borne n'est posee
        (aucun filtrage a appliquer -- a distinguer d'une liste vide,
        qui signifie "aucun echantillon ne correspond").
    """
    if to_number(minimum) is None and to_number(maximum) is None:
        return None

    try:
        brains = catalog({"getKeyword": keyword})
    except Exception:
        logger.exception("Filtre de plage impossible sur %s", keyword)
        return None

    matching = set()
    for brain in brains:
        sample_id = to_text(getattr(brain, "getRequestID", "")).strip()
        if not sample_id:
            continue
        if in_range(getattr(brain, "getResult", ""), minimum, maximum):
            matching.add(sample_id)
    return sorted(matching)
