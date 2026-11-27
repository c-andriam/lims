# Noms par defaut des fichiers exportes

Demande utilisateur du 27 novembre 2026 : attribuer un nom approprie aux
exports, quel que soit leur type. Cette demande complete D10 et D13 du Word.

## Comportement

- CSV des listes : nom de la page, contexte et date du poste utilisateur.
  Exemple : `Echantillons-Client-Cooperative_Sambava-2026-11-27.csv`.
- Tableau de bord : `Tableau-de-bord-LIMS-2026-11-27.csv`.
- Work Sheet : `WS-001-classique.csv` et `WS-001-transposee.csv` conserves.
- Impression d'une Work Sheet : titre `Feuille-de-travail-WS-001`, utilise
  comme proposition lors de l'enregistrement PDF du navigateur.
- COA archive : nom fonde sur le Code echantillon conserve selon D10.
- PDF telecharge depuis l'apercu Impress : Code echantillon pour un seul
  echantillon ; `COA-N-echantillons.pdf` pour une selection multiple.
- Fichiers serveur : noms generiques tels que `download`, `report`,
  `invoice` et `sticker` remplaces par un nom tire du contexte ; les noms
  deja explicites, y compris les archives COA datees et les exports
  d'instruments identifies, sont conserves.

L'extension est conservee, les noms sont assainis pour Windows et les
en-tetes HTTP, et les extensions PDF doubles du moteur natif sont corrigees.
Le nom est une proposition : l'utilisateur peut le modifier dans son
dialogue d'enregistrement. Les fichiers historiques stockes ne sont pas
renommes en base.

## Sources applicatives

`export_names.py` gere les noms serveur avant l'envoi des en-tetes,
y compris les reponses utilisant `response.write`. Les abonnements sont
declares dans `configure.zcml` et limites a la couche navigateur Trimeta.
Les codes des echantillons selectionnes ne sont lus qu'apres controle du
droit de consultation de chaque objet.

`browser/resources/export_names.js` nomme les liens Blob des exports CSV
natifs et le PDF du bouton de telechargement Impress. Ce bouton reutilise
`window.impress.createPDF()` pour produire le contenu courant. Les autres
actions Impress, dont sauvegarde et envoi, gardent leur traitement natif.
`ExportNamesViewlet` charge la ressource dans les pages normales et dans
le gestionnaire natif `IPublishCustomHtmlHeadViewlets` des apercus Impress.

## Verification

- 321 tests purs Python reussis ; controles JavaScript des noms, extensions,
  caracteres, expiration du contexte de clic et erreurs de generation PDF.
- Telechargements reels : liste des echantillons, tableau de bord, deux
  dispositions WS-001 et bouton natif de telechargement de l'apercu COA.
- Requete PDF reelle : en-tete `attachment; filename="ECH-DEMO-002.pdf"`.
- Evenements ZPublisher enregistres verifies avec Python 2.7 et les objets
  natifs sur la copie de recette : noms appliques avant commit et avant
  streaming ; corps de reponse inchange.
- Impression WS-001 : titre confirme dans le navigateur.
- Les controles de nommage couvrent aussi XLS/XLSX, XML, JSON, TXT et ZIP.
  Ils ne pretendent pas que l'instance dispose d'un producteur natif pour
  chacun de ces formats.
- `make test` tente ; lanceur Plone complet absent de l'image locale.

Aucun echantillon ni resultat metier modifie, aucun rapport publie et
aucun courriel envoye pendant ces controles.
