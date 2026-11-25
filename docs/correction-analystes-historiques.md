# Analystes et historiques des équipements — D6 et D7

Ces corrections répondent aux paragraphes 102 et 103 du document
`AMELIORATIONS SENAITE LIMS.docx`. Les exigences sont confrontées au code,
indépendamment des images et des tests préexistants.

## Analyste affecté à chaque analyse

Le champ natif `Analyst` contient un identifiant de compte utilisé par le
workflow. Il ne permet pas de référencer tous les contacts du laboratoire.
Le champ `AssignedLabAnalyst` ajoute une référence unique vers un `LabContact`.
La colonne « Analyste (contact labo) » et le bouton « Affecter » apparaissent
dans les grilles d'analyses des échantillons et des feuilles de travail.

Le formulaire propose les contacts actifs, y compris sans compte utilisateur.
L'affectation est facultative et modifiable tant que l'analyse est enregistrée,
non attribuée ou attribuée. Elle est verrouillée après soumission. La permission
native de modification des conditions d'analyse est requise ; le formulaire
contrôle le jeton CSRF et refuse une révision devenue obsolète.

Un contact devenu inactif reste visible dans l'historique de son affectation.
Il peut être remplacé ou retiré avant soumission. Aucun compte, rôle ou résultat
n'est modifié par cette affectation. Le champ natif `Analyst` est conservé pour
le workflow et l'identité de l'utilisateur ayant effectivement saisi les résultats.

La migration 1012 reprend les anciens identifiants uniquement lorsqu'ils
correspondent à un seul contact du laboratoire. Elle ne devine pas les liens
ambigus et ne rétablit pas une affectation volontairement effacée.

## Historiques des équipements

Chaque fiche équipement dispose de deux onglets utilisant les interventions
natives :

- « Historique des pannes » : interventions de type `Repair`.
- « Historique des entretiens » : interventions de type `Preventive`.

Les historiques reprennent les interventions existantes et permettent d'en
ajouter avec le type présélectionné. Les dates, l'intervenant, les travaux,
les remarques et la clôture restent gérés par les formulaires natifs.
Le type est désormais obligatoire et limité au vocabulaire natif lors de
l'enregistrement. Les améliorations (`Enhancement`) et les anciennes
interventions non classées restent accessibles dans l'onglet Maintenance.
Aucune intervention ancienne n'est reclassée ou supprimée automatiquement.

La migration ajoute les deux actions de manière idempotente. La désinstallation
retire ces actions et conserve les interventions et les références enregistrées.

## Vérification locale

Instance isolée : `http://localhost:8082/senaite`, profil 1012.
Sauvegarde vérifiée avant migration :
`backups/senaite-data-20261125-152056-49530.tar.gz` (772 fichiers).

Les contrôles natifs ont vérifié l'affectation de Paul Randria, contact sans
compte, sur VAN-0012 / VANILLINE, sans modifier l'analyste natif ; le rejet des
UID invalides, des sélections multiples, des révisions obsolètes et des jetons
CSRF invalides ; le refus d'accès anonyme et le verrouillage après soumission.
Le retrait volontaire d'une affectation survit à une nouvelle migration.

Les deux historiques incluent les anciennes interventions et les fixtures
`VERIF-PANNE` et `VERIF-ENTRETIEN`. L'intervention `VERIF-AMELIORATION`
n'apparaît dans aucun des deux historiques spécialisés. La présélection du type
est vérifiée lors de la création native.

Les contrôles navigateur ont confirmé le retrait puis la réaffectation du
contact, sa présence dans la grille, la traduction des deux onglets, la
présélection du type, la création et la consultation d'une intervention, et
l'absence de mélange entre les deux historiques. Les interventions
`VERIF-PANNE-UI` et `VERIF-ENTRETIEN-UI` sont conservées dans la copie locale,
clôturées avec des dates passées.

La création depuis le navigateur a révélé un défaut natif supplémentaire :
`Type` est un `StringField` utilisant un ancien `ReferenceWidget`, qui échoue
sur `field.relationship` à l'ouverture de la fiche. Le modificateur de schéma
utilise désormais le `SelectionWidget` natif ; l'enregistrement et l'ouverture
de la fiche ont ensuite été vérifiés avec une réponse HTTP 200.

Validation automatique : `make test-pure` passe ses 290 tests ; les 7 tests
ciblés de `tests/test_assignment_history.py` passent avec `bin/zopepy -m unittest
senaite.trimeta.samplefields.tests.test_assignment_history`. Les contrôles de
site utilisent les classes installées et la copie de la base. `make test` a
été tenté : le lanceur Plone complet n'est pas disponible dans l'image locale.

Le lot reste soumis à la validation utilisateur avant publication. Il ne
constitue pas une certification globale de toutes les exigences du document Word.
