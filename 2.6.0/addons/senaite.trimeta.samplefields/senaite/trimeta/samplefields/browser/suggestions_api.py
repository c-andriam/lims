# -*- coding: utf-8 -*-
"""Consultation et administration des suggestions partagees du laboratoire."""
import json

from AccessControl import Unauthorized, getSecurityManager
from Products.CMFCore.permissions import ManagePortal
from Products.Five.browser import BrowserView
from bika.lims import api
from plone.protect import CheckAuthenticator
from plone.protect.authenticator import createToken

from senaite.trimeta.samplefields import suggestions
from senaite.trimeta.samplefields.compat import string_types


class SuggestionsAPI(BrowserView):

    def __call__(self):
        response = self.request.response
        response.setHeader("Content-Type", "application/json")
        response.setHeader("Cache-Control", "private, no-store")
        user = api.get_current_user()
        if user is None or user.getUserName() == "Anonymous User":
            raise Unauthorized()

        method = self.request.get("REQUEST_METHOD")
        can_manage = getSecurityManager().checkPermission(ManagePortal, api.get_portal())
        if method == "GET":
            field = self.request.form.get("field", "")
            return json.dumps({
                "suggestions": suggestions.list_suggestions(field),
                "token": createToken() if can_manage else None,
            })
        if method != "POST":
            response.setStatus(405)
            response.setHeader("Allow", "GET, POST")
            return json.dumps({"success": False})
        if not can_manage:
            raise Unauthorized()
        CheckAuthenticator(self.request)
        form = self.request.form
        field = form.get("field")
        value = form.get("value")
        if (field not in suggestions.REMEMBERED_FIELDS or
                not isinstance(value, string_types) or not value.strip() or
                form.get("action") not in ("add", "remove")):
            response.setStatus(400)
            return json.dumps({"success": False})
        if form["action"] == "add":
            suggestions.add_suggestion(field, value)
        else:
            suggestions.remove_suggestion(field, value)
        return json.dumps({"success": True})
