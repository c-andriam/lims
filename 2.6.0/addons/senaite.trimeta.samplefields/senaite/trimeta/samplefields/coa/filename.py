# -*- coding: utf-8 -*-
"""
Nommage des fichiers COA (demande D10).

    "Le nom du COA devrait etre le << Code echantillon / Sample code >>
     au lieu de << Sample ID >>"

Ou le nom est fabrique
----------------------
SENAITE le fabrique a TROIS endroits distincts, tous a partir du Sample
ID. Les trois derivent du meme calcul, et les trois sont repris par
l'add-on -- n'en reprendre qu'un laisserait le laboratoire recevoir
tantot ECH-042.pdf, tantot W-0031.pdf, pour le meme rapport:

    1. telechargement unitaire ......... coa/download.py
    2. piece jointe d'un courriel ...... coa/email.py
    3. archive ZIP d'un lot de COA ..... coa/workflow.py

Ce module porte le calcul commun. Il ne connait ni requete, ni reponse,
ni ZODB: c'est ce qui le rend testable sans container (voir
tests/test_coa_filename.py).

Pourquoi tant de precautions sur une chaine
-------------------------------------------
Le Code echantillon est un champ de TEXTE LIBRE saisi par l'operateur.
Contrairement au Sample ID -- fabrique par SENAITE, toujours de la
forme `W-0031` -- il peut contenir a peu pres n'importe quoi. Or cette
valeur part:

- dans un en-tete HTTP `Content-Disposition`. Un retour chariot y
  ouvrirait une injection d'en-tete; un espace, dans la forme NON
  ENTRE GUILLEMETS qu'utilise senaite.core, tronquerait le nom au
  premier blanc;
- dans un nom de fichier sur le poste du destinataire. Une barre
  oblique y creerait un chemin, un nom reserve Windows (`CON`, `AUX`,
  `LPT1`...) y serait refuse;
- dans une entree d'archive ZIP, ou deux entrees homonymes sont
  acceptees sans broncher par `zipfile` mais ou la plupart des
  extracteurs n'en montrent qu'une.

D'ou `sanitize()`, et d'ou `unique_name()`.

Le repli
--------
Un Code echantillon vide, ou entierement compose de caracteres
inutilisables, redonne le Sample ID. Un rapport doit TOUJOURS porter un
nom exploitable: mieux vaut l'ancien nom que pas de nom.
"""

import logging
import re
import unicodedata

from senaite.trimeta.samplefields.compat import to_text

logger = logging.getLogger("senaite.trimeta.samplefields")

# Nom du champ porte par notre extension de schema (voir extender.py).
SAMPLE_CODE_FIELD = "SampleCode"

# Longueur maximale de la partie NOM, extension non comprise. Les
# systemes de fichiers courants admettent 255 octets; on reste tres en
# deca pour laisser de la place a un suffixe de desambiguisation et
# survivre a une arborescence profonde cote destinataire.
MAX_LENGTH = 120

# Nom de dernier recours, si meme le Sample ID est inexploitable.
FALLBACK = u"COA"

# Caracteres de controle: le danger principal, puisque \r et \n
# permettraient une injection dans l'en-tete HTTP.
CONTROL = re.compile(u"[\\x00-\\x1f\\x7f]")

# Interdits sur au moins un systeme de fichiers courant, ou porteurs
# d'un sens de chemin.
ILLEGAL = re.compile(u"[\\\\/:*?\"<>|]+")

WHITESPACE = re.compile(u"\\s+")

# Plusieurs separateurs de suite ne servent a rien.
REPEATS = re.compile(u"[_-]{2,}")

# Noms de peripheriques reserves sous Windows: un fichier ainsi nomme
# ne peut pas y etre cree, avec ou sans extension.
WINDOWS_RESERVED = frozenset([
    u"CON", u"PRN", u"AUX", u"NUL",
    u"COM1", u"COM2", u"COM3", u"COM4", u"COM5",
    u"COM6", u"COM7", u"COM8", u"COM9",
    u"LPT1", u"LPT2", u"LPT3", u"LPT4", u"LPT5",
    u"LPT6", u"LPT7", u"LPT8", u"LPT9",
])


