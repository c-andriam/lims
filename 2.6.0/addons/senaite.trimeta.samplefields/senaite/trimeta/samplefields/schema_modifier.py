# -*- coding: utf-8 -*-
"""
Rend le champ natif DateReceived (Sample/AnalysisRequest) visible et
modifiable manuellement, plutot que reserve au seul mecanisme
automatique du workflow (transition "Receive").

Utilise ISchemaModifier (fourni par archetypes.schemaextender), qui
permet de modifier un champ EXISTANT du schema (contrairement a
IOrderableSchemaExtender qui ne fait qu'ajouter de nouveaux champs).
"""

from archetypes.schemaextender.interfaces import ISchemaModifier
from zope.component import adapts
from zope.interface import implementer
from zope.i18nmessageid import MessageFactory

from bika.lims.interfaces import IAnalysisRequest

_ = MessageFactory("senaite.trimeta.samplefields")

DATE_RECEIVED_VISIBLE = {
    "edit": "visible",
    "view": "visible",
    "add": "edit",
}


@implementer(ISchemaModifier)
class DateReceivedSchemaModifier(object):
    """Debloque la visibilite/modification manuelle de DateReceived."""

    adapts(IAnalysisRequest)

    def __init__(self, context):
        self.context = context

    def fiddle(self, schema):
        field = schema.get("DateReceived")
        if field is not None:
            field.mode = "rw"
            field.widget.visible = DATE_RECEIVED_VISIBLE
            field.widget.description = _(
                u"Actual date and time the sample was received. "
                u"Can be corrected manually if entered after the fact."
            )
        return schema
