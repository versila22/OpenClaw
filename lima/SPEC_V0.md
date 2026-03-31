# LIMA App — Spécification V0

## Stack

| Composant | Technologie |
|-----------|------------|
| Frontend | React + TypeScript + Tailwind + shadcn/ui (Lovable bootstrap → GitHub) |
| Backend | FastAPI (Python 3.12) |
| DB | PostgreSQL 16 |
| Auth | JWT (email/mdp) + bcrypt |
| Hébergement | Railway (backend + DB) / Vercel ou Railway (frontend) |
| LLM | Aucun en V0 |

---

## Modèle de données

### 1. `seasons` — Saisons
```sql
CREATE TABLE seasons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) NOT NULL,           -- "2025-2026"
    start_date DATE NOT NULL,            -- 2025-09-01
    end_date DATE NOT NULL,              -- 2026-08-31
    is_current BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

### 2. `members` — Membres
```sql
CREATE TABLE members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),          -- NULL tant que pas activé
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    date_of_birth DATE,
    address TEXT,
    postal_code VARCHAR(10),
    city VARCHAR(100),
    
    -- Rôle app
    app_role VARCHAR(20) NOT NULL DEFAULT 'member',  -- 'admin' | 'member'
    is_active BOOLEAN DEFAULT true,
    
    -- Activation
    activation_token VARCHAR(255),
    activation_expires_at TIMESTAMPTZ,
    
    -- Reset password
    reset_token VARCHAR(255),
    reset_expires_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

### 3. `member_seasons` — Inscription par saison
```sql
CREATE TABLE member_seasons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    member_id UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    season_id UUID NOT NULL REFERENCES seasons(id) ON DELETE CASCADE,
    
    -- Statut joueur
    player_status VARCHAR(10) NOT NULL DEFAULT 'A',  -- 'M' (Match) | 'C' (Cabaret) | 'L' (Loisir) | 'A' (Adhérent)
    
    -- Cotisation HelloAsso
    membership_fee DECIMAL(6,2),         -- 20.00
    player_fee DECIMAL(6,2),             -- 75.00 | 160.00 | NULL
    helloasso_ref VARCHAR(50),           -- Référence commande
    
    -- Rôle asso
    asso_role VARCHAR(50),               -- 'co_president' | 'co_treasurer' | 'secretary' | 'ca_member' | 'coach' | NULL
    
    created_at TIMESTAMPTZ DEFAULT now(),
    
    UNIQUE(member_id, season_id)
);
```

### 4. `commissions` — Commissions
```sql
CREATE TABLE commissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(20) UNIQUE NOT NULL,    -- 'comspec', 'comprog', 'comform', 'comadh', 'comcom'
    name VARCHAR(100) NOT NULL,          -- 'Commission Spectacles'
    description TEXT
);
```

### 5. `member_commissions` — Affectation aux commissions
```sql
CREATE TABLE member_commissions (
    member_id UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    commission_id UUID NOT NULL REFERENCES commissions(id) ON DELETE CASCADE,
    season_id UUID NOT NULL REFERENCES seasons(id) ON DELETE CASCADE,
    PRIMARY KEY (member_id, commission_id, season_id)
);
```

### 6. `venues` — Lieux
```sql
CREATE TABLE venues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,          -- "Le Welsh", "Salle Giffard", "Le Germoir", "Digital Village"
    address TEXT,
    city VARCHAR(100),
    contact_info TEXT,                   -- Nom + tel du contact
    is_home BOOLEAN DEFAULT true,        -- true = Angers, false = déplacement
    created_at TIMESTAMPTZ DEFAULT now()
);
```

