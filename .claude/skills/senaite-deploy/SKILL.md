---
name: senaite-deploy
description: Deployer, redeployer et diagnostiquer l'instance SENAITE 2.6.0 conteneurisee de ce depot. A charger pour demarrer ou arreter l'instance, recharger l'add-on apres modification, jouer une etape de mise a jour GenericSetup, lancer les tests, reparer les droits apres un git pull qui echoue, sauvegarder ou restaurer la base.
---

# Exploiter l'instance SENAITE

Tout passe par le `Makefile` de `2.6.0/`. `make help` liste les cibles.
Le moteur de conteneur (podman ou docker) et l'outil compose sont
detectes automatiquement — ne jamais coder `docker` en dur dans un
script du depot, la moitie des cibles casserait sur une machine qui n'a
que podman.

    cd 2.6.0

## Boucle de travail courante

| Situation | Commande |
|---|---|
| Verifier l'etat general | `make doctor` |
| Demarrer / arreter | `make up` / `make down` |
| Suivre les logs | `make logs` |
| Apres une modification de l'add-on | `make redeploy-addon` |
| Tests de logique pure (instantane, sans container) | `make test-pure` |
| Tests d'integration (container requis) | `make test` |
| Shell dans le container | `make shell` |

`make redeploy-addon` rejoue buildout puis redemarre. Sur un serveur
juste en memoire, il peut se faire tuer (code 137) : utiliser alors
`make redeploy-instance`, qui saute l'etape `plonesite`.

## Apres un redeploiement : ne pas oublier l'etape de mise a jour

Redeployer le code ne cree **ni** index **ni** colonne de catalogue.
Cela se joue dans GenericSetup :

    http://<hote>:8080/senaite/portal_setup/manage_upgrades

et on y execute les etapes de `senaite.trimeta.samplefields`.

Une etape qui cree un index **reindexe tout l'historique** : compter de
l'ordre de la minute pour quelques milliers d'echantillons. Sans elle,
les nouvelles colonnes restent vides pour tous les echantillons
anterieurs — symptome classique d'un « ca ne marche pas » qui n'est
qu'une etape oubliee.

Si le profil n'a jamais ete installe :

    http://<hote>:8080/senaite/prefs_install_products_form

## Le piege des droits

Python 2 ecrit ses `.pyc` **a cote** des sources, pas dans un
`__pycache__`. Le container en produirait donc dans `addons/`, monte
depuis l'hote, **sous son identite a lui** — et git ne pourrait plus y
toucher. C'est la cause reelle des `Permission denied` au `git pull`.

Deux protections, les deux en place :

- `PYTHONDONTWRITEBYTECODE=1` dans `compose.yml` ;
- `make sync` (= reparer les droits, **puis** `git pull`). Toujours
  preferer `make sync` a un `git pull` direct sur le serveur.

En cas de blocage : `make fix-perms`.

## Inventorier l'instance plutot que deviner

Trois cibles interrogent le container et impriment ce qu'il contient
reellement. Les utiliser **avant** d'ecrire du code qui suppose une API
amont :

    make impress-info     # gabarits senaite.impress, registre des templates
    make dashboard-info   # index et colonnes disponibles dans les catalogues
    make test-env         # quel testrunner est disponible

Une valeur relevee dans le container vaut mieux qu'une valeur lue sur
GitHub : la branche `2.x` amont est en avance sur le tag 2.6.0 embarque.

## Donnees a confirmer dans l'instance, pas dans le code

Certaines valeurs sont **saisies dans l'instance** et ne peuvent pas
etre devinees depuis le depot :

- les **mots-cles des services d'analyse**
  (`dashboard/columns.DASHBOARD_ANALYSES`), lus dans
  *Configuration > Analyses*, colonne `Keyword`. Un mot-cle faux ne
  leve aucune erreur : la colonne reste vide. La vue journalise un
  avertissement quand un mot-cle ne ramene jamais rien ;
- les **contacts du laboratoire** et leurs comptes utilisateur, sans
  lesquels les selecteurs d'operateur restent vides.

## Sauvegarde

    make backup
    make restore FILE=backups/xxx.tar.gz CONFIRM=yes

`make clean` et `make fclean` **detruisent le volume de donnees**. Ne
jamais les lancer sur le serveur du laboratoire sans sauvegarde prise
et verifiee.

## Configuration locale

`2.6.0/.env` (non versionne, modele dans `.env.example`) porte
`SENAITE_PORT` et `SENAITE_HOST`. Priorite :
ligne de commande (`make up PORT=8081`) > `.env` > defaut 8080.
