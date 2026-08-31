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
- **Colonnes de listing** — le code échantillon apparaît dans la liste
  des Échantillons (avec le Lot), dans la grille de saisie des Work
  Sheets et dans la liste des rapports d'analyse.

## Configuration de la machine

Chaque serveur a son adresse et ses ports libres. Ces valeurs vivent
dans `2.6.0/.env`, qui n'est **pas** versionné :

```bash
cd 2.6.0
cp .env.example .env
$EDITOR .env          # SENAITE_PORT, SENAITE_HOST
make down && make up
```

`make debug` affiche l'adresse publiée et indique si le port vient de
`.env` ou de la valeur par défaut. `make doctor` liste les ports libres
parmi les candidats habituels.

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

### Si `git checkout` échoue avec « Permission denied »

`compose.yml` monte ce répertoire dans le container. Quand buildout
s'exécute dedans, il y écrit des fichiers (`egg-info`, `__pycache__`)
sous l'identité de l'utilisateur du container — et git ne peut alors
plus les modifier depuis l'hôte.

```bash
cd 2.6.0
make fix-perms
```

Le script essaie d'abord `podman unshare`, qui ne demande aucun droit
root, puis retombe sur `sudo chown` si nécessaire.

`make redeploy-addon` l'exécute automatiquement juste après buildout,
et il supprime au passage les `.pyc` récupérés.

**La cause de fond est ailleurs** : Python 2 écrit son bytecode *à côté*
des sources, pas dans un `__pycache__`. Le container en produisait donc
dans `addons/` — monté depuis l'hôte — à chaque import, c'est-à-dire à
chaque démarrage de SENAITE. `compose.yml` pose maintenant
`PYTHONDONTWRITEBYTECODE=1`, ce qui supprime le problème à la racine.

Ce réglage ne prend effet qu'après recréation du container :

```bash
make down && make up
```

`egg-info/` n'est volontairement **pas** versionné : buildout le
régénère à chaque déploiement. Après un `git checkout` qui l'a supprimé,
relancer `make redeploy-addon` pour le reconstruire — sans lui, le
paquet n'est pas résolu et l'add-on ne se charge pas.

## Tests

```bash
make test-pure               # logique pure, instantané, sans container
make test                    # toute la suite, dans le container
make test-list               # liste les tests sans les exécuter
make test ARGS="-t test_sample_is_findable_by_code"
```

`make test` s'exécute **dans le container**, sur une instance Plone
jetable montée par la couche de test de `senaite.core` : les données de
production ne sont jamais touchées. Le premier lancement prend une
minute, le temps de monter le site.

`make test-pure` couvre la partie de l'add-on qui ne dépend ni de Zope
ni de SENAITE — déclaration des champs, vocabulaires, normalisation
d'index, insertion de colonnes, discrimination des adaptateurs de
listing. Il tourne en quelques millisecondes sur n'importe quel poste,
en remplaçant les imports SENAITE par des doublures minimales.

**`make test-pure` ne remplace pas `make test`.** Il ne prouve pas que
l'add-on fonctionne dans SENAITE : l'installation du profil, les index
de catalogue, le schéma sur un échantillon réel et les suggestions ont
besoin d'un vrai site.

## Python 2, pas Python 3

L'image `senaite/senaite:v2.6.0` déployée ici tourne en **Python 2.7**
(eggs `cp27mu`, `/usr/local/bin/python` → 2.7.18). Le code de l'add-on
doit rester compatible avec les deux versions.

Le piège principal est le type des chaînes : sur Python 2, `str`
désigne des **octets** et `unicode` du texte ; sur Python 3, c'est
l'inverse. Un `isinstance(valeur, str)` écrit pour Python 3 est donc
faux sur Python 2, et le comportement qui s'ensuit est **silencieux** :

- `str(u"Réception")` lève `UnicodeEncodeError` — l'échantillon devient
  non indexable ;
- `tuple(u"AnalysisRequest")` renvoie quinze caractères au lieu d'un
  type de contenu — une colonne de listing disparaît sans erreur.

Utiliser `compat.string_types` et `compat.to_text` plutôt que `str`.
`unittest.assertLogs` n'existe pas non plus sur 2.7 : voir
`capture_logs` dans `tests/test_listings.py`.

`tests/run_pure.py` fait exception : il s'exécute sur le **Python 3 de
l'hôte**, jamais dans le container, et peut donc utiliser `importlib`.

## Architecture

| Fichier | Rôle |
|---|---|
| `extender.py` | Champs des sections Réception et Analyse |
| `qualitydata/` | Section Assurance Qualité (41 champs) |
| `listings/` | Colonnes ajoutées aux listings |
| `schema_modifier.py` | Retouches sur les champs natifs |
| `patches/` | Correctif sur `after_receive` du workflow |
| `compat.py` | Compatibilité Python 2 / 3 sur les chaînes |
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

### Les adaptateurs de listing

L'usage courant est d'enregistrer un `IListingViewAdapter` pour une
classe de vue précise. C'est plus fin, mais fragile : SENAITE a déplacé
ses vues de listing d'un module à l'autre au fil des versions 2.x, et
un chemin devenu faux fait échouer le chargement du ZCML — donc le
démarrage complet de l'instance, pas seulement la colonne concernée.

Les adaptateurs sont donc enregistrés pour l'interface `IListingView` et
un contexte quelconque, et chacun déclare ce sur quoi il s'applique via
sa liste `portal_types`. Le coût est de deux comparaisons de chaînes par
listing affiché ; le bénéfice est qu'une réorganisation interne de
SENAITE fait au pire disparaître une colonne, jamais tomber le site.

Même logique pour les erreurs : `before_render` et `folder_item`
attrapent tout et journalisent. Mieux vaut une colonne vide qu'un écran
de listing qui ne s'affiche plus.

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
| 1002 | Index `getOrigin` et colonnes du tableau de bord (lot 5) |
| 1003 | Index `getTrimetaSampleTypeUID` (filtre Type d'echantillon) |
