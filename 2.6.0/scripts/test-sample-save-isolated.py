# -*- coding: utf-8 -*-
"""Recette sur une copie restauree uniquement, jamais sur /data.

Executer avec le Python du conteneur, apres restauration de la sauvegarde
dans /tmp/trimeta-sample-recipe. Deux passages: create puis verify.
"""
import ast
import json
import os
import sys

INSTANCE = "/home/senaite/senaitelims"
RECIPE = "/tmp/trimeta-sample-recipe"
MODE = sys.argv[1]
assert MODE in ("create", "verify"), "Mode attendu: create ou verify"
sys.argv[1:] = []
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
from Testing.makerequest import makerequest
from AccessControl.SecurityManagement import newSecurityManager
from zope.component.hooks import setSite
from zope.interface import alsoProvides
from senaite.trimeta.samplefields.interfaces import ISenaiteTrimetaLayer
from senaite.trimeta.samplefields.browser.sample_add import SampleAddView
RECEPTION_FIELDS = tuple((name, True) for name in (
    "SampleCode", "CodeArticle", "Designation", "ReceptionWeight",
    "QuantityReceived", "QuantityUnderAnalysis", "TechSampleWeight",
    "ReceptionTemperature", "SampleCondition", "PackagingCondition",
    "Origin", "SupplierCustomerDetail", "Receptionist", "Contract",
    "EntryVoucher"))
ANALYSE_FIELDS = (("AnalysisSheetNumber", True),) + tuple(
    (name, False) for name in ("AnalysisStart", "AnalysisEnd",
                             "AnalysisPreparer", "PodLength",
                             "AromaDevelopment", "Aroma", "Color", "Texture"))

