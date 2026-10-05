# Lot 1 — quatre demandes réglées par paramétrage

Ces quatre points du document *AMÉLIORATIONS SENAITE LIMS* ne
demandaient à l'origine aucun développement : la fonctionnalité existe
déjà dans SENAITE, elle n'était simplement pas configurée.

> **Deux d'entre eux sont depuis passés dans le code.** Documenter une
> manipulation que personne au laboratoire ne sait faire déplace le
> problème sans le résoudre, et un réglage posé à la main se perd à la
> première réinstallation. **D9** et **D11** sont désormais posés par
> le profil d'installation (`defaults.py`, étape de mise à jour
> 1004 → 1005) : il n'y a plus rien à faire à la main. Les
> manipulations restent décrites ci-dessous, parce qu'il faut pouvoir
> vérifier ce que le code a posé, et le corriger au cas par cas.
>
> **D7** l'est en partie : le rôle `Analyst` est attribué
> automatiquement aux comptes existants, mais **créer** un compte exige
> un mot de passe — cela reste manuel. **D6** reste une convention.

| Réf | Demande | Où | État |
|---|---|---|---|
| D7 | Analyste assigné à chaque analyse | Contacts du laboratoire | rôle automatique, compte manuel |
| D9 | Répétitions et moyenne automatique | Calculs + Analyses | **posé par le code** |
| D6 | Historique des pannes et des entretiens | Instruments | **onglet activé par le code**, convention à tenir |
| D11 | Export de plusieurs COA au contenu identique | Écran de publication | **posé par le code** |

Les noms de menus sont donnés en français puis en anglais entre
parenthèses : l'interface bascule selon la langue du compte.

---

## D7 — Analyste assigné à chaque analyse

### Le constat

Le document demande « un champ *Analyste* assigné pour chaque analyse,
les noms devant être liés au module Contact du laboratoire ».

Le champ existe déjà : SENAITE gère un analyste par ligne d'analyse. Ce
qui manque, c'est le contenu de sa liste déroulante. Elle ne se remplit
pas avec les *contacts du laboratoire* mais avec les **utilisateurs**
ayant le rôle `Analyst`. Un contact sans compte utilisateur n'y apparaît
donc jamais — d'où l'impression que le champ est absent.

### La manipulation

Pour **chaque** personne qui doit pouvoir être désignée comme analyste :

1. Aller dans **Configuration › Contacts du laboratoire**
   (*Setup › Lab Contacts*).
2. Ouvrir le contact — ou le créer s'il n'existe pas encore.
3. Onglet **Détails de connexion** (*Login details*).
4. Créer un compte : identifiant, mot de passe, adresse e-mail.
5. Cocher le rôle **Analyst**.
6. Enregistrer.

Un contact et un compte utilisateur restent deux objets distincts :
c'est cet onglet qui fait le lien entre les deux.

### Vérification

Ouvrir une Work Sheet existante, ou en créer une. Le sélecteur
**Analyste** doit maintenant proposer les personnes configurées. Sur la
grille de saisie des résultats, chaque ligne d'analyse peut recevoir son
propre analyste.

> **À savoir** : SENAITE refuse de créer une Work Sheet sans analyste.
> Il faut donc au moins un contact configuré avant de pouvoir en ouvrir
> une.

---

## D9 — Répétitions et moyenne automatique

### Le principe

Le document demande de « pouvoir faire deux ou plusieurs répétitions
pour un même échantillon et de calculer automatiquement la moyenne ».

SENAITE fait cela avec des **champs intermédiaires** (*interim fields*) :
des cases de saisie supplémentaires sur une analyse, dont un **calcul**
tire le résultat final. Le technicien saisit ses répétitions, le
résultat publié est la moyenne.

### Étape 1 — créer le calcul

1. **Configuration › Calculs** (*Setup › Calculations*) › **Ajouter**.
2. Titre : `Moyenne de 3 répétitions`.
3. Section **Champs intermédiaires** (*Interim fields*) — ajouter trois
   lignes :

   | Mot-clé | Intitulé | Valeur | Unité |
   |---|---|---|---|
   | `R1` | Répétition 1 | *(vide)* | |
   | `R2` | Répétition 2 | *(vide)* | |
   | `R3` | Répétition 3 | *(vide)* | |

   Le **mot-clé** est ce qui sera utilisé dans la formule. Pas
   d'espaces, pas d'accents.

4. Champ **Formule** (*Calculation Formula*) :

   ```
   ([R1] + [R2] + [R3]) / 3
   ```

5. Enregistrer.

### Étape 2 — rattacher le calcul à l'analyse

