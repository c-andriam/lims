# Date de reception dans l'onglet Analyse

## Demande et ecart

Le document Word place la date de reception obligatoire dans la section
Analyse, apres le numero de fiche d'analyse. Le modificateur existant la
rendait obligatoire et saisissable, mais elle conservait la section native
`default`. Le schema reel de VAN-0006 confirmait cet emplacement.

## Correction

`ReceptionFieldsExtender.getOrder()` deplace le champ natif `DateReceived`
apres `AnalysisSheetNumber` dans `Analyse`. Il le retire de son ancien
emplacement, sans doublon ni nouveau champ. Si le champ natif n'existe pas
dans le schema transmis, aucun nom de champ inexistant n'est ajoute.

Le mecanisme installe d'archetypes.schemaextender applique cet ordre et
change la section du champ avant de jouer les modificateurs du schema.
Le caractere obligatoire, les date et heure stockees, le widget calendrier,
les permissions et les bornes natives sont conserves. Aucun changement de
schema persistant ni migration GenericSetup n'est requis.

## Verification du 26 novembre 2026

- 310 tests purs reussis, dont un controle du deplacement unique, de la
  conservation des autres champs natifs et de l'idempotence de l'ordre.
- Lecture du schema reel avant/apres sur la copie du port 8082 : passage
  de `default` a `Analyse`, ordre attendu, obligation et valeur historique
  `2026/09/15 10:50:00 GMT+3` conservees. Lecture terminee par transaction.abort().
- Formulaires HTTP reels de VAN-0009 et VAN-0012 : la date et l'heure sont
  dans `Analyse`, apres le numero de fiche, avec leurs valeurs existantes.
- Ouverture de l'onglet Analyse de VAN-0009 dans le navigateur : champ
  visible et saisissable. Le formulaire de creation `ar_add` propose aussi
  le champ natif. Aucun enregistrement d'echantillon pendant cette recette.
- `make test` tente : l'image locale ne fournit pas le lanceur Plone complet.

Sur VAN-0006, le champ reste absent de l'ecran de modification : l'adaptateur
natif `DateReceivedFieldVisibility` interdit cette modification lorsque
`isOpen()` est faux ou que l'echantillon est secondaire. Ce verrouillage
est conserve. Un champ verrouille ne doit pas etre assimile a un champ
perdu : sa valeur reste disponible dans le schema et dans les rapports.

Pour la validation utilisateur, ouvrir VAN-0009, Modifier, puis Analyse :
numero de fiche, date de reception avec heure, debut et fin d'analyse.
