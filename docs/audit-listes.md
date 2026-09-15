# Audit des listes : toute donnée existante doit s'afficher

Exigence du laboratoire : aucune colonne vide dans les tableaux du
logiciel, sauf quand la donnée elle-même n'existe pas.

Plusieurs colonnes annoncées comme « faites » ne s'affichaient en
réalité jamais. Cet audit vérifie donc chaque liste à partir de ce que
le serveur renvoie vraiment, et chaque colonne vide à partir de la
donnée source.

---

## Méthode

1. **Lister les tableaux** d'une page : chaque liste SENAITE déclare son
   adresse de données (`data-api_url`).
2. **Demander toutes les lignes** (`folderitems`, `pagesize` élevé). Un
   premier passage limité à la première page avait faussement signalé
   la colonne « Calcul » des services comme vide.
3. **Repérer les colonnes visibles entièrement vides** : ni valeur brute,
   ni HTML de remplacement.
4. **Vérifier chaque colonne vide à la source** (API JSON, objet par
   objet) : si aucun objet n'a la donnée, le vide est normal.
5. **Renseigner la donnée sur un objet de démonstration**, puis relancer
   l'audit : la colonne doit se remplir. C'est la seule façon de prouver
   qu'une donnée existante est bien affichée.

## Défauts trouvés et corrigés

| Liste | Défaut | Correctif |
|---|---|---|
| Échantillons (globale et client) | Colonnes « Code échantillon » et « Lot » jamais ajoutées : la liste interroge le `sample_catalog` sans `portal_type` | `listings/base.py` : type déduit du catalogue |
| Work Sheet | Colonne « Code échantillon » jamais ajoutée : la grille filtre sur `getWorksheetUID` sans `portal_type` | `listings/worksheets.py` |
| Rapports d'analyses | Colonne « Lot » vide : c'était le *Batch* natif, traduit « Lot » | vraie colonne « Lot » ; `Batch` masquée par défaut |
| Work Sheet | Colonne « Échéance » vide : bug de `senaite.core`, qui passe l'analyse au lieu de sa date | `worksheet/views.py` recalcule `getDueDate()` |
| Work Sheet Transposed | Export CSV sans résultats ni échantillons | voir `d13-export-work-sheet.md` |
| COA | E-mail de « Published by » encore affiché dans « Responsibles » | voir `lot4-coa.md` |

Chaque correctif a été vérifié sur l'instance locale, par une vraie
requête.

## Colonnes vérifiées en renseignant la donnée

| Liste | Colonnes |
|---|---|
| Clients | Adresse mail, Téléphone |
| Contacts du client | Adresse mail, téléphone professionnel, téléphone mobile |
| Contacts du laboratoire | Départements, Téléphone, Téléphone mobile |
| Services d'analyse | Méthodes, Unité, Calcul, Clé de tri |
| Calculs | Description |
| Types d'échantillon | Description, Dangereux, Matrice, Contenant par défaut |
| Catégories d'analyse | Département, Clé de tri |
| Départements | Téléphone du gestionnaire |
| Tableau de bord | Opérateur HPLC, Opérateur TH, Opérateur AW |
| Work Sheet (classique et Transposed) | Échéance, Code échantillon |

## Vides normaux constatés

La donnée n'existe pas sur l'instance de démonstration : incertitude,
spécification, pièces jointes, date de saisie et auteur d'un résultat
non soumis, modèle de Work Sheet, destinataires d'un rapport non envoyé,
descriptions non saisies, identifiant utilisateur d'un contact sans
compte.

## Limites

- **Colonnes booléennes** (« Dangereux », « Pré-conservé », « Caché ») :
  SENAITE n'affiche rien quand la valeur est *Non*. C'est le
  comportement natif, conservé.
- **Listes sans données sur la démo** (instruments, *Batch*) : leurs
  colonnes ne sont pas vérifiées.
- **Audit à rejouer sur le serveur réel**, avec ses vraies données :

  ```bash
  cd 2.6.0
  SENAITE_PASSWORD=... make audit-listes
  SENAITE_PASSWORD=... make audit-listes PAGES="/clients /samples"
  ```

  L'adresse vient de `.env` ; `SENAITE_URL` la remplace si besoin. Toute
  colonne signalée vide se vérifie ensuite à la source.
