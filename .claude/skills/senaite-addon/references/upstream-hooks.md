# Points d'accroche amont (releves sur les sources 2.6.0)

Tout ce qui suit a ete lu sur les tags **`senaite.core v2.6.0`** et
**`senaite.impress 2.6.0`**, les versions reellement embarquees par
l'image `senaite/senaite:v2.6.0`.

> Ces signatures sont recopiees ici pour eviter d'avoir a refaire
> l'archeologie a chaque fois. **Elles valent pour 2.6.0 et pour elle
> seule.** Avant de s'y fier apres une montee de version, les
> reverifier : `make shell` puis lire le source dans
> `/home/senaite/senaitelims/eggs/`.

---

## Nommage des fichiers COA

Trois endroits distincts fabriquent le nom d'un PDF de rapport. Les
trois derivent du **Sample ID**, et les trois doivent etre repris pour
que le laboratoire voie partout le **Code echantillon**.

### 1. Telechargement unitaire

`bika/lims/browser/publish/downloadview.py`

```python
class DownloadView(BrowserView):
    def __call__(self):
        filename = self.get_report_filename(self.context)
        pdf = self.context.getPdf()
        self.download(pdf.data, filename)

    def get_report_filename(self, report):
        sample = report.getAnalysisRequest()
        return "{}.pdf".format(api.get_id(sample))
```

Enregistrement (`browser/publish/configure.zcml`) :

```xml
<browser:page for="*" name="download_pdf"
    class=".downloadview.DownloadView"
    permission="senaite.core.permissions.ManageAnalysisRequests"
    layer="bika.lims.interfaces.IBikaLIMS" />
```

Lien construit par `reports_listing.py` :
`"{}/download_pdf".format(obj.absolute_url())`.

### 2. Pieces jointes d'un envoi par courriel

`bika/lims/browser/publish/emailview.py`

```python
    def get_report_filename(self, report):
        sample = report.getAnalysisRequest()
        return "{}.pdf".format(api.get_id(sample))
```

Consomme par la propriete `email_attachments`. Enregistre en
`browser:page name="email"` pour `IClient` **et** pour
`IAnalysisRequest`, toujours sur `layer="bika.lims.interfaces.IBikaLIMS"`.

### 3. Telechargement groupe (archive ZIP)

`bika/lims/browser/workflow/client.py`

```python
class WorkflowActionDownloadReportsAdapter(RequestContextAware):
    def __call__(self, action, uids):
        reports = map(api.get_object_by_uid, uids)
        pdfs = []
        for report in reports:
            sample = report.getAnalysisRequest()
            sample_id = api.get_id(sample)
            pdf = self.get_pdf(report)
            if pdf is None:
                self.add_status_message(...)
                continue
            pdf.filename = "{}.pdf".format(sample_id)
            pdfs.append(pdf)

        if len(pdfs) == 1:
            return self.download(pdfs[0].data, pdfs[0].filename, ...)

        with self.create_archive(pdfs) as archive:
            timestamp = DateTime().strftime("%Y%m%d_%H%M%S")
            archive_name = "Reports-{}.zip".format(timestamp)
            ...
```

Ce n'est **pas** une `browser:page` mais un adaptateur nomme :

```xml
<adapter name="workflow_action_download_reports"
    for="bika.lims.interfaces.IClient
         zope.publisher.interfaces.browser.IBrowserRequest"
    factory=".client.WorkflowActionDownloadReportsAdapter"
    provides="bika.lims.interfaces.IWorkflowActionAdapter"
    permission="zope.Public" />
```

(idem pour `IAnalysisRequest`.) Pour le surcharger, reenregistrer le
meme `name` avec **notre couche** a la place de `IBrowserRequest` :
elle en derive, donc elle est plus specifique et gagne.

Deux fragilites de l'implementation amont, corrigees cote add-on :

- `pdf.filename = ...` **mute l'objet `Pdf` persistant** lu depuis la
  ZODB ;
- `zipfile.writestr()` accepte deux entrees de meme nom sans broncher.
  Le Code echantillon etant du texte libre, deux rapports peuvent
  parfaitement porter le meme : l'archive contiendrait alors deux
  entrees homonymes, et la plupart des extracteurs n'en montrent
  qu'une.

