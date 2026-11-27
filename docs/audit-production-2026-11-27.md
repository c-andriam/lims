# Audit des améliorations SENAITE LIMS

**Avis du 27 novembre 2026 — mise en production à différer.** Le commit audité est `3b58760`. Les 165 paragraphes non vides de **AMELIORATIONS SENAITE LIMS.docx** définissent les exigences. La comparaison porte sur les déclarations, traitements, vues et raccordements de l’extension. Les images et les tests existants ne servent pas de preuve de couverture. Les choix ultérieurs du laboratoire sont pris en compte, notamment la température de 15 à 31 °C et le masquage du courriel personnel côté laboratoire.

## Anomalies et conditions de clôture

Les chemins ci-dessous sont relatifs au paquet `senaite/trimeta/samplefields`. La priorité reflète l’impact potentiel sur le travail du laboratoire. Un défaut établi à la lecture du code ne prouve pas qu’un incident a eu lieu sur le serveur de production.

| Priorité | Constat et preuve | Conséquence et contrôle à réaliser après correction |
|---|---|---|
| Haute · A1 | Dans `browser/suggestions_api.py`, la vue pose `IDisableCSRFProtection`. Pour ajouter ou retirer une suggestion, elle vérifie que la personne est connectée, sans vérifier de permission métier propre à la modification du référentiel partagé. La vue est enregistrée avec la permission de consultation dans `browser/configure.zcml`. | Un utilisateur ayant accès à cette vue peut modifier des propositions utilisées par d’autres opérateurs. Rétablir la protection native des écritures et définir les droits de gestion. Vérifier avec un profil de consultation et un gestionnaire, y compris le refus d’une écriture dépourvue de jeton valide. |
| Haute · A2 | Une erreur de lecture du catalogue dans `dashboard/results.py:242` renvoie la même valeur que l’absence de filtre. Dans `dashboard/view.py:200`, la vue poursuit alors la recherche sans restriction Vanilline. | Une liste ou son export peut contenir des échantillons hors de la plage demandée. Prévoir un état d’erreur explicite. Vérifier qu’une panne de catalogue ne permet pas d’exporter une liste présentée comme filtrée. |
| Haute · A3 | Entre deux résultats renseignés d’une même analyse reprise, `dashboard/results.py:117` choisit le dernier rencontré si l’une des dates manque. L’appel réel à `_is_better(('1', None), ('2', 123))` renvoie vrai. En inversant l’ordre, la même branche choisit l’autre résultat. | La valeur affichée, le tri et l’appartenance à une plage peuvent dépendre de l’ordre de lecture. Faire valider le critère de priorité historique, puis vérifier que l’inversion de l’ordre des entrées conserve le même résultat. |
| Moyenne · A4 | `browser/resources/field_suggestions.js:228` déclenche un ajout lors de la sortie du champ. `browser/suggestions_api.py` enregistre cet ajout dans une requête distincte de la sauvegarde de l’échantillon. Le mécanisme concerne notamment les lots de solvants de `suggestions.py`. | Une faute de saisie ou une valeur abandonnée peut être proposée au prochain opérateur. Mémoriser les nouvelles valeurs après sauvegarde réussie. Contrôler successivement annulation, échec de validation et sauvegarde. |
| Moyenne · A5 | Le serveur conserve le point intérieur du code dans `coa/filename.py`. Le navigateur le remplace par un tiret et tronque à 150 caractères dans `browser/resources/export_names.js:4`, avant le téléchargement de l’aperçu à la ligne 54. | Pour le code `LOT.24`, l’archive propose `LOT.24.pdf` et l’aperçu `LOT-24.pdf`. Ce dernier nom peut aussi désigner un autre code. Réutiliser le nom serveur dans tous les parcours et comparer aperçu, téléchargement, pièce jointe et archive. |
| Moyenne · A6 | Pour un nom Windows réservé, `coa/filename.py:33` ajoute le suffixe à la fin du code entier. L’appel au générateur installé avec le code `CON.01` a produit `CON.01_.pdf`. | Le premier segment reste réservé sur Windows. Assainir ce segment avant la première extension et contrôler l’enregistrement et l’extraction sur un poste du laboratoire. |

## Comparaison des quatorze demandes

