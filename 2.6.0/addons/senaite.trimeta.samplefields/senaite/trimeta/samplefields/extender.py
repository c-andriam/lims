# -*- coding: utf-8 -*-
"""
Extension de schema pour le type Sample (AnalysisRequest) de SENAITE.

Ajoute les 15 champs de la section RECEPTION demandes par Trimeta Group.
Utilise archetypes.schemaextender, la methode standard pour etendre un
schema Archetypes sans toucher au code core de SENAITE.

Designation, Sample Condition, Packaging Condition et Origin sont des
champs texte libre avec autocompletion dynamique et partagee (voir
suggestions.py + browser/suggestions_api.py +
resources/reception_separator.js), plutot que des listes deroulantes
fixes.

Reception Temperature et Item Code (ex-Sample Reference) restent des
listes deroulantes strictes. Received By est une reference dynamique
vers les LabContacts existants.
"""

from AccessControl import ClassSecurityInfo
from Products.Archetypes.public import (
    StringField,
    FixedPointField,
    SelectionWidget,
    StringWidget,
    DecimalWidget,
)
from archetypes.schemaextender.field import ExtensionField
from archetypes.schemaextender.interfaces import IOrderableSchemaExtender
from zope.component import adapts
from zope.interface import implementer
from zope.i18nmessageid import MessageFactory

from bika.lims.interfaces import IAnalysisRequest
from bika.lims.browser.fields import UIDReferenceField
from bika.lims.browser.widgets import DateTimeWidget
from senaite.core.browser.fields.datetime import DateTimeField
from senaite.core.browser.widgets.referencewidget import ReferenceWidget
from senaite.core.catalog import CONTACT_CATALOG

from senaite.trimeta.samplefields import vocabularies as vocab
from senaite.trimeta.samplefields import PRODUCT_NAME

_ = MessageFactory("senaite.trimeta.samplefields")

# Visibilite explicite requise pour que nos champs apparaissent dans la
# grille "Request new analyses" (mode 'add'). Sans cela, les widgets AT
# standards retombent sur 'invisible' par defaut pour ce mode precis,
# meme si le champ est bien present dans le schema etendu.
ADD_VISIBLE = {
    "edit": "visible",
    "view": "visible",
    "add": "edit",
}


# --- Champs custom (ExtensionField = version "extensible" des champs AT) ---

class ExtStringField(ExtensionField, StringField):
    """Champ texte extensible."""
    security = ClassSecurityInfo()


class ExtFixedPointField(ExtensionField, FixedPointField):
    """Champ numerique (poids, quantite) extensible."""
    security = ClassSecurityInfo()


class ExtUIDReferenceField(ExtensionField, UIDReferenceField):
    """Champ de reference moderne (UID, rendu AJAX) extensible.

    C'est le meme mecanisme que celui utilise nativement par SENAITE
    pour Client/Contact (bika.lims.browser.fields.UIDReferenceField +
    senaite.core.browser.widgets.referencewidget.ReferenceWidget),
    contrairement a l'ancien Products.Archetypes.public.ReferenceField
    qui provoque une erreur de rendu (NameError: same_type) avec le
    moteur de template Chameleon utilise par ar_add2.pt.
    """
    security = ClassSecurityInfo()


class ExtDateTimeField(ExtensionField, DateTimeField):
    """Champ date/heure extensible, meme mecanisme que DateSampled."""
    security = ClassSecurityInfo()


