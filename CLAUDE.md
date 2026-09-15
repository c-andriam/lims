# SENAITE LIMS — Trimeta Group

Personnalisation de [SENAITE LIMS](https://www.senaite.com/) 2.6.0 pour
le laboratoire de Trimeta Group (analyse de la vanille : HPLC, taux
d'humidite, activite de l'eau).

Le cahier des charges est le document **`AMELIORATIONS SENAITE LIMS.docx`**
a la racine. Il fait foi. Toute modification doit pouvoir se rattacher a
l'une de ses demandes.

## Structure

    AMELIORATIONS SENAITE LIMS.docx   cahier des charges (source de verite)
    2.6.0/                            deploiement conteneurise
      Makefile                        toutes les operations d'exploitation
      compose.yml                     image senaite/senaite:v2.6.0
      addons/senaite.trimeta.samplefields/
                                      l'add-on, seul code metier du depot
    docs/                             conception et mode d'emploi, par lot
    .claude/skills/                   conventions chargees automatiquement

## Avant toute modification

Charger la skill **`senaite-addon`** : elle porte les contraintes de la
plateforme (Python 2.7, Archetypes, schemaextender) et les cinq points
d'extension utilises ici. Pour tout ce qui touche au container, aux
tests d'integration ou aux etapes de mise a jour, charger
**`senaite-deploy`**.

## Les regles du projet

**Le theme LIMS ne change pas.** Le cahier des charges demande « les
memes interfaces ». On ajoute des champs et des colonnes avec les
composants natifs de SENAITE (`senaite.app.listing`, widgets
Archetypes, `ReferenceWidget`, classes Bootstrap du theme). Aucun style
maison sans necessite demontree.

**Python 2.7 et 3 a la fois.** L'image tourne en 2.7. Pas de f-strings,
pas d'annotations. Pour tester une chaine, `compat.string_types`.

**Pas d'accents dans les sources Python.** Commentaires et docstrings
en francais, sans caracteres accentues : l'encodage du container n'est
pas garanti. Les libelles utilisateur passent par `MessageFactory` et
peuvent tout contenir.

**Une page ne tombe jamais pour une valeur manquante.** Chaque hook de
listing ou de rendu enveloppe son travail dans un `try/except` qui
journalise. Une colonne vide est un desagrement ; un ecran qui ne
s'affiche plus est un arret de travail.

**Rien n'est fini sans tests.** `make test-pure` (instantane, sans
container) avant chaque commit. `make test` quand l'instance tourne.

**Documenter le lot.** Chaque lot a son fichier dans `docs/`, qui dit
ce qui est fait, ce qui reste, et ce qui a ete appris — y compris les
erreurs commises, parce qu'elles se reproduiraient ailleurs.

## Etat des demandes du cahier des charges

| Ref | Demande | Traitement |
|---|---|---|
| D1 | Champs section Reception (15) | `extender.py` |
| D2 | Champs section Analyse (9) | `extender.py` |
| D3 | Donnees assurance qualite (41 champs, 7 sous-sections) | `qualitydata/` |
| D4 | Colonnes Code echantillon / Lot sur les echantillons | `listings/samples.py` |
| D5 | Contenu du COA | `coa/templates/reports/COA-Trimeta.pt` |
| D6 | Historique pannes / entretiens | parametrage, `docs/lot1-parametrage.md` |
| D7 | Analyste par analyse | parametrage, `docs/lot1-parametrage.md` |
| D8 | Code echantillon dans la Work Sheet | `listings/worksheets.py` |
| D9 | Repetitions et moyenne automatique | parametrage, `docs/lot1-parametrage.md` |
| D10 | Nom du COA = Code echantillon | `coa/filename.py` et ses trois surcharges |
| D11 | Export de plusieurs COA au contenu identique | parametrage, `docs/lot1-parametrage.md` |
| D12 | Tableau de bord (20 colonnes, 6 filtres) | `dashboard/` |
| D13 | Bug d'export de donnees depuis la Work Sheet | en attente du symptome, `docs/lot4-coa.md` |
| D14 | Code echantillon dans la liste des rapports | `listings/reports.py` |

## Git

Branche par lot (`lotN-sujet`), PR vers `main`. Message de commit en
francais, imperatif. Pousser apres chaque modification verifiee — jamais
avant que `make test-pure` ne passe.
