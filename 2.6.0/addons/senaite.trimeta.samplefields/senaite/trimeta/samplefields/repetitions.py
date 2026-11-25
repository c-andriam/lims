# -*- coding: utf-8 -*-
"""Moyenne d'un nombre variable de repetitions, sans plafond metier."""
import math
import re

from senaite.trimeta.samplefields.compat import string_types

TITLE = u"Moyenne des repetitions"
FORMULA = "mean_repetitions(%(context_uid)s)"
IMPORTS = [{"module": "senaite.trimeta.samplefields.repetitions",
            "function": "mean_repetitions"}]
KEYWORD = re.compile(r"^R([1-9][0-9]*)$")


def normalize_values(values):
    """Valide toutes les cases avant la moindre ecriture."""
    if isinstance(values, string_types) or len(values) < 2:
        raise ValueError(u"Saisissez au moins deux repetitions.")
    normalized = []
    for index, value in enumerate(values, 1):
        text = value if isinstance(value, string_types) else str(value)
        text = text.strip().replace(",", ".")
        try:
            number = float(text)
        except (TypeError, ValueError, OverflowError):
            raise ValueError(u"Repetition {} : saisissez un nombre.".format(index))
        if not text or math.isnan(number) or math.isinf(number):
            raise ValueError(u"Repetition {} : saisissez un nombre fini.".format(index))
        normalized.append(text)
    return normalized


def average_interims(interims):
    """Une case absente, vide ou invalide interdit une moyenne partielle."""
    fields = {}
    for field in interims:
        match = KEYWORD.match(field.get("keyword", ""))
        if not match:
            continue
        index = int(match.group(1))
        if index in fields:
            return "NA"
        fields[index] = field.get("value", "")
    if sorted(fields) != list(range(1, len(fields) + 1)):
        return "NA"
    try:
        values = normalize_values([fields[key] for key in sorted(fields)])
        # Diviser avant la somme evite le debordement d'une somme finie.
        result = math.fsum(float(value) / len(values) for value in values)
        return result if not math.isnan(result) and not math.isinf(result) else "NA"
    except (ValueError, TypeError, OverflowError):
        return "NA"


def mean_repetitions(uid):
    """Fonction importee par le moteur natif de Calculation de SENAITE."""
    from bika.lims import api
    analysis = api.get_object_by_uid(uid)
    if analysis is None:
        return "NA"
    return average_interims(analysis.getInterimFields())


def is_dynamic_calculation(calculation):
    if calculation is None:
        return False
    return (getattr(calculation, "trimeta_variable_repetitions", False) is True
            and calculation.getFormula() == FORMULA
            and list(calculation.getPythonImports()) == IMPORTS)


def is_repetition_calculation(calculation):
    """Reconnaissance stricte; aucun calcul personnalise n'est remplace."""
    if is_dynamic_calculation(calculation):
        return True
    if calculation is None:
        return False
    from senaite.trimeta.samplefields.defaults import build_formula, build_interims
    fields = []
    for field in calculation.getInterimFields():
        field = dict(field)
        # Les anciens profils ne stockaient pas ces deux options false.
        field.setdefault("hidden", False)
        field.setdefault("wide", False)
        fields.append(field)
    for count in (2, 3):
        if (calculation.Title() == u"Moyenne de {} repetitions".format(count)
                and calculation.getFormula() == build_formula(count)
                and fields == build_interims(count)
                and list(calculation.getPythonImports()) == [
                    {"module": "math", "function": "ceil"},
                    {"module": "math", "function": "floor"}]):
            return True
    return False
