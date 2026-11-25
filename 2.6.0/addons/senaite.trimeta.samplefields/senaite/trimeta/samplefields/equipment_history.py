# -*- coding: utf-8 -*-
"""Deux historiques structures utilisant les interventions natives."""
from archetypes.schemaextender.interfaces import ISchemaModifier
from bika.lims.interfaces import ICancellable
from Products.Archetypes.public import SelectionWidget
from zope.component import adapts
from zope.interface import implementer
from zope.i18nmessageid import MessageFactory

from senaite.trimeta.samplefields.listings.instruments import maintenance_type_value

_ = MessageFactory("senaite.trimeta.samplefields")
HISTORY_ACTIONS = (
    ("trimeta_breakdowns", _(u"Breakdown history"), "trimeta-breakdown-history"),
    ("trimeta_maintenance", _(u"Maintenance history"), "trimeta-maintenance-history"),
)


def belongs_to_history(raw, kind):
    value = maintenance_type_value(raw)
    expected = {"breakdown": "Repair", "maintenance": "Preventive"}.get(kind)
    return expected is not None and value == expected


def setup_history_actions(portal):
    fti = portal.portal_types.Instrument
    known = set(action.getId() for action in fti.listActions())
    added = []
    for action_id, title, view in HISTORY_ACTIONS:
        if action_id not in known:
            fti.addAction(action_id, title, "string:${object_url}/" + view,
                          "", ("View",), "object", visible=1)
            added.append(action_id)
    # addAction convertit le titre en str et perd le domaine i18n.
    titles = dict((name, title) for name, title, _view in HISTORY_ACTIONS)
    for action in fti.listActions():
        title = titles.get(action.getId())
        if title is not None and getattr(action.Title(), 'domain', None) != title.domain:
            action.edit(title=title)
    return added


def remove_history_actions(portal):
    fti = portal.portal_types.Instrument
    ours = set(action_id for action_id, _title, _view in HISTORY_ACTIONS)
    positions = [i for i, action in enumerate(fti.listActions()) if action.getId() in ours]
    if positions:
        fti.deleteActions(positions)


@implementer(ISchemaModifier)
class MaintenanceTaskSchemaModifier(object):
    adapts(ICancellable)

    def __init__(self, context):
        self.context = context

    def fiddle(self, schema):
        if getattr(self.context, "portal_type", "") == "InstrumentMaintenanceTask":
            field = schema.get("Type")
            if field is not None:
                field.required = True
                field.enforceVocabulary = True
                # Le type est une chaine de vocabulaire, pas une reference.
                # L'ancien ReferenceWidget plante la fiche apres sauvegarde.
                field.widget = SelectionWidget(label=field.widget.label, format="select")
        return schema


def preset_task_type(task, event):
    if getattr(task, "portal_type", "") != "InstrumentMaintenanceTask":
        return
    from zope.globalrequest import getRequest
    request = getRequest()
    if request is None:
        return
    selected = request.form.get("trimeta_maintenance_type")
    if selected not in ("Repair", "Preventive"):
        return
    field = task.getField("Type")
    if field is not None and not field.get(task):
        field.set(task, selected)
