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


def col(msgid, default):
    """Libelle propre au tableau de bord.

    Pourquoi des identifiants dedies plutot que ceux du formulaire:
    un en-tete de colonne et une etiquette de champ n'ont pas les memes
    contraintes. "Poids a la reception (g)" est juste sur un
    formulaire; dans un en-tete, il se replie sur trois lignes et rend
    la ligne d'en-tetes illisible.

    Raccourcir les libelles existants aurait raccourci du meme coup
    ceux du formulaire d'echantillon, ou la version longue est la
    bonne. D'ou ce jeu d'identifiants prefixes `dashboard_`.
    """
    return _(msgid, default=default)


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
    ("Vanillin",      "VANILLINE",      col("dashboard_vanillin", u"Vanillin")),
    ("GlucoVanillin", "GLUCOVANILLINE", col("dashboard_gluco", u"Gluco-vanillin")),
    ("VanillicAcid",  "ACVANILLIQUE",   col("dashboard_vanillic", u"Vanillic ac.")),
    ("PHB",           "PHB",            col("dashboard_phb", u"PHB")),
    ("PHBAcid",       "ACPHB",          col("dashboard_phb_acid", u"PHB ac.")),
    ("Moisture",      "TH",             col("dashboard_th", u"TH")),
    ("WaterActivity", "AW",             col("dashboard_aw", u"AW")),
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
    ("SampleCode", col("dashboard_sample_code", u"Sample Code"),
     "getSampleCode", "getSampleCode"),
    ("Lot", col("dashboard_lot", u"Lot"),
     "getClientSampleID", "getClientSampleID"),
    ("Client", col("dashboard_client", u"Client"),
     "getClientTitle", "getClientTitle"),
    ("SampleType", col("dashboard_sample_type", u"Type"),
     "getSampleTypeTitle", None),
    ("Origin", col("dashboard_origin", u"Origin"),
     "getOrigin", "getOrigin"),
    ("ReceptionWeight", col("dashboard_weight", u"Weight (g)"),
     "getReceptionWeight", None),
    ("DateReceived", col("dashboard_received", u"Received"),
     "getDateReceived", "getDateReceived"),
    ("AnalysisStart", col("dashboard_start", u"Analysis start"),
     "getAnalysisStart", None),
    ("AnalysisEnd", col("dashboard_end", u"Analysis end"),
     "getAnalysisEnd", None),
    ("DateVerified", col("dashboard_validated", u"Validated"),
     "getDateVerified", "getDateVerified"),
)

# Les trois operateurs, places apres les resultats qu'ils concernent
# dans le document. Ils ferment donc le tableau.
OPERATOR_COLUMNS = (
    ("HPLCOperator", col("dashboard_op_hplc", u"Op. HPLC"),
     "getHPLCOperator"),
    ("MoistureOperator", col("dashboard_op_th", u"Op. TH"),
     "getMoistureOperator"),
    ("WaterActivityOperator", col("dashboard_op_aw", u"Op. AW"),
     "getWaterActivityOperator"),
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


# ---------------------------------------------------------------------
# Infobulles
# ---------------------------------------------------------------------
#
# Les en-tetes sont courts par necessite: vingt colonnes ne tiennent pas
# autrement. Le sens complet est donc rendu au survol.
#
# On reutilise ici les msgid LONGS -- ceux du formulaire d'echantillon,
# deja traduits. C'est exactement ce a quoi ils servent: dire la chose
# en entier quand la place ne manque pas.
COLUMN_HELP = (
    ("SampleCode",      _(u"Sample Code")),
    ("Lot",             _(u"Lot")),
    ("Client",          _(u"Client")),
    ("SampleType",      _(u"Sample Type")),
    ("Origin",          _(u"Origin")),
    ("ReceptionWeight", _(u"Reception Weight (g)")),
    ("DateReceived",    _(u"Date Received")),
    ("AnalysisStart",   _(u"Beginning of Analysis")),
    ("AnalysisEnd",     _(u"End of Analysis")),
    ("DateVerified",    _(u"Date Validated")),
    ("Vanillin",              _(u"Vanillin")),
    ("GlucoVanillin",         _(u"Gluco-vanillin")),
    ("VanillicAcid",          _(u"Vanillic acid")),
    ("PHB",                   _(u"PHB")),
    ("PHBAcid",               _(u"PHB acid")),
    ("Moisture",              _(u"Moisture (TH)")),
    ("WaterActivity",         _(u"Water activity (AW)")),
    ("HPLCOperator",          _(u"HPLC operator")),
    ("MoistureOperator",      _(u"Moisture operator")),
    ("WaterActivityOperator", _(u"Water activity operator")),
)


def get_column_help():
    """{cle de colonne: libelle complet} pour les infobulles."""
    return dict(COLUMN_HELP)


def get_column_labels():
    """{cle de colonne: intitule court affiche en en-tete}."""
    labels = {}
    for key, title, _attr, _index in METADATA_COLUMNS:
        labels[key] = title
    for key, _keyword, title in DASHBOARD_ANALYSES:
        labels[key] = title
    for key, title, _attr in OPERATOR_COLUMNS:
        labels[key] = title
    return labels


def get_metadata_map():
    """{cle de colonne: attribut du brain} pour les colonnes catalogue."""
    mapping = {}
    for key, _title, attr, _index in METADATA_COLUMNS:
        mapping[key] = attr
    for key, _title, attr in OPERATOR_COLUMNS:
        mapping[key] = attr
    return mapping
