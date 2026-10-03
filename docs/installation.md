# Installation SENAITE LIMS Trimeta

Le cahier des charges est `AMELIORATIONS SENAITE LIMS.docx`. Les champs,
COA, listes, export des feuilles de travail et tableau de bord sont livrés
par `senaite.trimeta.samplefields`, déjà présent dans le dépôt.

## Prérequis et installation

Installer Podman et podman-compose (ou Docker avec Compose), GNU Make,
Python 3 et curl avec le gestionnaire de paquets de la machine. Python 2.7,
Plone et les dépendances SENAITE sont fournis par l'image 2.6.0 ; ne pas
installer ces anciennes dépendances sur l'hôte.

```sh
cd 2.6.0
cp .env.example .env    # seulement si .env n'existe pas encore
# Adapter SENAITE_PORT et SENAITE_HOST dans .env
make first-setup
```

`first-setup` réutilise l'image locale si elle existe, sauvegarde la base
existante avec le serveur arrêté, répare les permissions du code, exécute
les tests purs et compile les traductions. Il active le profil Trimeta ou ses mises à jour dans un conteneur
temporaire partageant le même volume, pendant que le serveur est arrêté.
La transaction n'est validée qu'après vérification de la version du profil
et des index/colonnes. Enfin, il redémarre et vérifie le serveur.

En cas d'échec de l'activation, le serveur reste arrêté et la transaction
est annulée. Consulter l'erreur et les sauvegardes avant de relancer.
Cette procédure sert aussi à mettre à jour le profil après un changement
de version. Elle évite une activation manuelle dans l'interface.

Les scripts shell sont exécutables et accessibles depuis le Makefile :

| Commande | Usage |
|---|---|
| `make first-setup` | Installation avec activation du profil |
| `make wait-ready` | Attente HTTP, délai configurable `READY_TIMEOUT` |
| `make doctor` | Diagnostic du moteur, ports, données et permissions |
| `make backup` | Sauvegarde du volume réel du conteneur |
| `make restore FILE=… CONFIRM=yes` | Restauration d'une archive |
| `make redeploy-addon` | Reconstruction du code de l'extension |
| `make fix-perms` | Récupération des droits après buildout |
| `make i18n` | Compilation des catalogues de traduction |
| `make test-pure` | Tests sans serveur |
| `make test` | Tests Plone, installer le lanceur avec `make test-setup` |

`make backup` arrête temporairement le serveur et le relance s'il était
actif. `first-setup` garde le serveur arrêté pendant la sauvegarde et
l'activation du profil.

## Paramètres à renseigner au laboratoire

Créer les contacts du laboratoire et leurs comptes pour remplir les
listes d'analystes. Renseigner les services d'analyse et leurs mots-clés
pour alimenter les colonnes du tableau de bord. Les tâches de maintenance
et de panne des équipements doivent être saisies au fil des interventions.
Voir `lot1-parametrage.md`, `lot4-coa.md`, `lot5-tableau-de-bord.md` et
`d13-export-work-sheet.md` pour les limites et les vérifications métier.

## Corrections de l'installation

- Les montages du code, de la configuration et des scripts portent le
  label partagé `:z` pour fonctionner sous Podman avec SELinux.
- La sauvegarde utilise l'image SENAITE disponible, sans dépendre d'une
  seconde image Alpine ; la sortie est écrite par l'hôte pour éviter les problèmes de labels et
  de propriétaires.
- Le profil passe à 1008, en accord avec les étapes et tests existants.
  Les fonctions manquantes des réglages pays/devise, lundi et logo ont
  été rétablies. L'étape 1005 applique aussi le registre de langue/fuseau.
- Le module de nommage des COA fournit les fonctions attendues par les
  vues et les tests : assainissement des noms et collisions sans casse
  dans les ZIP.

## Sauvegardes complètes

`make backup` arrête maintenant le serveur s'il était actif et le relance
après l'archivage. Il sauvegarde **tout `/data`**, donc l'ensemble des
objets métier dans `filestorage/Data.fs` (échantillons, clients, contacts,
configuration, résultats, équipements, rapports) et les fichiers joints
dans `blobstorage`, ainsi que les autres fichiers de ce stockage.
Une autre instance active partageant `/data` entraîne un refus.

L'archive reste `.partial` jusqu'à vérification du gzip, de la base ZODB,
du répertoire de blobs et des chemins archivés. Un fichier `.sha256`
permet de contrôler son intégrité avant restauration. `make test-backup`
teste les archives vides, incomplètes, tronquées et les chemins dangereux.

Pour restaurer, conserver le conteneur afin de résoudre son vrai stockage :

```sh
make stop
make restore FILE=backups/senaite-data-….tar.gz CONFIRM=yes
make up
make wait-ready
```

La restauration valide l'archive **avant** toute suppression et conserve
une archive de secours de la base remplacée. Les données du laboratoire
ne sont pas stockées dans le dossier `2.6.0/data` du dépôt : ce dossier
historique n'est pas le volume réellement utilisé par Compose.

Les scripts et la configuration d'exécution restent dans le dépôt ; une
archive de `/data` doit être restaurée avec la même version de SENAITE et
l'extension correspondante.

## Enregistrements des échantillons

L'extension conserve la validation native des champs obligatoires. La
vue `ajax_ar_add` est surchargée pour annuler les écritures partielles
lorsque la création multiple annonce une erreur au navigateur. SENAITE
capture ces erreurs avant la fin de la requête ; sans cette protection,
une transaction partielle pouvait être validée malgré le message d'échec.
Les trois tests `TestAtomicSampleSubmit` vérifient l'annulation sur erreur
retournée, sur exception et la conservation des écritures en cas de succès.

`custom.cfg` désactive la recette `plonesite` au démarrage : elle
réappliquait les profils SENAITE sur un site existant. La création initiale
du site se fait désormais une seule fois dans `apply-profile.py`.

Les erreurs de création restent visibles dans le bandeau et près des
champs. Le filtre natif des champs décimaux supprimait la virgule et le
signe : `12,5` devenait `125`. La ressource `numeric_fields.js` convertit
une virgule décimale en point avant ce filtre et préserve les signes.
Les séparateurs ambigus restent soumis à la validation du serveur.
`node scripts/test-numeric-fields.js` vérifie huit cas de saisie.

Le profil 1008 rétablit les actions de modification attendues par
CMFFormController pour les types Archetypes sans action `edit`. Elles
restent masquées dans les menus et protégées par la permission native.
Le champ Client des échantillons reste obligatoire à la création ; il
est exclu de la validation de `base_edit`, où aucun champ de saisie Client
n'est rendu et où le client provient du dossier parent. Cette validation
bloquait toutes les modifications, y compris l'assurance qualité.

## Accès depuis le réseau local

Utiliser `http://<IP-du-PC>:8080/senaite` depuis un appareil du même
réseau. Compose publie le port 8080 sur toutes les interfaces.
`SENAITE_HOST` dans `.env` indique cette adresse dans les messages.

Sur cette machine, le 3 octobre 2026, le Wi-Fi utilise la zone firewalld
`public` et l'adresse `192.168.43.70`. Le port 8080 est bloqué dans cette
zone. Son ouverture nécessite une authentification administrateur :

```sh
sudo firewall-cmd --zone=public --add-port=8080/tcp
sudo firewall-cmd --permanent --zone=public --add-port=8080/tcp
```

L'ouverture automatique n'a pas été effectuée : sudo demande un mot de
passe et polkit refuse l'autorisation dans la session de l'agent.
L'adresse peut changer après reconnexion au Wi-Fi ; la vérifier avec
`ip -4 -brief address`.