Zope2.configure(RECIPE + "/recipe.conf")
app = makerequest(Zope2.app())
portal = app.senaite
setSite(portal)
request = app.REQUEST
portal.setupCurrentSkin(request)
alsoProvides(request, ISenaiteTrimetaLayer)
newSecurityManager(request, app.acl_users.getUserById("admin").__of__(app.acl_users))
catalog = portal.senaite_catalog_sample
code = "TEST-PERSISTENCE-20261002-ISOLATED"
try:
    if MODE == "verify":
        brains = catalog.unrestrictedSearchResults(getSampleCode=code)
        assert len(brains) == 1, len(brains)
        sample = brains[0].getObject()
        assert sample.getField("SampleCode").get(sample) == code
        from senaite.trimeta.samplefields.dashboard.view import DashboardView
        view = DashboardView(portal, request)
        assert sample.UID() in [b.UID for b in catalog(view.contentFilter)]
        request.form.update({"pagesize": "1000", "review_state": "all"})
        from senaite.core.browser.samples.view import SamplesView
        samples_view = SamplesView(portal.samples, request)
        from bika.lims import api
        for listing in (samples_view, view):
            # Initialisation de ListingView.__call__, sans le chrome HTML
            # qui exige une traversee HTTP complete et ses viewlets.
            listing.portal = portal
            listing.mtool = api.get_tool("portal_membership")
            listing.workflow = api.get_tool("portal_workflow")
            listing.member = api.get_current_user()
            listing.translate = listing.context.translate
            listing.update()
            listing.before_render()
            rows = listing.folderitems()
            assert sample.UID() in [r.get("uid") for r in rows], listing
        print("PASS: committed sample reopened in a new process and listed")
        from bika.lims.browser.analysisrequest.add2 import ajaxAnalysisRequestAddView
        from OFS.Folder import Folder
        original = ajaxAnalysisRequestAddView.create_samples
        def fail_after_write(self, records):
            portal._setObject("test-rollback-isolated", Folder("test-rollback-isolated"))
            raise RuntimeError("Simulated storage failure")
        ajaxAnalysisRequestAddView.create_samples = fail_after_write
        try:
            try:
                SampleAddView(portal, request).create_samples([{}])
                raise AssertionError("Expected failure")
            except RuntimeError:
                pass
            assert "test-rollback-isolated" not in portal.objectIds()
            print("PASS: failure after writing rolls back all partial changes")
        finally:
            ajaxAnalysisRequestAddView.create_samples = original
    else:
        clients = portal.clients.objectValues("Client")
        client = next(c for c in clients if c.objectValues("Contact"))
        view = SampleAddView(client, request)
        fields = view.get_ar_fields()
        by_name = dict((f.getName(), f) for f in fields)
        for name, required in RECEPTION_FIELDS + ANALYSE_FIELDS:
            assert bool(by_name[name].required) == required, name
        assert by_name["DateReceived"].required
        print("PASS: 17 required fields match the specification in the real schema")
        initial = len(catalog.unrestrictedSearchResults(portal_type="AnalysisRequest"))
        request.form.clear()
        request.form.update({"ar_count": "1", "SampleCode-0": code})
        result = view.ajax_submit()
        assert "errors" in result and "redirect_to" not in result, result
        assert "DateReceived-0" in result["errors"]["fielderrors"], result
        assert len(catalog.unrestrictedSearchResults(portal_type="AnalysisRequest")) == initial
        print("PASS: incomplete submission reports errors without creating a sample")
        request.form.clear()
        request.form["ar_count"] = "1"
        result = SampleAddView(client, request).ajax_submit()
        assert "errors" in result and "redirect_to" not in result, result
        print("PASS: empty submission cannot claim success")
        setup = portal.senaite_catalog_setup
        sample_type = setup.unrestrictedSearchResults(portal_type="SampleType")[0].getObject()
        service = setup.unrestrictedSearchResults(portal_type="AnalysisService")[0].getObject()
        contacts = portal.senaite_catalog_contact.unrestrictedSearchResults(portal_type="LabContact")
        values = dict((name, "TEST-ISOLATED") for name, required in RECEPTION_FIELDS + ANALYSE_FIELDS if required)
        values.update({
            "SampleCode": code, "Client": client.UID(),
            "Contact": client.objectValues("Contact")[0].UID(),
            "SampleType": sample_type.UID(), "Analyses": service.UID(),
            "DateSampled": "2026-10-02", "DateReceived": "2026-10-02",
            "CodeArticle": "V-GNN", "ReceptionTemperature": "20",
            "SampleCondition": "Conforme", "PackagingCondition": "Kraft",
            "Receptionist": contacts[0].UID,
        })
        for name in ("ReceptionWeight", "QuantityReceived", "QuantityUnderAnalysis", "TechSampleWeight"):
            values[name] = "10.00"
        for missing_name in [name for name, required in RECEPTION_FIELDS + ANALYSE_FIELDS if required] + ["DateReceived"]:
            incomplete = values.copy()
            incomplete[missing_name] = ""
            request.form.clear()
            request.form.update(dict((name + "-0", value) for name, value in incomplete.items()))
            request.form["ar_count"] = "1"
            result = SampleAddView(client, request).ajax_submit()
            assert missing_name + "-0" in result.get("errors", {}).get("fielderrors", {}), (missing_name, result)
            assert "redirect_to" not in result
        print("PASS: each of the 17 required fields individually blocks an incomplete save")
        request.form.clear()
        request.form.update(dict((name + "-0", value) for name, value in values.items()))
        request.form["ar_count"] = "1"
        view = SampleAddView(client, request)
        result = view.ajax_submit()
        assert "success" in result and "errors" not in result, result
        brains = catalog.unrestrictedSearchResults(getSampleCode=code)
        assert len(brains) == 1, len(brains)
        assert len(catalog.unrestrictedSearchResults(portal_type="AnalysisRequest")) == initial + 1
        transaction.commit()
        print("PASS: actual AJAX submit validated, created, indexed and committed one sample")
finally:
    transaction.abort()
    app._p_jar.close()
