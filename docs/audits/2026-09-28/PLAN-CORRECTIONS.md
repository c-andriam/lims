# Plan de correction et de recette

## Phase 0 — figer une référence reproductible

1. Identifier le checkout Git faisant foi et aligner le montage Podman sur ce
   répertoire.
2. Externaliser les secrets, exclure les fichiers ZODB et documenter une
   procédure de démarrage unique.
3. Effectuer une sauvegarde cohérente et tester sa restauration dans une
   instance isolée avant les changements métier.

Critère de sortie : même commit dans l'IDE et le conteneur, sauvegarde restaurée
et contrôle de santé réussi.

## Phase 1 — réparer la création d'échantillon (P0)

1. Supprimer le CSS qui masque les erreurs; afficher le message global et les
   erreurs par champ, puis conserver les valeurs saisies après échec.
2. Corriger le mécanisme d'extension afin que les 16 champs attendus soient
   réellement obligatoires dans le schéma exécuté. Rendre également la date de
   réception obligatoire conformément au cahier.
3. Ajouter des validations métier explicites : nombres finis, bornes décidées
   par Trimeta, cohérence des quantités et chronologie des dates.
4. Ajouter un test d'intégration qui soumet le même formulaire AJAX que le
   navigateur et vérifie : transaction, objet, catalogue, liste générale et
   tableau de bord.
5. Reproduire avec un véritable échantillon fourni par l'équipe métier. Relever
   son code avant soumission, puis contrôler le même code dans la ZODB et le
   catalogue. Ne jamais injecter de données inventées.

Critère de sortie : une création métier autorisée produit une confirmation
visible, un seul objet persistant et une ligne visible dans toutes les listes
attendues; un formulaire invalide affiche une erreur exploitable.

## Phase 2 — cohérence des listes et résultats (P1)

1. Remplacer le tri par date qui élimine les objets sans `DateReceived`, avec
   une stratégie explicite pour les valeurs absentes.
2. Choisir une règle unique pour les répétitions (dernier résultat valide, ou
   règle métier définie), puis l'utiliser pour le filtrage et l'affichage.
3. Rejeter `NaN`, les infinis et les formats ambigus avant stockage et avant
   comparaison.
4. Ajouter aux tests exécutés par défaut les trois modules actuellement omis et
   corriger le contrat de nommage COA.

Critère de sortie : nombre d'objets identique entre base, catalogue et vues
hors filtres métier explicites; filtre et valeur affichée utilisent la même
analyse.

## Phase 3 — recette des lots D3 à D14

Construire avec Trimeta un petit jeu de recette constitué uniquement de cas
réels autorisés : réception, analyse avec répétition, contrôle qualité,
feuille de travail, COA et rapports. Pour chaque lot, vérifier création,
modification, droits par rôle, recherche, export CSV/PDF et traçabilité. Les
preuves doivent contenir les identifiants, états et totaux, sans secrets ni
données personnelles inutiles.

Critère de sortie : matrice D1–D14 signée, chaque exigence reliée à un test et
à une preuve de l'instance de recette.

## Phase 4 — exploitation et migration

Rendre sauvegarde/restauration atomiques, ajouter un contrôle quotidien de
cohérence ZODB/catalogue et préparer la migration hors Python 2.7 dans une
branche séparée. La migration ne doit pas être mélangée aux corrections P0,
afin de garder un retour arrière simple.

## Ordre proposé des livraisons

- Livraison A : messages d'erreur + champs obligatoires + test de création.
- Livraison B : listes, dates, résultats non finis et répétitions.
- Livraison C : COA, exports et recette D3–D14.
- Livraison D : sauvegarde/restauration, secrets et trajectoire de migration.

Chaque livraison passe d'abord sur une copie isolée, puis sur l'environnement
de test avec une sauvegarde restaurable et une preuve de non-régression.
