# -*- coding: utf-8 -*-
"""
Compatibilite Python 2 / Python 3.

L'image `senaite/senaite:v2.6.0` deployee ici tourne en **Python 2.7**
(eggs cp27mu, /usr/local/bin/python -> 2.7.18). L'add-on doit donc
fonctionner sur les deux, faute de quoi certaines erreurs ne se
manifestent qu'en production.

Le piege principal est le type des chaines:

- sur Python 2, `str` designe des OCTETS et `unicode` du texte;
- sur Python 3, `str` designe du texte et `bytes` des octets.

Un `isinstance(valeur, str)` ecrit pour Python 3 est donc FAUX sur
Python 2 des que la valeur est du texte accentue -- et le
comportement qui s'ensuit est silencieux, pas une erreur franche:

- `str(u"Réception")` leve UnicodeEncodeError;
- `tuple(u"AnalysisRequest")` renvoie 15 caracteres au lieu d'un type
  de contenu, et une colonne de listing disparait sans explication.
"""

try:
    # Python 2
    text_type = unicode          # noqa: F821
    string_types = (str, unicode)  # noqa: F821
    PY2 = True
except NameError:
    # Python 3
    text_type = str
    string_types = (str,)
    PY2 = False


def to_text(value, default=u""):
    """Convertit n'importe quelle valeur en texte, sur les deux versions.

    Renvoie toujours du texte (`unicode` sur Python 2, `str` sur Python
    3), jamais des octets et jamais None. Les octets sont decodes en
    UTF-8, en remplacant les sequences invalides plutot qu'en levant:
    une donnee mal encodee ne doit pas empecher l'indexation d'un
    echantillon.
    """
    if value is None:
        return default
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace")
    if isinstance(value, text_type):
        return value
    return text_type(value)
