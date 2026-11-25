# Répétitions : saisie variable et moyenne automatique

Correction locale du 25 novembre 2026, demande D9. Le nombre de répétitions appartient à chaque analyse : le calcul ne se limite plus à deux ou trois mesures.

## Parcours utilisateur

Dans la liste des analyses d’un échantillon ou d’une feuille de travail, la colonne **Repetitions** propose **Saisir les repetitions** pour une analyse modifiable utilisant un calcul de moyenne reconnu.

Le formulaire présente une case par mesure. **Ajouter une répétition** ajoute une case ; **Retirer la dernière répétition** retire la dernière case, avec confirmation si elle contient une valeur. Deux mesures constituent le minimum. Aucun plafond métier n’est fixé à trois, cinq ou vingt.

**Enregistrer et calculer la moyenne** conserve les valeurs dans les champs intermédiaires natifs de l’analyse et recalcule le résultat avec le moteur de Calculation de SENAITE. Cette action ne soumet pas l’analyse à vérification. Le bouton de retour ramène à l’échantillon ; les valeurs sont disponibles dans sa grille native et sur la feuille de travail.

Toutes les cases doivent être numériques et finies. Les décimales avec point ou virgule sont acceptées. Une case vide, une limite de détection telle que `<3`, un texte, NaN ou l’infini interdit l’enregistrement ; les valeurs précédentes restent intactes. Le zéro est une mesure valide. Le calcul natif renvoie NA si une série stockée devient incomplète, plutôt qu’une moyenne partielle.

## Intégration et conservation des choix

`repetitions.mean_repetitions` est importée par le mécanisme natif PythonImports de Calculation. La formule unique `mean_repetitions(%(context_uid)s)` lit les champs R1 à Rn de l’analyse courante, vérifie leur continuité et calcule leur moyenne. Les champs supplémentaires sans mot-clé Rn sont conservés et ne participent pas à la moyenne.

`defaults.setup_dynamic_calculation()` crée de façon idempotente **Moyenne des repetitions**, avec deux cases initiales. Deux est une présentation de départ, pas une limite du calcul. Les nouveaux services reconnus sans calcul reçoivent cette moyenne variable. La résolution des services actifs utilise les mêmes mots-clés et intitulés que le tableau de bord.

Les calculs existants des services sont conservés. Les anciennes moyennes livrées à deux ou trois répétitions peuvent ouvrir le nouveau formulaire uniquement si leur titre, formule, champs et imports correspondent aux définitions d’origine. Les anciennes options hidden/wide absentes sont assimilées à false. Une formule, une valeur initiale ou un import personnalisé exclut la conversion. Le calcul d’une analyse historique n’est remplacé par le calcul variable que lors d’un enregistrement explicite depuis le formulaire.

Les résultats historiques ne sont pas recalculés par la migration. Les moyennes fixes restent disponibles pour compatibilité.

## Permissions, état et concurrence

Le formulaire contrôle les permissions natives EditResults ou EditFieldResults selon le point de capture, ainsi que FieldEditAnalysisResult. Il exige un échantillon actif et une analyse à l’état unassigned ou assigned. Les analyses soumises, vérifiées, publiées ou retirées sont exclues. Ce contrôle est exécuté côté serveur, indépendamment de la présence du lien.

Chaque POST vérifie l’authentificateur CSRF natif. Une empreinte du calcul, des champs, du résultat et de l’état empêche d’écraser une saisie modifiée depuis l’ouverture du formulaire. Une erreur pendant l’écriture annule le point de sauvegarde transactionnel. Une demande périmée conserve son ancienne empreinte et ne devient pas valide par une simple seconde soumission.

Les pages et boutons utilisent les composants et classes du thème SENAITE, sans CSS ajouté.

## Déploiement

Le profil passe de 1008 à 1009 pour le rattachement des services, puis à **1010** pour la moyenne variable. Les deux étapes sont fournies ; une nouvelle installation utilise le même traitement. Le profil 1010 est appliqué sur la copie locale du port 8082.

Sauvegarde préalable vérifiée : `/home/candriam/lims-review-point1/backups/senaite-data-20261125-095139-139342.tar.gz` : ZODB, blobs et 768 fichiers. Les sources précédentes sont conservées dans `source-backup-variable-20261125`. La base d’origine n’a pas été modifiée.

## Vérifications

Les **277 contrôles de logique pure passent**. Les nouveaux cas couvrent les séries de longueur variable, zéro et valeurs négatives, virgule et exposant, séries incomplètes, doublons, champs non consécutifs, valeurs non finies, grandes valeurs finies et protection des calculs personnalisés.

Contrôles effectués avec les objets et le moteur natifs de SENAITE 2.6.0 sur la copie locale :

| Série | Moyenne obtenue |
|---|---|
| 1 à 2 | 1.5 |
| 1 à 3 | 2.0 |
| 1 à 4 | 2.5 |
| 1 à 5 | 3.0 |
| 1 à 20 | 10.5 |
| 2.0 ; 2.2 ; 2.1 ; 2.3 | 2.15 |

Les contrôles natifs vérifient aussi l’idempotence du calcul, la conservation des affectations existantes lors de la migration, le refus des séries invalides et des empreintes périmées sans modification des données, le résultat NA après suppression d’une valeur et recalcul explicite, le refus d’un utilisateur anonyme et le verrouillage après la transition native de soumission. Les mutations des scénarios négatifs sont annulées.

Dans le navigateur, le parcours depuis l’échantillon a été vérifié : ajout d’une cinquième case, refus du texte `abc`, enregistrement des cinq valeurs et restitution après rechargement. Un POST sans authentificateur retourne 403 et conserve les données.

Échantillon de démonstration conservé uniquement sur la copie : **VAN-0012**, code **VERIF-P3-VARIABLE**, lot **LOT-VERIF-P3**, avec cinq répétitions : 2.0, 2.2, 2.1, 2.3, 2.4 ; moyenne **2.2**.

La suite Plone complète n’est pas disponible dans cette image, faute de lanceur : `make test` confirme cette absence. Les contrôles ciblés ci-dessus ne remplacent pas cette suite.

Statut : correction et contrôles locaux réalisés ; validation utilisateur reçue le 25 novembre 2026 pour publication sur `main`.
