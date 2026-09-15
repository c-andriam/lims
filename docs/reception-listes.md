# Condition de l'échantillon et état de l'emballage

## Ce que demande le cahier des charges

> *Condition de l'échantillon (Sample condition : conforme – non
> conforme) (champ obligatoire)
>
> *Etat de l'emballage (Packaging condition : sous vide, sachet zip,
> kraft, autres) (champ obligatoire)

La question « listes fixes ou texte libre ? » est donc tranchée par le
document lui-même : ce sont des listes.

## Ce qui a été fait

| Champ | Choix proposés | Widget |
|---|---|---|
| Condition de l'échantillon | — Choisir —, Conforme, Non conforme | liste déroulante |
| État de l'emballage | Sous vide, Sachet zip, Kraft, Autre… | liste + saisie libre |

- **Condition** : l'entrée « — Choisir — » oblige à un choix explicite.
  Sans elle, « Conforme » serait présélectionné sans que personne l'ait
  décidé, et le champ obligatoire serait satisfait d'office.
- **Emballage** : « autres » correspond au choix « Autre… » du widget
  natif de senaite.core (`SelectOtherWidget`), qui ouvre une zone de
  saisie libre.
- **Données existantes** : la valeur enregistrée est le libellé lui-même
  (« Conforme », « Sachet zip »). Les échantillons déjà saisis restent
  valides sans migration ; un emballage saisi autrement s'affiche comme
  « Autre… » avec sa valeur.
- Ces deux champs ne sont plus des champs à suggestions
  (`suggestions.SUGGESTION_FIELDS`).

Code : `vocabularies.py` (`SAMPLE_CONDITION_VOCAB`,
`PACKAGING_CONDITION_VOCAB`), `extender.py`. Tests :
`test_vocabularies.py`.
