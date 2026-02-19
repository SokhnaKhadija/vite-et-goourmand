-- ════════════════════════════════════════════════════════════
-- Vite & Gourmand — Script SQL complet
-- Base de données : PostgreSQL
-- Création des tables + données initiales de test
-- ════════════════════════════════════════════════════════════

-- Supprimer les tables si elles existent (ordre inverse des dépendances)
DROP TABLE IF EXISTS token_reinitialisation CASCADE;
DROP TABLE IF EXISTS suivi_commande CASCADE;
DROP TABLE IF EXISTS avis CASCADE;
DROP TABLE IF EXISTS commande CASCADE;
DROP TABLE IF EXISTS image_menu CASCADE;
DROP TABLE IF EXISTS menu_plat CASCADE;
DROP TABLE IF EXISTS plat_allergene CASCADE;
DROP TABLE IF EXISTS plat CASCADE;
DROP TABLE IF EXISTS menu CASCADE;
DROP TABLE IF EXISTS allergene CASCADE;
DROP TABLE IF EXISTS regime CASCADE;
DROP TABLE IF EXISTS theme CASCADE;
DROP TABLE IF EXISTS horaire CASCADE;
DROP TABLE IF EXISTS utilisateur CASCADE;
DROP TABLE IF EXISTS role CASCADE;

-- ────────────────────────────────────────────────────────────
-- 1. Référentiels
-- ────────────────────────────────────────────────────────────

