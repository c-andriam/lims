# Lot 4 — Le certificat d'analyse

Contenu du COA et nommage des fichiers produits. Deux demandes du
document *AMÉLIORATIONS SENAITE LIMS* :

| Réf | Demande | État |
|---|---|---|
| D5 | Ce qui doit s'afficher sur le COA | ✅ |
| D10 | Le nom du COA doit être le Code échantillon | ✅ |

Une troisième, **D13** (bug d'export depuis la Work Sheet), est traitée
en fin de document : elle reste bloquée, et on explique pourquoi.

---

## D5 — Le contenu du COA

### Un gabarit à nous, à côté du gabarit natif

`senaite.impress` découvre ses gabarits dans les répertoires de
ressources Plone de type `senaite.impress.reports`. L'add-on en déclare
un (`coa/configure.zcml`), et y dépose
`coa/templates/reports/COA-Trimeta.pt`.

Rien n'est modifié dans `senaite.impress`. `Default.pt` et
`MultiDefault.pt` restent disponibles, et restent le choix par défaut :
en cas de doute, le laboratoire peut toujours revenir au rapport natif
depuis le sélecteur **Gabarit** de l'écran de publication.

Le gabarit reprend la structure de `Default.pt` — mêmes sections
`render_controls` / `render_js` / `render_css` / `render_header` /
`render_info` / `render_alerts`, mêmes `render_results`,
`render_signatures`, `render_footer`. Le code-barres, les alertes, les
pièces jointes et les signatures se comportent donc exactement comme
avant. Seul le bloc central change.

> **Être découvrable ne suffit pas à être proposé.** La liste des
> gabarits *actifs* du sélecteur est un enregistrement du registre
> Plone, `senaite.impress.templates`, figé au moment où le profil
> `senaite.impress:default` a été appliqué la première fois. Constaté
> sur l'instance : le gabarit natif s'affichait, pas le nôtre.
> `setuphandlers.register_coa_template()` nous y ajoute, de façon
> idempotente, et `unregister_coa_template()` nous en retire à la
> désinstallation.

### Ce qui s'affiche

Le document liste en vert ce qui figurait déjà sur le COA, en noir ce
qui manquait. Le tableau ci-dessous reprend cette lecture.

| Ligne du document | Déjà présent | Source de la valeur |
|---|---|---|
| Sample reference (Sample ID) | oui | `model/getId` |
| **Report reference** | non | `model/AnalysisSheetNumber` — *voir ci-dessous* |
| Sample reception date | oui | `model.DateReceived` |
| **Start and End of Analyses** | non | `model.AnalysisStart` / `model.AnalysisEnd` |
| Date Validated | oui | `model.getDateVerified()` |
| **Validated by** | non | `model/FinalValidator/Fullname` |
| Date Published | oui | `view.timestamp` |
| Published by | oui | `reporter/fullname`, **sans le lien mailto** |
| **Sample weight** | non | `model/ReceptionWeight` |
| **SAMPLE INFORMATION** | non | tableau ajouté |
| — Reception temperature | | `model/ReceptionTemperature` |
| — Designation | | `model/Designation` |
| — Lot | | `model/ClientSampleID` (champ natif) |
| — Client | oui | `client/Name` |
| **ORGANOLEPTIC ANALYSIS** | non | tableau ajouté |
| — Texture / Color / Aroma | | `model/Texture`, `model/Color`, `model/Aroma` |

« Supprimer l'adresse mail » : la ligne *Published by* du gabarit natif
enveloppe le nom dans un lien `mailto:`. Ici, le nom seul.

Les champs `model/ReceptionWeight`, `model/Designation`,
`model/FinalValidator`… viennent du schemaextender de l'add-on.
SuperModel les expose par leur **nom de champ**, pas par un accesseur
`get*` — même mécanisme que `model/ClientSampleID`, déjà utilisé par le
gabarit natif.

### Le point à confirmer avec le laboratoire : « Report reference »

C'est la seule ligne du document dont la valeur ne se déduit pas.

La référence du rapport lui-même n'existe pas au moment où le gabarit
est rendu : `senaite.impress` produit le PDF **puis** crée l'`ARReport`
qui le portera. Impossible, donc, d'afficher un identifiant de rapport.

Le gabarit affiche à la place le **Numéro de fiche d'analyse**
(`AnalysisSheetNumber`), la référence que le laboratoire attribue
lui-même à l'analyse. C'est l'interprétation la plus plausible d'une
« référence de rapport » sur ce COA, mais **c'est une hypothèse**.

Trois réponses possibles, à trancher en regardant un COA papier
existant :

1. c'est bien le numéro de fiche d'analyse → rien à faire ;
2. c'est une autre référence déjà saisie quelque part → changer une
   ligne du gabarit ;
3. c'est un numéro propre au rapport, à générer → cela redevient du
   développement : un champ sur l'`ARReport` et un compteur.

---

## D10 — Le nom du fichier

### Le constat

Un COA téléchargé s'appelait `W-0031.pdf` : le **Sample ID**, fabriqué
par SENAITE. Le laboratoire travaille avec le **Code échantillon**,
qu'il saisit lui-même.

### Trois endroits, pas un

SENAITE fabrique ce nom à trois endroits distincts, tous à partir du
Sample ID :

| Ce que fait l'opérateur | Code amont |
|---|---|
| Télécharge un COA | `DownloadView.get_report_filename` |
| Envoie un COA par courriel | `EmailView.get_report_filename` |
| Télécharge une sélection (ZIP) | `WorkflowActionDownloadReportsAdapter.__call__` |

Les trois sont repris. N'en reprendre qu'un laisserait le laboratoire
recevoir tantôt `ECH-042.pdf`, tantôt `W-0031.pdf`, pour le même
rapport — pire que de ne rien changer.

### Une couche de navigateur, pas un monkey patch

`senaite.core` enregistre ces vues sur `layer="…IBikaLIMS"`. L'add-on
déclare une couche qui en dérive (`interfaces.ITrimetaLayer`), l'active
par `profiles/default/browserlayer.xml`, et réenregistre les mêmes vues
dessus. Le registre d'adaptateurs retient la plus spécifique.

Le code amont n'est pas touché, et **désinstaller l'add-on redonne
exactement le comportement natif**. Sur des documents qualité, pouvoir
revenir en arrière proprement compte autant que le changement lui-même.

`ITrimetaLayer` dérive aussi de `IBrowserRequest`. Ce n'est pas
décoratif : le téléchargement groupé n'est pas une `browser:page` mais
un **adaptateur nommé**, dont l'amont déclare la requête comme
`IBrowserRequest` — or `IBikaLIMS`, contrairement à
l'`IDefaultBrowserLayer` habituel de Plone, n'en dérive pas. Sans cet
héritage, notre surcharge l'emporterait quand même, mais pour une
raison fragile (l'ordre des interfaces *directement fournies* à la
requête). Avec, le choix découle de la hiérarchie et se vérifie à la
lecture.

### Pourquoi assainir la chaîne

Le Sample ID était fabriqué par SENAITE : toujours `W-0031`, jamais de
surprise. Le **Code échantillon est du texte libre**. Il part pourtant
dans un en-tête HTTP, dans un nom de fichier chez le destinataire, et
dans une entrée d'archive ZIP.

`coa/filename.sanitize()` traite, dans cet ordre :

| Cas | Traitement | Pourquoi |
|---|---|---|
| Accents | translittérés (`Récolte` → `Recolte`) | l'en-tête de senaite.core n'a pas de forme `filename*=` ; chaque navigateur rend l'UTF-8 à sa façon |
| Blancs, tabulations, sauts de ligne | deviennent `_` | un blanc tronquerait le nom au premier mot |
| Autres caractères de contrôle | supprimés | un `\r\n` ouvrirait une **injection d'en-tête HTTP** |
| `/ \ : * ? " < > \|` | deviennent `-` | créeraient un chemin, ou seraient refusés |
| Points et séparateurs en bordure | retirés | fichier caché sous Unix, nom refusé sous Windows |
| `CON`, `AUX`, `LPT1`… | suffixés `_` | noms de périphériques réservés sous Windows |
| Longueur | bornée à 120 | marge pour un suffixe et une arborescence profonde |
| Résultat vide | repli sur le Sample ID | un rapport doit **toujours** porter un nom exploitable |

L'ordre compte : tabulation, retour chariot et saut de ligne sont à la
fois des blancs **et** des caractères de contrôle. Les effacer
purement collerait deux mots ensemble (`Lot 1⇥Vert` → `Lot_1Vert`) ; on
les rend séparateurs d'abord.

En complément, l'en-tête `Content-Disposition` entoure désormais le nom
de **guillemets**, ce que l'amont ne faisait pas. `sanitize()` remplace
déjà les blancs ; les guillemets sont la seconde barrière, celle qui
tient même si `sanitize()` évolue.

### Trois défauts amont corrigés en passant

**L'objet persistant n'est plus modifié.** L'amont écrit
`pdf.filename = …` sur l'objet `Pdf` lu depuis la ZODB, pour le relire
juste après. Écrire dans un objet persistant pour s'en servir comme
variable locale salit la transaction sans aucun besoin.

**Les noms de l'archive sont rendus uniques.** Le Code échantillon
n'est soumis à **aucune contrainte d'unicité** dans SENAITE : deux
rapports d'une même sélection peuvent porter le même.
`zipfile.writestr()` accepterait les deux entrées sans broncher, et la
plupart des extracteurs n'en montreraient qu'une — un COA disparaîtrait
en silence. La deuxième devient `ECH-1-2.pdf`. La comparaison ignore la
casse : le destinataire peut extraire sur un système de fichiers qui ne
la distingue pas.

**Une sélection dont aucun PDF n'est lisible donne un message** au lieu
d'un `IndexError`.

### Vérification

1. Ouvrir un échantillon publié, onglet **Rapports d'analyse**, cliquer
   sur le PDF : le fichier enregistré doit porter le Code échantillon.
2. Sélectionner deux rapports, **Télécharger** : l'archive
   `COA-<horodatage>.zip` contient deux fichiers nommés par leur Code
   échantillon.
3. **Envoyer par courriel** : la pièce jointe porte le même nom.
4. Un échantillon sans Code échantillon — il en reste dans l'historique
   — doit redonner `W-00xx.pdf`, pas un fichier sans nom.

---

## D13 — Le bug d'export depuis la Work Sheet

Le document donne une URL et un titre, « Bug exportation données », sur
l'écran de saisie des résultats d'une Work Sheet :

    /senaite/worksheets/WS-005/manage_results?…&analyses_form_pagesize=9999999

**Aucun symptôme n'est décrit.** Ni ce qui était attendu, ni ce qui
s'est produit.

C'est la seule des quatorze demandes qui reste ouverte, et elle le
reste volontairement. Sans symptôme, corriger reviendrait à deviner :
on modifierait du code qui marche, sur un écran de saisie de résultats
— l'écran le plus sensible du LIMS — pour un défaut dont on ne sait
même pas s'il vient de SENAITE, du navigateur, ou d'une attente
différente.

Ce qu'il faut recueillir auprès de la personne qui l'a rencontré :

1. quel bouton exactement (« Export » du listing ? « Imprimer » ?) ;
2. quel format demandé (CSV, XLSX) ;
3. ce qui est sorti : fichier vide ? colonnes manquantes ? accents
   cassés ? seulement la première page ? rien du tout ?
4. combien d'analyses affichées — l'URL porte
   `pagesize=9999999`, ce qui est une piste : une page qui charge
   plusieurs milliers de lignes peut faire expirer la requête ;
5. le message d'erreur s'il y en a un, et ce que disent les logs
   (`make logs`) au même instant.

Avec ces cinq éléments, le défaut est reproductible, donc corrigeable.

---

## À déployer

Après un `git pull` sur le serveur :

```bash
cd 2.6.0
make sync            # droits d'abord, puis pull
make redeploy-addon
```

Puis jouer l'étape de mise à jour **1003 → 1004** :

    http://<hôte>:8080/senaite/portal_setup/manage_upgrades

Elle active la couche de navigateur. Sans elle, une instance déjà
installée garderait le nommage par Sample ID : `browserlayer.xml` n'est
lu qu'à l'installation du profil, jamais rejoué tout seul. L'étape est
instantanée — elle ne réindexe rien, contrairement aux étapes 1001 à
1003.

Enfin, sur l'écran de publication, choisir le gabarit
**`senaite.trimeta.samplefields:COA-Trimeta.pt`**. Le laboratoire peut
le définir comme gabarit par défaut dans *Configuration › Impress*.
