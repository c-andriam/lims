# Audit technique SENAITE Trimeta — 28 septembre 2026

## Périmètre et méthode

L'audit couvre l'add-on `senaite.trimeta.samplefields`, sa configuration
SENAITE 2.6.0, les scripts d'exploitation et l'instance locale de test
`http://localhost:8080/senaite`. Les contrôles applicatifs ont été effectués
en lecture seule. Aucun échantillon, client, résultat ou autre donnée métier
n'a été créé, modifié ou supprimé.

Les preuves reproductibles sont dans `preuves-http.json` et
`preuves-zodb.json`. La première interroge les listings HTTP avec le compte
local configuré. La seconde ouvre une connexion ZODB explicitement déclarée
en lecture seule et compare les objets aux index du catalogue.

## Conclusion

La base et le catalogue sont cohérents pour les six échantillons existants :
six objets directs, six entrées de catalogue, aucun UID manquant et aucun
écart entre `SampleCode` stocké et indexé. Le symptôme « nouvel échantillon
absent » ne peut donc pas être attribué à une corruption générale du
catalogue à partir des données présentes.

Le chemin de création comporte toutefois deux défauts confirmés qui peuvent
produire le comportement silencieux décrit :

1. Le formulaire masque volontairement le bandeau natif d'erreur
   (`portalMessage.alert-danger`). Une erreur globale renvoyée par SENAITE
   devient invisible après la soumission.
2. Les champs de réception sont déclarés `required=True` dans le fichier
   source, mais les 24 champs étendus chargés dans l'instance ont tous
   `required=False`. Le schéma réel ne porte donc pas les règles métier
   attendues. Seuls `Client`, `Contact`, `SampleType` et `Analyses` sont
   obligatoires au moment du contrôle natif.

Une soumission incomplète a renvoyé « Aucun échantillon n'a pu être créé » et
a redirigé vers la liste. Ce test n'a créé aucune donnée. La cause exacte
d'une soumission réelle et complète devra être capturée avec le code de
l'échantillon concerné ou pendant une reproduction contrôlée avec des valeurs
métier autorisées.

## Défauts confirmés et risques

| Priorité | Constat | Preuve / effet |
|---|---|---|
| P0 | Les erreurs globales de création sont cachées | `browser/viewlets.py` injecte `display:none!important` sur le bandeau d'erreur. L'utilisateur obtient un retour silencieux. |
| P0 | Les obligations métier ne sont pas actives dans le schéma chargé | Les 24 champs de l'extension sont `required=False` à l'exécution, malgré 16 déclarations obligatoires dans le source. |
| P1 | Le tableau de bord omet des échantillons sans date de réception | 6 lignes avec tri `created`, 4 avec tri `getDateReceived`; `VAN-0002` et `VAN-0003` disparaissent. |
| P1 | Trois fichiers de tests ne sont pas exécutés par le lanceur annoncé | 218 tests passent, mais `test_catalog_wiring.py`, `test_field_references.py` et `test_coa_filename.py` sont exclus. Leur exécution révèle une erreur de contrat COA (`SAMPLE_CODE_FIELD` absent). |
| P1 | Les valeurs numériques non finies sont acceptées | La conversion par `float()` laisse passer `nan` et `inf`, ce qui peut fausser les filtres et résultats. |
| P1 | La logique de répétition n'utilise pas partout la même analyse | Le filtrage peut retenir un ancien résultat dans l'intervalle tandis que l'affichage choisit le dernier résultat non vide. |
| P1 | Sauvegarde et restauration insuffisamment sûres | La sauvegarde copie un FileStorage actif sans mécanisme de snapshot; la restauration demande la suppression du conteneur avant validation complète de l'archive. |
| P2 | Deux moteurs de conteneurs peuvent être sélectionnés indépendamment | Sur une machine qui possède Docker et Podman, `ENGINE` et `COMPOSE` peuvent diverger. |
| P2 | Secrets et artefacts de base figurent dans les fichiers du projet | Les identifiants doivent être externalisés et l'historique Git assaini; `Data.fs` et fichiers de verrouillage ne doivent pas être versionnés. |
| P2 | Socle obsolète | Python 2.7 n'est plus maintenu et augmente les risques de sécurité, compatibilité et maintenance. Une migration doit être préparée séparément. |

## Couverture du cahier d'améliorations

| Lot | État constaté | Travail restant avant recette |
|---|---|---|
| D1 Réception | Partiel, validation obligatoire défaillante | Corriger le schéma réel, rendre `DateReceived` obligatoire, valider les formats et relations, tester une création autorisée de bout en bout. |
| D2 Analyse | Partiel | Rétablir l'obligation du numéro de fiche; valider chronologie, préparateurs multiples et opérateur par analyse. |
| D3 Assurance qualité | 41 champs présents | Valider persistance, droits, rendu et export sur une donnée métier approuvée. |
| D4 Listes échantillons | Code et lot câblés | Tester toutes les vues et états; corriger les disparitions liées au tri. |
| D5 Certificat d'analyse | Implémentation présente, contrats de tests divergents | Unifier la génération active, les noms, auteurs/dates et contrôler un PDF réel. |
| D6–D10 Fonctions natives | Dépendantes de la configuration | Recette fonctionnelle avec rôles, instruments, feuilles de travail, calculs et nommage. |
| D11 PDF multiples | Non prouvé en conditions réelles | Définir le comportement multi-modèle et vérifier les téléchargements. |
| D12 Tableau de bord | 20 colonnes et filtres présents | Corriger le tri qui exclut les dates absentes et sécuriser les résultats non finis/répétés. |
| D13 Export feuille de travail | Correctif présent | Vérifier page courante, export complet, orientation et séparateur avec un jeu métier autorisé. |
| D14 Rapports | Câblage présent | Valider affichage et export de `SampleCode` sur les rapports réels. |

## Limites de la preuve actuelle

Les six échantillons existants portent des données de démonstration déjà
présentes. Ils ont uniquement été lus. Aucun test positif de création n'a été
effectué car il nécessiterait des valeurs métier réelles et l'autorisation de
les enregistrer. Les tests purs prouvent des fonctions isolées; ils ne
prouvent pas une transaction ZODB complète, l'indexation asynchrone, les
permissions ni le rendu navigateur final.

## Éléments à préserver

Le dépôt Windows et le répertoire réellement monté par Podman sous WSL ne
pointent pas vers le même checkout Git. Toute correction doit être appliquée
au dépôt de référence puis déployée explicitement, afin d'éviter de tester un
code différent de celui relu dans l'IDE. Les modifications locales existantes
dans `setup.py`, `extender.py` et `check_catalog.py` n'ont pas été écrasées.
