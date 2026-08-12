# -*- coding: utf-8 -*-
"""
Vocabularies (dropdown lists) for the custom fields of the
Reception section on sample intake.

Expected format for Archetypes DisplayList: list of tuples
(stored_value, display_label). Display labels are wrapped in the
i18n MessageFactory so they can be translated (see locales/).
"""

from zope.i18nmessageid import MessageFactory

_ = MessageFactory("senaite.trimeta.samplefields")

# 3. Sample designation
DESIGNATION_VOCAB = (
    ("raw_material", _(u"Raw material")),
    ("finished_product", _(u"Finished product")),
    ("semi_finished_product", _(u"Semi-finished product")),
    ("water", _(u"Water")),
    ("packaging", _(u"Packaging")),
    ("other", _(u"Other")),
)

# 9. Sample condition
SAMPLE_CONDITION_VOCAB = (
    ("compliant", _(u"Compliant")),
    ("non_compliant", _(u"Non-compliant")),
)

# 10. Packaging condition
PACKAGING_CONDITION_VOCAB = (
    ("vacuum_sealed", _(u"Vacuum-sealed")),
    ("zip_bag", _(u"Zip bag")),
    ("kraft_paper", _(u"Kraft paper")),
    ("other", _(u"Other")),
)

# 11. Origin
ORIGIN_VOCAB = (
    ("tana", _(u"Antananarivo")),
    ("toamasina", _(u"Toamasina")),
    ("sambava", _(u"Sambava")),
    ("almavillas", _(u"Almavillas")),
    ("external", _(u"External / Client")),
)

# 13. Received by
RECEPTIONIST_VOCAB = (
    ("agent_1", _(u"Reception Agent 1")),
    ("agent_2", _(u"Reception Agent 2")),
    ("lab_manager", _(u"Lab Manager")),
)


def as_displaylist(vocab_tuple):
    """Convert a vocabulary tuple into an Archetypes DisplayList."""
    from Products.Archetypes.public import DisplayList
    return DisplayList(list(vocab_tuple))
