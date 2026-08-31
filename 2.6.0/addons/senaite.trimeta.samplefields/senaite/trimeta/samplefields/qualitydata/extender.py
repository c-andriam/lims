# -*- coding: utf-8 -*-
"""
Extension de schema: section "Assurance Qualite" du type Sample.

Les 41 champs sont declares par sous-section, dans l'ordre exact du
document AMELIORATIONS SENAITE LIMS. Chaque sous-section est un tuple
(identifiant, titre affiche, liste de champs); c'est cette structure qui
sert a la fois:

- a construire la liste plate des champs remise a schemaextender,
- a ordonner l'onglet,
- a dessiner les separateurs de sous-sections dans le formulaire
  (browser/viewlets.py transmet SECTIONS au JavaScript).

Une seule source de verite, donc: ajouter un champ a une sous-section
suffit, tout le reste suit.
"""

from archetypes.schemaextender.interfaces import IOrderableSchemaExtender
from bika.lims.interfaces import IAnalysisRequest
from zope.component import adapts
from zope.i18nmessageid import MessageFactory
from zope.interface import implementer

from senaite.trimeta.samplefields.qualitydata.fields import SCHEMATA
from senaite.trimeta.samplefields.qualitydata.fields import choice_field
from senaite.trimeta.samplefields.qualitydata.fields import conformity_field
from senaite.trimeta.samplefields.qualitydata.fields import count_field
from senaite.trimeta.samplefields.qualitydata.fields import date_field
from senaite.trimeta.samplefields.qualitydata.fields import operator_field
from senaite.trimeta.samplefields.qualitydata.fields import remarks_field
from senaite.trimeta.samplefields.qualitydata.fields import text_field
from senaite.trimeta.samplefields.qualitydata.vocabularies import (
    TRANSMISSION_VOCAB)

_ = MessageFactory("senaite.trimeta.samplefields")


# Les appareils dont la performance est verifiee. Chacun donne une paire
# (date de verification, conformite): 8 appareils, 16 champs.
INSTRUMENT_CHECKS = (
    ("ExtractorTemp", _(u"Extractor temperature")),
    ("Balance", _(u"Balance")),
    ("DesiccatorWeight", _(u"Desiccator weights")),
    ("DesiccatorTemp", _(u"Desiccator temperature")),
    ("Smartcal", _(u"Smartcal")),
    ("AWMeter", _(u"AW meter")),
    ("Pipette", _(u"Pipettes")),
    ("HPLCStandard", _(u"HPLC standard")),
)


def instrument_check_fields():
    """Genere les 16 champs de verification de performance."""
    fields = []
    for prefix, label in INSTRUMENT_CHECKS:
        fields.append(date_field(
            "{}CheckDate".format(prefix),
            _(u"${name} - check date", mapping={"name": label}),
        ))
        fields.append(conformity_field(
            "{}Conformity".format(prefix),
            _(u"${name} - conformity", mapping={"name": label}),
        ))
    return fields


# (identifiant de sous-section, titre affiche, champs)
SECTIONS = (
    ("extraction", _(u"Extraction"), [
        date_field("ExtractionDate", _(u"Extraction start date")),
        operator_field("ExtractionOperator", _(u"Extraction operator")),
        count_field("ExtractionCount", _(u"Number of extractions")),
    ]),

    ("hplc", _(u"HPLC assay"), [
        date_field("HPLCDate", _(u"HPLC assay date")),
        operator_field("HPLCOperator", _(u"HPLC operator")),
        count_field("HPLCCount", _(u"Number of HPLC analyses")),
        conformity_field("HPLCBlankCheck", _(u"HPLC blank check")),
    ]),

    ("desiccator", _(u"Desiccator"), [
        date_field("MoistureDate", _(u"Moisture analysis date")),
        operator_field("MoistureOperator", _(u"Moisture operator")),
        count_field("MoistureCount", _(u"Number of moisture analyses")),
    ]),

    ("awmeter", _(u"AW meter"), [
        date_field("WaterActivityDate", _(u"Water activity date")),
        operator_field("WaterActivityOperator",
                       _(u"Water activity operator")),
        count_field("WaterActivityCount",
                    _(u"Number of water activity analyses")),
    ]),

    ("instruments", _(u"Instrument performance check"),
     instrument_check_fields()),

    ("consumables", _(u"Consumables"), [
        text_field("EthanolLot", _(u"Ethanol lot"),
                   _(u"Remembered and suggested on later samples.")),
        text_field("AcetonitrileLot", _(u"Acetonitrile lot")),
        text_field("HPLCWaterLot", _(u"HPLC water lot")),
        text_field("IsopropanolLot", _(u"Isopropanol lot")),
        conformity_field("SolventConformity", _(u"Solvent conformity")),
        text_field("ColumnSerialNumber", _(u"Column serial number")),
        text_field("LampSerialNumber", _(u"Lamp serial number")),
    ]),

    ("validation", _(u"Validation and results"), [
        operator_field("TechnicalValidator", _(u"Technical validator")),
        operator_field(
            "FinalValidator",
            _(u"Final validation and report signatory"),
        ),
        remarks_field(
            "NokRemarks",
            _(u"Remarks and action if NOK"),
            _(u"Corrective action taken when a check came back NOK."),
        ),
        choice_field("TransmissionMode",
                     _(u"Results transmission mode"),
                     TRANSMISSION_VOCAB),
        date_field("TransmissionDate", _(u"Results transmission date")),
    ]),
)


def get_all_fields():
    """Liste plate des champs, dans l'ordre des sous-sections."""
    fields = []
    for _id, _title, section_fields in SECTIONS:
        fields.extend(section_fields)
    return fields


def get_section_map():
    """[(identifiant, titre, [noms de champs])] pour le JavaScript."""
    return [
        (section_id, title, [f.getName() for f in fields])
        for section_id, title, fields in SECTIONS
    ]


@implementer(IOrderableSchemaExtender)
class QualityDataExtender(object):
    """Ajoute la section Assurance Qualite au Sample."""

    adapts(IAnalysisRequest)

    fields = get_all_fields()

    def __init__(self, context):
        self.context = context

    def getFields(self):
        return self.fields

    def getOrder(self, schematas):
        """Ordonne l'onglet Assurance Qualite.

        On ne touche a aucune autre schemata: l'extender de la section
        Reception/Analyse tourne en parallele et gere les siennes.
        """
        schematas[SCHEMATA] = [f.getName() for f in self.fields]
        return schematas
