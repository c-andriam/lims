# Export de la liste des rapports et libellés du COA

## Défaut reproduit

Sur la liste des rapports du client de démonstration, réactiver la colonne
« Info » fait apparaître dans le CSV le HTML de son icône. Le téléchargement
réel avant correction comporte 26 lignes concernées. Les guillemets HTML sont
échappés par le générateur CSV natif, ce qui peut aussi perturber la lecture
des colonnes dans un tableur.

## Correction

L'adaptateur `listings/reports.py` conserve le lien HTML dans `replace["Info"]`
pour l'affichage natif. La valeur brute `Info`, utilisée par l'export, devient
l'URL du même lien. Le lien relatif est résolu dans le contexte de la liste.
Une icône sans lien laisse une valeur vide ; une valeur déjà textuelle n'est
pas remplacée. La colonne reste masquée par défaut et peut être réactivée.

Le code échantillon, le lot, les données des rapports et les liens PDF ne sont
pas modifiés. Aucun changement de schéma ou migration GenericSetup n'est requis.

## Français du COA

Les libellés ajoutés lors du lot précédent sont complétés dans le catalogue :
« Designated signatory » devient « Signataire désigné » et « Not recorded »
devient « Non renseigné ». Les messages de valeur manquante passent par le
mécanisme de traduction ; les noms des personnes restent des données sans
traduction. Le COA complet et le catalogue français ont été vérifiés avec les
classes installées. L'historique, le champ qualité et les 29 PDF sont conservés.

## Contrainte de réception confirmée

Le 26 novembre 2026, l'utilisateur a explicitement demandé de conserver la
liste des températures à la réception de **15 à 31 °C**. Ce paramétrage est
maintenu ; aucune saisie libre ou nouvelle plage n'est introduite dans ce lot.

## Vérification

`make test-pure` : 308 tests réussis. Les 48 contrôles ciblés de listing et de
raccordement de validation passent sur Python 2.7. Le lanceur Plone complet
reste indisponible dans l'image locale.

Le CSV après correction a été réellement téléchargé avec « Info » visible :
26 lignes, 11 colonnes, aucune balise HTML et aucun décalage de colonnes.
Les 26 icônes natives sont conservées dans les données d'affichage et le premier
lien d'information exporté répond HTTP 200. Les préférences de colonnes de la
session de vérification ont ensuite été restaurées.
