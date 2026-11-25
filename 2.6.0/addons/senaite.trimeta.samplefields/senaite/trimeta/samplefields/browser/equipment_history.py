# -*- coding: utf-8 -*-
"""Historiques de pannes et d'entretiens dans l'interface native."""
import logging
from bika.lims import api
from bika.lims.browser.instrument import InstrumentMaintenanceView
from plone.protect.authenticator import createToken
from senaite.core.i18n import translate as t
from zope.i18nmessageid import MessageFactory
from senaite.trimeta.samplefields.equipment_history import belongs_to_history

_ = MessageFactory("senaite.trimeta.samplefields")
logger = logging.getLogger("senaite.trimeta.samplefields")


class EquipmentHistoryView(InstrumentMaintenanceView):
    kind = ""
    history_title = u""

    def __init__(self, context, request):
        super(EquipmentHistoryView, self).__init__(context, request)
        self.form_id = "trimeta_" + self.kind + "_history"
        self.title = t(_(self.history_title), context=request)
        self.default_review_state = "all"
        task_type = "Repair" if self.kind == "breakdown" else "Preventive"
        # createObject perd les parametres lors de sa redirection. Le
        # formulaire temporaire natif les recoit ici des sa creation.
        temporary_id = context.generateUniqueId("InstrumentMaintenanceTask")
        creation_url = (context.absolute_url() + "/portal_factory/InstrumentMaintenanceTask/"
                        + temporary_id + "/edit?trimeta_maintenance_type=" + task_type
                        + "&_authenticator=" + createToken())
        self.context_actions = {_(u"Add intervention"): {
            "url": creation_url,
            "icon": "++resource++bika.lims.images/add.png"}}

    def isItemAllowed(self, brain):
        if not super(EquipmentHistoryView, self).isItemAllowed(brain):
            return False
        try:
            return belongs_to_history(api.get_object(brain).getType(), self.kind)
        except Exception:
            logger.exception("Intervention illisible pour l'historique %s", self.kind)
            return False


class BreakdownHistoryView(EquipmentHistoryView):
    kind = "breakdown"
    history_title = u"Breakdown history"


class MaintenanceHistoryView(EquipmentHistoryView):
    kind = "maintenance"
    history_title = u"Maintenance history"
