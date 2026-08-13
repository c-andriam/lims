# -*- coding: utf-8 -*-
"""
JSON API for the Reception fields' dynamic suggestions.

GET  @@trimeta-suggestions?field=Designation
     -> {"suggestions": ["Raw material", "Water", ...]}

POST @@trimeta-suggestions  (action=remove, field=Designation, value=Water)
     -> {"success": true}

Only authenticated users may call this (no anonymous access), and
CSRF protection is disabled for the POST since this is a low-risk,
purely list-management operation restricted to logged-in lab staff.
"""

import json
import logging

from AccessControl import Unauthorized
from plone.protect.interfaces import IDisableCSRFProtection
from Products.Five.browser import BrowserView
from zope.interface import alsoProvides

from senaite.trimeta.samplefields import suggestions

logger = logging.getLogger("senaite.trimeta.samplefields")


class SuggestionsAPI(BrowserView):

    def __call__(self):
        alsoProvides(self.request, IDisableCSRFProtection)
        self.request.response.setHeader("Content-Type", "application/json")

        from bika.lims import api
        current_user = api.get_current_user()
        if current_user is None or \
                current_user.getUserName() == "Anonymous User":
            raise Unauthorized("Authentication required")

        method = self.request.get("REQUEST_METHOD", "GET")
        if method == "POST":
            return self._handle_post()
        return self._handle_get()

    def _handle_get(self):
        fieldname = self.request.get("field", "")
        items = suggestions.list_suggestions(fieldname)
        return json.dumps({"suggestions": items})

    def _handle_post(self):
        action = self.request.get("action", "")
        fieldname = self.request.get("field", "")
        value = self.request.get("value", "")

        if action == "remove":
            suggestions.remove_suggestion(fieldname, value)
            return json.dumps({"success": True})

        return json.dumps({"success": False, "error": "unknown action"})
