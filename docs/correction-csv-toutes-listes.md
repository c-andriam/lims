# Caracteres speciaux dans les CSV des listes natives

Suite du lot de nommage, le 27 novembre 2026.

## Probleme et correction

Le moteur `senaite.app.listing` construit les lignes CSV avec
`JSON.stringify`. Ce traitement est commun aux listes d'echantillons,
au tableau de bord, aux rapports et aux Work Sheets. Le defaut de
guillemets confirme pour D13 affecte donc aussi les autres listes.

Le convertisseur existant `worksheet_csv_format.js` est etendu aux boutons
d'export des listes natives. Il conserve son nom de ressource pour
continuite, mais son perimetre couvre maintenant ces listes. Il decode les
valeurs JSON puis applique l'echappement CSV, sans conversion numerique.

`ExportNamesViewlet` le charge une seule fois avec `?v=2`, apres le script
de nommage, dans les pages normales et les apercus Impress. L'injection
specifique a `WorksheetAnalystColumnsViewlet` est retiree pour eviter une
double conversion. Les nouveaux noms de fichiers sont conserves.

Seul un lien CSV Blob declenche dans le meme evenement que le bouton
d'export d'une liste est transforme. Les PDF, les liens ordinaires et
les telechargements declenches plus tard ne sont pas interceptes.
Le marqueur UTF-8, les lignes, colonnes et choix de pagination natifs sont
conserves. Cette correction ne charge pas toutes les pages automatiquement.

## Verification

- 321 tests purs Python reussis et controles JavaScript reussis.
- Telechargements reels des listes echantillons, tableau de bord et rapports.
  Valeur de recette avec guillemets, virgule, accent et retour a la ligne
  injectee uniquement dans les reponses JSON du navigateur, puis retiree.
- Lecture independante stricte des fichiers : respectivement 13 lignes et
  10 colonnes, 18 lignes et 20 colonnes, 26 lignes et 10 colonnes ; chaine
  de recette retrouvee exactement et marqueur UTF-8 confirme.
- Work Sheet classique et transposee : telechargements reels, noms
  conserves, nombres de colonnes coherents et resultats 0.61, 27.9, 2.05
  conserves apres lecture stricte.
- `make test` tente ; lanceur Plone complet absent de l'image locale.

Aucune valeur de recette enregistree en base et aucun document publie.
