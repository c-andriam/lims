# -*- coding: utf-8 -*-
"""Reference LabContact independante du compte utilise par le workflow."""
from AccessControl import ClassSecurityInfo
from archetypes.schemaextender.interfaces import IOrderableSchemaExtender
from bika.lims import api
from bika.lims.interfaces import IAnalysis
from senaite.core.permissions import FieldEditAnalysisConditions
from zope.component import adapts
from zope.interface import implementer
from zope.i18nmessageid import MessageFactory

from senaite.trimeta.samplefields.analysts import FIELD, EDIT_STATES
from senaite.trimeta.samplefields.extender import ExtUIDReferenceField
from senaite.core.browser.widgets.referencewidget import ReferenceWidget
from senaite.core.catalog import CONTACT_CATALOG

_ = MessageFactory("senaite.trimeta.samplefields")


class AssignedAnalystField(ExtUIDReferenceField):
    security = ClassSecurityInfo()

    def set(self, context, value, **kwargs):
        migration = kwargs.pop("_trimeta_migration_", False)
        if isinstance(value, (list, tuple)):
            if len(value) > 1:
                raise ValueError("Un seul analyste peut etre affecte.")
            value = value[0] if value else ""
        uid = self.get_uid(value) if value else ""
        if value and not uid:
            raise ValueError("Contact du laboratoire invalide.")
        if kwargs.get("_initializing_", False) and not uid:
            return super(AssignedAnalystField, self).set(context, "", **kwargs)
        old = self.getRaw(context) or ""
        if old == uid:
            if not kwargs.get("_initializing_", False):
                context._trimeta_assigned_analyst_set = True
            return
        state = api.get_workflow_status_of(context)
        if state and state not in EDIT_STATES and not migration:
            raise ValueError("L'affectation d'une analyse soumise ou validee est verrouillee.")
        if uid:
            contact = api.get_object_by_uid(uid)
            if (getattr(contact, "portal_type", "") != "LabContact"
                    or (not migration and not api.is_active(contact))):
                raise ValueError("Choisissez un contact actif du laboratoire.")
        result = super(AssignedAnalystField, self).set(context, uid, **kwargs)
        context._trimeta_assigned_analyst_set = True
        return result


@implementer(IOrderableSchemaExtender)
class AnalysisAnalystExtender(object):
    adapts(IAnalysis)

    def __init__(self, context):
        self.context = context

    def getFields(self):
        return [AssignedAnalystField(
            FIELD, required=False, multiValued=False,
            relationship="AnalysisAssignedLabAnalyst", allowed_types=("LabContact",),
            write_permission=FieldEditAnalysisConditions,
            widget=ReferenceWidget(
                label=_(u"Assigned laboratory analyst"),
                visible={"view": "visible", "edit": "invisible", "add": "invisible"},
                catalog=CONTACT_CATALOG, query={"portal_type":"LabContact", "is_active":True}))]

    def getOrder(self, original):
        return original
