# -*- coding: utf-8 -*-
"""
Traductions de l'add-on: priorité sur les autres catalogues, et .mo.

Pourquoi une priorité
---------------------
zope.i18n range les catalogues d'un même domaine dans l'ordre de leur
chargement, et rend la traduction du PREMIER qui connaît le message
(TranslationDomain.translate). senaite.core est chargé avant l'add-on:
nos catalogues ne pouvaient que combler ses trous, jamais corriger ce
qu'il traduit mal -- « Batch » rendu par « Lot », qui se confond avec le
lot de l'échantillon, ou « Profiles d'analyse ». Au démarrage, nos
catalogues sont donc placés en tête de chaque domaine qu'ils couvrent.

Pourquoi un compilateur sans dépendance
---------------------------------------
Zope ne compile pas les .po au démarrage (variable
zope_i18n_compile_mo_files absente du conteneur): seuls les .mo sont
lus. `build_mo` les produit (scripts/compile-mo.py, `make i18n`), et un
test vérifie que chaque .mo livré correspond à son .po: une traduction
ajoutée sans recompilation n'apparaîtrait jamais à l'écran.

Les imports Zope restent DANS les fonctions qui en ont besoin: le reste
du module sert aussi hors de Zope (script, tests purs).
"""

import ast
import logging
import os
import re
import struct

logger = logging.getLogger("senaite.trimeta.samplefields")

LOCALES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "locales")

MO_MAGIC = 0x950412de


def prioritize_catalogs(names, prefix):
    """Catalogues situés sous `prefix` d'abord, ordre relatif conservé.

    :param names: identifiants des catalogues (chemins des .mo)
    :param prefix: répertoire des traductions de l'add-on
    """
    root = os.path.realpath(prefix)

    def is_ours(name):
        try:
            return os.path.realpath(name).startswith(root + os.sep)
        except Exception:
            return False

    ours = [n for n in names if is_ours(n)]
    others = [n for n in names if not is_ours(n)]
    return ours + others


def prioritize_trimeta_catalogs(event=None):
    """Abonné de démarrage: nos catalogues en tête de leurs domaines."""
    from zope.component import getUtilitiesFor
    from zope.i18n.interfaces import ITranslationDomain

    for name, domain in getUtilitiesFor(ITranslationDomain):
        catalogs = getattr(domain, "_catalogs", None)
        if not catalogs:
            continue
        for language in list(catalogs.keys()):
            names = catalogs[language]
            reordered = prioritize_catalogs(names, LOCALES_DIR)
            if reordered != list(names):
                catalogs[language] = reordered
                logger.info("Traductions %s (%s): catalogue Trimeta prioritaire",
                            name, language)


def parse_po(text):
    """{msgid: msgstr} d'un contenu .po.

    Ignore les entrées floues (#, fuzzy) et non traduites. Gère les
    chaînes sur plusieurs lignes, les échappements et msgctxt (clé
    « contexte\\x04msgid », comme gettext).
    """
    messages = {}
    text = text.replace(u"\r\n", u"\n")
    for block in re.split(u"\n[ \t]*\n", text):
        lines = [line.strip() for line in block.split(u"\n") if line.strip()]
        if any(line.startswith(u"#,") and u"fuzzy" in line for line in lines):
            continue
        parts = {u"msgctxt": [], u"msgid": [], u"msgstr": []}
        current = None
        for line in lines:
            if line.startswith(u"#"):
                continue
            for key in (u"msgctxt", u"msgid", u"msgstr"):
                if line.startswith(key + u" "):
                    current = key
                    line = line[len(key):].strip()
                    break
            if current and line.startswith(u'"'):
                parts[current].append(ast.literal_eval(line))
        if not parts[u"msgid"] and not parts[u"msgstr"]:
            continue
        msgid = u"".join(parts[u"msgid"])
        msgstr = u"".join(parts[u"msgstr"])
        if parts[u"msgctxt"]:
            msgid = u"".join(parts[u"msgctxt"]) + u"\x04" + msgid
        if msgstr:
            messages[msgid] = msgstr
    return messages


def build_mo(messages):
    """Contenu binaire d'un .mo (format GNU gettext, petit-boutiste)."""
    encoded = sorted((k.encode("utf-8"), v.encode("utf-8"))
                     for k, v in messages.items())
    ids = b""
    strs = b""
    offsets = []
    for key, value in encoded:
        offsets.append((len(ids), len(key), len(strs), len(value)))
        ids += key + b"\x00"
        strs += value + b"\x00"
    count = len(encoded)
    keystart = 7 * 4 + 16 * count
    valuestart = keystart + len(ids)
    table = []
    for key_offset, key_len, _value_offset, _value_len in offsets:
        table += [key_len, key_offset + keystart]
    for _key_offset, _key_len, value_offset, value_len in offsets:
        table += [value_len, value_offset + valuestart]
    header = struct.pack("<7I", MO_MAGIC, 0, count, 7 * 4,
                         7 * 4 + count * 8, 0, 0)
    return header + struct.pack("<%dI" % len(table), *table) + ids + strs


def compile_directory(path):
    """Compile chaque .po sous `path` en .mo, si le contenu change.

    :returns: liste des .mo réécrits
    """
    import io

    written = []
    for root, _dirs, files in os.walk(path):
        for filename in sorted(files):
            if not filename.endswith(".po"):
                continue
            po_path = os.path.join(root, filename)
            mo_path = po_path[:-3] + ".mo"
            with io.open(po_path, encoding="utf-8") as po_file:
                content = build_mo(parse_po(po_file.read()))
            previous = None
            if os.path.exists(mo_path):
                with open(mo_path, "rb") as mo_file:
                    previous = mo_file.read()
            if previous != content:
                with open(mo_path, "wb") as mo_file:
                    mo_file.write(content)
                written.append(mo_path)
    return written
