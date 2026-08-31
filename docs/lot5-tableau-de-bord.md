# Lot 5 — Tableau de bord

Conception et état d'avancement du module « tableau de bord » demandé
en fin du document *AMÉLIORATIONS SENAITE LIMS*.

---

## Ce qui est demandé

> Ajouter un module tableau de bord pour faciliter la visualisation et
> l'exploitation des données.

Vingt colonnes, six filtres et un bouton de recherche.

### Les vingt colonnes

| # | Colonne | D'où vient la valeur | État |
|---|---|---|---|
| 1 | Code échantillon | `getSampleCode` (add-on, profil 1001) | ✅ |
| 2 | Lot | `getClientSampleID` (natif) | ✅ |
| 3 | Client | `getClientTitle` (natif) | ✅ |
| 4 | Type d'échantillon | `getSampleTypeTitle` (natif) | ✅ |
| 5 | Provenance | `getOrigin` (add-on, profil **1002**) | ✅ |
| 6 | Poids à la réception | `getReceptionWeight` (profil 1002) | ✅ |
| 7 | Date de réception | `getDateReceived` (natif) | ✅ |
| 8 | Début d'analyse | `getAnalysisStart` (profil 1002) | ✅ |
| 9 | Fin d'analyse | `getAnalysisEnd` (profil 1002) | ✅ |
| 10 | Date de validation | `getDateVerified` (natif) | ✅ |
| 11 | Vanilline | résultat d'analyse | ⏳ |
| 12 | Gluco-vanilline | résultat d'analyse | ⏳ |
| 13 | AC Vanillique | résultat d'analyse | ⏳ |
| 14 | PHB | résultat d'analyse | ⏳ |
| 15 | AC PHB | résultat d'analyse | ⏳ |
| 16 | Opérateur HPLC | `getHPLCOperator` (profil 1002) | ✅ |
| 17 | TH (taux d'humidité) | résultat d'analyse | ⏳ |
| 18 | Opérateur TH | `getMoistureOperator` (profil 1002) | ✅ |
| 19 | AW (activité de l'eau) | résultat d'analyse | ⏳ |
| 20 | Opérateur AW | `getWaterActivityOperator` (profil 1002) | ✅ |

✅ = la valeur est disponible dans le catalogue.
⏳ = reste à faire, voir « Les colonnes de résultats » plus bas.

### Les six filtres

| Filtre | Index utilisé |
|---|---|
| Période (date de réception) | `getDateReceived`, natif, requête par plage |
| Lot | `getClientSampleID`, natif |
| Client | `getClientTitle` / `getClientUID`, natifs, indexés |
| Type d'échantillon | `getTrimetaSampleTypeUID`, **créé par le profil 1003** |
| Provenance | `getOrigin`, **créé par le profil 1002** |
| Vanilline | résultat d'analyse, **plage min / max** |

> **Corrigé après inventaire de l'instance.** Une version antérieure
> de ce document annonçait `getSampleTypeUID` comme index natif du
> `sample_catalog`. C'est faux : `getSampleTypeTitle` et
> `getSampleTypeUID` y sont des **colonnes de métadonnées, pas des
> index**, et `AnalysisRequest` n'expose même aucun accesseur
> `getSampleTypeUID` — les seuls existants sont sur `Analysis` et sur
> `SampleType`. D'où l'index propre à l'add-on, décrit ci-dessous.

#### Pourquoi un index à nous pour le type d'échantillon

`getTrimetaSampleTypeUID` est alimenté par notre propre indexeur, qui
lit le champ natif `SampleType` et en tire l'UID. Trois raisons :

1. il ne dépend d'aucun détail interne de SENAITE ;
2. il ne peut pas entrer en collision avec un index que `senaite.core`
   ajouterait dans une version future ;
3. c'est l'**UID** qui est indexé, pas l'intitulé : renommer un type
   d'échantillon ne casse aucun filtre enregistré.

C'est le même raisonnement que pour `getOrigin`, et l'inverse de celui
retenu pour le « Lot » — là, le champ natif `ClientSampleID` était déjà
indexé, il n'y avait rien à créer.

---

## Décisions prises

### Colonne de métadonnées ou index ?

Les deux coûtent à l'écriture, mais pas la même chose :

- une **colonne de métadonnées** laisse le listing afficher la valeur
  sans réveiller l'objet depuis la ZODB — c'est ce qui rend un tableau
  de plusieurs centaines de lignes utilisable ;
- un **index** permet en plus de filtrer et trier, au prix d'une
  structure maintenue à chaque modification d'échantillon.

Seule la **Provenance** est indexée, parce qu'elle porte un filtre. Le
poids, les dates d'analyse et les trois opérateurs sont de simples
colonnes. Ajouter un index plus tard reste une ligne dans `catalog.py`
et une étape de mise à jour.

### Le filtre Vanilline est une plage

Deux cases, « de ___ à ___ ». C'est ce qui permet de sortir les lots
hors spécification, l'usage réel attendu au laboratoire. Un simple
seuil ou une case à cocher « a une valeur » ne le permettrait pas.

Conséquence technique : ce filtre ne peut pas être une requête
catalogue sur le `sample_catalog`, puisque la vanilline n'est pas un
champ de l'échantillon mais le résultat d'une analyse. Il s'applique
donc **après** la requête, sur les résultats déjà rapatriés.

### Les colonnes de résultats

Les sept colonnes de résultats ne sont pas des champs de l'échantillon :
ce sont des objets `Analysis` rattachés à lui. L'inventaire de
l'`analysis_catalog` a confirmé que tout ce qu'il faut y existe déjà,
en index **et** en colonne de métadonnées :

| Élément | Rôle | Statut |
|---|---|---|
| `getRequestID` | identifiant de l'échantillon parent | index + colonne |
| `getKeyword` | mot-clé du service | index + colonne |
| `getResult` | résultat saisi | colonne |
| `getResultCaptureDate` | date de saisie | index + colonne |

Une **seule requête** ramène donc les résultats de toute la page
affichée, sans réveiller un seul objet depuis la ZODB. Le coût ne
dépend pas du nombre de lignes.

L'alternative — dénormaliser le résultat dans le `sample_catalog` au
moment de l'indexation — aurait été plus rapide encore à l'affichage,
mais il aurait fallu réindexer l'échantillon à chaque saisie de
résultat. Un état dupliqué à tenir cohérent est une source de valeurs
fausses en silence ; c'est écarté.

#### Le cas des reprises

Un échantillon peut porter **plusieurs** analyses pour un même mot-clé,
quand une première a été reprise. La règle retenue, testée :

1. un résultat renseigné l'emporte sur une case vide ;
2. entre deux résultats renseignés, le plus récemment saisi gagne ;
3. sans date exploitable, le dernier rencontré gagne.

#### Le cas des résultats censurés

SENAITE enregistre les limites de détection sous la forme `<0.5` ou
`>100`. Ces valeurs ne sont **pas** des nombres : le filtre de plage
les écarte, et c'est délibéré. Traiter `<0.5` comme `0.5` le ferait
entrer dans un intervalle auquel il n'appartient peut-être pas, sans
que personne ne s'en aperçoive.

Conséquence à connaître : un échantillon dont la vanilline vaut `<0.5`
disparaît dès qu'une borne est posée sur cette colonne.

#### Où s'applique le filtre de plage

Avant la pagination, sinon le nombre de pages annoncé serait faux. La
mécanique : requête sur l'`analysis_catalog` pour le seul mot-clé
concerné → tri numérique en Python (`getResult` n'est qu'une colonne,
pas un index) → liste d'identifiants passée au `sample_catalog` via
`getId`, qui lui est indexé.

### Les services sont retrouvés par leur mot-clé

Une analyse est identifiée par son **mot-clé** (`Keyword`), pas par son
intitulé : l'intitulé peut être renommé dans l'interface, le mot-clé
est la clé stable.

Ces mots-clés sont des **données saisies dans l'instance**, pas du code.
Ils ne peuvent donc pas être devinés depuis le dépôt. Ils se lisent
dans :

    Configuration › Analyses  (Setup › Analysis Services)
    /senaite/bika_setup/bika_analysisservices

Un service absent donnera simplement une colonne vide, sans erreur.

---

## Où on en est

### Fait

- **Profil 1002** — index `getOrigin`, sept colonnes de métadonnées,
  indexeurs nommés, étape de mise à jour 1001 → 1002 qui réindexe les
  échantillons existants.
- **Profil 1003** — index `getTrimetaSampleTypeUID` pour le filtre
  « Type d'échantillon », et son étape 1002 → 1003.
- **Lecture des résultats d'analyse** — `dashboard/results.py` : une
  requête par page sur l'`analysis_catalog`, la règle des reprises, le
  filtre de plage.
- **`make dashboard-info`** — inventorie depuis le serveur l'API de
  `senaite.app.listing`, les index et métadonnées réellement présents
  sur les deux catalogues, et une vue de listing existante prise comme
  modèle.
- **Tests** — 103 tests purs (`make test-pure`), plus les tests
  d'intégration des index et colonnes dans `make test`.

### Reste à faire

1. Lancer `make dashboard-info` sur le serveur et récupérer sa sortie.
   Une vue de listing écrite en devinant l'API produit au mieux une
   colonne vide, au pire un ZCML qui ne charge pas — donc une instance
   qui ne démarre plus. C'est l'erreur que ce script existe pour
   éviter, comme `impress-info.sh` avant lui pour le lot 4.
2. Relever les mots-clés des sept services d'analyse.
3. Écrire la vue `@@trimeta-dashboard` : les vingt colonnes, la barre de
   filtres, le bouton de recherche.
4. Ajouter l'entrée de menu.

### À déployer

Après un `git pull` sur le serveur :

```bash
cd 2.6.0
make redeploy-addon
```

Puis jouer l'étape de mise à jour **1001 → 1002** :

    http://<hôte>:8080/senaite/portal_setup/manage_upgrades

Cette étape réindexe tous les échantillons. Sur une base fournie,
compter de l'ordre de la minute pour quelques milliers d'échantillons.
Sans elle, les nouvelles colonnes resteraient vides pour tout
l'historique.