CREATE TABLE role (
    id      SERIAL PRIMARY KEY,
    libelle VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE theme (
    id      SERIAL PRIMARY KEY,
    libelle VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE regime (
    id      SERIAL PRIMARY KEY,
    libelle VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE allergene (
    id      SERIAL PRIMARY KEY,
    libelle VARCHAR(100) UNIQUE NOT NULL
);

-- ────────────────────────────────────────────────────────────
-- 2. Utilisateur
-- ────────────────────────────────────────────────────────────

CREATE TABLE utilisateur (
    id                SERIAL PRIMARY KEY,
    nom               VARCHAR(100) NOT NULL,
    prenom            VARCHAR(100) NOT NULL,
    email             VARCHAR(150) UNIQUE NOT NULL,
    mot_de_passe_hash VARCHAR(255) NOT NULL,
    telephone         VARCHAR(20),
    adresse           VARCHAR(200),
    ville             VARCHAR(100),
    code_postal       VARCHAR(10),
    role_id           INTEGER NOT NULL REFERENCES role(id),
    actif             BOOLEAN NOT NULL DEFAULT TRUE,
    created_at        TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_utilisateur_email ON utilisateur(email);

-- ────────────────────────────────────────────────────────────
-- 3. Token de réinitialisation
-- ────────────────────────────────────────────────────────────

CREATE TABLE token_reinitialisation (
    id               SERIAL PRIMARY KEY,
    utilisateur_id   INTEGER NOT NULL REFERENCES utilisateur(id) ON DELETE CASCADE,
    token            VARCHAR(200) UNIQUE NOT NULL,
    expiration       TIMESTAMP NOT NULL,
    utilise          BOOLEAN NOT NULL DEFAULT FALSE
);

-- ────────────────────────────────────────────────────────────
-- 4. Plat
-- ────────────────────────────────────────────────────────────

CREATE TABLE plat (
    id          SERIAL PRIMARY KEY,
    titre       VARCHAR(200) NOT NULL,
    type_plat   VARCHAR(20) NOT NULL CHECK (type_plat IN ('entree', 'plat', 'dessert')),
    description TEXT,
    photo       VARCHAR(200)
);

CREATE TABLE plat_allergene (
    plat_id     INTEGER NOT NULL REFERENCES plat(id) ON DELETE CASCADE,
    allergene_id INTEGER NOT NULL REFERENCES allergene(id) ON DELETE CASCADE,
    PRIMARY KEY (plat_id, allergene_id)
);

-- ────────────────────────────────────────────────────────────
-- 5. Menu
-- ────────────────────────────────────────────────────────────

CREATE TABLE menu (
    id                  SERIAL PRIMARY KEY,
    titre               VARCHAR(200) NOT NULL,
    description         TEXT,
    theme_id            INTEGER NOT NULL REFERENCES theme(id),
    regime_id           INTEGER NOT NULL REFERENCES regime(id),
    nb_personnes_min    INTEGER NOT NULL CHECK (nb_personnes_min >= 1),
    prix_base           DOUBLE PRECISION NOT NULL CHECK (prix_base >= 0),
    conditions          TEXT,
    stock               INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    actif               BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE menu_plat (
    menu_id INTEGER NOT NULL REFERENCES menu(id) ON DELETE CASCADE,
    plat_id INTEGER NOT NULL REFERENCES plat(id) ON DELETE CASCADE,
    PRIMARY KEY (menu_id, plat_id)
);

CREATE TABLE image_menu (
    id      SERIAL PRIMARY KEY,
    menu_id INTEGER NOT NULL REFERENCES menu(id) ON DELETE CASCADE,
    chemin  VARCHAR(200) NOT NULL
);

-- ────────────────────────────────────────────────────────────
-- 6. Commande
-- ────────────────────────────────────────────────────────────

CREATE TABLE commande (
    id                       SERIAL PRIMARY KEY,
    numero                   VARCHAR(50) UNIQUE NOT NULL,
    utilisateur_id           INTEGER NOT NULL REFERENCES utilisateur(id),
    menu_id                  INTEGER NOT NULL REFERENCES menu(id),
    date_commande            TIMESTAMP NOT NULL DEFAULT NOW(),
    date_prestation          DATE NOT NULL,
    heure_livraison          VARCHAR(10) NOT NULL,
    adresse_livraison        VARCHAR(200) NOT NULL,
    ville_livraison          VARCHAR(100) NOT NULL,
    code_postal_livraison    VARCHAR(10),
    nb_personnes             INTEGER NOT NULL CHECK (nb_personnes >= 1),
    prix_menu                DOUBLE PRECISION NOT NULL,
    prix_livraison           DOUBLE PRECISION NOT NULL DEFAULT 0,
    prix_total               DOUBLE PRECISION NOT NULL,
    statut                   VARCHAR(50) NOT NULL DEFAULT 'en_attente',
    pret_materiel            BOOLEAN NOT NULL DEFAULT FALSE,
    motif_annulation         TEXT,
    mode_contact_annulation  VARCHAR(20)
);

CREATE INDEX idx_commande_statut ON commande(statut);
CREATE INDEX idx_commande_utilisateur ON commande(utilisateur_id);

CREATE TABLE suivi_commande (
    id                  SERIAL PRIMARY KEY,
    commande_id         INTEGER NOT NULL REFERENCES commande(id) ON DELETE CASCADE,
    statut              VARCHAR(50) NOT NULL,
    date_modification   TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ────────────────────────────────────────────────────────────
-- 7. Avis
-- ────────────────────────────────────────────────────────────

CREATE TABLE avis (
    id              SERIAL PRIMARY KEY,
    utilisateur_id  INTEGER NOT NULL REFERENCES utilisateur(id),
    commande_id     INTEGER NOT NULL REFERENCES commande(id),
    note            SMALLINT NOT NULL CHECK (note BETWEEN 1 AND 5),
    commentaire     TEXT,
    statut          VARCHAR(20) NOT NULL DEFAULT 'en_attente',
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ────────────────────────────────────────────────────────────
-- 8. Horaires
-- ────────────────────────────────────────────────────────────

CREATE TABLE horaire (
    id               SERIAL PRIMARY KEY,
    jour             VARCHAR(20) UNIQUE NOT NULL,
    heure_ouverture  VARCHAR(10),
    heure_fermeture  VARCHAR(10),
    ferme            BOOLEAN NOT NULL DEFAULT FALSE
);

-- ════════════════════════════════════════════════════════════
-- DONNÉES INITIALES
-- ════════════════════════════════════════════════════════════

-- Rôles
INSERT INTO role (libelle) VALUES ('utilisateur'), ('employe'), ('administrateur');

-- Thèmes
INSERT INTO theme (libelle) VALUES ('Noël'), ('Pâques'), ('Classique'), ('Événement');

-- Régimes
INSERT INTO regime (libelle) VALUES
    ('Classique'), ('Végétarien'), ('Vegan'), ('Sans gluten'), ('Sans lactose'), ('Halal');

-- Allergènes (14 allergènes réglementaires)
INSERT INTO allergene (libelle) VALUES
    ('Gluten'), ('Crustacés'), ('Œufs'), ('Poissons'), ('Arachides'), ('Soja'),
    ('Lait'), ('Fruits à coque'), ('Céleri'), ('Moutarde'), ('Graines de sésame'),
    ('Anhydride sulfureux et sulfites'), ('Lupin'), ('Mollusques');

-- Horaires (lun–dim)
INSERT INTO horaire (jour, heure_ouverture, heure_fermeture, ferme) VALUES
    ('Lundi',    '09:00', '18:00', FALSE),
    ('Mardi',    '09:00', '18:00', FALSE),
    ('Mercredi', '09:00', '18:00', FALSE),
    ('Jeudi',    '09:00', '18:00', FALSE),
    ('Vendredi', '09:00', '18:00', FALSE),
    ('Samedi',   '09:00', '14:00', FALSE),
    ('Dimanche', NULL,    NULL,    TRUE);

-- Compte administrateur (José)
-- Mot de passe haché : Admin@VG2025!
-- ⚠ Ce hash est un exemple, la vraie valeur est générée par bcrypt au démarrage de l'app.
-- Pour l'environnement de test, utilisez le script run.py qui crée automatiquement le compte.

-- ────────────────────────────────────────────────────────────
-- Données de démonstration
-- ────────────────────────────────────────────────────────────

-- Plats
INSERT INTO plat (titre, type_plat, description) VALUES
    ('Velouté de butternut', 'entree', 'Velouté onctueux de courge butternut, crème fraîche et noix de muscade'),
    ('Saumon gravlax', 'entree', 'Saumon mariné à l''aneth et citron, blinis maison'),
    ('Foie gras de canard mi-cuit', 'entree', 'Foie gras artisanal, chutney de figues et pain brioché'),
    ('Magret de canard aux cerises', 'plat', 'Magret de canard rôti, sauce aux cerises et pommes sarladaises'),
    ('Filet de bœuf en croûte', 'plat', 'Filet de bœuf Wellington, sauce périgueux et légumes de saison'),
    ('Risotto aux cèpes', 'plat', 'Risotto crémeux aux cèpes et parmesan 36 mois (végétarien)'),
    ('Bûche de Noël au chocolat', 'dessert', 'Bûche de Noël maison, mousse chocolat noir, insert framboise'),
    ('Crème brûlée à la vanille', 'dessert', 'Crème brûlée traditionnelle, vanille bourbon de Madagascar'),
    ('Tarte aux fraises', 'dessert', 'Tarte sablée, crème pâtissière, fraises Gariguette fraîches');

-- Allergènes sur les plats
INSERT INTO plat_allergene (plat_id, allergene_id)
SELECT p.id, a.id FROM plat p, allergene a
WHERE (p.titre = 'Saumon gravlax' AND a.libelle IN ('Poissons', 'Gluten', 'Œufs'))
   OR (p.titre = 'Foie gras de canard mi-cuit' AND a.libelle IN ('Gluten', 'Lait'))
   OR (p.titre = 'Filet de bœuf en croûte' AND a.libelle IN ('Gluten'))
   OR (p.titre = 'Bûche de Noël au chocolat' AND a.libelle IN ('Œufs', 'Lait', 'Gluten', 'Fruits à coque'))
   OR (p.titre = 'Crème brûlée à la vanille' AND a.libelle IN ('Œufs', 'Lait'))
   OR (p.titre = 'Tarte aux fraises' AND a.libelle IN ('Gluten', 'Œufs', 'Lait'));

-- Menus
INSERT INTO menu (titre, description, theme_id, regime_id, nb_personnes_min, prix_base, conditions, stock, actif)
VALUES
(
    'Menu Noël Prestige',
    'Un repas de Noël d''exception pour impressionner vos convives. Produits nobles et saveurs festives.',
    (SELECT id FROM theme WHERE libelle = 'Noël'),
    (SELECT id FROM regime WHERE libelle = 'Classique'),
    8, 480.00,
    'Commander au moins 7 jours avant la date de prestation. Conservation entre 2°C et 4°C recommandée.',
    15, TRUE
),
(
    'Menu Végétarien du Printemps',
    'Un voyage gustatif à travers les saveurs végétales de saison.',
    (SELECT id FROM theme WHERE libelle = 'Pâques'),
    (SELECT id FROM regime WHERE libelle = 'Végétarien'),
    6, 240.00,
    'Commander au moins 5 jours avant la prestation.',
    20, TRUE
),
(
    'Menu Classique Bordeaux',
    'Le grand classique de Vite & Gourmand, fidèle à la tradition gastronomique bordelaise.',
    (SELECT id FROM theme WHERE libelle = 'Classique'),
    (SELECT id FROM regime WHERE libelle = 'Classique'),
    10, 550.00,
    'Minimum 10 personnes requis. Livraison possible dans tout le département.',
    10, TRUE
);

-- Association menus ↔ plats
INSERT INTO menu_plat (menu_id, plat_id)
SELECT m.id, p.id FROM menu m, plat p
WHERE (m.titre = 'Menu Noël Prestige' AND p.titre IN ('Foie gras de canard mi-cuit', 'Filet de bœuf en croûte', 'Bûche de Noël au chocolat'))
   OR (m.titre = 'Menu Végétarien du Printemps' AND p.titre IN ('Velouté de butternut', 'Risotto aux cèpes', 'Tarte aux fraises'))
   OR (m.titre = 'Menu Classique Bordeaux' AND p.titre IN ('Foie gras de canard mi-cuit', 'Magret de canard aux cerises', 'Crème brûlée à la vanille'));
