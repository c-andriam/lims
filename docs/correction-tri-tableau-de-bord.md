# Tableau de bord : ordre des colonnes et tris globaux

Correction locale du 25 novembre 2026, demande D12 du document AMELIORATIONS SENAITE LIMS.

## Ordre des vingt colonnes

Les dix colonnes descriptives sont suivies de : Vanilline, Gluco-vanilline, AC Vanillique, PHB, AC PHB, opérateur HPLC, TH, opérateur TH, AW, opérateur AW.

Les opérateurs ne sont donc plus regroupés à la fin du tableau. La liste textuelle du Word place PHB avant AC PHB, alors que le tableau du même document inverse ces deux intitulés. Cette correction conserve la liste textuelle déjà utilisée par le projet ; elle corrige l’écart certain sur les opérateurs.

SENAITE conserve aussi l’ordre dans le stockage local du navigateur. Le script du tableau de bord, version **6**, reprend uniquement une configuration correspondant exactement à l’ancien ordre par défaut. Il remet les entrées dans l’ordre courant en conservant leurs options, notamment les colonnes masquées. Les autres ordres personnalisés et les préférences des autres listes ne sont pas modifiés. Une préférence illisible n’empêche pas la page de s’afficher.

## Tri par type et par Vanilline

Les en-têtes Type et Vanilline sont triables dans les deux sens. SENAITE fournit un point d’extension `sort_brains` utilisé dans `ListingView.search()` avant `_fetch_brains()` et sa pagination. Les deux critères sont déclarés explicitement comme tris manuels ; ils ne sont pas transmis comme des index inexistants au catalogue.

Le tri Type utilise le libellé affiché, sans distinction de casse ou d’accents. Le tri Vanilline est numérique : 2 précède 10. Il utilise la même sélection de service et de reprise que l’affichage et le filtre de plage : priorité aux mots-clés reconnus, puis au résultat renseigné le plus récent pour chaque mot-clé.

Les résultats absents, textuels, non finis ou assortis d’une limite de détection sont placés à la fin dans les deux sens. Les égalités conservent un ordre stable par identifiant et UID, afin de stabiliser le passage entre les pages.

Le tri travaille sur les échantillons déjà retenus par les filtres, la recherche et les permissions du catalogue natif. La Vanilline est lue par une requête groupée sur les analyses de cette sélection. Aucun objet d’analyse n’est ouvert pendant le tri. Ce tri global demande de traiter toutes les lignes retenues avant de découper les pages ; son coût augmente avec la taille de la sélection.

## Limites de détection et profil 1011

Le code natif d’`AbstractAnalysis.setResult()` stocke séparément le nombre et `DetectionLimitOperand`. Le catalogue d’analyses natif expose `getResult` mais ne conserve pas ce signe dans une colonne. Lire uniquement le nombre perdait donc une information nécessaire au tableau de bord.

La nouvelle colonne de métadonnées `getTrimetaDetectionLimitOperand`, alimentée par un indexeur `IAnalysis`, conserve le signe. Le regroupement des résultats rétablit `<` ou `>` devant la valeur avant l’affichage, le filtrage de plage et le tri. Un texte déjà préfixé ne reçoit pas un second signe. NaN et les infinis sont également exclus des nombres comparables.

L’étape **1010 → 1011** ajoute cette colonne et actualise les métadonnées des analyses existantes. Elle ne recalcule ni ne remplace les résultats d’analyse. Une installation neuve utilise le même mécanisme de configuration des catalogues. Le redémarrage et l’application du profil sont nécessaires ; charger les seuls fichiers ne suffit pas pour les anciennes analyses.

## Données et vérifications

Sauvegarde préalable vérifiée de la copie locale : `/home/candriam/lims-review-point1/backups/senaite-data-20261125-142116-1488.tar.gz` : ZODB, blobs et 773 fichiers. Les sources précédentes sont conservées dans `source-backup-dashboard-sort-20261125`. La base d’origine est conservée.

Les **290 contrôles de logique pure passent**. Ils couvrent notamment l’ordre des vingt colonnes, les six critères de tri demandés, les nombres avec virgule, le tri numérique, les égalités, les reprises, les limites de détection, les nombres non finis, les métadonnées absentes et les libellés de type non latins.

Quatre tests ciblés exécutent `search()` et `_fetch_brains()` de la vraie classe native avec des catalogues de test : tri avant pagination, sens descendant avec reprise, tri des types et absence de transmission des deux critères manuels comme index au catalogue.

Cinq contrôles JavaScript exécutent le vrai script et vérifient la migration des préférences, la conservation des options, l’idempotence, les ordres personnalisés, les données illisibles et l’absence d’effet sur une autre liste ou une autre page.

Sur la copie locale, le profil 1011 a été appliqué et les résultats stockés des **51 analyses existantes** ont été comparés avant et après : ils sont conservés. Le contrôle compare les objets stockés, car la réindexation peut actualiser des métadonnées antérieurement différentes.

Six échantillons identifiés par les codes `VERIF-TRI-*` sont conservés uniquement sur la copie, dans le lot **LOT-VERIF-TRI**. Ils couvrent les valeurs 0, 2, 2, 10, une limite `<0.5` et une case vide, réparties entre deux types. La valeur 10 provient d’une reprise, après une première mesure à 1. Pour la limite, le jeu de contrôle active les options natives de saisie sur cette analyse seulement : le moteur refuse normalement un signe lorsque ces options sont désactivées.

Les contrôles natifs et navigateur confirment :

- les tris Type et Vanilline dans les deux sens par clic sur les en-têtes ;
- l’ordre ascendant 0, 2, 2, 10, puis limite et case vide ;
- les opérateurs à leur place parmi les vingt colonnes ;
- le chargement par deux lignes avec **Afficher plus**, sans rupture du tri global ni perte du filtre Lot ;
- la plage 0 à 1, qui retient la mesure exacte 0 et exclut `<0.5`.

Les données et calculs natifs de ces contrôles ont été utilisés sur la copie du port 8082. Aucun certificat historique n’a été régénéré.

La migration des préférences a aussi été contrôlée dans le navigateur : une ancienne configuration avec Provenance masquée affichait encore les opérateurs en fin de tableau malgré le nouvel ordre serveur. Après chargement du script version 6, l’ordre enregistré et l’ordre affiché sont corrigés, et Provenance reste masquée. Les préférences de cette simulation ont ensuite été restaurées ; la page de démonstration affiche de nouveau les vingt colonnes.

La suite Plone complète reste indisponible dans cette image, faute de lanceur. Les contrôles ciblés ne remplacent pas cette suite.

Statut : correction et contrôles locaux réalisés, profil 1011 appliqué sur la copie. Correction non commitée et non poussée, en attente de validation utilisateur.