def sanitize(value, fallback=FALLBACK, max_length=MAX_LENGTH):
    """Rend une valeur saisie utilisable comme nom de fichier.

    Sans extension: `sanitize(u"Lot 12/A")` donne `u"Lot_12-A"`.

    Les accents sont transliteres plutot que conserves. Ce n'est pas de
    la coquetterie: l'en-tete `Content-Disposition` de senaite.core
    n'encode pas l'UTF-8 (pas de forme `filename*=`), et un octet non
    ASCII y est rendu differemment par chaque navigateur. Un nom en
    ASCII est le seul qui arrive intact partout. `Vanille Bourbon`
    reste donc lisible, et `Recolte` (saisi avec accent) devient `Recolte`.

    Renvoie toujours une chaine non vide.
    """
    text = to_text(value).strip()

    # Transliteration: NFKD separe la lettre de son accent, l'encodage
    # ASCII "ignore" ne garde que la lettre.
    try:
        text = unicodedata.normalize("NFKD", text)
        text = text.encode("ascii", "ignore").decode("ascii")
    except (UnicodeError, TypeError):
        # Valeur exotique: on repart du texte brut, le nettoyage qui
        # suit s'en chargera.
        text = to_text(value)

    # L'ordre compte. Les blancs D'ABORD: tabulation, retour chariot et
    # saut de ligne sont a la fois des caracteres de controle et des
    # blancs. Les supprimer purement collerait deux mots ensemble
    # ("Lot 1\tVert" -> "Lot_1Vert"); on les rend donc separateurs
    # avant d'effacer le reste des caracteres de controle.
    text = WHITESPACE.sub(u"_", text)
    text = CONTROL.sub(u"", text)
    # ILLEGAL peut creer des suites de tirets: REPEATS passe apres.
    text = ILLEGAL.sub(u"-", text)
    text = REPEATS.sub(lambda m: m.group(0)[0], text)

    # Un point ou un separateur en bordure produit un fichier cache sous
    # Unix, ou un nom refuse sous Windows.
    text = text.strip(u"._- ")

    if len(text) > max_length:
        text = text[:max_length].rstrip(u"._- ")

    if not text:
        return fallback

    # `CON.pdf` reste refuse sous Windows: c'est la partie avant le
    # point qui compte.
    if text.split(u".")[0].upper() in WINDOWS_RESERVED:
        text = u"{}_".format(text)

    return text


def unique_name(name, taken):
    """Rend `name` unique vis-a-vis de l'ensemble `taken`.

    `taken` est modifie: le nom retenu y est ajoute. La comparaison
    ignore la casse, parce que le destinataire peut extraire l'archive
    sur un systeme de fichiers qui ne la distingue pas -- deux entrees
    `ECH-1.pdf` et `ech-1.pdf` s'y ecraseraient l'une l'autre.

    Le Code echantillon n'etant soumis a aucune contrainte d'unicite
    dans SENAITE, deux rapports d'une meme selection peuvent
    parfaitement porter le meme. `zipfile.writestr()` accepterait les
    deux entrees sans rien dire, et la plupart des extracteurs n'en
    montreraient qu'une: un COA disparaitrait en silence.

        ECH-1.pdf, ECH-1.pdf, ECH-1.pdf
        -> ECH-1.pdf, ECH-1-2.pdf, ECH-1-3.pdf
    """
    if name.lower() not in taken:
        taken.add(name.lower())
        return name

    stem, dot, extension = name.rpartition(u".")
    if not dot:
        stem, extension = name, u""
    suffix = 2
    while True:
        candidate = u"{}-{}{}{}".format(stem, suffix, dot, extension)
        if candidate.lower() not in taken:
            taken.add(candidate.lower())
            return candidate
        suffix += 1


def get_sample_code(sample):
    """Code echantillon d'un echantillon, ou chaine vide.

    Un champ ajoute par schemaextender n'a pas d'accesseur de classe:
    il n'existe aucun `sample.getSampleCode()`. On passe donc par le
    schema. Un echantillon cree avant l'ajout du champ n'a simplement
    pas ce champ -- ce n'est pas une erreur, c'est un repli.
    """
    if sample is None:
        return u""
    try:
        field = sample.getField(SAMPLE_CODE_FIELD)
        if field is None:
            return u""
        return to_text(field.get(sample)).strip()
    except Exception:
        logger.exception("Lecture du Code echantillon impossible")
        return u""


def build_filename(sample_code, sample_id, extension=u".pdf"):
    """Assemble le nom final a partir des deux valeurs candidates.

    Separe du reste pour etre testable sans le moindre objet SENAITE.
    Le Code echantillon l'emporte; le Sample ID prend le relais quand il
    est vide ou inexploitable.
    """
    name = sanitize(sample_code, fallback=u"")
    if not name:
        name = sanitize(sample_id, fallback=FALLBACK)
    return u"{}{}".format(name, extension)


def get_report_filename(report, extension=u".pdf"):
    """Nom du fichier pour un ARReport.

    C'est la surcharge de `get_report_filename()` de senaite.core, qui
    renvoie `"{}.pdf".format(api.get_id(sample))`.

    Ne leve jamais: un nom de repli vaut mieux qu'un telechargement qui
    echoue.
    """
    sample = None
    sample_id = u""
    try:
        sample = report.getAnalysisRequest()
        sample_id = to_text(sample.getId())
    except Exception:
        logger.exception("Echantillon introuvable pour le rapport %r", report)

    return build_filename(get_sample_code(sample), sample_id, extension)