---

## Stockage des rapports (senaite.impress 2.6.0)

`senaite/impress/storage.py`

```python
class PdfReportStorageAdapter(object):
    implements(IPdfReportStorage)

    def store(self, pdf, html, uids, metadata=None):
        objs = map(api.get_object_by_uid, uids)
        if not self.store_multireports_individually():
            objs = [self.get_primary_report(objs)]
        reports = []
        for obj in objs:
            reports.append(self.create_report(obj, pdf, html, uids, metadata))
        return reports

    @synchronized(max_connections=1)
    def create_report(self, parent, pdf, html, uids, metadata):
        ...
        report = api.create(
            parent, "ARReport",
            AnalysisRequest=api.get_uid(parent),
            Pdf=pdf, Html=html,
            ContainedAnalysisRequests=uids, Metadata=metadata)
        transaction.commit()
        return report
```

**C'est l'explication du symptome « 5 fichiers, meme contenu »**
(demande D11 du cahier des charges) : le **meme** `pdf` est passe a
chaque `create_report()`. Quand le gabarit choisi est un `Multi…`, ce
PDF unique contient les cinq echantillons ; on obtient donc cinq
rapports aux noms differents et au contenu identique. Ce n'est pas un
defaut, c'est le gabarit. Voir `docs/lot1-parametrage.md`.

Le type cree est **`ARReport`** en 2.6.0. La branche `2.x` amont l'a
depuis renomme `ResultsReport`, avec des champs en minuscules
(`sample`, `pdf`, `contained_samples`) : ne pas se fier au code de
`master` / `2.x` sur GitHub.

---

## Decouverte des gabarits de rapport

`senaite.impress.template.TemplateFinder` balaie les repertoires de
ressources Plone de type `senaite.impress.reports` :

```xml
<plone:static
    directory="templates/reports"
    type="senaite.impress.reports"
    name="senaite.trimeta.samplefields" />
```

Le gabarit s'appelle alors
`senaite.trimeta.samplefields:COA-Trimeta.pt`.

**Etre decouvrable ne suffit pas a etre propose.** La liste des
gabarits *actifs* du selecteur de publication est un enregistrement du
registre Plone, `senaite.impress.templates`, fige au moment ou le profil
`senaite.impress:default` a ete applique. Il faut s'y ajouter
explicitement — voir `setuphandlers.register_coa_template()`.

Un gabarit dont le nom **commence ou finit par `Multi`** recoit la
totalite des echantillons selectionnes : c'est ainsi que
`senaite.impress` distingue un rapport groupe d'un rapport unitaire.

---

## Schema ARReport (senaite.core v2.6.0)

`bika/lims/content/arreport.py` — champs utiles :

| Champ | Type | Contenu |
|---|---|---|
| `AnalysisRequest` | `UIDReferenceField` | echantillon principal |
| `ContainedAnalysisRequests` | `UIDReferenceField` multivalue | tous les echantillons du PDF |
| `Pdf` | `BlobField` | le PDF |
| `Html` | `TextField` | le HTML source |
| `Metadata` | `RecordField` | `paperformat`, `timestamp`, `orientation`, `template`, `contained_requests` |
| `SendLog` | `RecordsField` | historique des envois |

Accesseurs : `getAnalysisRequest()`, `getPdf()`, `getMetadata()`.
`getPdf()` peut lever `POSKeyError` si le blob a disparu — l'amont
l'attrape, nous aussi.

---

## Catalogues

| Catalogue | Constante | Usage ici |
|---|---|---|
| `senaite_catalog_sample` | `senaite.core.catalog.SAMPLE_CATALOG` | echantillons, tableau de bord |
| `senaite_catalog_analysis` | `ANALYSIS_CATALOG` | resultats (`getRequestID`, `getKeyword`, `getResult`, `getResultCaptureDate`) |
| `senaite_catalog_contact` | `CONTACT_CATALOG` | `ReferenceWidget` vers les `LabContact` |

API de manipulation : `senaite.core.api.catalog` —
`get_catalog`, `get_indexes`, `get_columns`, `add_index`, `add_column`,
`del_index`, `del_column`.
