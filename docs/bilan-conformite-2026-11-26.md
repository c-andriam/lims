# Bilan de suivi des 14 demandes du Word

Reference : texte de `AMELIORATIONS SENAITE LIMS.docx`, paragraphes 1 a 165.
Base de suivi : code de `main` a `072bc09`, complete par le Code article
extensible choisi par l'utilisateur le 26 novembre 2026.

Ce bilan actualise le diagnostic initial apres les lots de correction.
Les statuts ci-dessous reposent sur les declarations, traitements et
raccordements du code. Les images et les fichiers de tests ne sont pas
utilises comme preuves de couverture des exigences. La presence du code
ne certifie pas son deploiement sur le serveur de production.

## Couverture dans le code

Les chemins courts renvoient au paquet
`2.6.0/addons/senaite.trimeta.samplefields/senaite/trimeta/samplefields/`.

| Ref | Couverture actuelle | Sources applicatives |
|---|---|---|
| D1 | 15 champs Reception obligatoires, contacts laboratoire et choix/suggestions. Temperature 15-31 degC conservee par decision utilisateur. Liste Code article conservee et extensible apres sauvegarde, selon le choix utilisateur. | [extender.py](../2.6.0/addons/senaite.trimeta.samplefields/senaite/trimeta/samplefields/extender.py#L126), [vocabularies.py](../2.6.0/addons/senaite.trimeta.samplefields/senaite/trimeta/samplefields/vocabularies.py#L20) |
| D2 | Numero de fiche et DateReceived obligatoires ; autres champs d'analyse facultatifs ; preparateurs multiples ; ClientReference masque. DateReceived placee dans Analyse. | [extender.getOrder](../2.6.0/addons/senaite.trimeta.samplefields/senaite/trimeta/samplefields/extender.py#L469), [schema_modifier.py](../2.6.0/addons/senaite.trimeta.samplefields/senaite/trimeta/samplefields/schema_modifier.py#L60) |
| D3 | 41 champs facultatifs dans sept categories ; conformite OK/NOK, nombres 1/2/3, contacts laboratoire, modes de transmission et lots memorises. Position du titre Validation corrigee. | [qualitydata/extender.py](../2.6.0/addons/senaite.trimeta.samplefields/senaite/trimeta/samplefields/qualitydata/extender.py#L69), [qualitydata/fields.py](../2.6.0/addons/senaite.trimeta.samplefields/senaite/trimeta/samplefields/qualitydata/fields.py#L54), [quality_sections.js](../2.6.0/addons/senaite.trimeta.samplefields/senaite/trimeta/samplefields/browser/resources/quality_sections.js#L32) |
| D4 | Code echantillon et Lot ajoutes aux listes d'echantillons et a leurs etats. | [listings/samples.py](../2.6.0/addons/senaite.trimeta.samplefields/senaite/trimeta/samplefields/listings/samples.py#L31), [listings/configure.zcml](../2.6.0/addons/senaite.trimeta.samplefields/senaite/trimeta/samplefields/listings/configure.zcml#L24) |
| D5 | Rubriques demandees dans COA-Trimeta ; validation lue dans l'historique ; signataire designe distinct ; coordonnees client sans mail ; precision numerique conservee. Les autres gabarits natifs ne sont pas tous reecrits. | [COA-Trimeta.pt](../2.6.0/addons/senaite.trimeta.samplefields/senaite/trimeta/samplefields/coa/templates/reports/COA-Trimeta.pt#L92), [coa/reportview.py](../2.6.0/addons/senaite.trimeta.samplefields/senaite/trimeta/samplefields/coa/reportview.py#L51), [coa/validation.py](../2.6.0/addons/senaite.trimeta.samplefields/senaite/trimeta/samplefields/coa/validation.py#L8) |
| D6 | Deux historiques separes, Pannes et Entretiens, utilisant les interventions natives Repair et Preventive. Il s'agit de listes structurees, plutot que de deux zones de texte. | [equipment_history.py](../2.6.0/addons/senaite.trimeta.samplefields/senaite/trimeta/samplefields/equipment_history.py#L13), [browser/equipment_history.py](../2.6.0/addons/senaite.trimeta.samplefields/senaite/trimeta/samplefields/browser/equipment_history.py#L15) |
| D7 | Contact laboratoire affecte a chaque analyse, y compris sans compte utilisateur ; permissions et verrouillage des analyses soumises conserves. Compte executant natif distinct. | [analyst_extender.py](../2.6.0/addons/senaite.trimeta.samplefields/senaite/trimeta/samplefields/analyst_extender.py#L20), [browser/analyst.py](../2.6.0/addons/senaite.trimeta.samplefields/senaite/trimeta/samplefields/browser/analyst.py#L19) |
| D8 | Code echantillon dans les grilles et positions des feuilles de travail, avec identifiant natif en complement. | [worksheet/views.py](../2.6.0/addons/senaite.trimeta.samplefields/senaite/trimeta/samplefields/worksheet/views.py#L35), [listings/worksheets.py](../2.6.0/addons/senaite.trimeta.samplefields/senaite/trimeta/samplefields/listings/worksheets.py#L33) |
| D9 | Repetitions variables, deux au minimum, moyenne automatique, controles de saisie et de concurrence. Calculs personnalises existants conserves. | [repetitions.py](../2.6.0/addons/senaite.trimeta.samplefields/senaite/trimeta/samplefields/repetitions.py#L33), [browser/repetitions.py](../2.6.0/addons/senaite.trimeta.samplefields/senaite/trimeta/samplefields/browser/repetitions.py#L83), [defaults.py](../2.6.0/addons/senaite.trimeta.samplefields/senaite/trimeta/samplefields/defaults.py#L75) |
| D10 | Noms PDF fondes sur SampleCode, assainis, avec repli pour les anciens echantillons sans code. Suffixes uniques dans les archives. | [coa/filename.py](../2.6.0/addons/senaite.trimeta.samplefields/senaite/trimeta/samplefields/coa/filename.py#L37), [coa/configure.zcml](../2.6.0/addons/senaite.trimeta.samplefields/senaite/trimeta/samplefields/coa/configure.zcml#L67) |
| D11 | Gabarit unitaire propose a la place des deux valeurs Multi d'usine ; telechargement groupe raccorde aux PDF stockes, sans mutation des objets. Les gabarits groupes choisis explicitement restent disponibles. | [defaults.set_default_coa_template](../2.6.0/addons/senaite.trimeta.samplefields/senaite/trimeta/samplefields/defaults.py#L75), [coa/workflow.py](../2.6.0/addons/senaite.trimeta.samplefields/senaite/trimeta/samplefields/coa/workflow.py#L59) |
| D12 | 20 colonnes, six familles de filtres, recherche, ordre des operateurs et tri global Type/Vanilline et tris des dates avant pagination. Meme resultat effectif pour afficher, filtrer et trier. | [dashboard/view.py](../2.6.0/addons/senaite.trimeta.samplefields/senaite/trimeta/samplefields/dashboard/view.py#L77), [dashboard/columns.py](../2.6.0/addons/senaite.trimeta.samplefields/senaite/trimeta/samplefields/dashboard/columns.py#L227), [dashboard/results.py](../2.6.0/addons/senaite.trimeta.samplefields/senaite/trimeta/samplefields/dashboard/results.py#L130) |
| D13 | CSV classique et transpose, positions et resultats, precision conservee et noms explicites. Le Word ne decrit le bug initial que par une URL : la cloture de ce symptome exact reste a confirmer par le laboratoire. | [worksheet/views.py](../2.6.0/addons/senaite.trimeta.samplefields/senaite/trimeta/samplefields/worksheet/views.py#L35), [worksheet/export.py](../2.6.0/addons/senaite.trimeta.samplefields/senaite/trimeta/samplefields/worksheet/export.py#L46), [worksheet_csv.js](../2.6.0/addons/senaite.trimeta.samplefields/senaite/trimeta/samplefields/browser/resources/worksheet_csv.js#L2) |
| D14 | SampleCode et Lot dans la liste/export des rapports ; liens exportables en texte, sans HTML dans la colonne Info. | [listings/reports.py](../2.6.0/addons/senaite.trimeta.samplefields/senaite/trimeta/samplefields/listings/reports.py#L61) |

## Ce qui reste a decider ou a receptionner

1. **Code article — decision recue** : l'utilisateur conserve les sept codes
   actuels et permet des ajouts memorises. Les deux possibilites sont
   implementees ensemble ; voir [Code article extensible](correction-code-article-extensible.md).
2. **Adresse mail sur le COA** : le mail du contact client est retire du
   gabarit Trimeta. Le pied de page natif du laboratoire reste conserve.
   Supprimer aussi le mail du laboratoire ou modifier tous les autres
   gabarits necessite de preciser ce perimetre.
3. **Anciens rapports** : aucun PDF archive n'est regenere automatiquement.
   Si des rapports historiques ont un contenu errone, leur reprise demande
   d'identifier les fichiers et de decider leur traitement documentaire.
4. **Export historique WS-005** : les cas classique/transpose et leurs
   decimales sont traites. La conformite au symptome initial doit etre
   receptionnee avec les donnees concernees ; le Word ne le detaille pas.
5. **Donnees du laboratoire** : contacts, operateurs, descriptions
   organoleptiques et champs qualite doivent contenir les valeurs metier
   validees. Une case vide ne prouve pas l'absence de code. Aucune valeur
   n'est inventee pour completer un affichage.
6. **Production** : confirmer le deploiement du code, la couche navigateur
   et le profil GenericSetup 1012 sur le serveur cible. Les travaux locaux
   sur le port 8082 ne constituent pas cette confirmation.

## Distinctions a conserver

Les choix qualite 1/2/3 proviennent explicitement du Word. Ils ne limitent
pas le nombre de repetitions de mesures, qui est variable depuis la demande
ulterieure de l'utilisateur. La temperature 15-31 degC est un choix confirme.

Les tris Reception et Validation conservent les echantillons sans date,
places en dernier dans les deux sens. La date de validation actuelle est
vide dans un etat provisoire, meme en presence d'un ancien evenement de
validation dans l'historique. Voir la [correction des tris de dates](correction-tri-dates-tableau-de-bord.md).

L'etat dans la liste des rapports correspond a celui de l'echantillon.
Date de generation et Genere par decrivent le fichier ; un rapport provisoire
ne prouve pas une publication finale. Le contact signataire designe n'est
pas automatiquement l'acteur du workflow.

La persistance et la couverture des exigences sont deux controles distincts.
La [recette isolee des 67 champs](correction-libelles-et-persistance.md)
documente l'enregistrement et la relecture ; elle ne remplace pas la preuve
par le code utilisee dans le tableau ci-dessus. Le lanceur Plone complet
reste indisponible dans l'image locale.

Ce bilan ne declare pas une conformite integrale et inconditionnelle :
les limites, les decisions encore ouvertes et la reception en production
restent explicites.
