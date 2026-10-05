# -*- coding: utf-8 -*-
"""Inventaire direct de la ZODB SENAITE, avec FileStorage en lecture seule.

A executer avec le Python 2.7 DU CONTENEUR, sans bin/instance run.
Le script reprend les chemins Python de bin/instance, puis ouvre une
configuration temporaire dont FileStorage interdit toute ecriture.
Il ne cree aucun objet, ne reindexe rien et termine par transaction.abort.
Il examine les echantillons directement contenus dans les clients.
"""

import ast
import json
import os
import sys
import tempfile

def main():
    instance = os.environ.get("INSTANCE_DIR", "/home/senaite/senaitelims")
    with open(os.path.join(instance, "bin", "instance")) as source:
        tree = ast.parse(source.read())
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(isinstance(target, ast.Subscript) and
               isinstance(target.value, ast.Attribute) and
               isinstance(target.value.value, ast.Name) and
               target.value.value.id == "sys" and
               target.value.attr == "path" for target in node.targets):
            sys.path[0:0] = ast.literal_eval(node.value)
    with open(os.path.join(instance, "parts", "instance", "etc", "zope.conf")) as source:
        config = source.read()
    # Refuser une configuration inconnue au lieu d'ouvrir la base en ecriture.
    if config.count("<filestorage>") != 1 or "<zeoclient" in config:
        raise RuntimeError("Configuration FileStorage simple attendue")
    if "read-only" in config:
        raise RuntimeError("Verifier manuellement la configuration read-only existante")
    config = config.replace("<filestorage>",
                            "<filestorage>\n        read-only true")
    handle = tempfile.NamedTemporaryFile(
        prefix="lims-audit-readonly-", suffix=".conf", delete=False)
    handle.write(config.encode("utf-8"))
    handle.close()
    app = None
    try:
        import Zope2
        import transaction
        Zope2.configure(handle.name)
        app = Zope2.app()
        if not app._p_jar.db().storage.isReadOnly():
            raise RuntimeError("Lecture seule non active: audit interrompu")
        from zope.component.hooks import setSite
        from senaite.core.catalog import SAMPLE_CATALOG
        from senaite.trimeta.samplefields.extender import ReceptionFieldsExtender
        portal = app[os.environ.get("SITE", "senaite")]
        setSite(portal)
        catalog = getattr(portal, SAMPLE_CATALOG)
        samples = [sample for client in portal.clients.objectValues("Client")
                   for sample in client.objectValues("AnalysisRequest")]
        direct_uids = set(sample.UID() for sample in samples)
        brains = catalog.unrestrictedSearchResults(portal_type="AnalysisRequest")
        catalog_uids = set(brain.UID for brain in brains)
        by_uid = dict((brain.UID, brain) for brain in brains)
        report = {
            "read_only": True,
            "scope": "samples directly contained in clients",
            "direct_count": len(direct_uids),
            "catalog_count": len(catalog_uids),
            "direct_missing_from_catalog": len(direct_uids - catalog_uids),
            "catalog_not_in_direct_scope": len(catalog_uids - direct_uids),
            "profile_version": portal.portal_setup.getLastVersionForProfile(
                "senaite.trimeta.samplefields:default"),
            "declared_reception_fields": [
                {"name": field.getName(), "required": bool(field.required)}
                for field in ReceptionFieldsExtender.fields],
            "samples": [],
        }
        for sample in samples:
            brain = by_uid.get(sample.UID())
            field = sample.getField("SampleCode")
            value = field.get(sample) if field is not None else None
            report["samples"].append({
                "id": sample.getId(),
                "code_matches_catalog": brain is not None and
                    value == getattr(brain, "getSampleCode", None),
                "schema_required_fields": [f.getName()
                    for f in sample.Schema().fields() if f.required],
                "custom_required_fields": [
                    {"name": f.getName(),
                     "required": bool(sample.getField(f.getName()).required)}
                    for f in ReceptionFieldsExtender.fields
                    if sample.getField(f.getName()) is not None],
            })
        print(json.dumps(report, indent=2, sort_keys=True))
    finally:
        if app is not None:
            transaction.abort()
            app._p_jar.close()
        os.unlink(handle.name)


if __name__ == "__main__":
    main()
