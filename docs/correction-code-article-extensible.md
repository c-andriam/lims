# Code article : liste initiale et ajouts memorises

Le 26 novembre 2026, l'utilisateur a choisi de conserver les codes
existants ET de permettre de nouveaux codes memorises. Cette decision
complete le Word, qui exige un Code article obligatoire sans definir
la liste de ses valeurs.

## Utilisation

Le selecteur natif SENAITE propose toujours V-GNN, V-GTK, V-RAF, V-RBF,
V-RCF, V-LLB et AUTRES. Le choix « Autre… » ouvre une saisie libre pour
un nouveau code. AUTRES reste une valeur historique distincte, conservee
avec son sens et son orthographe d'origine.

Apres l'enregistrement reussi de l'echantillon, le nouveau code est
propose dans les prochains formulaires, pour tous les utilisateurs du
site. Les codes ajoutes sont tries entre les six codes produits initiaux
et AUTRES. Les doublons exacts sont elimines. La casse et les caracteres
saisis sont conserves ; les espaces de debut et de fin sont retires.

Une valeur vide, y compris « Autre… » sans code ou une saisie composee
d'espaces, reste refusee. Un brouillon abandonne n'alimente pas la liste.
Les champs non remplis ne recoivent aucune valeur par defaut.

## Implementation

- `ItemCodeField` conserve le nom CodeArticle et le stockage StringField.
  Son vocabulaire ajoute les codes memorises aux sept valeurs livrees.
- `SelectOtherWidget` assure la selection et l'ajout avec les composants
  natifs. La consultation utilise la macro native de valeur texte.
- Le magasin de suggestions partage memorise CodeArticle sur les
  evenements natifs d'enregistrement. Ce champ est exclu du script de
  suggestions qui memorise les autres champs lors de la sortie du champ.
- La lecture des suggestions ne cree plus de magasin ou de rubrique vide.
  Un echec de lecture conserve les codes initiaux disponibles.
- Avant validation de la creation AJAX, la valeur du choix Autre est
  extraite par le widget natif et nettoyee. Le controle obligatoire lit
  ainsi le code reel, plutot qu'une liste non vide contenant un code vide.
- Les libelles sont conserves sur les formulaires de modification et ne
  sont pas dupliques dans le tableau de creation.

Aucune migration des echantillons, reindexation ou nouvelle version de
profil n'est requise. Les valeurs historiques restent stockees dans le
meme champ ; aucun remplacement en masse n'est effectue. La temperature
de reception reste une liste de 15 a 31 degC.

## Verification

317 tests purs et 21 controles cibles sous Python 2.7 reussis. `make test`
a ete tente : le lanceur Plone complet reste absent de l'image locale.

Sur la restauration isolee de recette, un code a ete ajoute par modification
avec `processForm` et un second par creation avec `ajax_submit`, en utilisant
le format liste du choix natif Autre. Le second contient un caractere
accentue. Les sept codes initiaux restent proposes. Les 66 autres valeurs
controlees sur l'echantillon modifie restent intactes.

Deux creations avec Autre vide ou seulement des espaces sont refusees,
avec erreur sur CodeArticle-0, sans echantillon cree ni code memorise.
Un nouveau processus rouvre ensuite la base et retrouve les deux codes
dans les echantillons et dans le vocabulaire partage.

Dans le navigateur sur le port 8082 : sept codes initiaux et Autre visibles,
code nouveau saisissable, brouillon non memorise, valeur historique retrouvee
apres rechargement. Le formulaire d'ajout a deux colonnes conserve les
deux selecteurs obligatoires et un seul libelle par ligne.

Aucun echantillon de demonstration n'a ete enregistre dans l'instance
interactive pendant ces controles ; les creations sont limitees au
volume isole `lims-fields-persistence-20261126`.
