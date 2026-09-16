# Lot 4 — COA : contenu et nom du fichier

Deux demandes du document *AMÉLIORATIONS SENAITE LIMS* :

> Ce qui devrait s'afficher sur le COA pour les caractéristiques des
> échantillons […] Supprimer l'adresse mail.

> Le nom du COA devrait être le « Code échantillon / Sample code » au
> lieu de « Sample ID ».

Rien n'est modifié dans `senaite.impress` ni dans `senaite.core` : tout
vit dans le sous-paquet `coa/` de l'add-on.

---

## Le gabarit `COA-Trimeta.pt`

### Comment SENAITE le trouve

`senaite.impress` ne liste pas ses gabarits en dur. Il parcourt les
répertoires de ressources Plone du type `senaite.impress.reports`
(`senaite.impress.template.TemplateFinder`). `coa/configure.zcml` en
déclare un de plus :

```xml
<plone:static
    directory="templates/reports"
    type="senaite.impress.reports"
    name="senaite.trimeta.samplefields" />
```

Le gabarit apparaît alors sous le nom
`senaite.trimeta.samplefields:COA-Trimeta.pt`.

### Découvert n'est pas proposé

Le sélecteur de l'écran de publication ne montre pas tous les gabarits
découverts. Il montre la liste enregistrée dans le registre Plone
`senaite.impress.templates`, **figée** au moment où `senaite.impress` a
été installé sur le site. Un gabarit ajouté après n'y entre pas tout
seul : constaté sur l'instance de démonstration, où il apparaissait dans
*Configuration › Impress* mais pas dans le sélecteur.

`setuphandlers.register_coa_template()` l'y ajoute, sans retirer les
gabarits déjà choisis. Il est appelé par `post_install` (installation
neuve) et par l'étape de mise à jour 1003 → 1004 (site existant).

### Ce qu'il affiche

Structure reprise de `senaite.impress:Default.pt` : en-tête, bloc
client/laboratoire, alertes, résultats, signatures et pied de page sont
rendus par les méthodes natives (`view.render_*`). Seul le tableau
*Summary* est réécrit, suivi de deux tableaux ajoutés.

| Ligne du COA | Source |
|---|---|
| Sample ID | `model/getId` (natif) |
| Sample Type, Specification | natifs |
| Date Received | `model.DateReceived` (natif) |
| Beginning / End of analysis | `AnalysisStart`, `AnalysisEnd` (add-on) |
| Date Validated | `model.getDateVerified()` (natif) |
| Validated by | `FinalValidator` → nom du contact labo (add-on) |
| Date Published, Published by | natifs, **sans le lien mailto** |
| Sample weight | `ReceptionWeight` (add-on) |
| *Sample information* : Reception temperature, Designation | add-on |
| *Sample information* : Lot, Client | `ClientSampleID`, `Client` (natifs) |
| *Organoleptic analysis* : Texture, Color, Aroma | add-on |

Les champs sont lus par leur **nom de champ** (`model/ReceptionWeight`),
pas par l'accesseur `get…` : c'est ce que `SuperModel` expose, et il
résout lui-même un champ référence en objet (`model/FinalValidator/Fullname`).

---

## Le nom du PDF

### Les trois endroits

`senaite.core` construit `<ID échantillon>.pdf` à trois endroits, tous
côté serveur. L'écran de publication n'en fixe aucun : *Save* enregistre
le rapport, qui est ensuite téléchargé depuis la liste des rapports.

| Où | Vue ou adaptateur de senaite.core | Remplacé par |
|---|---|---|
| Liste des rapports › clic sur un PDF | `download_pdf` | `TrimetaDownloadView` |
| Envoi des résultats par e-mail | `email` | `TrimetaEmailView` |
| Liste des rapports › action *Download* groupée | `workflow_action_download_reports` | `TrimetaDownloadReportsAdapter` |

Les trois appellent `coa/filename.get_report_filename()`.

### La couche navigateur

Pour remplacer une vue sans conflit ZCML, l'add-on déclare sa propre
couche, `interfaces.ISenaiteTrimetaLayer`, qui étend `IBikaLIMS`. Une vue
du même nom enregistrée pour cette couche est plus spécifique, elle
gagne. La couche est posée par `profiles/default/browserlayer.xml` : tant
que ce fichier n'est pas importé (étape 1004 non jouée), ce sont les vues
de `senaite.core` qui répondent.

### La règle de nommage

`build_coa_filename(code, id)` :

1. le Code échantillon, débarrassé de tout caractère hors
   `A-Z a-z 0-9 . _ -` ;
2. l'ID SENAITE si le code est vide ou n'est fait que de caractères
   retirés.

Le nettoyage n'est pas cosmétique. Le nom finit **non quoté** dans
l'en-tête `Content-Disposition` et comme nom d'entrée dans le zip : un
espace, un `;`, un `/` ou un retour à la ligne saisi dans le code
casserait le téléchargement, ou permettrait d'injecter un en-tête. Couvert
par `tests/test_coa.py`.

