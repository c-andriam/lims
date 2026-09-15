# -*- coding: utf-8 -*-
"""Logique pure de la Work Sheet, testable sans Zope."""


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
