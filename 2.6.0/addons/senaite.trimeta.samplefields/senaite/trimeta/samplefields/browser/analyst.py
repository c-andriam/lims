# -*- coding: utf-8 -*-
"""Formulaire protege d'affectation d'un analyste de laboratoire."""
import logging
import transaction
from AccessControl import Unauthorized
from bika.lims import api
from plone.protect import CheckAuthenticator
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent

from senaite.trimeta.samplefields import analysts
from senaite.trimeta.samplefields.compat import string_types, to_text

logger = logging.getLogger("senaite.trimeta.samplefields")


class AssignAnalystView(BrowserView):
    index = ViewPageTemplateFile("templates/analyst.pt")

    def __call__(self):
        if not analysts.can_assign(self.context):
            raise Unauthorized("Affectation de l'analyste interdite")
        self.error, self.saved = u"", False
        field = self.context.getField(analysts.FIELD)
        self.selected = field.getRaw(self.context) or ""
        self.token = analysts.revision(self.context)
        self.contacts = [(api.get_uid(c), api.get_title(c)) for c in analysts.lab_contacts()]
        current = field.get(self.context)
        if current is not None and self.selected not in [uid for uid, _title in self.contacts]:
            self.contacts.append((self.selected, to_text(api.get_title(current)) + u" (inactif)"))
        if self.request.get("REQUEST_METHOD") == "POST":
            CheckAuthenticator(self.request)
            checkpoint = transaction.savepoint(optimistic=True)
            try:
                if self.request.form.get("revision") != self.token:
                    raise ValueError("L'affectation a change. Rechargez la page.")
                value = self.request.form.get("lab_analyst", "")
                if not isinstance(value, string_types):
                    raise ValueError("Choisissez un seul contact du laboratoire.")
                field.set(self.context, value)
                self.context.reindexObject()
                notify(ObjectModifiedEvent(self.context))
                self.saved = True
                self.selected = field.getRaw(self.context) or ""
                self.token = analysts.revision(self.context)
            except ValueError as error:
                checkpoint.rollback()
                self.error = str(error)
                self.token = self.request.form.get("revision", "")
            except Exception:
                checkpoint.rollback()
                logger.exception("Affectation de l'analyste annulee")
                self.error = u"Enregistrement impossible. Aucune affectation n'a ete modifiee."
                self.token = self.request.form.get("revision", "")
        return self.index()

    def back_url(self):
        return self.context.getRequest().absolute_url()
