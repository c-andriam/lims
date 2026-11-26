# Libelles des formulaires et conservation des valeurs

## Comportement attendu

Un champ facultatif non renseigne reste vide. Une valeur enregistree avec
succes doit etre conservee apres rechargement et reouverture de la base.
Un champ vide garde son libelle pour que l'utilisateur puisse l'identifier.
Aucune date, aucun preparateur et aucune donnee qualite ne sont ajoutes
automatiquement par cette correction.

## Affichage corrige

Les widgets de dates et de references declares avec `render_own_label=True`
masquaient leur libelle dans le formulaire de modification. Cette option
convient au tableau d'ajout `ar_add`, dont une colonne porte deja le libelle,
mais pas au formulaire `base_edit`.

Le modificateur utilise maintenant le libelle natif du widget dans les
sections Reception, Analyse et Assurance Qualite des echantillons existants,
ainsi que pour DateReceived. A la creation, il conserve le libelle de la
colonne de gauche, sans doublon. Chaque champ et widget concernes sont copies
localement au schema de la requete pour isoler creation et modification.
La description de la date de reception est traduite en francais.

La copie utilise `field.copy()`, methode native qui copie aussi le widget.
Une copie Python generique n'est pas compatible avec certaines classes
ExtensionClass des references ; ce cas a ete detecte puis corrige pendant
la verification sur SENAITE, avant publication du changement.

Les widgets, les champs obligatoires, les permissions, les valeurs stockees
et les verrous du workflow sont conserves. Aucune migration n'est necessaire.

## Verifications du 26 novembre 2026

- 311 tests purs reussis. Le controle des libelles verifie aussi l'isolation
  des schemas de creation et de modification.
- Schema et classes installes : libelles des dates et contacts retablis,
  valeurs de VAN-0009 intactes ; debut, fin et preparateur non renseignes
  toujours vides. La transaction de cette verification est annulee.
- Navigateur : libelles francais visibles dans Analyse, date de reception
  conservee, debut et fin vides. Le formulaire d'ajout conserve exactement
  un libelle par champ et les marqueurs obligatoires attendus.
- `make test` tente : le lanceur Plone complet reste absent de l'image.

## Recette de persistance sur restauration isolee

`2.6.0/scripts/test-custom-fields-persistence-isolated.py` restaure la
sauvegarde `senaite-data-20261125-165146-135026.tar.gz` dans un volume dedie,
`lims-fields-persistence-20261126`, monte sur `/tmp/trimeta-fields-recipe`.
Le montage original `/data` est en lecture seule et la configuration Zope
est explicitement reecrite vers la copie. Aucune donnee de recette n'est
enregistree dans l'instance accessible au laboratoire.

Le mode `write` valide puis traite les 65 champs personnalises, la date de
reception et le lot par `processForm`, avec les widgets et mutateurs natifs,
puis commite la transaction. Les valeurs sont comparees aux saisies, et un
instantane est conserve dans le volume de recette.

Le mode `verify`, execute dans un nouveau conteneur et un nouveau processus,
rouvre la base et compare les 67 valeurs a cet instantane. Resultat :
**67/67 champs enregistres et 67/67 champs retrouves apres reouverture**.
Le controle couvre les dates, nombres decimaux, listes, references aux
contacts, deux preparateurs simultanes, accents et remarques multilignes.

La recette utilise les cles reelles des listes (`coa` pour le mode COA),
les classes natives des champs numeriques et le fuseau GMT+3 de ces donnees.
Une date saisie sans fuseau doit etre interpretee comme une heure locale,
avant de comparer son instant enregistre.

Cette verification porte sur les 67 champs precises ; elle ne remplace pas
la suite Plone complete ni une verification de toutes les fonctions natives
de SENAITE. Aucun defaut de stockage de ces champs n'a ete constate.
