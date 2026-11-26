# -*- coding: utf-8 -*-
"""Rendu reel du bloc client, avec et sans adresse mail."""
import os
import unittest
from lxml import html
from Products.PageTemplates.PageTemplate import PageTemplate
from zope.component import getGlobalSiteManager
from zope.interface import Interface
from zope.traversing.adapters import DefaultTraversable
from zope.traversing.interfaces import ITraversable
from senaite.trimeta.samplefields.coa import reportview


class View(object):
    __allow_access_to_unprotected_subobjects__ = 1
    model = {
        'Client': {'Name': 'CLIENT-TEST', 'PostalAddress': {
            'address': 'RUE-CLIENT', 'zip': '001', 'city': 'VILLE', 'country': 'PAYS'}},
        'Contact': {'Fullname': 'CONTACT-TEST', 'EmailAddress': 'private@example.invalid',
                    'Phone': '123456', 'Fax': ''},
        'absolute_url': 'http://example.invalid/sample',
    }
    laboratory = {'title': 'LAB-TEST', 'Supervisor': None, 'PostalAddress': {
        'address': 'RUE-LAB', 'zip': '002', 'city': 'VILLE', 'country': 'PAYS'},
        'LabURL': 'https://example.invalid', 'LaboratoryAccredited': False,
        'AccreditationBodyLogo': None}


class TestCoaContactEmail(unittest.TestCase):
    def setUp(self):
        registry = getGlobalSiteManager()
        previous = registry.adapters.registered((Interface,), ITraversable)
        registry.registerAdapter(DefaultTraversable, (Interface,), ITraversable)
        def restore():
            registry.unregisterAdapter(DefaultTraversable, (Interface,), ITraversable)
            if previous is not None:
                registry.registerAdapter(previous, (Interface,), ITraversable)
        self.addCleanup(restore)

    def render(self, **options):
        path = os.path.join(os.path.dirname(reportview.__file__), 'templates', 'info.pt')
        with open(path, 'rb') as source:
            template = PageTemplate()
            template.write(source.read().decode('utf-8'))
        return template.pt_render(extra_context={'view': View(), 'options': options})

    def test_coa_mode_removes_email_text_and_link_but_preserves_contact_info(self):
        output = self.render(include_contact_email=False)
        self.assertNotIn('private@example.invalid', output)
        self.assertNotIn('mailto:', output)
        root = html.fragment_fromstring(output, create_parent='div')
        for value in ('CLIENT-TEST', 'CONTACT-TEST', 'RUE-CLIENT', '123456', 'LAB-TEST', 'RUE-LAB'):
            self.assertIn(value, root.text_content())
        self.assertTrue(root.xpath('.//*[contains(@class,"qrcode")]'))

    def test_default_and_explicit_native_modes_preserve_their_email(self):
        for options in ({}, {'include_contact_email': True}):
            output = self.render(**options)
            self.assertIn('mailto:private@example.invalid', output)
            self.assertIn('private@example.invalid', html.fragment_fromstring(output, create_parent='div').text_content())

    def test_single_and_multi_controllers_use_the_same_template(self):
        self.assertIs(reportview.TrimetaSingleReportView.__dict__['INFO_TEMPLATE'],
                      reportview.TrimetaMultiReportView.__dict__['INFO_TEMPLATE'])


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromTestCase(TestCoaContactEmail)
