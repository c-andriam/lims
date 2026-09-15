# -*- coding: utf-8 -*-
"""
Colonne "Type" de l'historique des pannes et entretiens d'un equipement.

Ecran vise: l'onglet Maintenance d'un Instrument (vue "maintenance" de
bika.lims.browser.instrument). senaite.core 2.6 y affiche
`obj.getType()[0]`: le champ Type etait autrefois une liste, c'est
aujourd'hui une chaine, et l'indice [0] n'en garde que la premiere
lettre. Une reparation s'affichait donc "R", un entretien preventif "P".
"""

from bika.lims import api
from bika.lims import senaiteMessageFactory as _core
from senaite.app.listing.interfaces import IListingViewAdapter
from zope.interface import implementer

from senaite.trimeta.samplefields.compat import string_types
from senaite.trimeta.samplefields.listings.base import BaseListingAdapter

TYPE_COLUMN = "getType"


def maintenance_type_value(raw):
    """Valeur brute du champ Type, qu'il soit chaine ou liste."""
    if isinstance(raw, (list, tuple)):
        raw = raw[0] if raw else ""
    if not isinstance(raw, string_types):
        return ""
    return raw.strip()


@implementer(IListingViewAdapter)
class InstrumentMaintenanceAdapter(BaseListingAdapter):
    """Affiche le libelle complet et traduit du type d'intervention."""

    portal_types = ("InstrumentMaintenanceTask",)

    def add_columns(self):
        # La colonne existe deja: seul son contenu est faux.
        pass

    def translate(self, value):
        context = getattr(self.listing, "context", None)
        if context is None or not hasattr(context, "translate"):
            return value
        return context.translate(_core(value))

    def fill_item(self, obj, item, index):
        task = api.get_object(obj)
        value = maintenance_type_value(task.getType())
        item[TYPE_COLUMN] = self.translate(value) if value else ""