| Demande et paragraphes du Word | Réalisation identifiée dans le code | Appréciation |
|---|---|---|
| D1 · Réception, §2–18 et 32 | `extender.py`, `vocabularies.py` et `browser/sample_submit.py` définissent les champs, choix et contrôles de création. Le code article accepte les ajouts sauvegardés. | Implémentée avec réserves A1 et A4 sur les suggestions. |
| D2 · Analyse, §19–32 | `extender.py` et `schema_modifier.py` définissent numéro de fiche, réception obligatoire, dates facultatives, préparateurs multiples et masquage de la référence. | Implémentée. A1 et A4 concernent aussi les suggestions organoleptiques. |
| D3 · Assurance qualité, §33–78 | `qualitydata/fields.py`, `qualitydata/extender.py` et `quality_sections.js` organisent 41 champs facultatifs en sept sections. | Implémentée avec réserves A1 et A4 sur la mémoire des lots. |
| D4 · Liste des échantillons, §79 | `listings/samples.py` ajoute le code et le lot aux états de la liste. | Couverture identifiée. |
| D5 · COA, §80–101 | `coa/templates/reports/COA-Trimeta.pt`, `coa/reportview.py` et `coa/validation.py` alimentent synthèse, validation, caractéristiques et résultats organoleptiques. | Couverture identifiée pour le modèle Trimeta. Vérifier le modèle actif en production. |
| D6 · Équipements, §102 | `browser/equipment_history.py` et `equipment_history.py` distinguent les interventions Repair et Preventive. | Couverture identifiée. Séparation et pagination déjà vérifiées sur copie isolée. |
| D7 · Analyste par analyse, §26 et 103 | `analyst_extender.py` et `browser/analyst.py` enregistrent un contact du laboratoire sur l’analyse. | Couverture identifiée. La précédente tentative de vérification d’une annulation individuelle n’a pas abouti, la transition demandée étant indisponible pour l’analyse choisie. |
| D8 · Code dans la feuille de travail, §104 | `worksheet/views.py` et `worksheet/export.py` associent code et identifiant aux positions. | Couverture identifiée pour les deux dispositions. |
| D9 · Répétitions, §105 | `repetitions.py` et `browser/repetitions.py` traitent deux mesures ou davantage, vérifient la séquence et calculent la moyenne. | Couverture identifiée. Les choix 1 à 3 du formulaire qualité sont une exigence distincte. |
| D10 · Nom du COA, §106 | `coa/filename.py`, `coa/download.py`, `coa/email.py` et le script de téléchargement utilisent le code échantillon. | Partiel pour les codes concernés par A5 et A6. |
| D11 · Export groupé, §107 | `defaults.py` propose le modèle unitaire et `coa/workflow.py` archive les PDF stockés avec des noms distincts. | Couverture identifiée pour le parcours unitaire. Une archive ne répare pas des PDF historiques déjà identiques. Contrôler le contenu individuel sur une sélection représentative. |
| D12 · Tableau de bord, §108–163 | `dashboard/columns.py`, `filters.py`, `results.py` et `view.py` fournissent 20 colonnes, les filtres, le tri et la recherche. | Partiel pour la fiabilité de la sélection Vanilline et des reprises, A2 et A3. |
| D13 · Export de feuille de travail, §164 | `worksheet/export.py` renseigne les positions et résultats. Le convertisseur CSV conserve les cellules multilignes. | L’utilisateur a confirmé la résolution de l’export vide sur le parcours local WS-001. |
| D14 · Export de rapports, §165 | `listings/reports.py` renseigne le code échantillon, le lot et les liens exportables. | Couverture identifiée. |

## Décision de livraison

**Suivi du correctif A1.** L’API vérifie désormais le droit Plone « Manage portal » sur le portail et le jeton natif avant toute écriture directe. Le formulaire transmet ce jeton pour retirer une suggestion. Les opérateurs alimentent la liste en enregistrant un échantillon. La sortie de champ et la touche Entrée ne déclenchent plus d’écriture anticipée, ce qui traite également le mécanisme signalé en A4.

Sur copie isolée, le gestionnaire a pu ajouter puis retirer une valeur avec son jeton. Les écritures sans jeton ou avec un jeton invalide ont été refusées. Un lecteur muni de son propre jeton a pu consulter les suggestions et sa tentative de suppression a été refusée. La vérification a contrôlé la valeur stockée après chaque refus.

Au cours de cet audit, 321 contrôles de logique Python ont réussi. La commande d’intégration Plone a été lancée et s’est arrêtée faute de lanceur dans l’image locale. Les contrôles locaux ne couvrent donc pas toute l’installation.

Traiter en premier A1 à A3. Pour A4 à A6, corriger les écarts ou documenter leur acceptation par le responsable métier avant livraison. La décision finale nécessite une recette sur une instance représentative avec les profils réels, un export multi-échantillons dont chaque PDF est comparé à sa source, et la vérification de la version déployée et du profil GenericSetup 1012. L’audit porte sur les améliorations demandées et ne vaut pas certification de toute la plateforme.
