# -*- coding: utf-8 -*-
"""
Socle commun aux adaptateurs de listing.

Choix de conception: enregistrement large, discrimination dans le code
--------------------------------------------------------------------
L'usage courant est d'enregistrer un IListingViewAdapter pour une classe
de vue precise, par exemple SamplesView. C'est plus fin, mais fragile:
SENAITE a deplace ses vues de listing d'un module a l'autre au fil des
versions 2.x, et un chemin devenu faux fait echouer le chargement du
ZCML -- donc le demarrage complet de l'instance, pas seulement la
colonne concernee.

On enregistre donc pour l'interface IListingView et un contexte
quelconque, et chaque adaptateur declare ce sur quoi il s'applique via
`portal_types`. Le cout est de deux comparaisons de chaines par listing
affiche; le benefice est qu'une reorganisation interne de SENAITE fait
au pire disparaitre une colonne, jamais tomber le site.
"""

import logging

from bika.lims import api

from senaite.trimeta.samplefields.compat import string_types

logger = logging.getLogger("senaite.trimeta.samplefields")


def insert_column_after(columns, after, key, definition):
    """Insere une colonne juste apres une autre, en preservant l'ordre.

    Les colonnes d'un listing sont un dictionnaire ordonne: y ajouter une
    cle la place en dernier, loin de la colonne a laquelle elle se
    rapporte. On reconstruit donc le dictionnaire.

    Si `after` n'existe pas, la colonne est ajoutee a la fin plutot que
    perdue.
    """
    if key in columns:
        return columns

    if after not in columns:
        columns[key] = definition
        return columns

    items = list(columns.items())
    columns.clear()
    for name, value in items:
        columns[name] = value
        if name == after:
            columns[key] = definition
    return columns


def show_in_all_states(listing, *keys):
    """Rend les colonnes visibles quel que soit le filtre actif.

    Sans cela, une colonne ajoutee n'apparait que dans l'onglet par
    defaut et disparait des que l'utilisateur clique sur "Recus" ou
    "Publies" -- symptome deroutant et difficile a relier a sa cause.
    """
    for state in listing.review_states:
        state_columns = list(state.get("columns", []))
        if not state_columns:
            continue
        for key in keys:
            if key not in state_columns:
                state_columns.append(key)
        state["columns"] = state_columns


class BaseListingAdapter(object):
    """Base des adaptateurs de listing de l'add-on.

    Les sous-classes declarent `portal_types` et implementent
    `add_columns()` et `fill_item()`.
    """

    # Priorite vis-a-vis des autres adaptateurs de listing.
    priority_order = 1000

    # Types de contenu listes auxquels l'adaptateur s'applique.
    portal_types = ()

    def __init__(self, listing, context):
        self.listing = listing
        self.context = context
        # Memo par rendu: evite de recharger dix fois le meme
        # echantillon quand plusieurs lignes en dependent.
        self._sample_cache = {}

    # -- discrimination ----------------------------------------------

    def get_listed_types(self):
        """Types de contenu que ce listing affiche."""
        content_filter = getattr(self.listing, "contentFilter", None) or {}
        portal_type = content_filter.get("portal_type")
        if not portal_type:
            return ()
        # string_types couvre str ET unicode: sur Python 2, un
        # portal_type unicode echouerait le test et tuple() le
        # decouperait en caracteres. La colonne disparaitrait alors
        # sans la moindre erreur.
        if isinstance(portal_type, string_types):
            return (portal_type,)
        return tuple(portal_type)

    def applies(self):
        listed = self.get_listed_types()
        if not listed:
            return False
        return any(t in self.portal_types for t in listed)

    # -- hooks IListingViewAdapter ------------------------------------

    def before_render(self):
        if not self.applies():
            return
        try:
            self.add_columns()
        except Exception:
            # Une colonne manquante est un desagrement; un listing qui
            # ne s'affiche plus est un arret de travail.
            logger.exception(
                "Ajout des colonnes Trimeta impossible sur %s",
                self.listing.__class__.__name__)

    def folder_item(self, obj, item, index):
        if not self.applies():
            return item
        try:
            self.fill_item(obj, item, index)
        except Exception:
            logger.exception("Remplissage de la ligne %s impossible", index)
        return item

    # -- a implementer -------------------------------------------------

    def add_columns(self):
        raise NotImplementedError

    def fill_item(self, obj, item, index):
        raise NotImplementedError

    # -- utilitaires ---------------------------------------------------

    def get_sample_code(self, sample):
        """Lit le Code echantillon d'un echantillon deja charge."""
        if sample is None:
            return ""
        field = sample.getField("SampleCode")
        if field is None:
            return ""
        return field.get(sample) or ""

    def get_cached_sample(self, uid):
        """Charge un echantillon une seule fois par rendu."""
        if not uid:
            return None
        if uid not in self._sample_cache:
            try:
                self._sample_cache[uid] = api.get_object_by_uid(uid)
            except Exception:
                self._sample_cache[uid] = None
        return self._sample_cache[uid]
