# Données de démonstration : doublons nettoyés

Concerne **uniquement l'instance locale** (WSL). Le serveur réel n'est
pas concerné : ses données sont celles du laboratoire.

## Le constat

Les scripts de données de test avaient été rejoués plusieurs fois. Chaque
passage recréait les mêmes objets, d'où des listes déroulantes et des
écrans de configuration encombrés.

| Type | Actifs avant | Doublons |
|---|---|---|
| Services d'analyse | 36 | 7 services en 5 exemplaires |
| Catégories d'analyse | 5 | 1 catégorie en 5 exemplaires |
| Types d'échantillon | 5 | « Vanille verte » en 5 exemplaires |
| Contacts du laboratoire | 10 | 2 personnes en 5 exemplaires |
| Clients | 5 | 4 copies sans nom de « Cooperative Sambava » |

## La méthode

1. **Sauvegarde** (`make backup`, 8,3 Mio) avant toute écriture.
2. **Audit en lecture seule**, relu avant application.
3. **Désactivation, jamais suppression** : tout reste réactivable, et les
   échantillons qui référencent un objet désactivé restent intacts.

Règles de choix de l'objet conservé, dans l'ordre :

- **lié à un compte utilisateur** : le contact « Marie Rakoto » relié au
  compte `mrakoto` est gardé ; désactiver l'autre aurait coupé son accès ;
- **le plus utilisé** : analyses pour un service, échantillons pour un
  type ou un client, services restés actifs pour une catégorie ;
- **le plus ancien**, à égalité.

Précautions :

- deux objets **sans intitulé** ne sont jamais regroupés. Seule
  exception, explicite : un client sans nom qui porte l'identifiant client
  d'un client nommé actif (TRIDEMO) en est une copie ;
- **catégories** : senaite.core refuse de désactiver une catégorie encore
  référencée par un service, même désactivé. Les services doublons ont
  d'abord été rattachés à la catégorie conservée.

## Résultat (15/09/2026)

48 objets désactivés. Restent actifs :

| Type | Actifs |
|---|---|
| Services d'analyse | 8 (les 7 du tableau de bord + « Vanilline (moyenne 3 rep.) ») |
| Catégories d'analyse | 1 |
| Types d'échantillon | 1 |
| Contacts du laboratoire | 2 |
| Clients | 1 (Cooperative Sambava) |

Les 6 échantillons de démonstration restent accessibles. VAN-0001 à
VAN-0004 appartiennent aux clients désactivés : visibles dans la liste
des échantillons, pas dans la liste des clients.

Script : `/tmp/dedupe.py` de la session de test (audit par défaut,
`APPLY=1` pour appliquer), non versionné car propre aux données locales.
