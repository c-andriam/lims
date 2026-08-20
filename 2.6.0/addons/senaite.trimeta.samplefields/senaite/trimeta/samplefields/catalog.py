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

Note: "Lot" n'apparait pas ici volontairement. Il correspond au champ
natif ClientSampleID, deja indexe ET deja en colonne de metadonnees
dans le sample_catalog de senaite.core (getClientSampleID). Rien a
creer de ce cote.
"""

from senaite.core.catalog import SAMPLE_CATALOG

# (id de l'index, type d'index, attribut indexe ou None)
#
# indexed_attrs=None => l'index utilise son propre id comme nom
# d'attribut, ce qui le fait passer par l'IndexableObjectWrapper de
# Plone et donc par notre indexeur nomme.
SAMPLE_INDEXES = (
    ("getSampleCode", "FieldIndex", None),
)

# Colonnes de metadonnees: permettent aux listings d'afficher la valeur
# sans reveiller l'objet complet depuis la ZODB.
SAMPLE_COLUMNS = (
    "getSampleCode",
)

# Regroupement par catalogue, consomme par setuphandlers et upgrades.
CATALOGS = (
    (SAMPLE_CATALOG, SAMPLE_INDEXES, SAMPLE_COLUMNS),
)
