# -*- coding: utf-8 -*-
"""Lecture commune des PDF stockes; aucune regeneration ni modification."""
import logging

from ZODB.POSException import POSKeyError

logger = logging.getLogger("senaite.trimeta.samplefields")


def get_pdf(report):
    if report is None:
        return None
    try:
        pdf = report.getPdf()
        if pdf is not None and pdf.data:
            return pdf
    except (POSKeyError, TypeError, AttributeError):
        logger.exception("PDF du rapport illisible")
    return None
