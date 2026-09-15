# -*- coding: utf-8 -*-
"""
Lecture et traduction des filtres du tableau de bord.

Le formulaire de filtres est un `<form method="get">` ordinaire: cliquer
sur "Rechercher" recharge la page avec les parametres dans l'URL. Aucun
JavaScript, donc rien qui puisse se desynchroniser de ce qu'affiche le
tableau, et une recherche reste partageable par simple copie de l'URL.

Les valeurs lues suivent ensuite deux chemins:

1. traduites en requete catalogue (`build_query`), fusionnee dans le
   `contentFilter` de la vue;
2. renvoyees au listing en champs caches (`hidden_fields`). C'est
   indispensable: la pagination et le tri de senaite.app.listing passent
   par AJAX, et sans ces champs la deuxieme page d'un resultat filtre
   afficherait tout le catalogue.

Tout ce module est de la logique pure -- aucune dependance a Zope --
donc entierement couvert par `make test-pure`.
"""

try:                                   # Python 2
    from urlparse import parse_qsl
except ImportError:                    # Python 3
    from urllib.parse import parse_qsl

from senaite.trimeta.samplefields.compat import to_text

# Prefixe des parametres, pour ne pas entrer en collision avec ceux de
# senaite.app.listing (form_id, pagesize, sort_on...).
PREFIX = "trimeta_"

# (nom du filtre, index du sample_catalog interroge)
#
# Les deux premiers sont des index natifs de senaite.core; les deux
# suivants sont crees par l'add-on (profils 1002 et 1003), justement
# parce que senaite ne les indexe pas.
SIMPLE_FILTERS = (
    ("lot", "getClientSampleID"),
    ("client", "getClientUID"),
    ("sample_type", "getTrimetaSampleTypeUID"),
    ("origin", "getOrigin"),
)

# Periode, sur la date de reception (DateIndex natif).
DATE_INDEX = "getDateReceived"
DATE_FILTERS = ("date_from", "date_to")

# Plage sur le resultat de vanilline. Ne peut pas etre une requete
# catalogue: getResult n'est qu'une colonne de metadonnees. Voir
# results.sample_ids_in_range.
RANGE_FILTERS = ("van_min", "van_max")

# Filtres dont la valeur est une liste d'UID (voir group_options). Jamais
# les champs texte: un Lot ou une Provenance peut contenir une virgule.
MULTI_VALUE_FILTERS = ("client", "sample_type")
MULTI_VALUE_SEPARATOR = ","

ALL_FILTERS = (
    tuple([name for name, _index in SIMPLE_FILTERS])
    + DATE_FILTERS
    + RANGE_FILTERS
)


def merged_form(form, query_string="", form_id=""):
    """Parametres de filtre, d'ou qu'ils viennent.

    :param form: request.form
    :param query_string: QUERY_STRING brut de la requete
    :param form_id: identifiant du formulaire du listing

    Trois sources, du moins au plus prioritaire:

    1. l'adresse: pour ses appels AJAX, le script de senaite.app.listing
       ajoute les parametres de la page (`location.search`) a l'URL mais
       envoie un corps JSON, et Zope n'analyse alors pas l'adresse;
    2. les cles prefixees `<form_id>_`, forme sous laquelle
       senaite.app.listing injecte les donnees AJAX dans le formulaire;
    3. le formulaire classique (chargement de la page).
    """
    form = form or {}
    # form_id commence lui aussi par "trimeta_": ses cles ne doivent pas
    # etre prises pour des filtres non prefixes.
    form_prefix = u"{}_".format(form_id) if form_id else None

    def is_filter_key(key):
        return key.startswith(PREFIX) and not (
            form_prefix and key.startswith(form_prefix))

    merged = {}
    for key, value in parse_qsl(query_string or "", keep_blank_values=False):
        if is_filter_key(key):
            merged[key] = value
    if form_prefix:
        for key, value in form.items():
            if key.startswith(form_prefix) and is_filter_key(key[len(form_prefix):]):
                merged[key[len(form_prefix):]] = value
    for key, value in form.items():
        if is_filter_key(key):
            merged[key] = value
    return merged


