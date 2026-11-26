# -*- coding: utf-8 -*-
"""Pas d'attribution d'une validation a une personne seulement designee."""
import unittest
from senaite.trimeta.samplefields.coa.validation import validation_details


class TestCoaValidation(unittest.TestCase):
    def test_date_and_name_come_from_the_latest_verify_event(self):
        history = [{'action':'publish','actor':'publisher','time':4},
                   {'action':'verify','actor':'second','time':3},
                   {'action':'verify','actor':'first','time':1}]
        data = validation_details('published', history, lambda actor: 'NAME-'+actor)
        self.assertEqual((data['date'],data['actor'],data['fullname']), (3,'second','NAME-second'))

    def test_provisional_or_retracted_sample_does_not_show_old_approval(self):
        history = [{'action':'verify','actor':'old','time':1}]
        for state in ('sample_due','sample_received','to_be_verified','invalid'):
            data = validation_details(state,history,lambda actor: actor)
            self.assertFalse(data['verified'])
            self.assertIsNone(data['date'])
            self.assertEqual(data['fullname'],'')

    def test_deleted_or_unnamed_account_keeps_recorded_identifier(self):
        data = validation_details('verified',[{'action':'verify','actor':'former-user','time':1}],lambda actor: '')
        self.assertEqual(data['fullname'],'former-user')

    def test_missing_actor_never_resolves_to_current_user(self):
        def forbidden(actor):
            raise AssertionError('No actor must not resolve to current user')
        data = validation_details('verified',[{'action':'verify','time':1}],forbidden)
        self.assertEqual(data['actor'],'')
        self.assertEqual(data['fullname'],'')
        self.assertEqual(data['date'],1)

    def test_missing_history_is_not_replaced_with_a_designated_contact(self):
        data = validation_details('verified',[],lambda actor: 'Designated signatory')
        self.assertTrue(data['verified'])
        self.assertEqual(data['fullname'],'')
        self.assertIsNone(data['date'])

    def test_latest_verification_with_missing_time_is_not_replaced_by_an_old_one(self):
        history = [{'action':'verify','actor':'new'}, {'action':'verify','actor':'old','time':1}]
        data = validation_details('verified',history,lambda actor: actor)
        self.assertIsNone(data['date'])
        self.assertEqual(data['actor'],'new')


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromTestCase(TestCoaValidation)
