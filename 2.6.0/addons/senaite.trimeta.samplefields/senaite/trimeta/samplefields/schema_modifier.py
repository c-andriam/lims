# -*- coding: utf-8 -*-
"""
Retouches sur les champs NATIFS du type Sample.

ISchemaModifier (fourni par archetypes.schemaextender) permet de
modifier un champ existant, la ou IOrderableSchemaExtender ne sait
qu'en ajouter.

Trois retouches:

1. DateReceived redevient saisissable manuellement, pour corriger une
   reception enregistree en retard.
2. ClientSampleID est renomme "Lot". C'est la mise en oeuvre cote
   interface de la decision d'architecture: le "Lot" du cahier des
   charges est ce champ natif, deja indexe et deja en colonne de
   metadonnees dans le sample_catalog. Creer un champ Lot maison aurait
   impose un index de plus, une migration, et un doublon fonctionnel.
3. ClientReference est masque: il fait doublon avec le Code article.
"""

from archetypes.schemaextender.interfaces import ISchemaModifier
from bika.lims.interfaces import IAnalysisRequest
from zope.component import adapts
from zope.i18nmessageid import MessageFactory
from zope.interface import implementer

_ = MessageFactory("senaite.trimeta.samplefields")

VISIBLE = {
    "edit": "visible",
    "view": "visible",
    "add": "edit",
}

INVISIBLE = {
    "edit": "invisible",
    "view": "invisible",
    "add": "invisible",
}

# Champs natifs masques car redondants avec un champ Trimeta.
#
# ClientReference ("Reference de l'echantillon") fait doublon avec le
# Code article de la section Reception. On le masque plutot que de le
# supprimer: les valeurs deja saisies restent en base et reapparaissent
# si l'on retire cette ligne.
#
# ATTENTION: ne jamais ajouter ClientSampleID ici. Ce champ porte
# desormais le "Lot" (voir plus bas) et il est utilise par les listings
# et le tableau de bord.
HIDDEN_NATIVE_FIELDS = (
    "ClientReference",
)


@implementer(ISchemaModifier)
class DateReceivedSchemaModifier(object):
    """Applique les retouches sur les champs natifs."""

    adapts(IAnalysisRequest)

    def __init__(self, context):
        self.context = context

    def fiddle(self, schema):
        self.unlock_date_received(schema)
        self.relabel_client_sample_id(schema)
        self.hide_redundant_fields(schema)
        return schema

    def unlock_date_received(self, schema):
        """Rend la date de reception modifiable a la main.

        Le workflow ne l'ecrase plus si elle est deja renseignee: voir
        patches/date_received_patch.py.
        """
        field = schema.get("DateReceived")
        if field is None:
            return
        field.mode = "rw"
        field.widget.visible = VISIBLE
        field.widget.description = _(
            u"Actual date and time the sample was received. "
            u"Can be corrected manually if entered after the fact."
        )

    def relabel_client_sample_id(self, schema):
        """Presente le champ natif ClientSampleID comme le "Lot"."""
        field = schema.get("ClientSampleID")
        if field is None:
            return
        field.widget.label = _(u"Lot")
        field.widget.description = _(
            u"Lot number of the batch this sample was taken from."
        )
        field.widget.visible = VISIBLE

    def hide_redundant_fields(self, schema):
        for name in HIDDEN_NATIVE_FIELDS:
            field = schema.get(name)
            if field is None:
                continue
            field.required = False
            field.widget.visible = INVISIBLE
