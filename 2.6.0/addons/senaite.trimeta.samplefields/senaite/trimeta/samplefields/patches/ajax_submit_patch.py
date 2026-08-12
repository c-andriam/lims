# -*- coding: utf-8 -*-
"""
Monkey patch de bika.lims.browser.analysisrequest.add2.ajaxAnalysisRequestAddView.ajax_submit

Objectif: n'afficher qu'UN SEUL message d'erreur "Field 'X' is required"
a la fois (le premier champ obligatoire non rempli), au lieu de tous les
afficher simultanement. Une fois ce champ rempli et le formulaire
resoumis, le message suivant (pour le prochain champ manquant) apparait,
et ainsi de suite.

Ce fichier est une copie fidele de la methode originale ajax_submit
(senaite.core 2.6.0 / bika.lims.browser.analysisrequest.add2), avec une
seule modification : la liste `missing` est tronquee au premier element
avant de generer les messages d'erreur. Toute la logique metier restante
(validation des contacts, des quantites, des conditions de service, la
creation des echantillons, etc.) est strictement identique a l'original.

IMPORTANT: en cas de mise a jour de senaite.core, verifier que la
signature et le comportement de ajax_submit n'ont pas change, et mettre
ce patch a jour en consequence.
"""

import logging
from collections import OrderedDict

from bika.lims import api
from bika.lims import bikaMessageFactory as _
from bika.lims.browser.analysisrequest.add2 import ajaxAnalysisRequestAddView
from bika.lims.interfaces import IAddSampleRecordsValidator
from Products.CMFPlone.utils import safe_unicode
from zope.component import getAdapters

logger = logging.getLogger("senaite.trimeta.samplefields")


def patched_ajax_submit(self):
    """Version patchee: un seul message d'erreur requis a la fois."""

    confirmation = self.check_confirmation()
    if confirmation:
        return {"confirmation": confirmation}

    max_samples_record = self.get_max_samples_per_record()

    fields = self.get_ar_fields()
    required_keys = [field.getName() for field in fields if field.required]

    records = self.get_records()

    fielderrors = {}
    errors = {"message": "", "fielderrors": {}}

    valid_records = []

    for num, record in enumerate(records):

        file_fields = filter(lambda f: f.endswith("_file"), record)
        uploads = map(lambda f: record.pop(f), file_fields)
        attachments = [self.to_attachment_record(f) for f in uploads]

        required_values = [record.get(key) for key in required_keys]
        required_fields = dict(zip(required_keys, required_values))

        if record.get("Client", False):
            required_fields.pop("Client", None)

        if not self.analyses_required():
            required_fields.pop("Analyses", None)

        contact = required_fields.pop("Contact", None)

        if not any(required_fields.values()):
            continue

        required_fields["Contact"] = contact

        contact_obj = api.get_object(contact, None)
        if not contact_obj:
            fielderrors["Contact"] = _("No valid contact")
        else:
            parent_uid = api.get_uid(api.get_parent(contact_obj))
            if parent_uid != record.get("Client"):
                msg = _("Contact does not belong to the selected client")
                fielderrors["Contact"] = msg

        num_samples = self.get_num_samples(record)
        if num_samples > max_samples_record:
            msg = _(u"error_analyssirequest_numsamples_above_max",
                    u"The number of samples to create for the record "
                    u"'Sample ${record_index}' (${num_samples}) is above "
                    u"${max_num_samples}",
                    mapping={
                        "record_index": num + 1,
                        "num_samples": num_samples,
                        "max_num_samples": max_samples_record,
                    })
            fielderrors["NumSamples"] = self.context.translate(msg)

        # Missing required fields
        missing = [f for f in required_fields if not record.get(f, None)]

        # Handle fields from Service conditions
        for condition in record.get("ServiceConditions", []):
            if condition.get("type") == "file":
                file_upload = condition.get("value")
                att = self.to_attachment_record(file_upload)
                if att:
                    att.update({
                        "Service": condition.get("uid"),
                        "Condition": condition.get("title"),
                    })
                    attachments.append(att)
                filename = file_upload and file_upload.filename or ""
                condition.value = filename

            if condition.get("required") == "on":
                if not condition.get("value"):
                    title = condition.get("title")
                    if title not in missing:
                        missing.append(title)

        # --- SEULE MODIFICATION PAR RAPPORT A L'ORIGINAL ---
        # On ne garde que le premier champ manquant, pour n'afficher
        # qu'un seul message d'erreur "requis" a la fois.
        if missing:
            missing = missing[:1]
        # --- FIN DE LA MODIFICATION ---

        for field in missing:
            fieldname = "{}-{}".format(field, num)
            label = self.get_field_label(field) or field
            msg = self.context.translate(_("Field '{}' is required"))
            fielderrors[fieldname] = msg.format(label)

        valid_record = dict()
        tmp_sample = self.get_ar()
        for field in fields:
            field_name = field.getName()
            field_value = record.get(field_name)
            if field_value in ['', None]:
                continue

            process_value = field.widget.process_form
            value, msgs = process_value(tmp_sample, field, record)
            if not value:
                continue

            valid_record[field_name] = value

            error = field.validate(value, tmp_sample)
            if error:
                field_name = "{}-{}".format(field_name, num)
                fielderrors[field_name] = error

        valid_record["attachments"] = filter(None, attachments)

        valid_records.append(valid_record)

    if fielderrors:
        errors["fielderrors"] = fielderrors
        return {'errors': errors}

    validators = getAdapters((self.request, ), IAddSampleRecordsValidator)
    for name, validator in validators:
        validation_err = validator.validate(valid_records)
        if validation_err:
            return {"errors": validation_err}

    try:
        samples = self.create_samples(valid_records)
    except Exception as e:
        errors["message"] = str(e)
        logger.error(e, exc_info=True)
        return {"errors": errors}

    ARs = OrderedDict()
    for sample in samples:
        ARs[sample.Title()] = sample.UID()

    level = "info"
    if len(ARs) == 0:
        message = _('No Samples could be created.')
        level = "error"
    elif len(ARs) > 1:
        message = _('Samples ${ARs} were successfully created.',
                    mapping={'ARs': safe_unicode(', '.join(ARs.keys()))})
    else:
        message = _('Sample ${AR} was successfully created.',
                    mapping={'AR': safe_unicode(ARs.keys()[0])})

    self.context.plone_utils.addPortalMessage(message, level)

    return self.handle_redirect(ARs.values(), message)


def apply_patch():
    ajaxAnalysisRequestAddView.ajax_submit = patched_ajax_submit
    logger.warning(
        "### TRIMETA: patch applique sur ajaxAnalysisRequestAddView.ajax_submit "
        "(un seul message d'erreur requis a la fois) ###"
    )
