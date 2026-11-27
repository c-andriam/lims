# Retrait de l'adresse mail du COA

> Historique du premier lot. La clarification utilisateur vise le mail du
> responsable cote laboratoire. Le retrait du mail client decrit ci-dessous
> est annule par la [correction du 27 novembre 2026](correction-mail-responsable-laboratoire.md).

Le paragraphe 100 du texte de `AMELIORATIONS SENAITE LIMS.docx` demande de
supprimer l'adresse mail. Le gabarit Trimeta supprimait déjà les liens mail
des responsables, mais `render_info()` déléguait au bloc natif de
`senaite.impress`, qui affiche l'adresse du contact client.

La correction ajoute une option au bloc d'informations du contrôleur de
rapport : `include_contact_email`. Le gabarit COA Trimeta impose `False`.
L'adresse et le lien `mailto:` du contact client sont alors absents du HTML.
Le nom du client, le nom du contact, l'adresse postale, le téléphone, les
coordonnées du laboratoire et le QR code restent présents.

Les autres modèles utilisent la valeur native par défaut. Les contrôleurs de
rapport simple et multiple emploient le même bloc d'informations. Aucun style,
contact, destinataire de courriel ou réglage d'envoi n'est modifié.

Les trois tests ciblés rendent réellement le gabarit avec le moteur Zope et
vérifient le retrait de l'adresse et de son lien, la conservation des autres
informations et le fonctionnement du mode natif. `make test-pure` conserve ses
298 tests réussis. Le lanceur Plone complet reste indisponible dans l'image.

Cette correction s'applique aux nouveaux rendus du COA. Les PDF déjà publiés
restent inchangés ; aucun rapport historique n'est régénéré automatiquement.

Un contrôle avec le modèle de données de `senaite.impress` et la copie de la base
a également rendu le COA complet. L'adresse du contact est absente dans les
contrôleurs simple et multiple ; les autres coordonnées restent identiques.
Les empreintes des 29 PDF stockés sont identiques avant et après ce contrôle.
La transaction de vérification est annulée après lecture.

Le pied de page natif du laboratoire est conservé. Sur la copie vérifiée,
il n'affiche actuellement aucune adresse mail du laboratoire. Le texte du Word
ne précise pas si une telle adresse, lorsqu'elle est renseignée, doit également
être retirée ; ce point de présentation fait l'objet d'une clarification.
