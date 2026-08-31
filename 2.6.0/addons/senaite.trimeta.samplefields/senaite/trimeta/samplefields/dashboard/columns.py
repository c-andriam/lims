# -*- coding: utf-8 -*-
"""
Definition des vingt colonnes du tableau de bord.

L'ordre est celui du document AMELIORATIONS SENAITE LIMS, colonne par
colonne. Chaque entree dit d'ou vient la valeur, ce qui rend le cout
visible d'un coup d'oeil:

- `metadata`  colonne de metadonnees du sample_catalog: lecture directe
              sur le brain, aucun objet reveille depuis la ZODB;
- `analysis`  resultat d'analyse: rempli en UNE requete groupee pour
              toute la page (voir results.py).

Seules les colonnes adossees a un INDEX sont declarees triables.
senaite.app.listing trie via le catalogue: proposer le tri sur une
colonne qui n'a pas d'index donnerait un en-tete cliquable qui ne trie
rien -- pire qu'un en-tete inerte, parce que l'utilisateur croit que
le tri a eu lieu.
"""

import collections

from zope.i18nmessageid import MessageFactory

_ = MessageFactory("senaite.trimeta.samplefields")


# ---------------------------------------------------------------------
# Les sept services d'analyse affiches en colonnes
# ---------------------------------------------------------------------
#
# ATTENTION -- LES MOTS-CLES CI-DESSOUS SONT A CONFIRMER.
#
# Une analyse est retrouvee par son MOT-CLE (Keyword), pas par son
# intitule: l'intitule peut etre renomme dans l'interface, le mot-cle
# est la cle stable.
#
# Ces mots-cles sont des donnees saisies dans l'instance, pas du code.
# Ils se lisent dans:
#
#     Configuration > Analyses  (Setup > Analysis Services)
#     /senaite/bika_setup/bika_analysisservices
#
# et c'est la colonne "Keyword" qui donne la valeur exacte.
#
# Un mot-cle qui ne correspond a aucun service ne provoque PAS d'erreur:
# la colonne reste simplement vide. C'est confortable, mais ca veut dire
# qu'une faute de frappe ici est silencieuse -- d'ou l'avertissement
# journalise par la vue quand une colonne ne ramene jamais rien.
#
# (identifiant de colonne, mot-cle du service, intitule affiche)
DASHBOARD_ANALYSES = (
    ("Vanillin",        "VANILLINE",       _(u"Vanillin")),
    ("GlucoVanillin",   "GLUCOVANILLINE",  _(u"Gluco-vanillin")),
    ("VanillicAcid",    "ACVANILLIQUE",    _(u"Vanillic acid")),
    ("PHB",             "PHB",             _(u"PHB")),
    ("PHBAcid",         "ACPHB",           _(u"PHB acid")),
    ("Moisture",        "TH",              _(u"Moisture (TH)")),
    ("WaterActivity",   "AW",              _(u"Water activity (AW)")),
)

# La colonne sur laquelle porte le filtre de plage du document.
VANILLIN_COLUMN = "Vanillin"


def get_keywords():
    """Mots-cles des services affiches, dans l'ordre des colonnes."""
    return [keyword for _id, keyword, _label in DASHBOARD_ANALYSES]


def get_keyword_for(column_id):
    """Mot-cle du service adosse a une colonne, ou None."""
    for cid, keyword, _label in DASHBOARD_ANALYSES:
        if cid == column_id:
            return keyword
    return None


# ---------------------------------------------------------------------
# Les colonnes issues du catalogue
# ---------------------------------------------------------------------
#
# (identifiant, intitule, attribut du brain, index de tri ou None)
#
# L'identifiant sert de cle de colonne dans le listing; l'attribut est
# la colonne de metadonnees lue sur le brain. Les deux different quand
# le nom technique n'a rien a dire a l'utilisateur.
METADATA_COLUMNS = (
    ("SampleCode",    _(u"Sample Code"),      "getSampleCode",     "getSampleCode"),
    ("Lot",           _(u"Lot"),              "getClientSampleID", "getClientSampleID"),
    ("Client",        _(u"Client"),           "getClientTitle",    "getClientTitle"),
    ("SampleType",    _(u"Sample Type"),      "getSampleTypeTitle", None),
    ("Origin",        _(u"Origin"),           "getOrigin",         "getOrigin"),
    ("ReceptionWeight", _(u"Reception Weight (g)"), "getReceptionWeight", None),
    ("DateReceived",  _(u"Date Received"),    "getDateReceived",   "getDateReceived"),
    ("AnalysisStart", _(u"Beginning of Analysis"), "getAnalysisStart", None),
    ("AnalysisEnd",   _(u"End of Analysis"),  "getAnalysisEnd",    None),
    ("DateVerified",  _(u"Date Validated"),   "getDateVerified",   "getDateVerified"),
)

# Les trois operateurs, places apres les resultats qu'ils concernent
# dans le document. Ils ferment donc le tableau.
OPERATOR_COLUMNS = (
    ("HPLCOperator",          _(u"HPLC operator"),           "getHPLCOperator"),
    ("MoistureOperator",      _(u"Moisture operator"),       "getMoistureOperator"),
    ("WaterActivityOperator", _(u"Water activity operator"), "getWaterActivityOperator"),
)


def build_columns():
    """Les vingt colonnes, dans l'ordre du cahier des charges."""
    columns = collections.OrderedDict()

    for key, title, _attr, index in METADATA_COLUMNS:
        definition = {"title": title, "toggle": True}
        if index:
            definition["index"] = index
            definition["sortable"] = True
        else:
            # Pas d'index: on le dit, plutot que de laisser croire a un
            # tri qui n'aurait pas lieu.
            definition["sortable"] = False
        columns[key] = definition

    for key, _keyword, title in DASHBOARD_ANALYSES:
        columns[key] = {
            "title": title,
            "toggle": True,
            # Un resultat d'analyse ne vit pas dans le sample_catalog:
            # aucun index ne peut le trier.
            "sortable": False,
        }

    for key, title, _attr in OPERATOR_COLUMNS:
        columns[key] = {"title": title, "toggle": True, "sortable": False}

    return columns


def get_metadata_map():
    """{cle de colonne: attribut du brain} pour les colonnes catalogue."""
    mapping = {}
    for key, _title, attr, _index in METADATA_COLUMNS:
        mapping[key] = attr
    for key, _title, attr in OPERATOR_COLUMNS:
        mapping[key] = attr
    return mapping
