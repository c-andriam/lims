# -*- coding: utf-8 -*-
"""
Couche de test et classe de base pour l'add-on.

On se greffe sur la couche BASE_LAYER_FIXTURE de senaite.core, qui monte
deja un site Plone complet avec senaite.core, senaite.app.listing,
senaite.impress et senaite.lims installes. On ajoute par-dessus le ZCML
de l'add-on puis on applique son profil GenericSetup, exactement comme
le ferait une installation reelle.
"""

import transaction
from plone.app.testing import FunctionalTesting
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import applyProfile
from senaite.core.tests.base import BaseTestCase
from senaite.core.tests.layers import BASE_LAYER_FIXTURE

PROFILE = "senaite.trimeta.samplefields:default"


class TrimetaLayer(PloneSandboxLayer):
    """Couche installant l'add-on Trimeta au-dessus de SENAITE."""

    defaultBases = (BASE_LAYER_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        super(TrimetaLayer, self).setUpZope(app, configurationContext)
        import senaite.trimeta.samplefields
        self.loadZCML(package=senaite.trimeta.samplefields)

    def setUpPloneSite(self, portal):
        super(TrimetaLayer, self).setUpPloneSite(portal)
        applyProfile(portal, PROFILE)
        transaction.commit()


TRIMETA_FIXTURE = TrimetaLayer()
TRIMETA_TESTING = FunctionalTesting(
    bases=(TRIMETA_FIXTURE,),
    name="SENAITE:TrimetaTesting",
)


class TrimetaTestCase(BaseTestCase):
    """Classe de base des tests de l'add-on."""

    layer = TRIMETA_TESTING

    def setUp(self):
        super(TrimetaTestCase, self).setUp()
        # On ne suppose pas que la classe de base les expose: on les
        # relit depuis la couche, seule source fiable.
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
