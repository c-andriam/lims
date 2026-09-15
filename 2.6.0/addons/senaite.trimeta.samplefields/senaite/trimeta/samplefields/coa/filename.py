# -*- coding: utf-8 -*-
"""Nom des PDF de COA: le Code echantillon plutot que l'ID SENAITE."""

import re

from bika.lims import api

from senaite.trimeta.samplefields.indexers import get_field_value

# Le nom finit non quote dans un en-tete Content-Disposition et comme nom
# d'entree dans l'archive zip: seuls ces caracteres y sont surs.
UNSAFE_CHARS = re.compile(r"[^A-Za-z0-9._-]+")


def build_coa_filename(sample_code, sample_id):
    """`<Code echantillon>.pdf`, ou `<ID>.pdf` si le code est inutilisable."""
    name = UNSAFE_CHARS.sub("_", (sample_code or "").strip()).strip("._")
    return "{}.pdf".format(name or sample_id)


def get_report_filename(report):
    """Nom du PDF d'un ARReport, d'apres l'echantillon dont il rend compte."""
    sample = report.getAnalysisRequest()
    return build_coa_filename(get_field_value(sample, "SampleCode"),
                              api.get_id(sample))
