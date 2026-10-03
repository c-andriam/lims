# -*- coding: utf-8 -*-
"""Nom des PDF de COA: le Code echantillon plutot que l'ID SENAITE."""

import os
import re
import unicodedata

from bika.lims import api
from senaite.trimeta.samplefields.compat import to_text

from senaite.trimeta.samplefields.indexers import get_field_value

FALLBACK = u"COA"
MAX_LENGTH = 180
SAMPLE_CODE_FIELD = "SampleCode"
RESERVED = set(["CON", "PRN", "AUX", "NUL"] +
               ["%s%d" % (prefix, n) for prefix in ("COM", "LPT")
                for n in range(1, 10)])


def sanitize(value, fallback=FALLBACK):
    """Nom ASCII utilisable dans les en-tetes et sur les postes Windows."""
    name = unicodedata.normalize("NFKD", to_text(value))
    name = name.encode("ascii", "ignore").decode("ascii")
    name = re.sub(r"\s+", "_", name.strip())
    name = re.sub(r"[\x00-\x1f\x7f]", "", name)
    name = re.sub(r'[\\/:*?"<>|;]', "-", name)
    name = re.sub(r"-+", "-", name)
    name = re.sub(r"_+", "_", name)
    name = re.sub(r"[-_]*-[-_]*", "-", name)
    name = name.strip("._- ")[:MAX_LENGTH].rstrip("._- ")
    if name.split(".")[0].upper() in RESERVED:
        name += "_"
    return name or fallback


def build_filename(sample_code, sample_id, extension=u".pdf"):
    """Code echantillon, sinon ID, sinon COA."""
    return (sanitize(sample_code, fallback=u"") or
            sanitize(sample_id)) + extension


def unique_name(filename, taken):
    """Evite les collisions a l'extraction, y compris sans casse."""
    base, ext = os.path.splitext(filename)
    candidate, number = filename, 1
    existing = set(name.lower() for name in taken)
    while candidate.lower() in existing:
        number += 1
        candidate = "{}-{}{}".format(base, number, ext)
    taken.add(candidate)
    return candidate


# Compatibilite avec les anciens consommateurs du module.
build_coa_filename = build_filename
unique_filename = unique_name


def get_sample_code(sample):
    return get_field_value(sample, SAMPLE_CODE_FIELD)


def get_report_filename(report):
    """Nom du PDF d'un ARReport, d'apres l'echantillon dont il rend compte."""
    sample = report.getAnalysisRequest()
    return build_coa_filename(get_field_value(sample, SAMPLE_CODE_FIELD),
                              api.get_id(sample))