### 7. `events` — Événements
```sql
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    season_id UUID NOT NULL REFERENCES seasons(id) ON DELETE CASCADE,
    venue_id UUID REFERENCES venues(id),
    
    title VARCHAR(200) NOT NULL,         -- "Match MPT vs CITO (Nantes)"
    event_type VARCHAR(30) NOT NULL,     -- 'match' | 'cabaret' | 'training_show' | 'training_leisure' | 'welsh' | 'formation' | 'ag' | 'other'
    
    start_at TIMESTAMPTZ NOT NULL,
    end_at TIMESTAMPTZ,
    
    is_away BOOLEAN DEFAULT false,       -- Déplacement
    away_city VARCHAR(100),              -- "Nantes", "Metz", "Paris"
    away_opponent VARCHAR(200),          -- "CITO", "Le Minou", etc.
    
    notes TEXT,
    
    -- Visibilité
    visibility VARCHAR(20) DEFAULT 'all',  -- 'all' | 'match' | 'cabaret' | 'loisir' | 'admin'
    
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

### 8. `alignments` — Grilles d'alignement (trimestre)
```sql
CREATE TABLE alignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    season_id UUID NOT NULL REFERENCES seasons(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,          -- "Trimestre 3 - 2025-2026"
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'draft',  -- 'draft' | 'published'
    created_by UUID REFERENCES members(id),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

### 9. `alignment_events` — Événements dans un alignement
```sql
CREATE TABLE alignment_events (
    alignment_id UUID NOT NULL REFERENCES alignments(id) ON DELETE CASCADE,
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    sort_order INT DEFAULT 0,
    PRIMARY KEY (alignment_id, event_id)
);
```

### 10. `alignment_assignments` — Affectations joueur ↔ événement
```sql
CREATE TABLE alignment_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alignment_id UUID NOT NULL REFERENCES alignments(id) ON DELETE CASCADE,
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    member_id UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    
    role VARCHAR(10) NOT NULL,           -- 'JR' (joueur) | 'DJ' | 'MJ_MC' | 'AR' (arbitre) | 'COACH'
    
    created_at TIMESTAMPTZ DEFAULT now(),
    
    UNIQUE(alignment_id, event_id, member_id)
);
```

### 11. `show_plans` — Plans de spectacle (persistance du formulaire front)
```sql
CREATE TABLE show_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID REFERENCES events(id),
    created_by UUID NOT NULL REFERENCES members(id),
    
    title VARCHAR(200) NOT NULL,
    show_type VARCHAR(30) NOT NULL,      -- 'match' | 'cabaret' | 'catch' | 'other'
    theme VARCHAR(200),
    duration VARCHAR(10),                -- '1h' | '1h15' | '1h30' | '2h'
    venue_name VARCHAR(200),
    venue_contact VARCHAR(200),
    
    -- Données du formulaire (JSON flexible)
    config JSONB NOT NULL DEFAULT '{}',  -- joueurs, équipes, DJ count, contraintes, etc.
    
    -- Plan généré (Markdown)
    generated_plan TEXT,
    
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

---

## Index recommandés
```sql
CREATE INDEX idx_member_seasons_season ON member_seasons(season_id);
CREATE INDEX idx_member_seasons_member ON member_seasons(member_id);
CREATE INDEX idx_events_season ON events(season_id);
CREATE INDEX idx_events_start ON events(start_at);
CREATE INDEX idx_events_type ON events(event_type);
CREATE INDEX idx_alignment_assignments_event ON alignment_assignments(event_id);
CREATE INDEX idx_alignment_assignments_member ON alignment_assignments(member_id);
CREATE INDEX idx_show_plans_event ON show_plans(event_id);
```

---

## API Endpoints

### Auth
| Méthode | Route | Description | Accès |
|---------|-------|-------------|-------|
| POST | `/auth/login` | Login email/mdp → JWT | Public |
| POST | `/auth/activate` | Activer compte (token + nouveau mdp) | Public |
| POST | `/auth/forgot-password` | Demander reset mdp | Public |
| POST | `/auth/reset-password` | Reset mdp avec token | Public |
| GET | `/auth/me` | Profil connecté | Auth |
| PUT | `/auth/me` | Modifier son profil | Auth |
| PUT | `/auth/me/password` | Changer son mdp | Auth |

### Members (admin)
| Méthode | Route | Description | Accès |
|---------|-------|-------------|-------|
| GET | `/members` | Liste des membres (saison courante) | Auth |
| GET | `/members/{id}` | Détail membre | Auth |
| POST | `/members/import` | Import CSV HelloAsso (adhérents + joueurs) | Admin |
| POST | `/members` | Créer un membre manuellement | Admin |
| PUT | `/members/{id}` | Modifier un membre | Admin |
| DELETE | `/members/{id}` | Désactiver un membre | Admin |
| POST | `/members/{id}/resend-activation` | Renvoyer mail activation | Admin |
| PUT | `/members/{id}/role` | Changer app_role (admin/member) | Admin |

### Seasons (admin)
| Méthode | Route | Description | Accès |
|---------|-------|-------------|-------|
| GET | `/seasons` | Liste des saisons | Auth |
| GET | `/seasons/current` | Saison courante | Auth |
| POST | `/seasons` | Créer une saison | Admin |
| PUT | `/seasons/{id}` | Modifier une saison | Admin |

### Events
| Méthode | Route | Description | Accès |
|---------|-------|-------------|-------|
| GET | `/events` | Liste événements (filtres: type, date, saison) | Auth |
| GET | `/events/{id}` | Détail événement | Auth |
| POST | `/events` | Créer un événement | Admin |
| PUT | `/events/{id}` | Modifier un événement | Admin |
| DELETE | `/events/{id}` | Supprimer un événement | Admin |
| POST | `/events/import-calendar` | Import Excel calendrier | Admin |

### Venues (admin)
| Méthode | Route | Description | Accès |
|---------|-------|-------------|-------|
| GET | `/venues` | Liste des lieux | Auth |
| POST | `/venues` | Créer un lieu | Admin |
| PUT | `/venues/{id}` | Modifier un lieu | Admin |

### Alignments (admin)
| Méthode | Route | Description | Accès |
|---------|-------|-------------|-------|
| GET | `/alignments` | Liste des grilles | Auth |
| GET | `/alignments/{id}` | Détail grille avec affectations | Auth |
| POST | `/alignments` | Créer une grille | Admin |
| PUT | `/alignments/{id}` | Modifier une grille (nom, dates, status) | Admin |
| DELETE | `/alignments/{id}` | Supprimer une grille | Admin |
| POST | `/alignments/{id}/events` | Ajouter événements à la grille | Admin |
| DELETE | `/alignments/{id}/events/{event_id}` | Retirer un événement | Admin |
| POST | `/alignments/{id}/assign` | Affecter un joueur (member_id, event_id, role) | Admin |
| DELETE | `/alignments/{id}/assign/{assignment_id}` | Retirer une affectation | Admin |
| PUT | `/alignments/{id}/publish` | Publier la grille (visible par tous) | Admin |

### Show Plans
| Méthode | Route | Description | Accès |
|---------|-------|-------------|-------|
| GET | `/show-plans` | Liste des plans (saison courante) | Auth |
| GET | `/show-plans/{id}` | Détail d'un plan | Auth |
| POST | `/show-plans` | Créer un plan | Admin |
| PUT | `/show-plans/{id}` | Modifier un plan | Admin |
| DELETE | `/show-plans/{id}` | Supprimer un plan | Admin |

### Commissions (admin)
| Méthode | Route | Description | Accès |
|---------|-------|-------------|-------|
| GET | `/commissions` | Liste des commissions | Auth |
| POST | `/commissions/{id}/members` | Affecter membre à commission | Admin |
| DELETE | `/commissions/{id}/members/{member_id}` | Retirer membre | Admin |

### Settings (admin)
| Méthode | Route | Description | Accès |
|---------|-------|-------------|-------|
| GET | `/settings` | Config asso | Admin |
| PUT | `/settings` | Modifier config | Admin |

---

## Flux Import CSV HelloAsso

1. Admin uploade les 2 CSV (adhérents + joueurs)
2. Backend parse, normalise les noms (trim, casse)
3. **Rapprochement par email** → fusionne adhérent + joueur
4. Pour chaque membre :
   - Crée ou met à jour `members` (email unique)
   - Crée `member_seasons` avec player_status déduit du tarif
   - Crée `member_commissions` si commission renseignée
5. Envoie un **email d'activation** avec token unique
6. Retourne un rapport : créés / mis à jour / erreurs

## Flux Calendrier

1. Admin uploade l'Excel calendrier
2. Backend parse les événements avec dates
3. Détecte le type via mots-clés : "Match", "Entraînement", "WELSH", "GIFFARD", etc.
4. Crée les `events` + associe les `venues` existants
5. Retourne rapport : créés / doublons ignorés

## Flux Alignement

1. Admin crée une grille (nom, dates début/fin)
2. Admin sélectionne les événements de la période
3. Vue grille : colonnes = événements, lignes = joueurs (séparés Cabaret/Match)
4. Admin clique sur une cellule → assigne un rôle (JR, DJ, MJ_MC, AR, COACH)
5. Admin publie → visible par tous les adhérents
6. Adhérent connecté voit sa ligne en surbrillance

---

## V1/V2 (hors scope V0)
- Génération de plans par LLM (Gemini Flash)
- Plans partagés entre orga/joueurs
- Casting intelligent / niveaux joueurs
- Gestion des disponibilités joueurs
- Notifications (email/push)
- Intégration Google Calendar
- Préférences utilisateur
