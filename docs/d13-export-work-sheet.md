# D13 — Export des données d'une Work Sheet

Deux demandes du document *AMÉLIORATIONS SENAITE LIMS* portent sur la
Work Sheet :

> Remplacer ou ajouter la référence de l'échantillon « ID échantillon »
> dans le module « Work Sheet » par « Code échantillon ».

> Bug exportation données : `…/worksheets/WS-005/manage_results…`

Aucun symptôme n'était décrit. La capture de WS-003 jointe au document
montre que le laboratoire travaille en mise en page **Transposed**.

---

## Comment fonctionne l'export

Le bouton *Exportation* sous une liste est entièrement géré par le
navigateur (`senaite.app.listing`, fonctions `export` et `to_csv_row`) :

- colonnes exportées : celles qui sont **visibles** ;
- lignes exportées : celles qui sont **chargées dans la page**. Si la
  liste affiche *Show more*, le reste n'est pas dans le fichier ;
- chaque cellule passe par `JSON.stringify`. Pour une cellule qui
  contient un objet, seuls `formatted_value` ou `value` sont lus ;
- séparateur : la **virgule**, fichier `download.csv`.

## Ce qui ne marchait pas

Reproduit sur l'instance locale avec une Work Sheet de quatre analyses.

**1. En mise en page Transposed, aucun résultat n'était exporté.** Chaque
cellule de position y contient une analyse complète, sans
`formatted_value` : le fichier ne contenait que les mots-clés
d'analyse, sans valeur ni échantillon.

**2. La colonne Code échantillon n'apparaissait jamais.** L'adaptateur du
lot 3 décide de s'appliquer d'après le `portal_type` interrogé par la
liste. La grille d'une Work Sheet filtre sur `getWorksheetUID`, sans
`portal_type` : la colonne n'était jamais ajoutée, ni à l'écran ni dans
l'export classique.

## Correctifs

| Fichier | Rôle |
|---|---|
| `listings/worksheets.py` | reconnaît le filtre `getWorksheetUID` ; colonne placée après « Position » |
| `worksheet/views.py` | remplace `analyses_classic_view` et `analyses_transposed_view` pour `ISenaiteTrimetaLayer` |
| `worksheet/export.py` | `fill_export_values()` : `formatted_value` = résultat dans les cellules d'analyse, `CODE (ID)` dans l'en-tête de position |

L'en-tête de chaque position affiche désormais `CODE (ID)`, par exemple
`ECH-DEMO-002 (VAN-0006)`, dans les deux mises en page. L'ID est gardé :
c'est lui qui porte le lien vers l'échantillon.

## Vérifié

Export émulé à partir des données réellement renvoyées par le serveur,
Work Sheet WS-001 :

```
"column_key","1"
"Position","ECH-DEMO-002 (VAN-0006)"
"AW","1"
"TH","28"
"VANMOY","2"
"VANILLINE","2"
```

Avant correctif, les cellules de la colonne `"1"` étaient vides.

## Ce qui reste

1. **Confirmer le symptôme** avec la personne qui a signalé le bug : les
   correctifs couvrent ce qui a été reproduit, pas nécessairement ce
   qu'elle a vu.
2. **Excel en français** attend un point-virgule. Un `download.csv`
   séparé par des virgules s'y ouvre dans une seule colonne : passer par
   *Données › À partir d'un fichier texte/CSV* et choisir la virgule.
   Changer le séparateur demanderait de modifier le JavaScript de
   `senaite.app.listing` ; ce n'est pas fait.
3. **Décimales** : l'export reprend le résultat *formaté*, arrondi selon
   la précision du service d'analyse (*Configuration › Analyses*, champ
   *Précision*). Sur l'instance de démonstration elle vaut 0 ; sur le
   serveur réel, les captures montrent 3 décimales pour Vanillin.
4. **Lignes non chargées** : exporter après avoir affiché toutes les
   lignes.
