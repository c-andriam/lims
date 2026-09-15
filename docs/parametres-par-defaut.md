# Paramètres par défaut du site

Réglages posés par l'add-on `senaite.trimeta.samplefields` : ils ne se
font plus à la main après une installation ou une réinstallation.

| Réglage | Valeur | Écran |
|---|---|---|
| Langue par défaut | Français | Configuration du site › Langue |
| Langues proposées | Français, anglais | idem |
| Langue du navigateur | Ignorée | idem |
| Sélecteur de langue (cookie) | Conservé | idem |
| Variantes régionales (fr-fr) | Désactivées | idem |
| Fuseau horaire du portail | Indian/Antananarivo | Configuration du site › Date et heure |
| Devise | Ariary malgache (MGA) | Setup › Accounting |
| Pays | Madagascar | Setup › Accounting |
| Séparateur décimal des rapports (COA) | Virgule | Setup › Results Reports |
| Premier jour de la semaine | Lundi | Configuration du site › Date et heure |
| Libellés de l'interface | Traduits en français | Catalogues de l'add-on |
| Logo de la barre d'outils | Trimeta Group (version blanche) | Setup › Apparence |

## Comment c'est appliqué

- **Langue et fuseau** : `profiles/default/registry.xml`. Seules les
  clés listées sont écrites ; le reste du registre n'est pas touché.
- **Devise et pays** : `set_lab_defaults()` dans `setuphandlers.py`.
  Ce sont des champs du Setup SENAITE, pas du registre. Seules les
  valeurs d'usine (EUR, pays vide) sont remplacées : un choix fait
  ensuite par le laboratoire est conservé. Une valeur absente de la liste
  du champ n'est jamais écrite.
- **Virgule décimale des rapports** : même fonction ; seul le point
  d'usine est remplacé. La saisie des résultats (`ResultsDecimalMark`)
  n'est pas modifiée : l'affichage change, pas la manière de saisir.
- **Lundi** : `set_first_weekday()`. Dimanche (6), posé par Plone à la
  création du site, est traité comme une valeur d'usine.
- **Site existant** : étapes de mise à jour **1004 → 1005** (langue,
  fuseau, devise, pays) puis **1005 → 1006** (virgule décimale, lundi),
  depuis Configuration du site › Modules, ou `portal_setup` › Upgrades.
- **Installation neuve** : appliqués directement par le profil.

## Logo de l'application

- **Image** : logo Trimeta Group, version blanche, 180 × 92 px, adaptée
  au fond sombre de la barre d'outils. Source :
  `https://trimetagroup.com/wp-content/uploads/2024/08/LOGO-GROUPE_BLANC-SANS-SINCE-RECTANGLE-180x92.png.webp`.
- **PNG plutôt que WebP** : même image, au format PNG proposé par le
  même site. SENAITE sert le logo à travers la chaîne d'images Python 2,
  qui ne garantit pas le WebP.
- **Embarqué dans l'add-on** (`setup_data/logo-trimeta-groupe-blanc.png`) :
  l'affichage ne dépend pas du site du groupe, ni d'un accès Internet
  depuis les postes du laboratoire.
- **Pose** : `set_site_logo()`, à l'installation et par l'étape
  **1006 → 1007**, avec une hauteur d'affichage de 32 px. Un logo déjà
  choisi dans Setup › Apparence est conservé.
- **Page de connexion** : non modifiée. Son fond est blanc, où la
  version blanche du logo serait invisible ; il faudrait la version
  couleur.

## Pourquoi le fuseau compte

Le fuseau du portail doit concorder avec `TZ=Indian/Antananarivo` du
conteneur (`compose.yml`). senaite.core compare certaines dates sans
convertir les fuseaux, par exemple la date de prélèvement et la date de
création de l'échantillon. Un écart fait refuser des enregistrements
valides (« Date Sampled is after … »). Les scripts ponctuels
(`bin/instance run`) doivent recevoir le même `TZ`.

## Choix de la langue

