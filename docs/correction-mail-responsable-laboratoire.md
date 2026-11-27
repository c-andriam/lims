# COA : masquer le mail personnel du responsable du laboratoire

Clarification utilisateur prise en compte le 27 novembre 2026 : le mail
a retirer est celui de la personne responsable cote laboratoire.
L'adresse du contact client et les coordonnees generales du laboratoire
ne sont pas concernees par cette demande.

## Correction

Le controleur du rapport retourne une copie des informations de l'auteur
avec un champ `email` vide pour le rendu. Les noms, identifiants et roles
restent disponibles. Si le nom complet manque, l'identifiant du compte
est utilise pour identifier le responsable sur les modeles natifs aussi.

Les gabarits SENAITE lisent ces informations dans la synthese et la section
Responsables. Le mail personnel n'est donc plus affiche dans ces deux
emplacements, pour les controleurs de rapport simple et multiple.
Les noms des autres responsables, fonctions, departements et signatures
conservent leurs rendus existants.

La suppression precedente du mail client est annulee. Le bloc de
coordonnees est de nouveau le bloc natif de senaite.impress, avec le mail
client. L'ancienne copie locale `coa/templates/info.pt` et son option
`include_contact_email` sont retirees. Le pied de page natif garde les
coordonnees generales du laboratoire, y compris son mail organisationnel.

Le filtrage est une presentation du rapport. Aucun compte, contact,
destinataire d'envoi ou parametre SMTP n'est modifie. Les PDF archives
restent intacts. Aucune migration de profil n'est necessaire.

## Verification

317 tests purs et 12 controles cibles reussis sur Python 2.7. Les controles
rendent les blocs natifs et verifient que le mail du client reste visible,
que le mail personnel est absent, que les noms et images de signature
sont conserves et que le dictionnaire du compte d'origine reste intact.

Un rendu complet sur la base isolee a compare quatre cas : COA Trimeta
publie, COA Trimeta provisoire, Default et MultiDefault. Avec des adresses
distinctes de recette, le mail du client et celui de l'organisation restent
dans le HTML et le mail personnel du responsable en est absent. Le modele
natif non surcharge sert de controle positif : il affiche encore ce mail.

Les valeurs temporaires des contacts sont annulees transactionnellement.
Le compte utilisateur et les empreintes des 29 PDF stockes sont conserves.
La suite Plone complete reste indisponible dans l'image locale.

Un PDF provisoire a aussi ete genere par le telechargement natif, sans
enregistrement de rapport ni envoi. Ses deux pages ont ete rendues et
controlees visuellement : mail client present, rubrique Responsables
sans mail personnel, decimales et codes-barres conserves. L'apercu local
`output/pdf/COA-ECH-DEMO-002-provisoire.pdf` porte la mention NON PUBLIE.
