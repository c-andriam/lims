from senaite.trimeta.samplefields.patches.date_received_patch import apply_patch

apply_patch()

# NOTE: le monkey patch ajax_submit (limitation a un seul message
# d'erreur a la fois) a ete retire sur demande utilisateur et n'est
# plus utilise. Seul date_received_patch reste actif desormais.
