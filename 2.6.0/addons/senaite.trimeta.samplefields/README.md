# senaite.trimeta.samplefields

Add-on SENAITE 2.6 pour Trimeta Group.

## Ce que fait l'add-on

- **Section Réception** — 15 champs obligatoires sur le formulaire
  d'échantillon (code échantillon, code article, désignation, poids,
  quantités, température, conditions, provenance, réceptionniste,
  contrat, bon d'entrée).
- **Section Analyse** — numéro de fiche, dates de début et de fin,
  préparateurs, longueur des gousses et descripteurs organoleptiques.
- **Suggestions partagées** — les valeurs saisies dans les champs
  libres sont mémorisées et reproposées à tous les postes. Les
  identifiants uniques (code échantillon, numéro de fiche, bon
  d'entrée) en sont volontairement exclus.
- **Date de réception modifiable** — un correctif permet de saisir une
  date de réception antérieure, sans qu'elle soit écrasée au moment de
  la transition « Receive ».
- **Section Assurance Qualité** — 41 champs facultatifs répartis en
  7 sous-sections (extraction, dosage HPLC, dessiccateur, AW mètre,
  vérification de performance des appareils, consommables, validation).
  Ils sont masqués à la création de l'échantillon et visibles ensuite,
  puisqu'ils sont renseignés après l'analyse.
- **Index de catalogue** — le code échantillon est indexé, ce qui le
  rend affichable, triable et filtrable dans les listings.
- **Champ « Lot »** — le champ natif `ClientSampleID` est présenté sous
  le libellé « Lot », et la référence en doublon est masquée.

## Installation

L'add-on est monté dans le container par `compose.yml` et compilé par
buildout via `custom.cfg`. Après toute modification du code :

```bash
make redeploy-addon
```

Puis, **une seule fois**, installer le profil depuis l'interface :

    Configuration du site → Modules complémentaires
    http://<hôte>:8080/senaite/prefs_install_products_form

Installer **« SENAITE Trimeta - champs personnalisés »**. C'est cette
étape qui crée les index de catalogue et réindexe les échantillons
déjà saisis.

Si l'add-on était déjà installé dans une version antérieure, jouer les
étapes de mise à jour :

    http://<hôte>:8080/senaite/portal_setup/manage_upgrades

## Tests

```bash
make test                    # toute la suite
make test-list               # liste les tests sans les exécuter
make test ARGS="-t test_sample_is_findable_by_code"
```

Les tests s'exécutent **dans le container**, sur une instance Plone
jetable montée par la couche de test de `senaite.core` : ils ne
touchent jamais les données de production.

Certains tests ne nécessitent aucun site Plone (vocabulaires,
normalisation d'index, déclaration du schéma) et s'exécutent en
quelques millisecondes ; les autres montent un site complet, ce qui
prend une minute au premier lancement.

## Architecture

| Fichier | Rôle |
|---|---|
| `extender.py` | Champs des sections Réception et Analyse |
| `qualitydata/` | Section Assurance Qualité (41 champs) |
| `schema_modifier.py` | Retouches sur les champs natifs |
| `patches/` | Correctif sur `after_receive` du workflow |
| `catalog.py` | Déclare les index et colonnes à créer |
| `indexers.py` | Indexeurs nommés pour les champs schemaextender |
| `setuphandlers.py` | Création des index + réindexation à l'installation |
| `upgrades/` | Étapes de mise à jour entre versions du profil |
| `suggestions.py` | Magasin de suggestions partagées (ZODB) |
| `browser/` | API JSON des suggestions, viewlet, JavaScript |
| `tests/` | Suite de tests |

### Pourquoi des indexeurs nommés

Les champs ajoutés par `archetypes.schemaextender` n'ont **pas**
d'accesseur sur la classe `AnalysisRequest` : `ExtensionField` fabrique
l'accesseur à la volée. Un index ZCatalog classique, qui résout son
attribut par `getattr(obj, "getSampleCode")`, resterait donc vide en
silence — sans erreur, avec juste des cases blanches dans les listings.

D'où le passage par `plone.indexer` : un adaptateur nommé que Plone
consulte via `IndexableObjectWrapper`, aussi bien pour l'index que pour
la colonne de métadonnées.

### Le champ « Lot »

Il n'y a pas de champ `Lot` dans cet add-on, et c'est délibéré. Le
« Lot » du cahier des charges correspond au champ natif
**`ClientSampleID`** de SENAITE — la référence que le client donne à
son propre échantillon. Il est déjà indexé *et* déjà en colonne de
métadonnées dans le `sample_catalog` de `senaite.core`. Il suffit de le
renommer « Lot » dans l'interface.

Le test `test_lot_uses_the_native_client_sample_id` documente ce choix
et alerte si SENAITE cessait de fournir cet index.

### La section Assurance Qualité

Les 41 champs se ramènent à cinq formes seulement : une date, un
opérateur, une conformité OK/NOK, un comptage 1/2/3, un texte libre.
Chaque forme est une fabrique dans `qualitydata/fields.py` ; les champs
eux-mêmes sont déclarés par sous-section dans `qualitydata/extender.py`.

Cette structure `SECTIONS` est la source unique de vérité : elle produit
la liste plate remise à schemaextender, l'ordre de l'onglet, **et** les
intitulés de sous-section dessinés dans le formulaire par
`quality_sections.js`. Ajouter un champ à une sous-section suffit — le
reste suit.

Les lots de solvants et les numéros de série bénéficient du « rajout
mémorisé ». Comme ils sont saisis après la création de l'échantillon,
un second abonné (`on_sample_modified`) est nécessaire : celui qui
écoute la création ne les verrait jamais.

## Traductions

Le catalogue français est dans `locales/fr/LC_MESSAGES/`. Le `.mo` doit
être recompilé après toute modification du `.po` :

```bash
msgfmt -o senaite.trimeta.samplefields.mo senaite.trimeta.samplefields.po
```

Par convention, les traductions existantes sont **sans accents**.
Conserver cette convention tant que le catalogue n'est pas repris
d'un bloc, pour éviter un fichier à moitié accentué.

## Versions du profil

| Version | Contenu |
|---|---|
| 1000 | Champs Réception et Analyse (avant profil GenericSetup) |
| 1001 | Index et colonne `getSampleCode` dans le `sample_catalog` |
