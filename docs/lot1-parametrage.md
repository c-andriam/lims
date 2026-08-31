# Lot 1 — quatre demandes réglées par paramétrage

Ces quatre points du document *AMÉLIORATIONS SENAITE LIMS* ne demandent
aucun développement : la fonctionnalité existe déjà dans SENAITE, elle
n'est simplement pas configurée.

| Réf | Demande | Où |
|---|---|---|
| D7 | Analyste assigné à chaque analyse | Contacts du laboratoire |
| D9 | Répétitions et moyenne automatique | Calculs + Analyses |
| D6 | Historique des pannes et des entretiens | Instruments |
| D11 | Export de plusieurs COA au contenu identique | Écran de publication |

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

### Le point à trancher avec le laboratoire

**Que faire si une seule ou deux répétitions sont saisies ?**

Avec la formule ci-dessus, un champ vide compte comme zéro : saisir
`2.0` et `2.2` seuls donne `1.4`, pas `2.1`. C'est faux, et rien ne le
signale.

Trois options, par ordre de sûreté :

1. **Imposer les trois répétitions.** Convention de travail, aucune
   configuration supplémentaire. La plus sûre.
2. **Créer deux calculs** — `Moyenne de 2 répétitions` et `Moyenne de
   3 répétitions` — et choisir le bon service selon le protocole.
   Explicite, sans piège.
3. **Une formule qui ignore les vides** :

   ```
   ([R1] + [R2] + [R3]) / max(1, ([R1] > 0) + ([R2] > 0) + ([R3] > 0))
   ```

   Élégant, mais le moteur de formules de SENAITE n'accepte qu'un
   sous-ensemble de Python. **À tester sur l'instance avant de s'en
   servir** : si le résultat n'apparaît pas, c'est que la construction
   n'est pas acceptée, et il faut retomber sur l'option 1 ou 2.

Recommandation : commencer par l'option 1, qui ne peut pas produire de
résultat faux.

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
   `senaite.impress:Default.pt` et non `senaite.impress:MultiDefault.pt`.
3. Décocher la case **Fusionner** (*merge*), qui regroupe tout en un
   seul PDF même sans gabarit `Multi`.
4. Générer.

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
- **D13** — le bug d'export de données depuis la Work Sheet, dont le
  symptôme reste à décrire par la personne qui l'a rencontré.
