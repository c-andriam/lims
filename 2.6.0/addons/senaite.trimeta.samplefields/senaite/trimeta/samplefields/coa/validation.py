# -*- coding: utf-8 -*-
"""Date et auteur issus du meme evenement de validation SENAITE."""
from senaite.trimeta.samplefields.compat import to_text

VALIDATED_STATES = ("verified", "published")


def validation_details(state, newest_first_history, display_name):
    """Suit le meme ordre d'historique que getDateVerified() du core."""
    result = {"verified": state in VALIDATED_STATES,
              "date": None, "actor": u"", "fullname": u""}
    if not result["verified"]:
        return result
    for event in newest_first_history:
        if event.get("action") != "verify":
            continue
        result["date"] = event.get("time")
        actor = to_text(event.get("actor") or u"")
        result["actor"] = actor
        # Ne jamais demander l'utilisateur courant pour un acteur absent.
        if actor:
            result["fullname"] = to_text(display_name(actor) or actor)
        break
    return result
