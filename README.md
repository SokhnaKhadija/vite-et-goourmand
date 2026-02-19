# 🍽️ Vite & Gourmand — Application Web Traiteur

Application web complète pour le traiteur bordelais **Vite & Gourmand**.
Développée avec **Python / Flask**, **PostgreSQL**, **MongoDB** et **Bootstrap 5**.

---

## Prérequis

- Python 3.11+
- PostgreSQL 15+
- MongoDB 6+ (local ou [Atlas gratuit](https://www.mongodb.com/atlas))
- pip

---

## Installation en local

### 1. Cloner le dépôt

```bash
git clone https://github.com/votre-user/vite-et-gourmand.git
cd vite-et-gourmand
```

### 2. Créer un environnement virtuel

```bash
python -m venv venv
source venv/bin/activate       # Linux / macOS
venv\Scripts\activate          # Windows
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Configurer les variables d'environnement

```bash
cp .env.example .env
```

Éditez `.env` et renseignez vos valeurs :

```env
SECRET_KEY=votre-cle-secrete-tres-longue
DATABASE_URL=postgresql://postgres:motdepasse@localhost/vite_et_gourmand
MONGO_URI=mongodb://localhost:27017/
ADMIN_EMAIL=jose@viteetsourmand.fr
ADMIN_PASSWORD=Admin@VG2025!
```

### 5. Créer la base de données PostgreSQL

```bash
# Se connecter à PostgreSQL
psql -U postgres

# Dans psql :
CREATE DATABASE vite_et_gourmand;
\q

# Importer le schéma et les données de démo
psql -U postgres -d vite_et_gourmand -f database.sql
```

> **Note :** Le script `run.py` crée également les tables automatiquement via SQLAlchemy
> et initialise le compte administrateur si la base est vide.

### 6. Lancer l'application

```bash
python run.py
```

L'application est accessible sur [http://localhost:5000](http://localhost:5000)

---

## Comptes de démonstration

| Rôle | Email | Mot de passe |
|------|-------|-------------|
| Administrateur | `jose@viteetsourmand.fr` | `Admin@VG2025!` |
| Employé | Créer via l'espace admin | — |
| Utilisateur | Créer via l'inscription | — |

---

## Structure du projet

```
ViteEtGourmand/
├── app/
│   ├── __init__.py          # Factory Flask
│   ├── models.py            # Modèles SQLAlchemy
│   ├── routes/              # Blueprints Flask
│   ├── templates/           # Templates Jinja2
│   ├── static/
│   │   ├── css/style.css    # Styles personnalisés
│   │   ├── js/main.js       # JavaScript
│   │   └── uploads/         # Images uploadées (auto-créé)
│   └── utils/
│       ├── email.py         # Service email (simulé en logs)
│       └── decorateurs.py   # Contrôle d'accès par rôle
├── config.py                # Configuration
├── run.py                   # Point d'entrée
├── requirements.txt
├── database.sql             # Schéma SQL + données de démo
├── .env.example
└── docs/
    └── architecture.md      # Documentation technique complète
```

---

## Fonctionnalités

### Public (non authentifié)
- Page d'accueil avec avis clients validés
- Catalogue des menus avec filtrage dynamique (sans rechargement)
- Détail complet d'un menu
- Page de contact (formulaire → email simulé)
- Création de compte (email de bienvenue automatique)
- Connexion / réinitialisation de mot de passe par email

### Espace utilisateur
- Historique des commandes
- Modification / annulation de commande (avant acceptation)
- Suivi de l'état des commandes
- Modification du profil
- Avis client (après commande terminée)

### Espace employé
- Gestion complète des menus (CRUD + galerie d'images)
- Gestion des plats et des allergènes
- Gestion des horaires d'ouverture
- Traitement des commandes (mise à jour des statuts)
- Modération des avis clients

### Espace administrateur
- Toutes les fonctionnalités employé
- Création / désactivation de comptes employés
- Statistiques et CA par menu (filtres par période / menu)
- Graphiques comparatifs (données MongoDB + Chart.js)

---

## Technologies utilisées

| Composant | Version |
|-----------|---------|
| Python | 3.11+ |
| Flask | 3.0.3 |
| Flask-SQLAlchemy | 3.1.1 |
| Flask-Login | 0.6.3 |
| bcrypt | 4.1.3 |
| psycopg2 | 2.9.9 |
| PyMongo | 4.7.1 |
| PostgreSQL | 15+ |
| MongoDB | 6+ |
| Bootstrap | 5.3.3 |
| Chart.js | 4.4.3 |

---

## Sécurité

- Mots de passe hashés avec **bcrypt**
- Protection CSRF via Flask-WTF (tokens de formulaire)
- Contrôle d'accès par rôle (décorateurs personnalisés)
- Validation des données côté serveur
- Tokens de réinitialisation à usage unique (validité 1h)
- Respect du **RGPD** : consentement explicite, données minimales
- Conformité **RGAA** : accessibilité complète

---

## Emails simulés

En mode développement, les emails ne sont pas envoyés réellement.
Ils sont affichés dans la console et enregistrés dans `emails.log`.

Pour configurer un vrai SMTP, modifier `app/utils/email.py`.

---

## Licence

Projet réalisé dans le cadre d'un TP académique — Vite & Gourmand © 2025.
