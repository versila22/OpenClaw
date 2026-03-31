# LIMA — Analyse des données sources

## Sources récupérées

### 1. CSV Joueurs (cotisation-joueur-euse-2025-2026)
- **39 joueurs** inscrits via HelloAsso
- Colonnes : Référence commande, Date commande, Statut, Nom, Prénom, Carte adhérent, Nom/Prénom payeur, Email payeur, Moyen paiement, Tarif, Montant, Téléphone, Email, Date naissance, **Groupe de Jeu** (Match/Cabaret/vide=Loisir), Commentaires
- Tarifs : Cotisation match/cab = 160€ | Cotisation Loisir = 75€

### 2. CSV Adhérents (bulletin-adhesion-lima-2025-2026)
- **55 adhérents** inscrits via HelloAsso
- Colonnes supplémentaires vs joueurs : Adresse, Code Postal, Ville, **Commission**
- Tarif unique : Adhésion = 20€
- Commissions : Comm' Spec', Comm' Prog, Comm' Form', Comm' Adh', Comm' Comm', Aucune

### 3. PDF Alignement T3 (saison 2024-25)
- Grille d'affectation joueurs ↔ événements par trimestre
- **Rôles par événement** : JR (Joueur), DJ, MJ-MC (Maître de Jeu/Cérémonie), AR (Arbitre), COACH
- **2 sections** : Joueurs Cabarets (14) + Joueurs Matchs (15) + Staff (4)
- **10 événements** sur le T3 2024-25

### 4. Excel Calendrier saison 2025-2026
- Calendrier complet août 2025 → juillet 2026
- **Types d'événements identifiés** :
  - Entraînement spectacle (32 occurrences)
  - Entrainement Loisirs (19)
  - MATCH (6)
  - WELSH (8)
  - Cabaret (1)
  - GIFFARD (6 = lieu : salle au Giffard)
  - FORMATION (0 cette saison dans le calendrier initial)
  - Digital village (1 + "2 autres à venir")
  - Germoir (2)
  - AG (1)
  - Déplacement (8)

### 5. PDF Trombinoscope 2025-2026
- **50 membres** avec photos
- **Statuts** : A (Adhérent), C (Cabaret), L (Loisir), M (Match)
- **Bureau** : 2 Co-Prez (Maïlys + Ronan), 2 Co-Trésoriers (Vincent + Antoine), 1 Secrétaire (Élodie)
- **CA** : Romain, Élisabeth, Jérôme, Géraldine, Marie
- **Coachs** : Antoine (Gasnier), Emmanuelle (Landais)
- **Commissions** : Comadh, Comcom, Comform, Comprog, Comspec

## Observations clés

### Double inscription HelloAsso
- Un adhérent a **2 inscriptions** : 1 adhésion (20€) + 1 cotisation joueur (75-160€)
- Certains n'ont que l'adhésion (pas joueurs = statut A)
- Le **mail** est la clé de rapprochement entre les 2 CSV

### Hiérarchie des rôles
```
Bureau (Co-Prez, Co-Trez, Secrétaire)
  └── CA (Conseil d'Administration)
       └── Admin dans l'app
            └── Adhérent lambda
```

### Statuts membre
- **M** (Match) = joueur compétition, cotisation 160€
- **C** (Cabaret) = joueur spectacle, cotisation 160€
- **L** (Loisir) = joueur loisir, cotisation 75€
- **A** (Adhérent simple) = pas joueur, adhésion 20€ seulement

### Alignement = concept central
- Chaque trimestre, un admin crée une grille événements × joueurs
- Les admins **affectent** les joueurs aux événements avec un rôle (JR, DJ, MJ-MC, AR, COACH)
- Un joueur = 1 seul rôle par événement
- Les Cabarets et Matcheurs sont séparés dans la grille
