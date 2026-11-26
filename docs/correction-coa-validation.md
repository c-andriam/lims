# Cohérence de la validation affichée sur le COA

Le Word demande « Date Validated » et « Validated by ». Jusqu'ici, le premier
champ utilisait la validation du workflow, alors que le second lisait
`FinalValidator`, contact facultatif choisi dans l'onglet Assurance Qualité.
Ces deux informations pouvaient donc concerner des personnes différentes,
ou présenter une date de validation avec un nom vide.

## Comportement

La date et le nom proviennent désormais du même événement `verify` de
l'historique SENAITE, lu du plus récent au plus ancien. C'est aussi l'ordre
utilisé par `AnalysisRequest.getDateVerified()` dans la version installée.
Le nom complet du compte enregistré est affiché ; si le compte a été supprimé
ou n'a pas de nom complet, l'identifiant historique est conservé.

Un acteur absent n'est jamais remplacé par l'utilisateur qui produit le COA.
Pour un échantillon actuellement validé ou publié, une métadonnée manquante est
indiquée par « Not recorded ». Pour un échantillon non encore validé ou revenu
à un état provisoire, une ancienne validation n'est pas présentée comme actuelle.

Le contact `FinalValidator`, lorsqu'il est renseigné, reste visible sous
« Designated signatory ». Il est ainsi distingué de l'auteur de la validation
enregistrée. Le champ qualité, les signatures natives, les rôles et les
transitions de workflow ne sont pas modifiés.

La correction concerne les nouveaux rendus du gabarit COA Trimeta, avec les
contrôleurs simple et multiple. Elle ne réécrit pas les PDF historiques et
ne requiert pas de migration GenericSetup.

## Vérification du 26 novembre 2026

- `make test-pure` : 304 tests réussis, dont 6 nouveaux cas de validation.
- 16 contrôles natifs ciblés réussis : raccordement, rendu des coordonnées
  et livraison des PDF.
- Le COA complet a été rendu sur la copie de la base avec un signataire
  temporairement désigné différent de l'acteur historique. « Validated by »
  affiche l'acteur `admin` enregistré dans l'événement ; « Designated signatory »
  affiche Paul Randria. La date correspond à `getDateVerified()`.
- La désignation de test a été annulée transactionnellement. L'historique,
  le champ qualité et les empreintes des 29 PDF stockés sont inchangés.

Les contrôles utilisent les modèles et les classes installés. Le lanceur
Plone complet reste absent de l'image locale.
