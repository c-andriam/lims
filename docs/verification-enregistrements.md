# Vérification des enregistrements — 3 octobre 2026

Les correctifs sont installés sur l'instance locale
`http://localhost:8080/senaite`, profil Trimeta **1008**. Le cahier des
charges utilisé est `AMELIORATIONS SENAITE LIMS.docx`.

## Problèmes corrigés

- Le bandeau d'erreur de création d'échantillon était masqué par
  l'extension. Les champs manquants sont maintenant signalés.
- Le filtre numérique natif transformait `12,5` en `125`. La virgule
  décimale est convertie en point et les signes sont conservés.
- La modification d'un échantillon échouait sur la validation du champ
  Client absent du formulaire. Ce client est fourni par le dossier
  parent ; le champ reste obligatoire à la création.
- Les actions `edit` manquantes des types Archetypes provoquaient une
  erreur serveur au retour de validation. Le profil ajoute ces actions
  avec les permissions natives, sans entrée supplémentaire dans les menus.
- Une erreur pendant une création multiple pouvait laisser des objets
  partiellement créés. Les écritures du lot sont annulées en cas d'erreur.
- Le démarrage réappliquait les profils SENAITE. L'activation du site et
  de Trimeta est maintenant explicite dans le script d'installation.
- Les sauvegardes utilisent le stockage réel et incluent les pièces
  jointes. La restauration vérifie l'archive avant toute suppression et
  conserve une sauvegarde de secours.

## Contrôles effectués

Les saisies de vérification ont été réalisées par Firefox sur une copie
isolée de la base, port 8082, volume `lims-verification-data`. Elles
n'ont pas été ajoutées à la base principale.

| Domaine | Vérification |
|---|---|
| Clients | Création, modification du nom et relecture |
| Contacts clients | Création et relecture |
| Contacts du laboratoire | Création et relecture |
| Types d'échantillons | Création et relecture |
| Départements | Création avec responsable et relecture |
| Catégories d'analyses | Création avec département et relecture |
| Types d'équipements | Création et relecture |
| Fabricants | Création et relecture |
| Fournisseurs | Création et relecture |
| Équipements | Création avec type, fabricant et fournisseur, relecture |
| Services d'analyses | Création et relecture |
| Échantillons | Création, modification de réception et assurance qualité, relecture |

Un formulaire d'échantillon sans analyse affiche l'erreur attendue.
Après sélection d'une analyse, la création réussit. Deux échantillons
ont été relus ; le poids saisi `12,5` ressort comme `12.50`. Le lot,
le code, la désignation, le lot d'éthanol et les remarques modifiées
ont été contrôlés. La pièce jointe téléchargée possède la même
empreinte SHA-256 que le fichier envoyé.

L'archive de vérification
`2.6.0/backups/senaite-data-20261003-075349-109047.tar.gz` contient
434 entrées. Le script de restauration l'a restaurée sur la copie
isolée, après sauvegarde de secours. Après redémarrage, les objets
des douze domaines, les valeurs des échantillons et la pièce jointe
ont été relus et vérifiés de nouveau.

## Tests automatisés

- `make test` : **344 tests**, zéro échec et zéro erreur, Python 2.7/Plone.
- `make test-pure` : **247 tests**, zéro échec, inclus également dans la suite complète.
- `make test-backup` : **6 tests**, dont refus des archives tronquées,
  vides, sans blobs et avec chemins ou liens dangereux.
- `node scripts/test-numeric-fields.js` : **8 contrôles** de conversion.
- `git diff --check` : aucune erreur.

Les résultats de création et de restauration sont des contrôles de
bout en bout sur les domaines listés. Ils ne certifient pas tous les
workflows possibles, les droits de chaque rôle ou une autre installation
accessible sur le réseau. Les procédures d'installation, de sauvegarde
et de restauration sont décrites dans [installation.md](installation.md).

## Correction complémentaire : date de réception obligatoire

La date native `DateReceived` devient obligatoire à la création et à la
modification. Son calendrier et son champ d'heure utilisent les widgets
SENAITE existants. La permission native d'écriture de `DateSampled` est
réutilisée : le workflow interdisait `DateReceived` dans l'état
`sample_due`, ce qui masquait ses entrées et empêchait sa sauvegarde.
Les permissions globales et les autres champs ne sont pas modifiés.

Le contrôle serveur conserve les bornes natives : après le prélèvement
et pas dans le futur. Une date déjà enregistrée reste conservée lors du
passage à l'état reçu grâce au patch de workflow existant.

Contrôles Firefox sur la copie isolée :

- création refusée sans date, avec message global et message de champ ;
- création avec `03/10/2026 08:00`, valeur relue identique ;
- suppression de la date en modification refusée, date initiale conservée ;
- correction à `08:15`, sauvegarde et relecture réussies ;
- code échantillon et poids inchangés après modification.

La suite complète passe désormais **348 tests**, zéro échec et zéro erreur.
Le schéma est modifié à l'exécution ; aucun remplissage automatique des
anciennes dates vides ni migration de données n'est effectué. Une ancienne
fiche sans date demandera sa date réelle lors de sa prochaine modification.
