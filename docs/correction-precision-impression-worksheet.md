# Décimales et identification des feuilles de travail

Demande du laboratoire du 25 novembre 2026, après le commit `57bcf0a` : corriger
les arrondis des CSV et des impressions, compléter l'identification des
échantillons et distinguer les responsabilités des analystes.

## Valeurs présentées

SENAITE conserve `27.9`, `0.61` et `2.05`, mais son formateur les présentait
`28`, `1` et `2` selon la précision configurée. Les feuilles de travail et leurs
sorties conservent désormais tous les chiffres du résultat numérique enregistré.
Le séparateur décimal suit celui utilisé par la vue native : les impressions
de ce client affichent ainsi `27,9`, `0,61` et `2,05`.

Le traitement ne convertit pas les résultats en flottants : il préserve les
zéros finaux et la notation scientifique. Les limites de détection restent
préfixées (`<0.61`, par exemple). Les résultats textuels, les codes de choix
et les valeurs non numériques conservent le formatage natif. Le contrôle natif
`ViewResults` reste préalable à la présentation dans les grilles.

Aucun résultat, compte utilisateur, état de validation, affectation ou réglage
de précision d'un service n'est modifié. Ce lot ne change pas les gabarits COA.
Les noms CSV du lot précédent sont conservés.

## Impression

La vue `print` est surchargée par une sous-classe de la vue native, sur la
couche de l'add-on et avec la même permission `ViewResults`. Les deux modèles
standards « Sample By Column » et « Sample By Row » sont dérivés des modèles
installés de SENAITE 2.6.0 ; leurs styles, contrôles, états et codes-barres natifs
sont conservés.

- Le code échantillon est ajouté en conservant l'identifiant SENAITE.
- L'en-tête indique « Analyste de la feuille ».
- Chaque résultat indique « Analyste affecté » et le contact enregistré pour
  cette analyse ; une affectation vide est explicitement signalée.
- Les modèles tiers restent délégués au moteur natif.

Les modèles sont sélectionnés par la même interface ; aucune modification du
registre de modèles ou nouvelle migration GenericSetup n'est nécessaire.

## Vérification

Sauvegarde locale vérifiée avant intervention :
`backups/senaite-data-20261125-165146-135026.tar.gz` (782 fichiers).

`make test-pure` : 298 tests réussis, dont 8 sur la précision. Les tests ciblés
utilisent les classes natives pour vérifier le raccordement, le masque de
permission, la sélection des modèles et la délégation des modèles tiers.

Un contrôle sur la copie de la base a vérifié les valeurs exactes dans les deux
vues et les deux modèles, la présence du code `ECH-DEMO-002`, de Paul Randria et
de Marie Rakoto. Une comparaison avant/après confirme la conservation des
résultats, opérandes, comptes, états, affectations et précisions des services.
Cette vérification est annulée transactionnellement après lecture.

Contrôle navigateur final du 26 novembre 2026 : les fichiers réellement
téléchargés `WS-001-classique.csv` et `WS-001-transposee.csv` contiennent
`27.9`, `0.61` et `2.05`. Les deux pages d'impression répondent HTTP 200 et
affichent le code échantillon, les décimales avec virgule, « Analyste de la
feuille » et les contacts affectés à chaque résultat. Les codes-barres natifs
de `VAN-0006` sont conservés.

Les 6 contrôles ciblés des classes natives passent. `make test` est également
tenté : le lanceur Plone complet reste absent de l'image locale.

Complément du 26 novembre : le modèle en lignes reprend désormais les six
informations du modèle en colonnes, avec leurs libellés : client, type
d'échantillon, identifiant, code échantillon, date d'échantillonnage avec heure
et date de réception. Le résumé compact natif omettait la date d'échantillonnage.
La présence des six champs et des décimales est vérifiée dans les deux pages
d'impression, sans changement des styles natifs.
