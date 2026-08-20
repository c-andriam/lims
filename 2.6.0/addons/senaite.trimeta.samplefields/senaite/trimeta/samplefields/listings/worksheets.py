# -*- coding: utf-8 -*-
"""
Colonne "Code echantillon" dans la grille de saisie d'une Work Sheet.

Le cahier des charges demande de "remplacer ou ajouter" l'identifiant.
On ajoute plutot que de remplacer: l'identifiant SENAITE reste la cle de
navigation vers l'echantillon, et le supprimer ferait perdre ce lien.

Ici, une ligne est une analyse, pas un echantillon: la valeur ne peut
pas venir d'une colonne de metadonnees du catalogue des analyses. On
charge donc l'echantillon parent, une seule fois par echantillon grace
au memo de BaseListingAdapter -- une Work Sheet contient typiquement
quelques dizaines d'analyses reparties sur bien moins d'echantillons.
"""

from bika.lims import api

from senaite.trimeta.samplefields.compat import string_types
from senaite.app.listing.interfaces import IListingViewAdapter
from zope.i18nmessageid import MessageFactory
from zope.interface import implementer

from senaite.trimeta.samplefields.listings.base import BaseListingAdapter
from senaite.trimeta.samplefields.listings.base import insert_column_after
from senaite.trimeta.samplefields.listings.base import show_in_all_states

_ = MessageFactory("senaite.trimeta.samplefields")

SAMPLE_CODE = "SampleCode"


@implementer(IListingViewAdapter)
class WorksheetAnalysesAdapter(BaseListingAdapter):
    """Ajoute le Code echantillon aux lignes d'analyse."""

    portal_types = (
        "Analysis",
        "DuplicateAnalysis",
        "ReferenceAnalysis",
    )

    def add_columns(self):
        insert_column_after(self.listing.columns, "getId", SAMPLE_CODE, {
            "title": _(u"Sample Code"),
            "sortable": False,   # pas d'index sur le catalogue analyses
            "toggle": True,
        })
        show_in_all_states(self.listing, SAMPLE_CODE)

    def get_sample_uid(self, analysis):
        """UID de l'echantillon parent, sans charger l'objet si possible.

        Les brains d'analyse exposent generalement getRequestUID; on
        retombe sur l'objet quand ce n'est pas le cas (analyses de
        controle, rendus particuliers).
        """
        uid = getattr(analysis, "getRequestUID", None)
        if isinstance(uid, string_types) and uid:
            return uid
        try:
            obj = api.get_object(analysis)
            request = obj.getRequest()
        except Exception:
            return None
        return api.get_uid(request) if request else None

    def fill_item(self, obj, item, index):
        sample = self.get_cached_sample(self.get_sample_uid(obj))
        item[SAMPLE_CODE] = self.get_sample_code(sample)
