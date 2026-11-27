# Verification des historiques d'equipement

Verification D6 du 27 novembre 2026, sur le code de `main` a `ecb0e7d`.

## Lecture du code

`browser/equipment_history.py` derive de la liste native des interventions
et conserve la recherche et la pagination du moteur SENAITE. Son filtre
`isItemAllowed` appelle `belongs_to_history` : `Repair` pour les pannes,
`Preventive` pour les entretiens. Les types sont normalises par le module
`listings/instruments.py`. La vue propose par defaut l'etat `all` afin de
ne pas masquer les anciennes interventions inactives.

Dans le moteur installe, `senaite.app.listing.view.ListingView.search`
applique `isItemAllowed` avant que `_fetch_brains` calcule le total et
decoupe la page. Les autres types d'intervention ne faussent donc pas les
compteurs ni les limites de pages des deux historiques.

## Controle sur objets natifs

Une copie isolee de la base a servi a creer temporairement 65 interventions
alternees : 33 Repair et 32 Preventive, en plus des interventions deja
presentes sur l'equipement de recette.

- Historique des pannes : 36 interventions, aucune intervention Preventive.
- Historique des entretiens : 35 interventions, aucune intervention Repair.
- Pages de dix lignes : dernieres pages completes selon le reliquat,
  compteurs exacts, aucun doublon et aucune intervention perdue.
- Etat par defaut `all` confirme avec la classe native.

La transaction de recette a ete annulee. La base interactive du port 8082
et les volumes d'origine n'ont pas ete modifies.

Aucun defaut confirme sur ce point : ce lot documente la verification et
n'ajoute pas de modification applicative. Il ne certifie pas le deploiement
de ces vues et du profil 1012 sur le serveur de production.
