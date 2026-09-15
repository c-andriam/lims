# Suggestions des champs libres (« rajout mémorisé »)

## Ce qui est demandé

Pour les champs saisis librement (provenance, désignation, lots de
solvants, numéros de série…), le document demande qu'une valeur déjà
saisie soit **mémorisée** et **proposée** lors des saisies suivantes.

## Où le menu apparaît

| Écran | Exemple de champs |
|---|---|
| Formulaire de création d'échantillon (`ar_add`) | Provenance, Désignation, Détail fournisseur… |
| Page de l'échantillon (en-tête modifiable) | Lot éthanol, Lot acétonitrile, Lot eau HPLC, Lot isopropanol, N° de série colonne et lampe |
| Modification complète (`base_edit`) | les mêmes champs |

La liste des champs a une seule source : `SUGGESTION_FIELDS` dans
`suggestions.py`. Le viewlet la publie pour le script
`browser/resources/field_suggestions.js`.

## Utilisation

- Cliquer dans le champ : le menu **Suggestions** s'ouvre. Il se filtre
  pendant la frappe.
- Cliquer une suggestion : elle remplit le champ.
- La croix ✕ au survol retire une suggestion devenue inutile.
- Une valeur est mémorisée **dès qu'on quitte le champ** (ou avec
  Entrée), pour tous les postes, sans attendre l'enregistrement.

## Choix techniques

- **Écoute déléguée au document.** L'en-tête de l'échantillon remplace
  ses champs après chaque modification, et le formulaire de création en
  ajoute (+Add). Un écouteur posé sur chaque champ perdait les nouveaux.
- **Fermeture différée ciblée.** En passant d'un champ à suggestions à
  un autre, le délai de fermeture du premier refermait le menu du
  second. Il ne ferme plus que les menus des autres champs.
- **Version du script** : `SUGGESTIONS_SCRIPT_VERSION` dans
  `browser/viewlets.py`, à incrémenter à chaque modification du script,
  sinon les navigateurs gardent l'ancienne version en cache.
- **API** : `@@trimeta-suggestions` (GET liste, POST `add` / `remove`),
  réservée aux utilisateurs connectés.

## Vérification (15/09/2026, Chromium sans interface)

Connexion par le formulaire, puis :

1. Page de VAN-0006 : menu ouvert sur *Lot éthanol*. `ETH-2026-034`
   saisi puis champ quitté : la valeur est mémorisée, et le menu la
   propose au clic suivant.
2. Enregistrement de l'en-tête : « Modifications sauvegardées ». La
   valeur est bien en base (API JSON).
3. `base_edit` et `ar_add` : menus ouverts sur *Lot éthanol*,
   *Provenance* et *Désignation*.
4. Aucune erreur JavaScript.

> **Piège rencontré, sans lien avec les suggestions.** Sur les
> échantillons de démonstration, l'en-tête refusait l'enregistrement
> (« Date Sampled is after … »). Ces échantillons avaient été créés par
> un script lancé **sans** `TZ`, donc en heure GMT, alors que le
> navigateur envoie l'heure de Madagascar. senaite.core compare les
> heures sans convertir les fuseaux. Sur le serveur, tout tourne dans le
> même fuseau (`TZ=Indian/Antananarivo` dans `compose.yml`) et le
> problème ne se pose pas. Il faut toujours passer ce `TZ` aux scripts
> ponctuels (`bin/instance run`).
