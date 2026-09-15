---
name: senaite-addon
description: Conventions de developpement de l'add-on senaite.trimeta.samplefields pour SENAITE LIMS 2.6.0 (Plone 5.2 / Python 2.7 / Archetypes). A charger AVANT toute modification sous 2.6.0/addons/ - etendre le schema Sample, ajouter un index ou une colonne de catalogue, ajouter une colonne a un listing, surcharger une vue de senaite.core, ecrire un gabarit senaite.impress, ou ajouter une etape de mise a jour GenericSetup.
---

# Developper dans senaite.trimeta.samplefields

Add-on SENAITE pour Trimeta Group (laboratoire vanille). Il repond au
cahier des charges `AMELIORATIONS SENAITE LIMS.docx`, a la racine du
depot.

## Contraintes non negociables

**Python 2.7.** L'image `senaite/senaite:v2.6.0` tourne en Python 2.7
(eggs `cp27mu`, `setuptools==44.1.1`). Le code doit rester compatible
2.7 **et** 3.x :

- pas de f-strings, pas d'annotations, pas de `pathlib` ;
- `from __future__` n'est pas utilise dans ce depot : ne pas
  l'introduire sans raison ;
- pour tester un type chaine, **toujours** `compat.string_types`, jamais
  `isinstance(x, str)` : sur Python 2, une valeur `unicode` echouerait
  le test et `tuple()` la decouperait en caracteres. Un bug silencieux
  de ce type a deja fait disparaitre une colonne sans lever d'erreur.

**Archetypes, pas Dexterity.** `AnalysisRequest` est encore un type
Archetypes en 2.6.0. On l'etend avec `archetypes.schemaextender`.
(`archetypes.schemaextender` a ete retire de `senaite.core` dans les
versions 3.x : cet add-on ne migrera pas sans reecriture.)

**Le francais sans accents dans le code.** Commentaires et docstrings
sont en francais, mais sans caracteres accentues dans les sources
Python : l'encodage du container n'est pas garanti. Les libelles
utilisateur, eux, passent par `MessageFactory` et peuvent tout
contenir.

**Ne jamais changer l'apparence.** Le cahier des charges demande « les
memes interfaces ». Toute modification doit se fondre dans SENAITE :
memes composants (`senaite.app.listing`, widgets Archetypes natifs,
`ReferenceWidget`), memes classes CSS Bootstrap, aucun style maison
sauf necessite demontree.

## Les cinq points d'extension utilises ici

| Besoin | Mecanisme | Exemple dans le depot |
|---|---|---|
| Ajouter des champs au Sample | `IOrderableSchemaExtender` | `extender.py`, `qualitydata/extender.py` |
| Rendre un champ natif visible/modifiable | `ISchemaModifier` | `schema_modifier.py` |
| Indexer un champ schemaextender | indexeur nomme `plone.indexer` | `indexers.py` + `catalog.py` |
| Ajouter une colonne a un listing | `IListingViewAdapter` | `listings/` |
| Surcharger une vue de `senaite.core` | couche de navigateur (browser layer) | `interfaces.py` + `coa/` |

### 1. Etendre le schema

Un champ schemaextender **n'a pas d'accesseur de classe**. Il n'existe
aucun `AnalysisRequest.getSampleCode()`. Consequences :

- un index ZCatalog classique ne trouvera rien : il faut un indexeur
  nomme (point 3) ;
- en Python, on lit la valeur par `sample.getField("SampleCode").get(sample)`
  (voir `listings/base.get_sample_code`) ;
- dans un gabarit `senaite.impress`, SuperModel expose le champ par son
  **nom** : `model/SampleCode`, pas `model/getSampleCode`.

Poser `visible=ADD_VISIBLE` (`extender.py`) sur tout champ qui doit
apparaitre a la creation : sans `"add": "edit"`, les widgets AT
retombent sur `invisible` pour ce mode precis, meme si le champ est
bien dans le schema.

Pour une reference vers un contenu, utiliser
`bika.lims.browser.fields.UIDReferenceField` +
`senaite.core.browser.widgets.referencewidget.ReferenceWidget`. **Pas**
`Products.Archetypes.public.ReferenceField` : il provoque
`NameError: same_type` avec le moteur Chameleon de `ar_add2.pt`.

### 2. Index ou colonne de metadonnees ?

Les deux coutent a l'ecriture, pas la meme chose :

- **colonne** : le listing affiche la valeur sans reveiller l'objet
  depuis la ZODB. C'est ce qui rend utilisable un tableau de plusieurs
  centaines de lignes ;
- **index** : permet en plus de filtrer et trier, au prix d'une
  structure maintenue a chaque modification.

**N'indexer que ce sur quoi on filtre reellement.** Le reste est une
simple colonne.

Ne pas recreer ce qui existe : `getClientSampleID` (Lot),
`getClientTitle`, `getSampleTypeTitle`, `getDateReceived`,
`getDateVerified` sont natifs. Verifier avec `make dashboard-info`
avant d'ajouter quoi que ce soit.

### 3. Les trois fichiers d'un index

Ajouter une colonne de catalogue demande **trois** modifications
solidaires. En oublier une la laisse vide, en silence :