@implementer(IOrderableSchemaExtender)
class ReceptionFieldsExtender(object):
    """Ajoute les champs de la section RECEPTION au Sample."""

    adapts(IAnalysisRequest)

    fields = [
        # 1. Sample Code
        ExtStringField(
            "SampleCode",
            required=True,
            searchable=True,
            schemata="Reception",
            widget=StringWidget(
                visible=ADD_VISIBLE,
                label=_(u"Sample Code"),
                description=_(u"Unique internal code assigned to the sample."),
            ),
        ),

        # 2. Code article (remplace l'ancien "Sample Reference", juge
        # redondant avec un autre champ)
        ExtStringField(
            "CodeArticle",
            required=True,
            vocabulary=vocab.as_displaylist(vocab.CODE_ARTICLE_VOCAB),
            schemata="Reception",
            widget=SelectionWidget(
                visible=ADD_VISIBLE,
                format="select",
                label=_(u"Item Code"),
            ),
        ),

        # 3. Designation - texte libre avec autocompletion dynamique
        ExtStringField(
            "Designation",
            required=True,
            schemata="Reception",
            widget=StringWidget(
                visible=ADD_VISIBLE,
                label=_(u"Designation"),
            ),
        ),

        # 4. Reception Weight
        ExtFixedPointField(
            "ReceptionWeight",
            required=True,
            precision=3,
            schemata="Reception",
            widget=DecimalWidget(
                visible=ADD_VISIBLE,
                label=_(u"Reception Weight (g)"),
            ),
        ),

        # 5. Quantity Received
        ExtFixedPointField(
            "QuantityReceived",
            required=True,
            precision=2,
            schemata="Reception",
            widget=DecimalWidget(
                visible=ADD_VISIBLE,
                label=_(u"Quantity Received"),
            ),
        ),

        # 6. Quantity Under Analysis
        ExtFixedPointField(
            "QuantityUnderAnalysis",
            required=True,
            precision=2,
            schemata="Reception",
            widget=DecimalWidget(
                visible=ADD_VISIBLE,
                label=_(u"Quantity Under Analysis (g)"),
            ),
        ),

        # 7. Technical Sample Weight
        ExtFixedPointField(
            "TechSampleWeight",
            required=True,
            precision=3,
            schemata="Reception",
            widget=DecimalWidget(
                visible=ADD_VISIBLE,
                label=_(u"Technical Sample Weight (g)"),
            ),
        ),

        # 8. Reception Temperature - liste deroulante stricte 15-31 degC
        ExtStringField(
            "ReceptionTemperature",
            required=True,
            vocabulary=vocab.as_displaylist(vocab.TEMPERATURE_VOCAB),
            schemata="Reception",
            widget=SelectionWidget(
                visible=ADD_VISIBLE,
                format="select",
                label=_(u"Reception Temperature (deg C)"),
                description=_(u"Must be between 15 and 31 deg C."),
            ),
        ),

        # 9. Sample Condition - texte libre avec autocompletion dynamique
        ExtStringField(
            "SampleCondition",
            required=True,
            schemata="Reception",
            widget=StringWidget(
                visible=ADD_VISIBLE,
                label=_(u"Sample Condition"),
            ),
        ),

        # 10. Packaging Condition - texte libre avec autocompletion dynamique
        ExtStringField(
            "PackagingCondition",
            required=True,
            schemata="Reception",
            widget=StringWidget(
                visible=ADD_VISIBLE,
                label=_(u"Packaging Condition"),
            ),
        ),

        # 11. Origin - texte libre avec autocompletion dynamique
        ExtStringField(
            "Origin",
            required=True,
            schemata="Reception",
            widget=StringWidget(
                visible=ADD_VISIBLE,
                label=_(u"Origin"),
            ),
        ),

        # 12. Supplier / Customer Details
        ExtStringField(
            "SupplierCustomerDetail",
            required=True,
            searchable=True,
            schemata="Reception",
            widget=StringWidget(
                visible=ADD_VISIBLE,
                label=_(u"Supplier / Customer Details"),
            ),
        ),

        # 13. Received By - reference dynamique vers les LabContacts
        # existants (menu de recherche, comme Client/Contact). Utilise
        # le meme mecanisme moderne (UIDReferenceField) que ces
        # champs natifs, compatible avec le rendu Chameleon de
        # ar_add2.pt.
        ExtUIDReferenceField(
            "Receptionist",
            required=True,
            schemata="Reception",
            allowed_types=("LabContact",),
            mode="rw",
            widget=ReferenceWidget(
                visible=ADD_VISIBLE,
                label=_(u"Received By"),
                description=_(u"Select the lab contact who received "
                               u"the sample."),
                render_own_label=True,
                ui_item="Title",
                catalog=CONTACT_CATALOG,
                query={
                    "portal_type": "LabContact",
                    "is_active": True,
                    "sort_on": "sortable_title",
                    "sort_order": "ascending",
                },
                columns=[
                    {"name": "Title", "label": _(u"Name")},
                ],
            ),
        ),

        # 14. Contract
        ExtStringField(
            "Contract",
            required=True,
            searchable=True,
            schemata="Reception",
            widget=StringWidget(
                visible=ADD_VISIBLE,
                label=_(u"Contract"),
            ),
        ),

        # 15. Lab Entry Voucher
        ExtStringField(
            "EntryVoucher",
            required=True,
            searchable=True,
            schemata="Reception",
            widget=StringWidget(
                visible=ADD_VISIBLE,
                label=_(u"Lab Entry Voucher"),
            ),
        ),

        # =====================================================
        # SECTION ANALYSE
        # =====================================================

        # A1. Analysis Sheet Number
        ExtStringField(
            "AnalysisSheetNumber",
            required=True,
            searchable=True,
            schemata="Analyse",
            widget=StringWidget(
                visible=ADD_VISIBLE,
                label=_(u"Analysis Sheet Number"),
            ),
        ),

        # A2. Beginning of analysis
        ExtDateTimeField(
            "AnalysisStart",
            required=False,
            mode="rw",
            schemata="Analyse",
            widget=DateTimeWidget(
                label=_(u"Beginning of Analysis"),
                show_time=True,
                visible=ADD_VISIBLE,
                render_own_label=True,
            ),
        ),

        # A3. End of analysis
        ExtDateTimeField(
            "AnalysisEnd",
            required=False,
            mode="rw",
            schemata="Analyse",
            widget=DateTimeWidget(
                label=_(u"End of Analysis"),
                show_time=True,
                visible=ADD_VISIBLE,
                render_own_label=True,
            ),
        ),

        # A4. Analysis Preparer (plusieurs possibles)
        ExtUIDReferenceField(
            "AnalysisPreparer",
            required=False,
            schemata="Analyse",
            allowed_types=("LabContact",),
            multiValued=True,
            mode="rw",
            widget=ReferenceWidget(
                visible=ADD_VISIBLE,
                label=_(u"Analysis Preparer"),
                description=_(u"One or more people who prepared "
                               u"this analysis."),
                render_own_label=True,
                ui_item="Title",
                catalog=CONTACT_CATALOG,
                query={
                    "portal_type": "LabContact",
                    "is_active": True,
                    "sort_on": "sortable_title",
                    "sort_order": "ascending",
                },
                columns=[
                    {"name": "Title", "label": _(u"Name")},
                ],
            ),
        ),

        # A5. Pod length
        ExtFixedPointField(
            "PodLength",
            required=False,
            precision=2,
            schemata="Analyse",
            widget=DecimalWidget(
                visible=ADD_VISIBLE,
                label=_(u"Pod Length (cm)"),
            ),
        ),

        # A6. Aroma development (texte libre simple, pas de suggestion)
        ExtStringField(
            "AromaDevelopment",
            required=False,
            schemata="Analyse",
            widget=StringWidget(
                visible=ADD_VISIBLE,
                label=_(u"Aroma Development"),
            ),
        ),

        # A7. Aroma - texte libre avec autocompletion dynamique
        ExtStringField(
            "Aroma",
            required=False,
            schemata="Analyse",
            widget=StringWidget(
                visible=ADD_VISIBLE,
                label=_(u"Aroma"),
            ),
        ),

        # A8. Color - texte libre avec autocompletion dynamique
        ExtStringField(
            "Color",
            required=False,
            schemata="Analyse",
            widget=StringWidget(
                visible=ADD_VISIBLE,
                label=_(u"Color"),
            ),
        ),

        # A9. Texture - texte libre avec autocompletion dynamique
        ExtStringField(
            "Texture",
            required=False,
            schemata="Analyse",
            widget=StringWidget(
                visible=ADD_VISIBLE,
                label=_(u"Texture"),
            ),
        ),
    ]

    def __init__(self, context):
        self.context = context

    def getFields(self):
        return self.fields

    def getOrder(self, schematas):
        """Regroupe correctement les champs par onglet (Reception,
        Analyse), selon la schemata reellement definie sur chacun."""
        reception_fields = [
            f.getName() for f in self.fields
            if f.schemata == "Reception"
        ]
        analyse_fields = [
            f.getName() for f in self.fields
            if f.schemata == "Analyse"
        ]
        schematas["Reception"] = reception_fields
        schematas["Analyse"] = analyse_fields
        return schematas