def read_filters(form):
    """Extrait les filtres d'un formulaire de requete.

    :param form: dictionnaire des parametres (request.form)
    :returns: {nom du filtre: valeur texte}, seulement les non vides

    Les valeurs sont normalisees en texte et debarrassees des espaces:
    une case laissee avec un espace ne doit pas produire un filtre qui
    ne trouve rien.
    """
    form = form or {}
    filters = {}
    for name in ALL_FILTERS:
        value = to_text(form.get(PREFIX + name, "")).strip()
        if value:
            filters[name] = value
    return filters


def date_range_query(date_from, date_to, to_date):
    """Requete de plage sur un DateIndex, ou None.

    :param to_date: convertisseur (texte, fin_de_journee) -> date ou None

    Le convertisseur est injecte plutot qu'importe: DateTime appartient
    a Zope, et ce module doit rester testable sans lui.

    La borne haute est prise en fin de journee. Sans cela, filtrer
    "jusqu'au 31 août" exclurait tout ce qui a ete recu ce jour-la apres
    minuit -- c'est-a-dire tout.
    """
    low = to_date(date_from, False) if date_from else None
    high = to_date(date_to, True) if date_to else None

    if low is not None and high is not None:
        return {"query": [low, high], "range": "min:max"}
    if low is not None:
        return {"query": low, "range": "min"}
    if high is not None:
        return {"query": high, "range": "max"}
    return None


def build_query(filters, to_date=None):
    """Traduit les filtres en fragment de requete catalogue.

    :param filters: sortie de read_filters
    :param to_date: convertisseur de date; sans lui la periode est
        ignoree plutot que de produire une requete invalide
    :returns: dict a fusionner dans le contentFilter

    Le filtre de plage sur la vanilline n'apparait pas ici: il ne peut
    pas s'exprimer en requete catalogue et se resout a part, en amont
    (voir results.sample_ids_in_range).
    """
    filters = filters or {}
    query = {}

    for name, index in SIMPLE_FILTERS:
        value = filters.get(name)
        if not value:
            continue
        if name in MULTI_VALUE_FILTERS and MULTI_VALUE_SEPARATOR in value:
            value = [v.strip() for v in value.split(MULTI_VALUE_SEPARATOR)
                     if v.strip()]
        query[index] = value

    if to_date is not None:
        date_query = date_range_query(
            filters.get("date_from"), filters.get("date_to"), to_date)
        if date_query is not None:
            query[DATE_INDEX] = date_query

    return query


def hidden_fields(filters):
    """Champs caches a poser sur le formulaire du listing.

    Sans eux, cliquer sur "page 2" d'un resultat filtre rechargerait le
    catalogue entier: la requete AJAX ne transporte que ce que le
    formulaire contient.
    """
    return [
        {"name": PREFIX + name, "value": filters[name]}
        for name in ALL_FILTERS
        if filters.get(name)
    ]


def is_active(filters):
    """Un filtre est-il pose ? Sert a afficher le bouton de remise a zero."""
    return bool(filters)


def group_options(options):
    """Options d'une liste deroulante: une entree par nom, aucune vide.

    :param options: [(uid, intitule)]
    :returns: [(uids separes par des virgules, intitule)], tries

    Plusieurs objets de meme nom (types d'echantillon crees en double)
    donnent une seule entree, qui filtre sur tous leurs UID. Un objet
    sans intitule n'est pas proposable: il est ecarte.
    """
    groups = {}
    for uid, label in options:
        label = to_text(label).strip()
        if not label or not uid:
            continue
        key = label.lower()
        if key not in groups:
            groups[key] = (label, [])
        groups[key][1].append(to_text(uid))
    return sorted(
        [(MULTI_VALUE_SEPARATOR.join(sorted(uids)), label)
         for label, uids in groups.values()],
        key=lambda pair: pair[1].lower())
