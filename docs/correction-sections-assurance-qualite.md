# Position des categories Assurance Qualite

Le Word demande sept categories pour les 41 champs facultatifs de
l'Assurance Qualite. Dans le formulaire de modification, le titre
« Validation et resultats » etait place avant les remarques, apres les
champs Validateur technique et Validation finale et signataire du rapport.
Ces deux champs apparaissaient donc dans la categorie Consommables.

`quality_sections.js` ne reconnaissait que les lignes de tableau et les
conteneurs `archetypes-fieldname-X`. Le ReferenceWidget natif utilise
directement l'identifiant du champ, precede de son libelle. Le script
reconnait maintenant ce conteneur et place le titre avant son libelle.
Les autres formes de widgets conservent leur traitement existant.

Le viewlet charge le script avec `?v=2` pour renouveler le cache navigateur.
Cette correction de placement ne modifie aucun champ ni aucune valeur.

Verification du 26 novembre 2026 sur VAN-0009 : sept titres, 41 champs
places entre les bons titres, dont les cinq champs de Validation et
resultats. Aucun marqueur obligatoire dans l'Assurance Qualite.
Reexecuter le script conserve les sept titres et toutes les valeurs du
formulaire, sans doublon. Aucun enregistrement d'echantillon effectue.

`make test-pure` : 311 tests reussis. `make test` tente : le lanceur Plone
complet reste absent de l'image. Le placement a ete verifie dans le DOM du
navigateur reel, avec les widgets SENAITE installes.
