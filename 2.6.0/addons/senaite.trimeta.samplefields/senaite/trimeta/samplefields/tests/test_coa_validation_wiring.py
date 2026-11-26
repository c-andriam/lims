# -*- coding: utf-8 -*-
"""Raccordement de la validation aux API natives, sans ecriture."""
import unittest
from senaite.trimeta.samplefields.coa import reportview


class Model(object):
    instance = object()
    FinalValidator = 'A designated contact is not a workflow actor'


class User(object):
    def getProperty(self, name, default=''):
        return 'Recorded Validator' if name == 'fullname' else default


class TestCoaValidationWiring(unittest.TestCase):
    def patch(self, name, value):
        self.addCleanup(setattr, reportview.api, name, getattr(reportview.api, name))
        setattr(reportview.api, name, value)

    def setUp(self):
        self.patch('get_review_status', lambda sample: 'published')
        self.patch('get_review_history', lambda sample: [
            {'action':'publish','actor':'publisher','time':4},
            {'action':'verify','actor':'validator','time':3}])
        self.patch('get_user', lambda actor: User())

    def test_report_uses_validation_actor_instead_of_current_user_or_designated_contact(self):
        data = reportview.CoaValidationMixin().get_coa_validation(Model())
        self.assertEqual((data['date'], data['actor'], data['fullname']),
                         (3, 'validator', 'Recorded Validator'))

    def test_deleted_account_keeps_its_recorded_login(self):
        self.patch('get_user', lambda actor: None)
        data = reportview.CoaValidationMixin().get_coa_validation(Model())
        self.assertEqual(data['fullname'], 'validator')

    def test_incomplete_history_does_not_fall_back_to_designated_contact(self):
        self.patch('get_review_history', lambda sample: [])
        data = reportview.CoaValidationMixin().get_coa_validation(Model())
        self.assertTrue(data['verified'])
        self.assertEqual(data['fullname'], '')
        self.assertIsNone(data['date'])

    def test_single_and_multi_controllers_have_the_validation_helper(self):
        self.assertTrue(issubclass(reportview.TrimetaSingleReportView, reportview.CoaValidationMixin))
        self.assertTrue(issubclass(reportview.TrimetaMultiReportView, reportview.CoaValidationMixin))


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromTestCase(TestCoaValidationWiring)
