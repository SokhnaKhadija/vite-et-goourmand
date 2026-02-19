# Documentation technique — Vite & Gourmand

## 1. Stack technique

| Composant | Technologie | Justification |
|-----------|-------------|---------------|
| **Backend** | Python 3.11 + Flask 3 | Léger, flexible, excellent écosystème Python |
| **ORM** | Flask-SQLAlchemy | Abstraction de la BDD, gestion des relations |
| **Authentification** | Flask-Login + bcrypt | Gestion de session sécurisée, hashage robuste |
| **BDD relationnelle** | PostgreSQL 16 | Fiabilité, contraintes d'intégrité, performances |
| **BDD NoSQL** | MongoDB | Statistiques flexibles, documents JSON natifs |
| **Frontend** | Bootstrap 5.3 + Jinja2 | Rendu côté serveur, accessibilité, réactivité |
| **Graphiques** | Chart.js | Bibliothèque légère, sans dépendance framework |

---

## 2. Architecture du projet

```
ViteEtGourmand/
├── app/
│   ├── __init__.py          # Factory Flask, initialisation BDD
│   ├── models.py            # Modèles SQLAlchemy (PostgreSQL)
│   ├── routes/
│   │   ├── main.py          # Accueil, contact, pages statiques
│   │   ├── auth.py          # Connexion, inscription, mot de passe
│   │   ├── menus.py         # Catalogue + API JSON de filtrage
│   │   ├── commandes.py     # Passage et calcul de commande
│   │   ├── utilisateur.py   # Espace client
│   │   ├── employe.py       # Espace employé (menus, plats, avis)
│   │   └── admin.py         # Espace administrateur
│   ├── utils/
│   │   ├── email.py         # Service email simulé (logs)
│   │   └── decorateurs.py   # Décorateurs de contrôle d'accès
│   ├── templates/           # Templates Jinja2 (HTML)
│   └── static/              # CSS, JS, uploads
├── config.py                # Configuration centralisée
├── run.py                   # Point d'entrée
├── requirements.txt
├── database.sql             # Schéma + données de démonstration
└── docs/
    └── architecture.md      # Ce fichier
```

---

## 3. Modèle Conceptuel de Données (MCD)

### Entités et relations

```
UTILISATEUR ──< COMMANDE >── MENU
    |                          |
    |                       MENU_PLAT
    |                          |
    |                         PLAT ──< PLAT_ALLERGENE >── ALLERGENE
    |
    └──< AVIS
           |
        COMMANDE

MENU ──> THEME
MENU ──> REGIME
MENU ──< IMAGE_MENU
COMMANDE ──< SUIVI_COMMANDE
UTILISATEUR ──> ROLE
UTILISATEUR ──< TOKEN_REINITIALISATION
```

### Tables principales

| Table | Description |
|-------|-------------|
| `utilisateur` | Clients, employés, administrateurs |
| `role` | utilisateur / employe / administrateur |
| `menu` | Menus proposés par Vite & Gourmand |
| `plat` | Entrées, plats, desserts réutilisables entre menus |
| `allergene` | 14 allergènes réglementaires (INCO) |
| `commande` | Commandes passées par les clients |
| `suivi_commande` | Historique des changements de statut |
| `avis` | Avis clients (soumis après commande terminée) |
| `horaire` | Horaires d'ouverture (lundi–dimanche) |
| `theme` | Thèmes des menus (Noël, Pâques, Classique, Événement) |
| `regime` | Régimes alimentaires (Végétarien, Vegan, etc.) |

---

## 4. Diagramme de cas d'utilisation

### Visiteur (non authentifié)
- Consulter la page d'accueil
- Parcourir et filtrer les menus
- Voir le détail d'un menu
- Créer un compte
- Se connecter
- Contacter l'entreprise
- Consulter les mentions légales / CGV

### Utilisateur (authentifié)
- Toutes les actions d'un visiteur
- Commander un menu
- Modifier / annuler une commande (avant acceptation)
- Suivre l'état d'une commande
- Consulter l'historique de commandes
- Modifier son profil
- Laisser un avis (après commande terminée)

### Employé
- Toutes les actions d'un utilisateur
- Gérer les menus (CRUD)
- Gérer les plats (CRUD)
- Gérer les horaires
- Traiter les commandes (changer les statuts)
- Valider / refuser les avis clients

### Administrateur
- Toutes les actions d'un employé
- Créer / désactiver des comptes employés
- Consulter les statistiques et le CA par menu (avec filtres)
- Visualiser le graphique comparatif des commandes par menu

---

## 5. Règles de gestion

### Calcul du prix
- **Prix par personne** = `prix_base / nb_personnes_min`
- **Prix menu** = `prix_par_personne × nb_personnes`
- **Réduction 10%** : si `nb_personnes ≥ nb_personnes_min + 5`
- **Livraison** : gratuite à Bordeaux, 15 € forfait hors Bordeaux (simplifié)

### Mot de passe
- Minimum 10 caractères
- Au moins : 1 majuscule, 1 minuscule, 1 chiffre, 1 caractère spécial
- Hashé avec bcrypt (facteur de coût 12)

### Statuts de commande
```
en_attente → accepte → en_preparation → en_cours_livraison → livre
                                                               ↓
                                              [si matériel prêté]
                                         en_attente_materiel → terminee
                                              [sinon]
                                                       livre → terminee
```
- `annulee` : accessible depuis `en_attente` uniquement (par employé ou client)

### Sécurité (RGPD)
- Les emails sont le seul identifiant (username)
- Pas de données personnelles dans les logs
- Réinitialisation de mot de passe par token UUID (validité 1h)
- Comptes employés désactivables sans suppression
- Consentement explicite requis à l'inscription

---

## 6. Collections MongoDB (stats)

```json
// Collection : stats_commandes
{
  "menu_id": 1,
  "menu_titre": "Menu Noël Prestige",
  "count": 42,
  "chiffre_affaires": 18540.00
}
```

Les données MongoDB sont mises à jour à chaque commande validée.

---

## 7. Accessibilité RGAA

Les mesures suivantes ont été implémentées :
- Attributs `lang="fr"` sur `<html>`
- Attributs `aria-label`, `aria-required`, `aria-live` sur les éléments interactifs
- Navigation au clavier : focus visible sur tous les éléments interactifs
- Contraste de couleurs conforme WCAG AA
- Liens d'évitement (`skip link`) vers le contenu principal
- Textes alternatifs (`alt`) sur toutes les images
- Structure sémantique HTML5 (`<nav>`, `<main>`, `<section>`, `<article>`, `<aside>`, `<footer>`)
- Labels explicites sur tous les champs de formulaire
- Messages d'erreur associés aux champs concernés
