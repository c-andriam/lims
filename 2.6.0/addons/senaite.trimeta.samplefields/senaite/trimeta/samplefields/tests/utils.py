# -*- coding: utf-8 -*-
"""
Fabriques d'objets pour les tests.

SENAITE a deplace une partie de sa configuration d'Archetypes vers
Dexterity au fil des versions 2.x: certains dossiers de setup vivent
sous `portal.bika_setup`, d'autres sous `portal.setup`. Les helpers
`get_setup_folder` ci-dessous resolvent l'emplacement au moment du test
plutot que de le coder en dur, et echouent avec un message explicite si
aucun emplacement connu ne correspond.
"""

from bika.lims import api
from bika.lims.utils.analysisrequest import create_analysisrequest

# Emplacements possibles, du plus recent au plus ancien.
SETUP_FOLDERS = {
    "sampletypes": ("setup/sampletypes", "bika_setup/bika_sampletypes"),
    "analysiscategories": ("setup/analysiscategories",
                           "bika_setup/bika_analysiscategories"),
    "analysisservices": ("setup/analysisservices",
                         "bika_setup/bika_analysisservices"),
    "labcontacts": ("setup/labcontacts", "bika_setup/bika_labcontacts"),
}


def get_setup_folder(portal, kind):
    """Retourne le dossier de configuration pour `kind`.

    :raises AssertionError: si aucun emplacement connu n'existe, avec la
        liste de ceux essayes (message lisible en sortie de test).
    """
    paths = SETUP_FOLDERS[kind]
    for path in paths:
        obj = portal
        for part in path.split("/"):
            obj = getattr(obj, part, None)
            if obj is None:
                break
        if obj is not None:
            return obj
    raise AssertionError(
        "Dossier de configuration '{}' introuvable. Emplacements "
        "essayes: {}. La structure de SENAITE a probablement change: "
        "mettre a jour SETUP_FOLDERS dans tests/utils.py.".format(
            kind, ", ".join(paths))
    )


def create_client(portal, name="Trimeta Group", client_id="TRI"):
    clients = portal.clients
    return api.create(clients, "Client", Name=name, ClientID=client_id)


def create_contact(client, firstname="Jean", surname="Dupont"):
    return api.create(client, "Contact", Firstname=firstname,
                      Surname=surname)


def create_labcontact(portal, firstname="Marie", surname="Rakoto"):
    folder = get_setup_folder(portal, "labcontacts")
    return api.create(folder, "LabContact", Firstname=firstname,
                      Surname=surname)


def create_sampletype(portal, title="Vanille verte", prefix="VAN"):
    folder = get_setup_folder(portal, "sampletypes")
    return api.create(folder, "SampleType", title=title, Prefix=prefix,
                      MinimumVolume="10 g")


def create_analysisservice(portal, title="Vanilline", keyword="Van"):
    categories = get_setup_folder(portal, "analysiscategories")
    category = api.create(categories, "AnalysisCategory",
                          title="Chromatographie")
    services = get_setup_folder(portal, "analysisservices")
    return api.create(services, "AnalysisService", title=title,
                      Keyword=keyword, Category=category, Price="10.00")


class SampleFactory(object):
    """Monte une fois les prerequis, puis fabrique des echantillons.

    Usage::

        factory = SampleFactory(self.portal, self.request)
        sample = factory.create(SampleCode="ECH-001")
    """

    def __init__(self, portal, request):
        self.portal = portal
        self.request = request
        self.client = create_client(portal)
        self.contact = create_contact(self.client)
        self.sampletype = create_sampletype(portal)
        self.service = create_analysisservice(portal)

    def create(self, **values):
        """Cree un echantillon. Les `values` surchargent les defauts."""
        from DateTime import DateTime
        data = {
            "Client": self.client,
            "Contact": self.contact,
            "SampleType": self.sampletype,
            "DateSampled": DateTime(),
        }
        data.update(values)
        return create_analysisrequest(
            self.client, self.request, data,
            [api.get_uid(self.service)])