1. **Configuration › Analyses** (*Setup › Analysis Services*).
2. Ouvrir le service concerné — commencer par **Vanilline**.
3. Onglet **Méthode** (*Method*).
4. Mettre **Utiliser le calcul par défaut de la méthode** (*Use the
   default calculation of method*) à **Non**.
5. Dans **Calcul alternatif** (*Alternative Calculation*), choisir
   `Moyenne de 3 répétitions`.
6. Enregistrer.

Une fois validé sur la Vanilline, répéter pour les autres services
(Gluco-vanilline, acide vanillique, PHB, acide PHB, TH, AW).

### Vérification

Sur une Work Sheet, la ligne de l'analyse affiche maintenant trois cases
`R1`, `R2`, `R3` au lieu d'une seule case Résultat. Saisir `2.0`, `2.2`
et `2.1` doit donner `2.1`.

### Une répétition oubliée est visible — correction

> **Cette section disait le contraire, et c'était faux.** Une version
> antérieure affirmait qu'un champ vide compte comme zéro, et que
> saisir `2.0` et `2.2` seuls donnerait `1.4` sans que rien ne le
> signale. Elle en tirait une recommandation : imposer les trois
> répétitions par convention de travail. Vérification faite sur le
> code de `senaite.core` v2.6.0, ce n'est pas ce qui se passe.

Dans `AbstractAnalysis.calculateResult` :

```python
# skip unset values
interim_value = i.get("value", "")
if interim_value == "":
    continue
```

Un champ vide **n'entre pas** dans le tableau de substitution. Son
marqueur `[R2]` survit donc dans la formule, y devient `%(R2)f`, et le
formatage lève un `KeyError` — rattrapé quelques lignes plus bas :

```python
except (KeyError, TypeError, ImportError) as e:
    self.setResult("NA")
```

**Une répétition manquante donne le résultat `NA`**, affiché à l'écran
comme sur le rapport. Pas une moyenne faussée par un zéro fantôme.

La conséquence est heureuse : la formule simple est **sûre**. Elle ne
peut pas produire un nombre plausible et faux — le seul risque qui
aurait justifié d'imposer quoi que ce soit aux opérateurs. Le logiciel
fait respecter la règle à leur place.

Le vrai piège est ailleurs, et il est désormais verrouillé par un
test : **ne jamais mettre `0` en valeur par défaut** sur les cases de
répétition. Trois cases pré-remplies dont deux seulement sont corrigées
donneraient, elles, une moyenne calculée sur un zéro — plausible,
fausse, et silencieuse. Voir `test_no_default_value_on_repetitions`.

---

## D6 — Historique des pannes et des entretiens

### Le constat

Le document demande d'« ajouter un champ *Historique des pannes* et
*Historique des entretiens* dans le module Équipements ».

Ces historiques existent déjà. SENAITE rattache à chaque instrument des
**tâches de maintenance** (*Maintenance tasks*) portant précisément ces
informations :

| Champ SENAITE | Contenu |
|---|---|
| Type | Préventif / **Réparation** / Amélioration |
| Immobilisé du / au | Période d'indisponibilité |
| Intervenant (*Maintainer*) | Qui est intervenu |
| Considérations | Précautions, contexte |
| Travaux effectués | Ce qui a été fait |
| Remarques | Notes libres |
| Coût | Montant |
| Clôturé | Terminé ou en cours |

### La convention à adopter

C'est le champ **Type** qui sépare les deux historiques demandés :

- **Historique des pannes** → tâches de type **Réparation** (*Repair*)
- **Historique des entretiens** → tâches de type **Préventif**
  (*Preventive*)

Cette convention est la seule chose à faire respecter. Sans elle, les
deux historiques se mélangent dans une liste unique.

### L'onglet était invisible — correction

> **Cette section indiquait d'ouvrir un onglet qui n'existe pas dans
> votre interface.** La consigne était donc littéralement impossible à
> suivre, et c'est la capture d'écran du cahier des charges qui l'a
> révélé : elle montre la barre d'onglets de l'équipement *AW Mètre 1*
> — `Edit | View | QC Results | Calibrations | Certificat
> d'étalonnage | Validations | Documents` — **sans Maintenance**.

La fonctionnalité n'est pas absente pour autant. `senaite.core` v2.6.0
embarque le type `InstrumentMaintenanceTask`, la vue
`InstrumentMaintenanceView` et son enregistrement. Tout fonctionne.
Seul l'**onglet** est masqué, dans le profil de `senaite.core`
lui-même :

```xml
<action action_id="calibrations" ... visible="True">
<action action_id="maintenance"  ... visible="False">
```

SENAITE livre cette fonction désactivée. **Le profil de l'add-on la
rend désormais visible** (`defaults.show_instrument_maintenance_tab`,
étape 1004 → 1005) : l'onglet **Maintenance** apparaît dans la barre,
à côté de *Validations*. Rien à faire à la main.

