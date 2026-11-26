# Etats des rapports et precision des nouveaux COA

## Comportement confirme

La colonne native `State` de la liste des rapports lit l'etat actuel de
l'echantillon, et non un etat propre au fichier PDF. VAN-0005 est publie ;
VAN-0006 est recu et son COA porte la mention de rapport provisoire.
Ces deux situations sont coherentes. Les PDF deja archives conservent
leur contenu a la date de leur generation.

## Corrections

La liste affiche desormais « Etat de l'echantillon », « Date de generation »
et « Genere par ». Les cles techniques natives, les tris et les liens PDF
restent identiques. Le createur du fichier et sa date de creation ne sont
ainsi plus presentes comme une preuve de publication de l'echantillon.

Dans un nouveau COA provisoire, les libelles de publication deviennent
« Date de generation » et « Genere par », y compris dans les responsables.
Les COA finaux conservent leurs libelles de publication. Les donnees de
validation continuent de provenir de l'historique du workflow.

Le seul gabarit COA-Trimeta utilise une copie du tableau natif des resultats
pour conserver les chiffres numeriques enregistres, sans arrondi
supplementaire : 27.9, 0.61 et 2.05 deviennent 27,9, 0,61 et 2,05 en francais.
Les limites de detection sont conservees et echappees pour le HTML.
Les choix, textes et valeurs absentes gardent le formatage natif ; les
analyses masquees, rejetees ou retractees restent filtrees comme en natif.
Les unites, intervalles, incertitudes et precisions des services ne sont
pas modifies. Aucun changement de schema ni migration n'est necessaire.

## Verification du 26 novembre 2026

- `make test-pure` : 309 tests reussis.
- Python 2.7 de l'image : 53 controles cibles reussis.
- `make test` tente : lanceur Plone complet absent de l'image locale.
- Rendu complet avec les classes installees pour VAN-0005 et VAN-0006 :
  etats, libelles finaux/provisoires et chiffres enregistres conformes.
- Controle de l'identite des 29 PDF archives avant/apres, des resultats,
  precisions et historiques : aucune modification.
- PDF provisoire genere par les points d'entree natifs de rendu et de
  telechargement, avec le traitement natif des codes-barres et QR codes :
  deux pages controlees visuellement, decimales et libelles verifies dans
  le texte du PDF. Aucun appel a l'enregistrement ou a l'envoi des rapports.

Un apercu local portant la mention « APERCU DE VERIFICATION - NON PUBLIE »
est disponible dans `output/pdf/COA-ECH-DEMO-002-provisoire.pdf`. Cet artefact
de controle est exclu de Git. Les anciens fichiers telecharges depuis la
liste restent des archives ; les corrections de rendu concernent les
nouveaux PDF. La configuration reelle du laboratoire et les champs encore
vides doivent etre completes avec les donnees metier validees.
