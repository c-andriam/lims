# -*- coding: utf-8 -*-
"""
Declaration des index et colonnes de catalogue ajoutes par l'add-on.

Pourquoi c'est necessaire
-------------------------
Les champs ajoutes par archetypes.schemaextender n'existent pas en tant
qu'attributs de l'objet: ExtensionField.getAccessor() fabrique un
accesseur a la volee, mais aucune methode getSampleCode() n'est generee
sur la classe AnalysisRequest. Un index ZCatalog classique, qui resout
son attribut via getattr(obj, "getSampleCode"), ne trouverait donc rien.

La solution est un indexeur nomme (plone.indexer), voir indexers.py.
Ce module ne fait que declarer QUOI indexer; setuphandlers.py se charge
de la creation effective au moment de l'installation du profil.

Index ou simple colonne de metadonnees ?
----------------------------------------
Les deux ont un cout a l'ecriture, mais pas le meme:

- une COLONNE de metadonnees permet a un listing d'afficher la valeur
  sans reveiller l'objet depuis la ZODB. C'est ce qui rend un tableau
  de plusieurs centaines de lignes utilisable;
- un INDEX permet en plus de filtrer et de trier dessus, au prix d'une
  structure de donnees supplementaire maintenue a chaque modification.

On n'indexe donc que ce sur quoi le tableau de bord filtre reellement
(la Provenance), et on se contente de colonnes pour ce qui n'est
qu'affiche. Ajouter un index plus tard reste une ligne ici plus une
etape de mise a jour.

Note: "Lot" n'apparait pas ici volontairement. Il correspond au champ
natif ClientSampleID, deja indexe ET deja en colonne de metadonnees
dans le sample_catalog de senaite.core (getClientSampleID). Rien a
creer de ce cote. Meme chose pour le Client, le Type d'echantillon, la
Date de reception et la Date de validation, tous natifs.
"""

from senaite.core.catalog import SAMPLE_CATALOG

# (id de l'index, type d'index, attribut indexe ou None)
#
# indexed_attrs=None => l'index utilise son propre id comme nom
# d'attribut, ce qui le fait passer par l'IndexableObjectWrapper de
# Plone et donc par notre indexeur nomme.
SAMPLE_INDEXES = (
    ("getSampleCode", "FieldIndex", None),
    # Filtre "Provenance" du tableau de bord (lot 5).
    ("getOrigin", "FieldIndex", None),
)

# Colonnes de metadonnees: permettent aux listings d'afficher la valeur
# sans reveiller l'objet complet depuis la ZODB.
#
# Les sept dernieres alimentent le tableau de bord du lot 5. Chacune a
# son indexeur nomme dans indexers.py et son enregistrement dans
# configure.zcml -- les trois vont ensemble, ajouter une colonne ici
# sans les deux autres la laisserait vide en silence.
SAMPLE_COLUMNS = (
    "getSampleCode",
    "getOrigin",
    "getReceptionWeight",
    "getAnalysisStart",
    "getAnalysisEnd",
    "getHPLCOperator",
    "getMoistureOperator",
    "getWaterActivityOperator",
)

# Regroupement par catalogue, consomme par setuphandlers et upgrades.
CATALOGS = (
    (SAMPLE_CATALOG, SAMPLE_INDEXES, SAMPLE_COLUMNS),
)
