# -*- coding: utf-8 -*-
"""
Vocabularies for the Reception section fields.

NOTE: The dropdown vocabularies for Designation, Sample Condition,
Packaging Condition, Origin and Received By have been removed. These
fields are now free-text with dynamic, shared autocomplete
suggestions (see suggestions.py) instead of a fixed list.

Only the Reception Temperature keeps a fixed vocabulary, since it
must stay within a strict 15-31 degC range.
"""

from zope.i18nmessageid import MessageFactory

_ = MessageFactory("senaite.trimeta.samplefields")

# Reception Temperature: fixed integer range 15-31 degC
TEMPERATURE_VOCAB = tuple(
    (str(i), u"{} \u00b0C".format(i)) for i in range(15, 32)
)


def as_displaylist(vocab_tuple):
    """Convert a vocabulary tuple into an Archetypes DisplayList."""
    from Products.Archetypes.public import DisplayList
    return DisplayList(list(vocab_tuple))
