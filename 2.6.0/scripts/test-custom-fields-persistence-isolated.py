# -*- coding: utf-8 -*-
"""Enregistre puis relit tous les champs ajoutes, sur restauration isolee.

Python 2.7 du conteneur. Deux processus : write, puis verify.
La sauvegarde doit etre montee en lecture seule sur /opt/review-backups.
Le repertoire /tmp/trimeta-fields-recipe doit etre un volume dedie vide.
Le volume original /data doit etre monte en lecture seule.
"""
import ast
import io
import json
import os
import sys
import tarfile

INSTANCE = "/home/senaite/senaitelims"
RECIPE = "/tmp/trimeta-fields-recipe"
BACKUP = "/opt/review-backups/senaite-data-20261125-165146-135026.tar.gz"
MODE = sys.argv[1]
assert MODE in ("write", "verify")
sys.argv[1:] = []
assert os.path.realpath(RECIPE) == RECIPE
if MODE == "write":
    assert not os.path.exists(RECIPE + "/expected.json"), "Recette deja enregistree"
if MODE == "write" and not os.path.exists(RECIPE + "/filestorage/Data.fs"):
    with tarfile.open(BACKUP, "r:gz") as archive:
        for member in archive.getmembers():
            target = os.path.realpath(os.path.join(RECIPE, member.name))
            assert target == RECIPE or target.startswith(RECIPE + "/"), member.name
            assert member.isfile() or member.isdir(), member.name
        archive.extractall(RECIPE)

with open(INSTANCE + "/bin/instance") as handle:
    tree = ast.parse(handle.read())
for node in tree.body:
    if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Subscript) and isinstance(t.value, ast.Attribute)
            and isinstance(t.value.value, ast.Name)
            and t.value.value.id == "sys" and t.value.attr == "path"
            for t in node.targets):
        sys.path[0:0] = ast.literal_eval(node.value)
with open(INSTANCE + "/parts/instance/etc/zope.conf") as handle:
    config = handle.read().replace("/data/", RECIPE + "/")
assert "path " + RECIPE + "/filestorage/Data.fs" in config
assert "path /data/" not in config
with open(RECIPE + "/recipe.conf", "w") as handle:
    handle.write(config)

import Zope2
import transaction
from DateTime import DateTime
from Products.Archetypes.public import FixedPointField
from AccessControl.SecurityManagement import newSecurityManager
from Testing.makerequest import makerequest
from zope.component.hooks import setSite
from zope.globalrequest import setRequest
from zope.interface import alsoProvides
from bika.lims import api
from senaite.core.browser.fields.datetime import DateTimeField
from senaite.core.interfaces import ISenaiteCore
from senaite.core.browser.widgets.referencewidget import ReferenceWidget
from senaite.trimeta.samplefields.compat import string_types
from senaite.trimeta.samplefields.extender import ReceptionFieldsExtender
from senaite.trimeta.samplefields.interfaces import ISenaiteTrimetaLayer
from senaite.trimeta.samplefields.qualitydata.extender import get_all_fields

Zope2.configure(RECIPE + "/recipe.conf")
app = makerequest(Zope2.app())
portal = app.senaite
setSite(portal)
request = app.REQUEST
portal.setupCurrentSkin(request)
setRequest(request)
alsoProvides(request, ISenaiteTrimetaLayer, ISenaiteCore)
newSecurityManager(request, app.acl_users.getUserById("admin").__of__(app.acl_users))
sample = portal.clients["client-5"]["VAN-0009"]
names = [f.getName() for f in ReceptionFieldsExtender.fields + get_all_fields()]
names += ["DateReceived", "ClientSampleID"]
assert len(names) == len(set(names)) == 67


def normalize(value):
    if isinstance(value, DateTime):
        return value.ISO8601()
    if isinstance(value, string_types):
        return value.decode("utf-8") if isinstance(value, bytes) else value
    if isinstance(value, (tuple, list)):
        return [normalize(item) for item in value]
    if isinstance(value, dict):
        return dict((key, normalize(item)) for key, item in value.items())
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return unicode(value)


def snapshot():
    return dict((name, normalize(sample.getField(name).getRaw(sample)))
                for name in names)


try:
    if MODE == "verify":
        with io.open(RECIPE + "/expected.json", encoding="utf-8") as handle:
            expected = json.load(handle)
        assert snapshot() == expected, "Valeur perdue apres reouverture ZODB"
        print("PERSISTENCE: 67/67 champs relus dans un nouveau processus")
    else:
        contacts = portal.senaite_catalog_contact.unrestrictedSearchResults(
            portal_type="LabContact", is_active=True)
        uids = [brain.UID for brain in contacts]
        assert len(uids) >= 2, "Deux contacts requis pour le preparateur multiple"
        schema = sample.Schema()
        # Un formulaire complet conserve aussi ses references natives.
        values = dict((f.getName(), f.getRaw(sample)) for f in schema.fields()
                      if isinstance(f.widget, ReferenceWidget))
        for name in names:
            field = sample.getField(name)
            if isinstance(field.widget, ReferenceWidget):
                values[name] = uids[:2] if field.multiValued else uids[0]
            elif isinstance(field, DateTimeField):
                values[name] = ("2026-11-25T10:15:00"
                                if field.widget.show_time else "2026-11-25")
            elif isinstance(field, FixedPointField):
                values[name] = "123.45"
            elif name == "CodeArticle":
                values[name] = "V-GNN"
            elif name == "ReceptionTemperature":
                values[name] = "23"
            elif name == "SampleCondition":
                values[name] = "Conforme"
            elif name == "PackagingCondition":
                values[name] = "Kraft"
            elif name.endswith("Count"):
                values[name] = "2"
            elif "Conformity" in name or name == "HPLCBlankCheck":
                values[name] = "NOK"
            elif name == "TransmissionMode":
                values[name] = "coa"
            else:
                values[name] = u"RECETTE-%s-\u00e9chantillon" % name
                if name == "NokRemarks":
                    values[name] += u"\nDeuxieme ligne conservee"

        errors = {}
        for name in names:
            error = sample.getField(name).validate(values[name], sample, errors=errors)
            assert not error, (name, error)
        # Meme traitement de widgets et mutateurs que base_edit.
        sample.processForm(values=values)
        for name in names:
            field = sample.getField(name)
            actual = field.getRaw(sample)
            expected = values[name]
            if isinstance(field, DateTimeField):
                # Les widgets interpretent l'heure locale dans le fuseau du site.
                local = DateTime(expected.replace("T", " ") + " GMT+3")
                assert actual.timeTime() == local.timeTime(), (
                    name, repr(actual), expected)
            elif isinstance(field, FixedPointField):
                assert float(field.get(sample)) == float(expected), name
            else:
                assert normalize(actual) == normalize(expected), (name, actual, expected)
        expected = snapshot()
        transaction.commit()
        with io.open(RECIPE + "/expected.json", "w", encoding="utf-8") as handle:
            handle.write(unicode(json.dumps(expected, ensure_ascii=True)))
        print("PERSISTENCE: 67/67 champs traites par les widgets natifs et commites")
finally:
    transaction.abort()
    app._p_jar.close()