### Plusieurs rapports d'un même échantillon

Un échantillon republié porte plusieurs rapports, donc plusieurs PDF au
même nom. Dans le zip de l'action groupée, ils s'écraseraient à
l'extraction (défaut déjà présent dans `senaite.core` avec l'ID).
`unique_filename()` numérote les suivants : `ECH-001.pdf`,
`ECH-001-2.pdf`, `ECH-001-3.pdf`.

### Vérifié

Par de vraies requêtes sur l'instance de démonstration, pour VAN-0005
(Code échantillon `ECH-DEMO-001`, trois rapports) :

| Point | Résultat |
|---|---|
| `download_pdf` | `inline; filename=ECH-DEMO-001.pdf` |
| Écran d'envoi par e-mail | pièce jointe `ECH-DEMO-001.pdf` |
| Action groupée, un rapport | `attachment; filename=ECH-DEMO-001.pdf` |
| Action groupée, trois rapports | zip contenant `ECH-DEMO-001.pdf`, `-2`, `-3` |

---

## Trois erreurs commises, et ce qu'elles ont appris

**1. Une permission ZCML doit être déclarée avant d'être utilisée.**
Les vues de `download_pdf` et `email` exigent
`senaite.core.permissions.ManageAnalysisRequests`. L'add-on étant chargé
avant `senaite.core`, Zope ne la connaissait pas encore : `ComponentLookupError`
au démarrage, et le conteneur a redémarré en boucle. D'où
`<include package="senaite.core.permissions" />` en tête de
`coa/configure.zcml`, comme `senaite.impress` le fait pour les siennes.

**2. Pas de `--` dans un commentaire XML.** Un tiret double dans un
commentaire de `configure.zcml` ou du gabarit rend le fichier invalide,
et Zope refuse de démarrer.

**3. `setup_catalogs()` passait des colonnes comme index.** Le profil
n'avait jamais été réellement installé : la première installation a
échoué sur `KeyError: 'getAnalysisEnd'`, un nom de colonne de
métadonnées transmis à `catalog_object(idxs=…)`, qui n'accepte que des
index. Corrigé : seuls les vrais index sont transmis, `update_metadata=True`
rafraîchit les colonnes de toute façon.

---

## À déployer

Après un `git pull` sur le serveur :

```bash
cd 2.6.0
make redeploy-addon
```

Puis jouer l'étape **1003 → 1004** (et les précédentes si elles ne
l'ont pas été) :

    http://<hôte>:8080/senaite/portal_setup/manage_upgrades

L'étape 1004 fait aussi de `COA-Trimeta.pt` le gabarit présélectionné,
sauf si le laboratoire en avait déjà choisi un autre que
`MultiDefault.pt`. Ce gabarit d'usine était la cause de la demande D11
(voir `lot1-parametrage.md`). Réglage modifiable dans
*Configuration › Impress › Default Template*.

## Langue du COA

Le COA est **en français**, sur demande du laboratoire (16/09/2026). Il
avait d'abord été laissé en anglais, les libellés du cahier des charges
étant énumérés en anglais (« Sample reference », « Report reference »,
« ORGANOLEPTIC ANALYSIS »…).

Deux catalogues sont en jeu, car le PDF mêle deux origines :

- `senaite.trimeta.coa.po` : les libellés de notre gabarit (Synthèse,
  Référence du rapport, Informations sur l'échantillon, Analyse
  organoleptique…) ;
- `senaite.impress.po` : les parties rendues par SENAITE (titre du
  rapport, tableau des résultats, responsables, mentions légales, pied
  de page, pagination).

Les libellés restent écrits en anglais **dans le gabarit** : ce sont les
identifiants de traduction. Pour repasser le COA en anglais, il suffirait
de retirer `senaite.trimeta.coa.po`.

Attention aux libellés à variable (`Results for ${id}`, la phrase de
reproduction avec le nom du laboratoire) : la variable doit être
conservée telle quelle dans la traduction. Un test le vérifie.

## Logo du laboratoire sur le COA

Le PDF portait le logo **SENAITE**, en haut à droite de la première
page. senaite.impress l'écrit en dur dans son en-tête
(`analysisrequest/templates/header.pt`, image `senaite.svg`) : aucun
réglage ne permet de le remplacer, et la fiche Laboratoire n'a de champ
logo que pour l'accréditation.

**L'en-tête est remplacé pour tous les gabarits**, pas seulement pour le
COA Trimeta : sinon, un utilisateur qui choisit un gabarit SENAITE dans
l'écran de publication retrouverait le logo SENAITE dans le PDF.

