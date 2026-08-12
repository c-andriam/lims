# -*- coding: utf-8 -*-
"""
Extension de schema pour le type Sample (AnalysisRequest) de SENAITE.

Ajoute les 15 champs de la section RECEPTION demandes par Trimeta Group.
Utilise archetypes.schemaextender, la methode standard pour etendre un
schema Archetypes sans toucher au code core de SENAITE.
"""

from AccessControl import ClassSecurityInfo
from Products.Archetypes.public import (
    StringField,
    FixedPointField,
    SelectionWidget,
    StringWidget,
    DecimalWidget,
)

# Visibilite explicite requise pour que nos champs apparaissent dans la
# grille "Request new analyses" (mode 'add'). Sans cela, les widgets AT
# standards retombent sur 'invisible' par defaut pour ce mode precis,
# meme si le champ est bien present dans le schema etendu.
ADD_VISIBLE = {
    "edit": "visible",
    "view": "visible",
    "add": "edit",
}
from archetypes.schemaextender.field import ExtensionField
from archetypes.schemaextender.interfaces import IOrderableSchemaExtender
from zope.component import adapts
from zope.interface import implementer

from bika.lims.interfaces import IAnalysisRequest
from zope.i18nmessageid import MessageFactory

_ = MessageFactory("senaite.trimeta.samplefields")

from senaite.trimeta.samplefields import vocabularies as vocab
from senaite.trimeta.samplefields import PRODUCT_NAME


# --- Champs custom (ExtensionField = version "extensible" des champs AT) ---

class ExtStringField(ExtensionField, StringField):
    """Champ texte extensible."""
    security = ClassSecurityInfo()


class ExtFixedPointField(ExtensionField, FixedPointField):
    """Champ numerique (poids, quantite, temperature) extensible."""
    security = ClassSecurityInfo()


@implementer(IOrderableSchemaExtender)
class ReceptionFieldsExtender(object):
    """Ajoute les champs de la section RECEPTION au Sample."""

    adapts(IAnalysisRequest)

    # ---------------------------------------------------------------
    # 1. Code echantillon
    fields = [
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

        # 2. Reference de l'echantillon
        ExtStringField(
            "SampleReference",
            required=True,
            searchable=True,
            schemata="Reception",
            widget=StringWidget(
                visible=ADD_VISIBLE,
                label=_(u"Sample Reference"),
            ),
        ),

        # 3. Designation (liste deroulante)
        ExtStringField(
            "Designation",
            required=True,
            vocabulary=vocab.as_displaylist(vocab.DESIGNATION_VOCAB),
            schemata="Reception",
            widget=SelectionWidget(
                visible=ADD_VISIBLE,
                label=_(u"Designation"),
                format="select",
            ),
        ),

        # 4. Poids a la reception
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

        # 5. Quantite recue
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

        # 6. Quantite mise sous analyse (grs)
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

        # 7. Poids de l'echantillon-tech
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

        # 8. Temperature a la reception
        ExtFixedPointField(
            "ReceptionTemperature",
            required=True,
            precision=1,
            schemata="Reception",
            widget=DecimalWidget(
                visible=ADD_VISIBLE,
                label=_(u"Reception Temperature (deg C)"),
            ),
        ),

        # 9. Condition de l'echantillon (liste deroulante)
        ExtStringField(
            "SampleCondition",
            required=True,
            vocabulary=vocab.as_displaylist(vocab.SAMPLE_CONDITION_VOCAB),
            schemata="Reception",
            widget=SelectionWidget(
                visible=ADD_VISIBLE,
                label=_(u"Sample Condition"),
                format="select",
            ),
        ),

        # 10. Etat de l'emballage (liste deroulante)
        ExtStringField(
            "PackagingCondition",
            required=True,
            vocabulary=vocab.as_displaylist(vocab.PACKAGING_CONDITION_VOCAB),
            schemata="Reception",
            widget=SelectionWidget(
                visible=ADD_VISIBLE,
                label=_(u"Packaging Condition"),
                format="select",
            ),
        ),

        # 11. Provenance (liste deroulante)
        ExtStringField(
            "Origin",
            required=True,
            vocabulary=vocab.as_displaylist(vocab.ORIGIN_VOCAB),
            schemata="Reception",
            widget=SelectionWidget(
                visible=ADD_VISIBLE,
                label=_(u"Origin"),
                format="select",
            ),
        ),

        # 12. Detail fournisseur / client
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

        # 13. Personne ayant receptionne (liste deroulante)
        ExtStringField(
            "Receptionist",
            required=True,
            vocabulary=vocab.as_displaylist(vocab.RECEPTIONIST_VOCAB),
            schemata="Reception",
            widget=SelectionWidget(
                visible=ADD_VISIBLE,
                label=_(u"Received By"),
                format="select",
            ),
        ),

        # 14. CONTRAT
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

        # 15. BE LABO
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
    ]

    def __init__(self, context):
        self.context = context

    def getFields(self):
        return self.fields

    def getOrder(self, schematas):
        """Place l'onglet Reception juste apres l'onglet par defaut."""
        default = schematas.get("default", [])
        reception_fields = [f.getName() for f in self.fields]
        schematas["Reception"] = reception_fields
        return schematas
