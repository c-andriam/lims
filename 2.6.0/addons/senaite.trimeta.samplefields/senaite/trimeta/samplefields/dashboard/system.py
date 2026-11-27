# -*- coding: utf-8 -*-
from AccessControl import Unauthorized
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from bika.lims import api
from bika.lims import bikaMessageFactory as _
from bika.lims.browser import BrowserView
from plone import api as ploneapi
from senaite.core.browser.dashboard.dashboard import DashboardView
from senaite.core.browser.dashboard.dashboard import is_panel_visible_for_user
from senaite.core.catalog import ANALYSIS_CATALOG
from zExceptions import BadRequest


PANELS = {
    "unassigned": (("unassigned",), _("Assignment pending")),
    "pending": (("unassigned", "assigned"), _("Results pending")),
    "to_be_verified": (("to_be_verified",), _("To be verified")),
    "verified": (("verified",), _("Verified")),
}


class SystemDashboard(DashboardView):
    def _getStatistics(self, name, description, url, catalog, criterias, total):
        if catalog.id == ANALYSIS_CATALOG and url == "#":
            states = tuple(criterias["review_state"])
            for key, (panel_states, title) in PANELS.items():
                if states == panel_states:
                    url = "dashboard-analyses?panel=" + key
                    if "Creator" in criterias:
                        url += "&mine=1"
                    break
        return super(SystemDashboard, self)._getStatistics(
            name, description, url, catalog, criterias, total)


class AnalysisPanel(BrowserView):
    template = ViewPageTemplateFile("analysis_panel.pt")
    page_size = 50

    def __call__(self):
        member = ploneapi.user.get_current()
        if (ploneapi.user.is_anonymous() or api.get_current_client() or
                not is_panel_visible_for_user("analyses", member)):
            raise Unauthorized("dashboard-analyses")
        key = self.request.form.get("panel")
        if not isinstance(key, basestring) or key not in PANELS:
            raise BadRequest("Unknown analysis panel")
        states, self.heading = PANELS[key]
        query = dict(portal_type="Analysis", is_active=True,
                     review_state=list(states), sort_on="created",
                     sort_order="descending")
        url = self.portal_url + "/dashboard-analyses?panel=" + key
        if self.request.form.get("mine") == "1":
            query["Creator"] = member.getId()
            url += "&mine=1"
        brains = api.search(query, ANALYSIS_CATALOG)
        try:
            page = int(self.request.form.get("page", 1))
        except (ValueError, TypeError):
            raise BadRequest("Invalid page")
        last = max(1, (len(brains) + self.page_size - 1) // self.page_size)
        page = min(last, max(1, page))
        start = (page - 1) * self.page_size
        self.previous = url + "&page=%d" % (page - 1) if page > 1 else None
        self.following = url + "&page=%d" % (page + 1) if page < last else None
        self.rows = []
        for brain in brains[start:start + self.page_size]:
            sample_url = brain.getURL().rsplit("/", 1)[0]
            self.rows.append(dict(title=brain.Title, url=sample_url,
                                  sample=sample_url.rsplit("/", 1)[-1]))
        return self.template()
