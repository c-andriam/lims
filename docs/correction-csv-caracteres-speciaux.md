# D13 : guillemets et caracteres speciaux dans les CSV de Work Sheet

## Defaut confirme dans le code natif

Le JavaScript installe de `senaite.app.listing` construit les cellules et
les titres CSV avec `JSON.stringify`. Dans une chaine, JSON encode un
guillemet avec une barre oblique inverse. Un lecteur CSV attend un
guillemet double a l'interieur d'une cellule entre guillemets.

Le resultat natif contenant `ECH-"VAN", ete` et `Marie "Test"` est refuse
par le lecteur CSV strict de Python : la separation des champs est invalide.
Les retours a la ligne et les barres obliques inverses etaient egalement
representes comme des sequences JSON plutot que comme leurs valeurs.
La demonstration execute la fonction `to_csv_row` extraite du bundle natif
installe, sans utiliser une image ou un ancien resultat de test comme
reference fonctionnelle.

## Correction

`worksheet_csv_format.js` intervient uniquement sur le telechargement CSV
des grilles classique et transposee d'une Work Sheet. Il decode les
cellules JSON natives puis construit des cellules CSV correctement citees.
Les guillemets, accents, virgules, retours a la ligne et valeurs vides sont
conserves. Les chaines numeriques ne sont pas converties en nombres : les
decimales stockees et les zeros significatifs restent presents.

Le bouton Exportation natif et les noms de fichiers existants sont
conserves. Le fichier garde son encodage UTF-8 avec marqueur BOM et utilise
la virgule comme separateur. Les autres telechargements et listes ne sont
pas interceptes. Le script est charge avec `?v=1` par le viewlet des feuilles
de travail ; aucun moteur natif ni schema de donnees n'est modifie.

La transformation conserve exactement les lignes et colonnes produites
par l'export natif. Elle ne charge pas les lignes qui ne sont pas encore
affichees et ne change pas la selection. Un fichier impossible a decoder
n'est pas telecharge silencieusement comme s'il etait valide.

## Verification du 27 novembre 2026

- 317 tests purs Python reussis. `make test` tente : lanceur Plone complet
  absent de l'image locale.
- Controles Node : guillemets, Unicode, textes multilignes, barres obliques
  inverses, valeurs vides, zero, limites de detection, precision, fichiers
  et listes hors perimetre, et absence de telechargement en cas d'erreur.
- Fonction d'export native executee puis conversion du fichier : le meme
  lecteur CSV strict retrouve les trois champs exacts apres correction.
- Navigateur reel sur WS-001 : fichiers `WS-001-classique.csv` et
  `WS-001-transposee.csv` effectivement telecharges. Le premier comporte
  trois lignes et 13 colonnes ; le second quatre lignes et deux colonnes.
- Deux autres exports ont utilise une valeur de recette contenant
  guillemets, virgule, accent et retour a la ligne, injectee seulement dans
  la reponse de listing du navigateur. Les quatre fichiers sont lus sans
  erreur par un lecteur CSV independant ; les colonnes et les resultats
  0.61, 27.9 et 2.05 sont conserves.

L'interception de recette est retiree et la page rechargee apres controle.
Aucun resultat, code echantillon ou analyste n'est enregistre en base.
Le document Word ne precisant pas le symptome du cas historique WS-005,
ce lot clot le defaut reproduit ici sans attribuer retrospectivement ce
symptome a la feuille historique.
