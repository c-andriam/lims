# -*- coding: utf-8 -*-
"""Noms par defaut des exports, sans modifier leur contenu."""
import logging
import os
import re
from email.message import Message

from senaite.trimeta.samplefields.coa.filename import sanitize

logger = logging.getLogger("senaite.trimeta.samplefields")
GENERIC = re.compile(r"^(download|export|report|reports|default|multidefault|"
                     r"sticker|stickers|document|file|output|invoice|coa-trimeta)"
                     r"(?:\.pt)?$", re.I)


def export_filename(original, default, extension=""):
    """Garde un nom explicite, remplace un nom generique et garde le type."""
    original = original or ""
    stem, suffix = os.path.splitext(original)
    suffix = suffix if re.match(r"^\.[a-zA-Z0-9]{1,10}$", suffix) else extension
    # Certains exports Impress ajoutent deux fois .pdf.
    if suffix and stem.lower().endswith(suffix.lower()):
        stem = stem[:-len(suffix)]
    if not stem or GENERIC.match(stem):
        stem = default
    return sanitize(stem, fallback="Export-LIMS") + suffix.lower()


def context_names(context, request):
    """Identifiants deja accessibles a l'utilisateur de la page."""
    from bika.lims import api
    from senaite.trimeta.samplefields.indexers import get_field_value
    kind = getattr(context, "portal_type", "")
    identifier = api.get_id(context) or "LIMS"
    title = api.get_title(context) or identifier
    labels = {"Worksheet": "Feuille-de-travail", "Client": "Client",
              "AnalysisRequest": "Echantillon", "Instrument": "Equipement",
              "Invoice": "Facture"}
    if kind == "Client":
        identifier = title
    if kind == "AnalysisRequest":
        identifier = get_field_value(context, "SampleCode") or identifier
    base = "{}-{}".format(labels.get(kind, "Export"), identifier)
    if kind == "Plone Site":
        base = "LIMS"
    pdf = base
    url = request.get("ACTUAL_URL", "")
    if "sticker" in url:
        pdf = "Etiquettes-{}".format(identifier)
    elif "invoice" in url:
        pdf = "Facture-{}".format(identifier)
    elif "publish" in url or "impress" in url or "/printview" in url:
        # Les droits sur chaque objet sont verifies avant de lire son code.
        from AccessControl import getSecurityManager
        from bika.lims.interfaces import IAnalysisRequest
        from senaite.trimeta.samplefields.compat import string_types
        items = request.get("items", request.get("uids", ""))
        if isinstance(items, string_types):
            items = items.split(",")
        codes = []
        for uid in dict.fromkeys(items or []):
            if not api.is_uid(uid):
                continue
            sample = api.get_object_by_uid(uid)
            if sample is not None and IAnalysisRequest.providedBy(sample) and \
                    getSecurityManager().checkPermission("View", sample):
                codes.append(get_field_value(sample, "SampleCode") or api.get_id(sample))
        if len(codes) == 1:
            pdf = codes[0]
        elif codes:
            pdf = "COA-{}-echantillons".format(len(codes))
        elif kind == "AnalysisRequest":
            pdf = identifier
    return {"context": sanitize(base), "title": sanitize(title),
            "pdf": sanitize(pdf)}


def remember_export_request(event):
    """Prepare le nom avant une eventuelle ecriture en flux."""
    from senaite.trimeta.samplefields.interfaces import ISenaiteTrimetaLayer
    request = event.request
    if ISenaiteTrimetaLayer.providedBy(request):
        request.response._trimeta_export_request = request


def name_export_response(event):
    """Applique le nom avant les en-tetes, aussi pour response.write()."""
    response = getattr(event, "response", None)
    if response is None:
        response = event.request.response
    request = getattr(response, "_trimeta_export_request", None)
    if request is None:
        return
    try:
        disposition = response.getHeader("Content-Disposition")
        if not disposition or response.getStatus() != 200:
            return
        # Le nom des COA archives est deja gere par D10, meme si un code
        # echantillon vaut litteralement "report" ou "download".
        if request.get("ACTUAL_URL", "").rstrip("/").endswith("/download_pdf"):
            return
        published = request.get("PUBLISHED")
        context = getattr(published, "context", None)
        if context is None:
            parents = request.get("PARENTS", [])
            context = parents[0] if parents else None
        if context is None:
            return
        header = Message()
        header["Content-Disposition"] = disposition
        original = header.get_filename() or response.getHeader("filename") or ""
        if "/printview" in request.get("ACTUAL_URL", "") and not request.get("filename"):
            # Le nom du fichier de gabarit n'identifie pas le rapport exporte.
            original = ""
        content_type = response.getHeader("Content-Type") or ""
        extension = {"application/pdf": ".pdf", "text/csv": ".csv",
                     "application/zip": ".zip", "application/json": ".json",
                     "text/xml": ".xml", "application/xml": ".xml",
                     "application/vnd.ms-excel": ".xls"}.get(content_type.split(";")[0], "")
        if not original and not extension:
            return
        names = context_names(context, request)
        default = names["pdf"] if extension == ".pdf" else names["context"]
        name = export_filename(original, default, extension)
        response.setHeader("Content-Disposition", '{}; filename="{}"'.format(
            disposition.split(";", 1)[0], name))
    except Exception:
        logger.exception("Nom du fichier exporte indisponible")
