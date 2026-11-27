# -*- coding: utf-8 -*-
"""
Logo du laboratoire sur TOUS les rapports, quel que soit le gabarit.

senaite.impress ecrit le logo SENAITE en dur dans son en-tete
(analysisrequest/templates/header.pt) et ne propose aucun reglage. Le
remplacer dans notre seul gabarit COA ne suffisait pas: un utilisateur
qui choisit un gabarit de SENAITE dans l'ecran de publication
retrouvait le logo SENAITE dans le PDF.

Point d'extension officiel
--------------------------
`PublishView.get_report_view_controller` cherche d'abord un adaptateur
qui adapte AUSSI le contexte::

    queryMultiAdapter((context, model_or_collection, request),
                      interface, name="AnalysisRequest")

et ne retombe sur celui de senaite.impress qu'a defaut -- le commentaire
du code dit explicitement que c'est la pour permettre a un tiers de
redefinir la vue via une couche navigateur. On enregistre donc nos vues
sur ISenaiteTrimetaLayer, et l'en-tete de tous les gabarits passe par
notre HEADER_TEMPLATE.

Nos vues recoivent TROIS arguments la ou celles de senaite.impress en
recoivent deux: le contexte s'ajoute devant. `self.context` reste ce
qu'en fait la classe de base (le portail), dont dependent les gabarits.
"""

import logging
from xml.sax.saxutils import escape
from bika.lims import api
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from senaite.impress.analysisrequest.reportview import MultiReportView
from senaite.impress.analysisrequest.reportview import SingleReportView
from senaite.impress.interfaces import IMultiReportView
from senaite.impress.interfaces import IReportView
from zope.interface import implementer
from zope.i18nmessageid import MessageFactory
from senaite.trimeta.samplefields.coa.validation import validation_details
from senaite.trimeta.samplefields.compat import to_text
from senaite.trimeta.samplefields.worksheet.export import worksheet_result

HEADER_TEMPLATE = ViewPageTemplateFile("templates/header.pt")
COA_RESULTS_TEMPLATE = ViewPageTemplateFile("templates/results.pt")
logger = logging.getLogger("senaite.trimeta.samplefields")
_coa = MessageFactory("senaite.trimeta.coa")


class CoaValidationMixin(object):
    """Separe validation enregistree et signataire choisi dans la qualite."""

    not_recorded_label = _coa(u"Not recorded")

    COA_RESULTS_TEMPLATE = COA_RESULTS_TEMPLATE

    @property
    def current_user(self):
        """Masque le mail personnel uniquement dans les donnees du rapport."""
        properties = dict(super(CoaValidationMixin, self).current_user or {})
        properties["email"] = u""
        properties["fullname"] = (properties.get("fullname")
                                  or properties.get("username")
                                  or properties.get("userid") or u"")
        return properties

    def get_coa_result(self, model, analysis):
        try:
            value = worksheet_result(analysis.instance, None, model.decimal_mark)
            if value is not None:
                return escape(to_text(value))
        except Exception:
            logger.exception("Precision du resultat COA indisponible")
        return model.get_formatted_result(analysis)

    def render_coa_results(self, context, **options):
        return self.COA_RESULTS_TEMPLATE(context, **options)

    def validation_actor_name(self, actor):
        try:
            user = api.get_user(actor)
            fullname = user.getProperty("fullname", "") if user is not None else ""
            return to_text(fullname or actor)
        except Exception:
            logger.exception("Nom du validateur indisponible pour %s", actor)
            return actor

    def get_coa_validation(self, model):
        try:
            sample = model.instance
            state = api.get_review_status(sample)
            return validation_details(state, api.get_review_history(sample),
                                      self.validation_actor_name)
        except Exception:
            logger.exception("Historique de validation du COA inaccessible")
            return validation_details("", [], self.validation_actor_name)


@implementer(IReportView)
class TrimetaSingleReportView(CoaValidationMixin, SingleReportView):
    """Rapport d'un echantillon, en-tete au logo du laboratoire."""

    HEADER_TEMPLATE = HEADER_TEMPLATE

    def __init__(self, context, model, request):
        super(TrimetaSingleReportView, self).__init__(model, request)


@implementer(IMultiReportView)
class TrimetaMultiReportView(CoaValidationMixin, MultiReportView):
    """Rapport de plusieurs echantillons, meme en-tete."""

    HEADER_TEMPLATE = HEADER_TEMPLATE

    def __init__(self, context, collection, request):
        super(TrimetaMultiReportView, self).__init__(collection, request)
