# Tableau de bord : trier les dates sans perdre d'echantillons

## Defaut reproduit

Cliquer sur Validation dans le tableau de bord reduisait la liste de
18 echantillons a un seul. Le tri DateIndex natif ne renvoyait que les
echantillons ayant une date indexee. Le meme mecanisme excluait les deux
anciens echantillons sans date de reception lors du tri Reception.
Un tri changeait donc la selection, alors qu'il devait seulement l'ordonner.

## Correction D12

Les tris Reception et Validation passent maintenant par `sort_brains()`,
apres la selection native et avant pagination, comme les tris Type et
Vanilline. Les cles de colonnes et de tri restent identiques : aucune
migration des preferences ni du profil GenericSetup n'est necessaire.

Les dates presentes sont triees dans le sens demande. Les dates absentes
restent vides et sont placees a la fin dans les deux sens. Les egalites
sont departagees par l'identifiant et l'UID pour stabiliser les pages.
Ce tri ne reveille aucun objet ZODB et ne demande aucune analyse.

La date de validation affichee et triee n'est actuelle que dans les etats
`verified` et `published`, comme sur le COA. Une ancienne validation suivie
d'un retour a un etat provisoire reste dans l'historique, mais n'est pas
presentee comme la validation actuelle. Les dates et historiques stockes
ne sont ni effaces ni reecrits.

Les filtres restent des filtres : une periode de reception choisie exclut
normalement les echantillons sans date. La correction empeche seulement
le tri de les exclure lorsqu'ils font partie de la selection.

Comme les autres tris manuels, le traitement parcourt la selection avant
pagination. Son cout augmente avec le nombre d'echantillons selectionnes.

## Verification du 26 novembre 2026

- 314 tests purs reussis.
- 23 controles cibles sur Python 2.7 : tris, pagination native et validation.
- `make test` tente : le lanceur Plone complet reste absent de l'image.
- Base restauree dans le volume isole de recette : les quatre tris
  Reception/Validation, croissant/decroissant, conservent 18 echantillons.
  Validation : une date et 17 cases vides. Reception : 16 dates et deux
  cases vides. Pagination par deux : aucun manque ni doublon.
- Simulation temporaire d'une validation suivie d'un retour a un etat
  provisoire dans cette copie : date historique presente au catalogue,
  case vide dans la ligne du tableau de bord et validation vide sur le
  controleur COA. Transaction annulee, historique et etat retrouves intacts.
- Navigateur sur le port 8082 : les quatre tris affichent chacun 18 lignes,
  avec les dates absentes en dernier. Aucun echantillon enregistre ou
  publie pendant cette verification.

Pour la validation utilisateur : ouvrir le tableau de bord, cliquer deux
fois sur Validation, puis deux fois sur Reception. Le sens change, mais
le nombre d'echantillons reste celui de la selection initiale.
