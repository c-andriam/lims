# Enregistrement des echantillons — 2 octobre 2026

Le document `AMELIORATIONS SENAITE LIMS.docx` impose 17 champs : les
15 champs de reception, le numero de fiche d'analyse et la date de
reception. Les autres champs d'analyse et tous les champs d'assurance
qualite restent facultatifs.

## Causes et corrections

Le conteneur Podman sous WSL monte `/home/candriam/lims/2.6.0/addons/`,
une autre copie que le workspace Windows. Cette copie declarait les
24 champs etendus facultatifs. Les declarations du workspace ont ete
deployees explicitement dans le repertoire monte. Le modificateur du
schema rend maintenant `DateReceived` obligatoire aussi.

Le bandeau natif d'erreur de creation etait masque par le viewlet :
ce masquage est retire. Un formulaire vide pouvait etre ignore par le
core puis produire une reponse `success` sans nouvel objet. La surcharge
`browser/sample_add.py`, enregistree sur la couche de l'add-on, renvoie
une erreur et conserve le formulaire dans ce cas.

La creation native intercepte les exceptions. Un savepoint englobe
maintenant toute la creation : un echec annule les ecritures partielles
avant que le core renvoie son erreur JSON. Le commit reste gere par la
transaction HTTP de Zope ; aucun commit manuel dans la vue.

Le tri par defaut du tableau de bord utilise `created`, toujours renseigne.
Le tri par `getDateReceived` excluait deux objets historiques sans date.
Les filtres de periode continuent d'utiliser la date de reception.
Un tri explicitement demande sur la date conserve le comportement natif
du catalogue pour les anciennes valeurs absentes.

## Verification

- `make test-pure` : 219 tests passes.
- Schema reel : les 17 obligations correspondent au document ; les huit
  autres champs d'analyse restent facultatifs.
- Navigateur Playwright et endpoint HTTP reel : 17 marqueurs obligatoires,
  erreurs visibles, formulaire incomplet rejete sans redirection.
- Instance apres redemarrage : six echantillons existants dans la liste
  generale et six dans le tableau de bord, tri par `created`.
- Base restauree dans `/tmp/trimeta-sample-recipe`, isolee de `/data` :
  chacun des 17 champs manquants bloque la creation ; une soumission
  complete par `ajax_submit` cree un seul objet indexe et commite.
- Un second processus rouvre cette base et retrouve l'objet dans les
  lignes de la liste generale et du tableau de bord.
- Un echec simule apres ecriture confirme le rollback des modifications.

La recette positive utilise uniquement la copie restauree : aucun
echantillon fictif n'a ete ajoute a l'instance du laboratoire.
Le script reproductible est `2.6.0/scripts/test-sample-save-isolated.py`
(modes `create`, puis `verify`, Python 2.7 du conteneur).

`make test` a ete tente : l'image ne fournit ni `bin/test` ni
`bin/zope-testrunner`, et `plone.app.testing` est absent. La suite Plone
complete n'a donc pas ete executee. La recette ci-dessus utilise le vrai
schema, les vues natives et la ZODB restauree.

## Donnees et exploitation locale

Le volume existant `260_senaite-data`, monte sur `/data`, est conserve.
La sauvegarde prise avec le conteneur arrete est
`/home/candriam/lims-backup-20261002-samples-stopped.tar.gz` ; elle a ete
restauree pour la recette. Le code precedent est conserve dans
`/home/candriam/lims-addon-backup-20261002`.

L'instance reste accessible sur `http://localhost:8080/senaite`.
Pour la relancer depuis Windows : `wsl -e podman start senaite`.
Ne pas utiliser `make clean` ou `compose down -v` : ces commandes
suppriment les volumes de donnees.

Pour les prochains deploiements, verifier le repertoire effectivement
monte avant de modifier l'add-on : editer uniquement le workspace Windows
ne met pas automatiquement a jour le code execute sous WSL.
