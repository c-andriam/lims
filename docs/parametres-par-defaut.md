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

## Comment c'est appliqué

- **Langue et fuseau** : `profiles/default/registry.xml`. Seules les
  clés listées sont écrites ; le reste du registre n'est pas touché.
- **Devise et pays** : `set_lab_defaults()` dans `setuphandlers.py`.
  Ce sont des champs du Setup SENAITE, pas du registre. Seules les
  valeurs d'usine (EUR, pays vide) sont remplacées : un choix fait
  ensuite par le laboratoire est conservé. Une valeur absente de la liste
  du champ n'est jamais écrite.
- **Site existant** : étape de mise à jour **1004 → 1005**
  (Configuration du site › Modules, ou `portal_setup` › Upgrades).
- **Installation neuve** : appliqués directement par le profil.

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

## Limite connue : libellés restés en anglais

Certains libellés restent en anglais (« Date Sampled », « Batch »…).
La langue n'y est pour rien : le catalogue français de senaite.core 2.6
n'est traduit qu'à moitié (1 117 entrées vides sur 2 225). Par exemple,
le libellé `label_sample_datesampled` de l'en-tête d'échantillon n'a pas
de traduction. Pour corriger, l'add-on peut fournir ses propres
traductions des libellés visibles.
