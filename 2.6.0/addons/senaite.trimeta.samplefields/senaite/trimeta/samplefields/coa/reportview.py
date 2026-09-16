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

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from senaite.impress.analysisrequest.reportview import MultiReportView
from senaite.impress.analysisrequest.reportview import SingleReportView
from senaite.impress.interfaces import IMultiReportView
from senaite.impress.interfaces import IReportView
from zope.interface import implementer

HEADER_TEMPLATE = ViewPageTemplateFile("templates/header.pt")


@implementer(IReportView)
class TrimetaSingleReportView(SingleReportView):
    """Rapport d'un echantillon, en-tete au logo du laboratoire."""

    HEADER_TEMPLATE = HEADER_TEMPLATE

    def __init__(self, context, model, request):
        super(TrimetaSingleReportView, self).__init__(model, request)


@implementer(IMultiReportView)
class TrimetaMultiReportView(MultiReportView):
    """Rapport de plusieurs echantillons, meme en-tete."""

    HEADER_TEMPLATE = HEADER_TEMPLATE

    def __init__(self, context, collection, request):
        super(TrimetaMultiReportView, self).__init__(collection, request)