senaite.impress prévoit ce cas. Avant de produire un rapport, il cherche
une vue qui adapte aussi le contexte, et ne prend la sienne qu'à défaut —
son code dit que c'est là pour permettre à un add-on de la redéfinir.
L'add-on enregistre donc ses propres vues de rapport
(`coa/reportview.py`), qui ne changent qu'une chose : l'en-tête
(`coa/templates/header.pt`), copie de celui de SENAITE avec la même
structure et les mêmes classes, où seule l'image change. La feuille de
style du rapport s'applique sans modification, et le gabarit COA reprend
l'appel standard, sans duplication.

Le logo est livré avec l'add-on
(`browser/resources/logo-trimeta-agrofood.png`, source
`https://trimetagroup.com/wp-content/uploads/2024/08/taf-logo1.png`).

- **Servi par l'application**, pas par le site du groupe : produire un
  PDF ne dépend d'aucun accès Internet.
- **Hauteur 45 px** au lieu des 30 px de la feuille de style, prévus pour
  le logotype allongé de SENAITE : ce logo-ci est presque carré.
- Ne pas confondre avec le logo de la **barre d'outils**, qui est la
  version blanche du logo du groupe (voir
  [parametres-par-defaut.md](parametres-par-defaut.md)).

## Mise en page : plus de page blanche

Le COA sortait sur **3 pages**, la première presque vide et la dernière
ne portant que les mentions légales.

**La cause.** La feuille de style des rapports pose
`div.row { page-break-inside: avoid }` : chaque section est insécable.
Nos tableaux sont longs ; une section qui ne tenait pas dans la place
restante basculait entière à la page suivante.

**Ce qui a été fait.**

- Le Summary, les informations d'échantillon et l'analyse organoleptique
  sont **trois sections distinctes**, au lieu d'un bloc unique.
- Le gabarit COA pose, après la feuille de style et plus spécifiquement
  qu'elle, une règle qui **autorise la coupure** de ses sections, y
  compris celles de senaite.impress (résultats, responsables, mentions
  légales). Seul le COA est concerné : les autres gabarits gardent le
  comportement d'origine.
- Deux garde-fous conservés : une ligne de tableau n'est jamais coupée en
  deux, et un titre ne reste jamais seul en bas de page.

**Résultat** (vérifié sur trois rapports republiés) : 2 pages au lieu de
3, première page remplie, les tableaux se poursuivant d'une page à
l'autre. Un blanc peut subsister en bas d'une page lorsqu'un titre de
section ne tiendrait pas avec au moins une ligne : c'est voulu.

## Export de la liste des rapports d'analyses

### Le constat

Le bouton **Exportation** produisait un fichier inexploitable :

- première colonne remplie de balises HTML
  (`<a href=\"analysisreport_info?...\">`) ;
- colonnes **Échantillon primaire** et **Télécharger le PDF** vides.

### La cause

L'export de `senaite.app.listing` se fait dans le navigateur. Il ne
retient que les colonnes **affichées**, et lit la **valeur** de chaque
cellule, jamais la version HTML (`replace`) utilisée à l'écran.

- La colonne *Info* a pour valeur le HTML de l'icône : il partait tel
  quel dans le fichier.
- senaite.core ne renseigne, pour l'échantillon primaire et le lien PDF,
  que la version HTML : l'export ne trouvait donc rien.

### Ce qui a été fait

- *Info* est **masquée par défaut** : elle sort du fichier et reste
  activable dans le menu des colonnes (« ··· »). Il n'existe pas
  d'indicateur « ne pas exporter » par colonne.
- **Échantillon primaire** exporte l'identifiant de l'échantillon,
  **Télécharger le PDF** l'adresse de téléchargement. Un rapport sans
  fichier laisse la cellule vide : aucune adresse n'est inventée.
- L'affichage ne change pas : à l'écran, `replace` reste prioritaire.

### Vérification (16/09/2026)

Fichier réellement téléchargé depuis le navigateur : 10 colonnes, aucune
balise HTML, aucune colonne *Info*. *Échantillon primaire* donne
`VAN-0005`, *Télécharger le PDF* l'adresse du fichier. Seule *Envoyé à*
reste vide, faute d'envoi par courriel sur ces rapports.

---

## Reste à trancher

1. **« Supprimer l'adresse mail »** a été compris comme le lien mailto
   de *Published by*. L'e-mail du contact client, dans le bloc d'en-tête
   natif, est toujours affiché : à confirmer avec le laboratoire.
2. **« Report reference »** — *tranché à partir du document*. Le même
   cahier des charges demande que le COA porte le nom du **Code
   échantillon** (nom du PDF) : c'est la référence sous laquelle le
   rapport circule. Le COA l'affiche donc sous « Référence du rapport »,
   avec repli sur le Numéro de fiche d'analyse si le code manque.
   L'identifiant de l'objet rapport de SENAITE ne peut pas servir : il
   n'existe pas encore quand le PDF est produit. À valider à la première
   relecture d'un COA par le laboratoire.
