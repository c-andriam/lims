# Affectation des analystes et export des feuilles de travail

Complément D7 et correction d'export D13 du 25 novembre 2026, après le commit
`f457458`.

Le contrôle d'une feuille réelle a révélé un raccordement incomplet :
`bika.lims.browser.worksheet.views.analyses.AnalysesView` filtre sur
`getWorksheetUID` et ne renseigne pas `portal_type`. L'adaptateur des analystes,
qui ne reconnaissait que ce dernier critère, n'ajoutait donc pas la colonne.

`AssignedAnalystAdapter.applies()` reconnaît désormais ce filtre natif.
En disposition classique, la colonne affiche le contact affecté et son lien
d'affectation. En disposition transposée, ces informations apparaissent dans
chaque cellule d'analyse, à la suite du résultat, sans ajouter de colonne de
position ni modifier la valeur ou son formatage.

Le navigateur mémorise également les colonnes dans `localStorage` et omet
les nouvelles colonnes du serveur lorsqu'une configuration existe déjà.
Une ressource chargée dans l'en-tête des feuilles complète uniquement la
configuration classique concernée, avant le démarrage de React. L'identifiant
de stockage vient de la vue native. Les positions, les attributs et les colonnes
masquées existantes sont conservés ; une colonne analyste déjà masquée reste
masquée. Un stockage absent, corrompu ou inaccessible n'empêche pas l'ouverture
de la page. Aucun effacement global du stockage n'est nécessaire.

Les contrôles métier restent ceux du formulaire commun : contact actif,
permission native, protection CSRF, contrôle de révision et verrouillage après
soumission. Les lignes de contrôle sans champ d'affectation sont conservées.

Sauvegarde locale avant intervention :
`backups/senaite-data-20261125-154310-77878.tar.gz` (776 fichiers vérifiés).
Le schéma et les données ne changent pas ; aucune nouvelle migration GenericSetup
n'est nécessaire.

Vérification automatique : 290 tests de logique ; 7 tests ciblés de raccordement,
de préservation des résultats, d'échappement HTML et de colonnes exportables ; contrôles JavaScript de
migration des préférences. Les 7 contrôles analystes/historiques continuent de
passer. Le lanceur Plone complet reste absent de l'image locale.

## Export des feuilles de travail — D13

Le Word signale un bug par une URL, sans décrire son symptôme. L'export CSV
classique de WS-001 se télécharge et contient les trois analyses et le code
`ECH-DEMO-002`. L'export natif utilise `formatted_result`, donc la précision
configurée du service, et non systématiquement le résultat brut : sur cette
copie, `27.9`, `0.61` et `2.05` sont exportés `28`, `1` et `2`.
Ce comportement doit être distingué d'un fichier manquant ou illisible ; cette
correction d'affectation ne change pas la précision des résultats.

Un autre écart est reproduit sur l'export transposé : avec une seule position,
il contient 14 colonnes, dont les colonnes classiques entièrement vides, au lieu
de deux. La vue native ajoute ses positions dans `self.columns` mais y conserve
les anciennes colonnes. `senaite.app.listing.get_columns_order()` les rajoute à
l'export, même si elles ne figurent pas dans les colonnes de l'état de revue.

`TrimetaAnalysesTransposedView.folderitems()` limite désormais les colonnes
visibles par défaut à `column_key` et aux positions réelles, dans leur ordre natif.
Les métadonnées des colonnes internes sont conservées : React en a besoin pour
rendre les cellules de résultat. Les en-têtes sont
« Analyse » et « Position N ». Le nombre de positions est dynamique. Les valeurs
et les codes échantillon continuent d'être fournis par `worksheet/export.py`.

Cette correction traite le défaut reproduit ; le symptôme initial non décrit
ne peut pas être déclaré identique sur la seule base de son URL.

## Contrôle navigateur final

Sur WS-001, trois liens « Affecter » sont présents dans chaque disposition.
Une configuration de colonnes ancienne a été simulée : la nouvelle colonne
apparaît et la colonne Méthode volontairement masquée le reste. Les préférences
de la session ont ensuite été restaurées.

Deux fichiers ont été réellement téléchargés puis analysés comme CSV :

- Classique : trois analyses, code `ECH-DEMO-002` et contact `Marie Rakoto`.
- Transposé : deux colonnes (`Analyse`, `Position 1`), une ligne portant
  `ECH-DEMO-002 (VAN-0006)` et trois lignes de résultats.

Aucune balise HTML n'est exportée. Les valeurs formatées `AW=1`, `TH=28` et
`VANILLINE=2` sont conservées. La disposition classique initiale a été rétablie.
Le laboratoire a validé ce complément, puis demandé le nommage des CSV ci-dessous.

## Noms des fichiers CSV

À la demande du laboratoire, le nom générique `download.csv` est remplacé par
l'identifiant de la feuille et sa disposition : `WS-001-classique.csv` ou
`WS-001-transposee.csv`. L'identifiant vient de l'objet Worksheet, avec des
caractères compatibles avec les noms de fichiers. Chaque feuille porte donc
son propre nom, sans identifiant de feuille codé en dur.

La ressource `worksheet_csv.js?v=1` conserve la génération CSV native et
renomme le lien de téléchargement pendant son clic, uniquement dans la grille
de résultats concernée. Les téléchargements PDF, les liens ordinaires et les
autres listings ne sont pas modifiés. Les contrôles JavaScript couvrent les
deux dispositions, les caractères spéciaux et l'isolation des téléchargements.

Les deux fichiers ont été réellement téléchargés depuis WS-001 ; le navigateur
confirme les noms `WS-001-classique.csv` et `WS-001-transposee.csv`.
