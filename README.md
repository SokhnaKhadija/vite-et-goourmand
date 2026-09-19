# 🍽️ Vite & Gourmand — Application Web Traiteur

Application web complète pour le traiteur bordelais **Vite & Gourmand**.
Développée avec **Python / Flask**, **MongoDB** (base de données unique) et **Bootstrap 5**.

---

## Prérequis

- Python 3.11+
- MongoDB 6+ (local ou [Atlas gratuit](https://www.mongodb.com/atlas))
- pip

---

## Installation en local

### 1. Cloner le dépôt

```bash
git clone https://github.com/SokhnaKhadija/vite-et-gourmand.git
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

Éditez `.env` et renseignez vos valeurs. `SECRET_KEY`, `MONGO_URI`, `ADMIN_EMAIL` et
`ADMIN_PASSWORD` sont **obligatoires** (aucune valeur par défaut dans le code) :

| Variable | Rôle | Défaut |
|----------|------|--------|
| `SECRET_KEY` | Clé de signature des sessions | — (obligatoire) |
| `MONGO_URI` | URI de connexion MongoDB (local ou Atlas) | — (obligatoire) |
| `MONGO_DBNAME` | Nom de la base | `vite_et_gourmand` |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | Compte administrateur initial | — (obligatoire) |
| `FLASK_HOST` / `FLASK_PORT` / `FLASK_DEBUG` | Serveur de développement | `127.0.0.1` / `5001` / `true` |
| `APP_BASE_URL` | URL utilisée dans les liens des e-mails | `http://localhost:5001` |
| `CONTACT_EMAIL` | Destinataire du formulaire de contact | `contact@viteetsourmand.fr` |
| `MAIL_LOG_FILE` | Fichier des e-mails simulés | `emails.log` |
| `MAX_UPLOAD_MB` | Taille maximale d'un upload | `16` |
| `VILLE_LIVRAISON_GRATUITE` | Ville où la livraison est gratuite | `Bordeaux` |
| `FRAIS_LIVRAISON_HORS_ZONE` | Forfait de livraison ailleurs (€) | `15` |

### 5. Initialiser la base de données MongoDB

Assurez-vous que MongoDB est démarré, puis lancez le script d'initialisation. Il crée les collections et
leurs index, puis alimente la base : thèmes, régimes, allergènes, horaires, compte administrateur et
données de démonstration (9 plats, 3 menus).

```bash
python init_db.py              # initialise / complète la base (relançable sans doublons)
python init_db.py --reset      # supprime la base puis la recrée (confirmation demandée)
python init_db.py --sans-demo  # sans les plats et menus de démonstration
```

> **Note :** au démarrage, `run.py` crée aussi les données de référence et le compte administrateur
> s'ils sont absents, mais pas les données de démonstration.

### 6. Lancer l'application

```bash
python run.py
```

L'application est accessible sur [http://localhost:5001](http://localhost:5001)
(port modifiable via `FLASK_PORT` dans `.env`)

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
│   ├── models.py            # Documents MongoEngine (collections MongoDB)
│   ├── seed.py              # Alimentation : références, admin, données de démo
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
├── init_db.py               # Script d'initialisation de la base MongoDB
├── requirements.txt
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
- Graphiques comparatifs (agrégations MongoDB + Chart.js)

---

## Technologies utilisées

| Composant | Version |
|-----------|---------|
| Python | 3.11+ |
| Flask | 3.0.3 |
| MongoEngine | 0.29.3 |
| Flask-Login | 0.6.3 |
| bcrypt | 4.1.3 |
| PyMongo | 4.7.1 |
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

Projet réalisé dans le cadre d'un TP académique — Vite & Gourmand © 2026.
