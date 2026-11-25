# -*- coding: utf-8 -*-
"""Regles de migration et de classement, avec les modules Zope reels."""
import unittest
from Products.Archetypes.public import Schema, StringField, ReferenceWidget, SelectionWidget

from senaite.trimeta.samplefields import analysts, equipment_history


class Contact(object):
    def __init__(self, username):
        self.username = username

    def getUsername(self):
        return self.username


class Action(object):
    def __init__(self, name):
        self.name = name

    def getId(self):
        return self.name

    def Title(self):
        return getattr(self, 'title', self.name)

    def edit(self, title):
        self.title = title


class FTI(object):
    def __init__(self):
        self.actions = [Action('maintenance'), Action('edit')]

    def listActions(self):
        return self.actions

    def addAction(self, name, *args, **kwargs):
        self.actions.append(Action(name))

    def deleteActions(self, positions):
        self.actions = [a for i, a in enumerate(self.actions) if i not in positions]


class Container(object):
    pass


class TestAssignmentHistory(unittest.TestCase):
    def test_contacts_without_accounts_are_not_used_for_migration(self):
        self.assertEqual(analysts.unique_user_contacts([Contact(''), Contact(None)]), {})

    def test_ambiguous_accounts_are_not_guessed(self):
        unique = Contact('unique')
        self.assertEqual(analysts.unique_user_contacts([
            Contact('same'), Contact('same'), unique]), {'unique': unique})

    def test_repairs_and_preventive_tasks_are_separate(self):
        for value in ('Repair', ['Repair'], ('Repair',)):
            self.assertTrue(equipment_history.belongs_to_history(value, 'breakdown'))
            self.assertFalse(equipment_history.belongs_to_history(value, 'maintenance'))
        for value in ('Preventive', ['Preventive']):
            self.assertTrue(equipment_history.belongs_to_history(value, 'maintenance'))
            self.assertFalse(equipment_history.belongs_to_history(value, 'breakdown'))

    def test_unknown_and_legacy_empty_types_are_not_misclassified(self):
        for value in (None, '', [], 'Enhancement', 'unknown'):
            for kind in ('breakdown', 'maintenance', 'unknown'):
                self.assertFalse(equipment_history.belongs_to_history(value, kind))

    def test_actions_are_idempotent_and_uninstall_preserves_native_actions(self):
        portal = Container()
        portal.portal_types = Container()
        portal.portal_types.Instrument = fti = FTI()
        self.assertEqual(len(equipment_history.setup_history_actions(portal)), 2)
        self.assertEqual(equipment_history.setup_history_actions(portal), [])
        for action in fti.listActions()[2:]:
            self.assertEqual(action.Title().domain, 'senaite.trimeta.samplefields')
        equipment_history.remove_history_actions(portal)
        self.assertEqual([a.getId() for a in fti.listActions()], ['maintenance', 'edit'])

    def test_maintenance_type_uses_a_vocabulary_widget_instead_of_a_reference(self):
        task = Container()
        task.portal_type = 'InstrumentMaintenanceTask'
        schema = Schema((StringField('Type', widget=ReferenceWidget(label='Type')),))
        equipment_history.MaintenanceTaskSchemaModifier(task).fiddle(schema)
        self.assertTrue(schema['Type'].required)
        self.assertTrue(schema['Type'].enforceVocabulary)
        self.assertIsInstance(schema['Type'].widget, SelectionWidget)

    def test_schema_modifier_does_not_change_other_cancellable_types(self):
        other = Container()
        other.portal_type = 'Analysis'
        schema = Schema((StringField('Type', required=False),))
        equipment_history.MaintenanceTaskSchemaModifier(other).fiddle(schema)
        self.assertFalse(schema['Type'].required)


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromTestCase(TestAssignmentHistory)