1. `catalog.py` : declarer dans `SAMPLE_INDEXES` et/ou `SAMPLE_COLUMNS` ;
2. `indexers.py` : ecrire l'indexeur nomme ;
3. `configure.zcml` : `<adapter name="getXxx" factory=".indexers.getXxx" />`
   — le `name` doit valoir **exactement** l'identifiant de
   `catalog.py`.

Puis : incrementer `profiles/default/metadata.xml`, ajouter
`upgrades/vNNNN.py` et son `<genericsetup:upgradeStep>`. L'etape
delegue a `setuphandlers.setup_catalogs()` + `reindex_catalog()`, pour
qu'une mise a jour et une installation neuve fassent rigoureusement la
meme chose.

Sans reindexation, les nouvelles colonnes restent vides pour tout
l'historique.

### 4. Adaptateurs de listing

Enregistrer **large** (`IListingView` + contexte quelconque) et
discriminer dans le code via `portal_types`. SENAITE deplace ses vues
de listing d'un module a l'autre entre versions mineures ; un chemin
devenu faux fait echouer le chargement du ZCML, donc le demarrage
complet de l'instance. Avec l'enregistrement large, au pire une colonne
disparait.

Toujours appeler `show_in_all_states()` : sans cela la colonne
n'apparait que dans l'onglet par defaut et disparait des qu'on clique
sur « Recus » ou « Publies ».

### 5. Surcharger une vue de senaite.core

`senaite.core` enregistre ses `browser:page` avec
`layer="bika.lims.interfaces.IBikaLIMS"`. Pour en reprendre une sans
patcher le code amont : declarer une couche plus specifique
(`interfaces.ITrimetaLayer(IBikaLIMS)`), l'activer par
`profiles/default/browserlayer.xml`, et reenregistrer la page avec
`layer=".interfaces.ITrimetaLayer"`. Le registre d'adaptateurs choisit
la plus specifique.

Meme principe pour un **adaptateur nomme** dont le `for` porte sur la
requete : `for="IClient .interfaces.ITrimetaLayer"` bat
`for="IClient IBrowserRequest"`.

Une couche activee par le profil se desactive a la desinstallation :
c'est reversible, contrairement a un monkey patch.

**Sous-classer, ne pas copier.** Herite de la classe amont et ne
redefinis que la methode concernee. Une copie se desynchronise a la
premiere mise a jour de SENAITE.

## Regles de robustesse tenues partout dans ce depot

**Ne jamais faire tomber une page pour une valeur manquante.** Chaque
hook (`folderitem`, `before_render`, remplissage de colonne) enveloppe
son travail dans un `try/except` qui journalise. Une colonne vide est
un desagrement ; un listing qui ne s'affiche plus est un arret de
travail.

**Une liste vide n'est pas « aucun resultat » dans une requete
catalogue.** Selon l'index, elle peut etre ignoree et ramener tout le
catalogue. Utiliser une valeur sentinelle impossible (voir
`dashboard/view.NO_MATCH`).

**Ne rien ajouter au rendu d'une vue de listing.**
`senaite.app.listing` reutilise la *meme vue* pour ses requetes AJAX :
du HTML prefixe dans `__call__` se retrouve devant la reponse JSON
(`JSON.parse: unexpected character at line 1 column 1`, tableau vide).
Passer par un **viewlet**.

**Les resultats censures ne sont pas des nombres.** SENAITE enregistre
les limites de detection sous la forme `<0.5` ou `>100`.
`results.to_number()` renvoie `None` : un filtre de plage les ecarte, et
c'est delibere.

**Versionner les ressources statiques.** `dashboard.js` est servi avec
`?v=N`. Sans cela un correctif deploye reste invisible. La version
existe a deux endroits (le script et le viewlet) et un test verifie
qu'elles concordent.

**Tout ce qui part dans un en-tete HTTP ou un nom de fichier doit etre
assaini.** Les champs libres (Code echantillon, Designation...) sont
saisis par l'utilisateur : ils peuvent contenir `/`, `\r\n`, des
accents. Voir `coa/filename.py`.

## Tests

Deux niveaux, les deux obligatoires avant de pousser :

    make test-pure     # logique pure, instantane, sans container
    make test          # tests d'integration, container requis

`tests/run_pure.py` remplace les symboles SENAITE par des doublures
minimales. Pour ajouter un cas pur : ecrire `tests/test_xxx.py`, puis
l'inscrire dans `PURE_CASES` — soit `None` (tout le fichier est pur),
soit la liste des classes purement logiques du fichier.

Les doublures sont volontairement minimales : si l'une derive de la
realite, l'import doit echouer bruyamment plutot que laisser passer un
test faux.

## Fichiers de reference

- `references/upstream-hooks.md` — les points exacts de `senaite.core`
  2.6.0 et `senaite.impress` 2.6.0 que l'add-on reprend, avec les
  signatures amont verbatim.
- `docs/lot1-parametrage.md` — les demandes reglees par paramtrage, sans
  code.
- `docs/lot4-coa.md` — gabarit COA et nommage des fichiers.
- `docs/lot5-tableau-de-bord.md` — conception du tableau de bord.
