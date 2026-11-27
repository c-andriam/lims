# -*- coding: utf-8 -*-
"""Le mail personnel du responsable est masque, celui du client conserve."""
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
    reporter = {'fullname': 'RESPONSABLE-LABO', 'username': 'publisher',
                    'email': 'lab-person@example.invalid'}

    @property
    def current_user(self):
        return self.reporter

    def uniquify_items(self, items):
        return items


class FilteredView(reportview.CoaValidationMixin, View):
    pass


class Model(object):
    __allow_access_to_unprotected_subobjects__ = 1
    managers = [{'Signature': True, 'absolute_url': 'http://example.invalid/manager',
                 'Salutation': 'Dr', 'Fullname': 'MANAGER-TEST', 'JobTitle': 'CHEF-LABO',
                 'DefaultDepartment': {'title': 'CHIMIE'}}]

    def __init__(self, provisional):
        self.provisional = provisional

    def is_provisional(self):
        return self.provisional


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

    def render(self, path, view):
        with open(path, 'rb') as source:
            template = PageTemplate()
            template.write(source.read().decode('utf-8'))
        return template.pt_render(extra_context={'view': view, 'options': {}})

    def test_native_info_preserves_client_email_and_other_coordinates(self):
        output = self.render(reportview.TrimetaSingleReportView.INFO_TEMPLATE.filename, FilteredView())
        self.assertIn('mailto:private@example.invalid', output)
        root = html.fragment_fromstring(output, create_parent='div')
        for value in ('CLIENT-TEST', 'CONTACT-TEST', 'RUE-CLIENT', '123456', 'LAB-TEST', 'RUE-LAB'):
            self.assertIn(value, root.text_content())
        self.assertTrue(root.xpath('.//*[contains(@class,"qrcode")]'))

    def test_personal_lab_email_is_absent_but_name_and_signature_remain(self):
        for provisional in (False, True):
            view = FilteredView()
            view.collection = [Model(provisional)]
            output = self.render(reportview.TrimetaSingleReportView.SIGNATURE_TEMPLATE.filename, view)
            self.assertNotIn('lab-person@example.invalid', output)
            self.assertNotIn('mailto:', output)
            root = html.fragment_fromstring(output, create_parent='div')
            for value in ('RESPONSABLE-LABO', 'MANAGER-TEST', 'CHEF-LABO', 'CHIMIE'):
                self.assertIn(value, root.text_content())
            self.assertTrue(root.xpath('.//img[@src="http://example.invalid/manager/Signature"]'))
            expected = 'Published by'
            self.assertIn(expected, root.text_content())

    def test_username_fallback_and_original_account_properties_are_preserved(self):
        view = FilteredView()
        view.collection = [Model(False), Model(True)]
        view.reporter = dict(View.reporter, fullname='')
        output = self.render(reportview.TrimetaSingleReportView.SIGNATURE_TEMPLATE.filename, view)
        root = html.fragment_fromstring(output, create_parent='div')
        self.assertIn('Published by', root.text_content())
        self.assertIn('publisher', root.text_content())
        self.assertEqual(view.reporter['email'], 'lab-person@example.invalid')
        self.assertEqual(view.reporter['fullname'], '')
        self.assertNotIn('lab-person@example.invalid', output)

    def test_single_and_multi_controllers_use_the_same_template(self):
        self.assertEqual(reportview.TrimetaSingleReportView.INFO_TEMPLATE.filename,
                         reportview.SingleReportView.INFO_TEMPLATE.filename)
        self.assertEqual(reportview.TrimetaMultiReportView.INFO_TEMPLATE.filename,
                         reportview.MultiReportView.INFO_TEMPLATE.filename)
        self.assertEqual(reportview.TrimetaSingleReportView.SIGNATURE_TEMPLATE.filename,
                         reportview.TrimetaMultiReportView.SIGNATURE_TEMPLATE.filename)


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromTestCase(TestCoaContactEmail)