`Schedule`, masqué lui aussi, est laissé tel quel : le cahier des
charges ne demande pas de planification.

### La manipulation

1. **Configuration › Instruments** (*Setup › Instruments*).
2. Ouvrir l'instrument concerné.
3. Onglet **Maintenance** (*Maintenance tasks*) › **Ajouter**.
4. Renseigner le Type selon la convention ci-dessus, les dates
   d'immobilisation, l'intervenant et les travaux effectués.
5. Laisser **Clôturé** décoché tant que l'intervention est en cours.

### Vérification

L'onglet Maintenance de l'instrument liste les interventions, avec leur
type et leur état. Une tâche non clôturée dont la date de fin est
dépassée ressort en retard.

### Essai local (15/09/2026)

Instrument « AW Metre 1 » (Novasina, type AW-Metre) créé avec deux
tâches : « Remplacement du capteur » (Réparation) et « Entretien annuel »
(Préventif). Les deux apparaissent dans l'onglet Maintenance, avec leurs
dates d'immobilisation et l'intervenant.

Défaut corrigé au passage : senaite.core 2.6 affiche `getType()[0]`,
c'est-à-dire la **première lettre** du type (« R », « P »). L'add-on
remplace ce contenu par le libellé complet et traduit
(`listings/instruments.py`), sans surcharger la vue.

> Si, à l'usage, le laboratoire a besoin de champs qui n'existent pas
> ici — numéro de bon d'intervention, prestataire externe, pièces
> remplacées — cela redevient du développement : une extension de schéma
> sur le type `Instrument`, sur le modèle de ce qui a été fait pour les
> échantillons. À signaler après quelques semaines d'utilisation
> réelle, pas avant.

---

## D11 — Export de plusieurs COA au contenu identique

### Le constat

Le document décrit : « je sélectionne 5 résultats et le logiciel génère
5 fichiers avec des noms différents mais qui ont tous le même contenu ».

Ce n'est probablement pas un défaut du logiciel, mais un effet du
gabarit choisi.

Dans `senaite.impress`, **un gabarit dont le nom commence ou finit par
`Multi` reçoit la totalité des échantillons sélectionnés**. C'est fait
pour produire un rapport groupé — en-tête une seule fois, résultats de
tous les échantillons à la suite.

Si l'opérateur choisit un gabarit `Multi…` tout en demandant un
enregistrement séparé, chaque fichier contient donc bien les cinq
échantillons. Cinq noms différents, un seul contenu : exactement le
symptôme décrit.

### La manipulation

Au moment de publier plusieurs échantillons :

1. Sélectionner les échantillons, puis **Publier** (*Publish*).
2. Dans le sélecteur **Gabarit** (*Template*), choisir un modèle dont
   le nom **ne contient pas** `Multi` — par exemple
   `senaite.trimeta.samplefields:COA-Trimeta.pt` ou
   `senaite.impress:Default.pt`, et non `senaite.impress:MultiDefault.pt`.
3. Générer (*Save*).

> **Confirmé dans le code** (`senaite.impress`, `ajax_save_reports` et
> `PdfReportStorageAdapter.store`) : un gabarit `Multi` rend un seul PDF
> pour tous les échantillons, et le réglage *Store Multi-Report PDFs
> Individually*, actif par défaut, rattache ce même PDF à chacun.
> Il n'existe pas de case « Fusionner » : une version antérieure de ce
> document en mentionnait une à tort.
>
> Le piège venait surtout du **gabarit présélectionné**, qui est
> `MultiDefault.pt` par défaut. Depuis le lot 4 (étape de mise à jour
> 1004), l'add-on présélectionne `COA-Trimeta.pt`, sauf si le
> laboratoire avait déjà choisi un autre gabarit par défaut.

### Vérification

Ouvrir deux des PDF produits : chacun ne doit contenir que son propre
échantillon.

> **Si le défaut persiste** avec un gabarit sans `Multi` et la fusion
> décochée, alors c'est un vrai bug. Le noter — quel gabarit, combien
> d'échantillons, quelle version — et il repasse en développement dans
> le lot 4.

---

## Récapitulatif

Une fois ces quatre points faits, **6 des 14 demandes** du document sont
livrées : les deux sections de champs déjà en place, plus ces quatre-ci.

Ce qui reste relève du développement :

- **Lot 4** — contenu du COA et nommage des fichiers ;
- **Lot 5** — tableau de bord avec ses filtres ;
- **D13** — le bug d'export de données depuis la Work Sheet : reproduit
  et corrigé, voir `d13-export-work-sheet.md`. Le symptôme reste à
  confirmer avec la personne qui l'a rencontré.