La langue du navigateur est ignorée : un poste configuré en anglais
affiche quand même le français. Qui veut basculer ponctuellement en
anglais utilise le sélecteur de langue ; le choix est gardé dans un
cookie, pour ce navigateur seulement.

## Vérification (15/09/2026, local)

Étape 1005 jouée sur la base de démonstration :

- **Avant** : langues fr, en, de, es ; variantes régionales activées ;
  fuseau UTC ; devise EUR ; pays vide.
- **Après** : langues fr, en ; variantes désactivées ; fuseau
  Indian/Antananarivo ; devise MGA ; pays MG.
- Page de connexion demandée par un navigateur en anglais, sans cookie :
  `lang="fr"`, « Se connecter », « Mot de passe ».
- Écrans de configuration : Indian/Antananarivo, Madagascar Ariary
  (MGA), Madagascar, Français.

## Traductions françaises

### Le constat

Passer le site en français ne suffisait pas : des libellés restaient en
anglais (« Date Sampled », « Batch », « Save »…), et les dates
s'affichaient au format ISO (2026-09-12 14:03).

- Le catalogue français de senaite.core 2.6 n'est traduit qu'à moitié :
  1 117 entrées vides sur 2 225, dont les formats de date.
- senaite.impress (écran de publication) n'a aucun catalogue français.
- Certaines traductions existantes sont trompeuses : « Batch » rendu
  par « Lot », qui se confond avec le lot de l'échantillon ; « Sauver » ;
  « Profiles d'analyse ».
- Les libellés propres à l'add-on étaient écrits sans accents.

### La méthode

1. Relevé des textes réellement affichés sur 15 écrans (navigateur
   connecté), croisé avec tous les catalogues SENAITE : 162 libellés à
   traduire.
2. Catalogues complémentaires dans `locales/fr/LC_MESSAGES/` :
   `senaite.core.po`, `plone.po`, `senaite.impress.po`. Le catalogue de
   l'add-on a reçu ses accents.
3. **Priorité** : zope.i18n rend la traduction du premier catalogue qui
   connaît un message, et senaite.core est chargé avant l'add-on. Au
   démarrage, `i18n.prioritize_trimeta_catalogs` place nos catalogues en
   tête ; sans cela, « Lot » serait resté.
4. **Compilation** : Zope ne lit que les `.mo`. Après toute modification
   d'un `.po` : `make i18n`, puis redéployer. Le test `test_i18n.py`
   échoue si un `.mo` ne correspond plus à son `.po`.

### Terminologie retenue

| Anglais | Français |
|---|---|
| Batch | Série |
| Date Sampled | Date de prélèvement |
| Sample Point | Point de prélèvement |
| Instruments | Équipements |
| Worksheets | Feuilles de travail |
| Save | Enregistrer |
| Analysis Profiles | Profils d'analyse |
| Container / Preservation | Contenant / Conservation |

Dates : jj/mm/aaaa, et jj/mm/aaaa hh:mm pour le format long.

### Vérification (15/09/2026)

Nouveau relevé sur les 15 écrans après redémarrage : 4 libellés sans
traduction, contre 162 au départ. Contrôlé à l'écran : en-tête de
l'échantillon (« Date de prélèvement », « Série », « Profils
d'analyse », « Enregistrer »), dates jj/mm/aaaa dans les listes, aucune
erreur JavaScript.

### Ce qui reste en anglais

- **Onglets et tuiles de la configuration** (« Accounting »,
  « Appearance », « Sticker », « Analysis Services »…) : ces écrans ne
  passent pas par les messages traduits de senaite.core ni de plone. À
  traiter à part si le laboratoire y travaille souvent.
- **Barre de l'éditeur de texte** (File, Edit, Insert, Undo…) : TinyMCE a
  ses propres fichiers de langue.
- **Pied de page** (« Browse the Docs », « Visit the Website »…) : écrit
  en dur dans le gabarit de SENAITE, sans message traduisible.
- Un écran non relevé peut encore montrer un libellé non traduit : le
  signaler, il suffit de l'ajouter au `.po` concerné puis `make i18n`.
