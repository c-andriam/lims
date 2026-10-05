# -*- coding: utf-8 -*-
"""Activation du profil sur l'instance arretee, via bin/instance run."""
import os
import transaction
from AccessControl.SecurityManagement import newSecurityManager
from Testing.makerequest import makerequest
from zope.component.hooks import setSite

PROFILE = "senaite.trimeta.samplefields:default"

app = makerequest(app)
user = app.acl_users.getUserById("admin")
if user is None:
    raise RuntimeError("Administrateur Zope introuvable")
newSecurityManager(None, user.__of__(app.acl_users))
site_id = os.environ.get("SITE", "senaite")
try:
    if site_id not in app.objectIds():
        from Products.CMFPlone.factory import addPloneSite
        addPloneSite(app, site_id, title="SENAITE LIMS",
                     extension_ids=("senaite.lims:default",),
                     default_language="fr", portal_timezone="Indian/Antananarivo")
    site = app[site_id]
    setSite(site)
    tool = site.portal_setup
    version = tool.getLastVersionForProfile(PROFILE)
    print("Profil Trimeta avant installation: %r" % (version,))
    if version == "unknown":
        site.portal_quickinstaller.installProduct("senaite.trimeta.samplefields")
    else:
        tool.upgradeProfile(PROFILE)
    expected = tuple(tool.getProfileInfo(PROFILE)["version"].split("."))
    actual = tool.getLastVersionForProfile(PROFILE)
    if actual != expected:
        raise RuntimeError("Profil incomplet: %r, attendu %r" % (actual, expected))
    from senaite.trimeta.samplefields.catalog import CATALOGS
    for name, indexes, columns in CATALOGS:
        catalog = getattr(site, name)
        missing = set(i[0] for i in indexes) - set(catalog.indexes())
        missing.update(set(columns) - set(catalog.schema()))
        if missing:
            raise RuntimeError("Catalogue %s incomplet: %r" % (name, missing))
    transaction.commit()
    print("Profil Trimeta actif: %r; catalogues verifies" % (actual,))
except Exception:
    transaction.abort()
    raise
finally:
    setSite(None)
    app.REQUEST.close()
