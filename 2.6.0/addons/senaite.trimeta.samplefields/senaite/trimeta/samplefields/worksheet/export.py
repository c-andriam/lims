# -*- coding: utf-8 -*-
"""Logique pure de la Work Sheet, testable sans Zope."""
import re
from senaite.trimeta.samplefields.compat import to_text

NUMERIC_RESULT = re.compile(
    r"^([<>]=?)?\s*([+-]?(?:\d+(?:[.,]\d*)?|[.,]\d+)(?:[eE][+-]?\d+)?)$")


def stored_numeric_result(value, operand="", decimalmark="."):
    """Conserve tous les chiffres stockes, sans conversion flottante."""
    match = NUMERIC_RESULT.match(to_text(value).strip())
    if match is None:
        return None
    number = match.group(2).replace(",", ".")
    if decimalmark == ",":
        number = number.replace(".", ",")
    prefix = match.group(1) or (operand if operand in ("<", ">", "<=", ">=") else "")
    return prefix + number


def worksheet_result(analysis, fallback, decimalmark="."):
    """Ne reformate que les valeurs numeriques, conserve les choix natifs."""
    if (analysis.getResultType() != "numeric"
            or getattr(analysis, "getResultOptions", lambda: [])()):
        return fallback
    value = stored_numeric_result(analysis.getResult(),
                                  analysis.getDetectionLimitOperand(), decimalmark)
    return fallback if value is None else value


def format_due_date(due_date, localize):
    """Echeance localisee, ou chaine vide si l'analyse n'en a pas."""
    if not due_date:
        return u""
    return localize(due_date) or u""


def slot_title(sample_code, sample_id):
    """`CODE (ID)` en tete de position, ou l'ID seul sans code."""
    if not sample_code:
        return sample_id
    return u"{} ({})".format(sample_code, sample_id)


def fill_export_values(rows, slots, sample_label):
    """Renseigne `formatted_value` dans les cellules transposees.

    L'export CSV de senaite.app.listing (to_csv_row) ne lit d'une cellule
    objet que `formatted_value` ou `value`. Une Work Sheet en mise en page
    Transposed s'exportait donc sans aucun resultat ni echantillon.

    :param rows: lignes rendues par AnalysesTransposedView.folderitems
    :param slots: cles des colonnes de position ("1", "2"...)
    :param sample_label: fonction(cellule d'analyse) -> libelle echantillon
    """
    labels = {}
    for row in rows:
        if row.get("item_key") != "Result":
            continue
        for slot in slots:
            cell = row.get(slot)
            if not isinstance(cell, dict):
                continue
            cell["formatted_value"] = (cell.get("formatted_result") or
                                       cell.get("Result") or u"")
            if slot not in labels:
                labels[slot] = sample_label(cell)
    for row in rows:
        if row.get("item_key") != "Pos":
            continue
        for slot in slots:
            cell = row.get(slot)
            if isinstance(cell, dict):
                cell["formatted_value"] = labels.get(slot, u"")
    return rows
