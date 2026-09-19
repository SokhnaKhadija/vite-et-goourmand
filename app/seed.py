"""Alimentation de la base MongoDB : données de référence, compte admin, données de démo.

Toutes les fonctions sont idempotentes (relançables sans créer de doublons) :
- `initialiser_references()` et `creer_admin()` sont appelées à chaque démarrage de l'app ;
- `charger_demo()` est appelée uniquement par `init_db.py`.
"""
from .models import (Allergene, Horaire, Menu, Plat, Regime, Theme, Utilisateur)

THEMES = ['Noël', 'Pâques', 'Classique', 'Événement']

REGIMES = ['Classique', 'Végétarien', 'Vegan', 'Sans gluten', 'Sans lactose', 'Halal']

# 14 allergènes réglementaires
ALLERGENES = [
    'Gluten', 'Crustacés', 'Œufs', 'Poissons', 'Arachides', 'Soja',
    'Lait', 'Fruits à coque', 'Céleri', 'Moutarde', 'Graines de sésame',
    'Anhydride sulfureux et sulfites', 'Lupin', 'Mollusques',
]

# (jour, ouverture, fermeture) — None/None = fermé
HORAIRES = [
    ('Lundi',    '09:00', '18:00'),
    ('Mardi',    '09:00', '18:00'),
    ('Mercredi', '09:00', '18:00'),
    ('Jeudi',    '09:00', '18:00'),
    ('Vendredi', '09:00', '18:00'),
    ('Samedi',   '09:00', '14:00'),
    ('Dimanche', None,    None),
]

# ── Données de démonstration ─────────────────────────────────────────────────

PLATS_DEMO = [
    # (titre, type, description, [allergènes])
    ('Velouté de butternut', 'entree',
     'Velouté onctueux de courge butternut, crème fraîche et noix de muscade', []),
    ('Saumon gravlax', 'entree',
     "Saumon mariné à l'aneth et citron, blinis maison", ['Poissons', 'Gluten', 'Œufs']),
    ('Foie gras de canard mi-cuit', 'entree',
     'Foie gras artisanal, chutney de figues et pain brioché', ['Gluten', 'Lait']),
    ('Magret de canard aux cerises', 'plat',
     'Magret de canard rôti, sauce aux cerises et pommes sarladaises', []),
    ('Filet de bœuf en croûte', 'plat',
     'Filet de bœuf Wellington, sauce périgueux et légumes de saison', ['Gluten']),
    ('Risotto aux cèpes', 'plat',
     'Risotto crémeux aux cèpes et parmesan 36 mois (végétarien)', []),
    ('Bûche de Noël au chocolat', 'dessert',
     'Bûche de Noël maison, mousse chocolat noir, insert framboise',
     ['Œufs', 'Lait', 'Gluten', 'Fruits à coque']),
    ('Crème brûlée à la vanille', 'dessert',
     'Crème brûlée traditionnelle, vanille bourbon de Madagascar', ['Œufs', 'Lait']),
    ('Tarte aux fraises', 'dessert',
     'Tarte sablée, crème pâtissière, fraises Gariguette fraîches', ['Gluten', 'Œufs', 'Lait']),
]

MENUS_DEMO = [
    {
        'titre': 'Menu Noël Prestige',
        'description': "Un repas de Noël d'exception pour impressionner vos convives. "
                       "Produits nobles et saveurs festives.",
        'theme': 'Noël', 'regime': 'Classique',
        'nb_personnes_min': 8, 'prix_base': 480.00,
        'conditions': 'Commander au moins 7 jours avant la date de prestation. '
                      'Conservation entre 2°C et 4°C recommandée.',
        'stock': 15,
        'plats': ['Foie gras de canard mi-cuit', 'Filet de bœuf en croûte',
                  'Bûche de Noël au chocolat'],
    },
    {
        'titre': 'Menu Végétarien du Printemps',
        'description': 'Un voyage gustatif à travers les saveurs végétales de saison.',
        'theme': 'Pâques', 'regime': 'Végétarien',
        'nb_personnes_min': 6, 'prix_base': 240.00,
        'conditions': 'Commander au moins 5 jours avant la prestation.',
        'stock': 20,
        'plats': ['Velouté de butternut', 'Risotto aux cèpes', 'Tarte aux fraises'],
    },
    {
        'titre': 'Menu Classique Bordeaux',
        'description': 'Le grand classique de Vite & Gourmand, fidèle à la tradition '
                       'gastronomique bordelaise.',
        'theme': 'Classique', 'regime': 'Classique',
        'nb_personnes_min': 10, 'prix_base': 550.00,
        'conditions': 'Minimum 10 personnes requis. Livraison possible dans tout le département.',
        'stock': 10,
        'plats': ['Foie gras de canard mi-cuit', 'Magret de canard aux cerises',
                  'Crème brûlée à la vanille'],
    },
]


# ── Fonctions d'alimentation ─────────────────────────────────────────────────

def initialiser_references():
    """Crée thèmes, régimes, allergènes et horaires s'ils n'existent pas."""
    # upsert : atomique, sans doublon même si plusieurs processus démarrent en même temps
    for modele, libelles in ((Theme, THEMES), (Regime, REGIMES), (Allergene, ALLERGENES)):
        for libelle in libelles:
            modele.objects(libelle=libelle).update_one(
                set_on_insert__libelle=libelle, upsert=True)

    for ordre, (jour, ouverture, fermeture) in enumerate(HORAIRES):
        Horaire.objects(jour=jour).update_one(
            set_on_insert__ordre=ordre,
            set_on_insert__heure_ouverture=ouverture,
            set_on_insert__heure_fermeture=fermeture,
            set_on_insert__ferme=ouverture is None,
            upsert=True,
        )


def creer_admin(email: str, mot_de_passe: str):
    """Crée le compte administrateur initial s'il n'existe pas. Retourne True si créé."""
    email = email.strip().lower()
    if Utilisateur.objects(email=email).first():
        return False
    admin = Utilisateur(
        nom='Vite', prenom='José', email=email,
        telephone='0600000000', adresse='1 rue des Saveurs',
        ville='Bordeaux', code_postal='33000',
        role='administrateur', actif=True,
    )
    admin.set_password(mot_de_passe)
    admin.save()
    return True


def charger_demo():
    """Insère les plats et menus de démonstration (ignore ceux qui existent déjà).

    Retourne (nb_plats_créés, nb_menus_créés).
    """
    allergenes = {a.libelle: a for a in Allergene.objects}
    plats_crees = 0
    plats = {}
    for titre, type_plat, description, noms_allergenes in PLATS_DEMO:
        plat = Plat.objects(titre=titre).first()
        if plat is None:
            plat = Plat(titre=titre, type_plat=type_plat, description=description,
                        allergenes=[allergenes[n] for n in noms_allergenes]).save()
            plats_crees += 1
        plats[titre] = plat

    themes = {t.libelle: t for t in Theme.objects}
    regimes = {r.libelle: r for r in Regime.objects}
    menus_crees = 0
    for donnees in MENUS_DEMO:
        if Menu.objects(titre=donnees['titre']).first():
            continue
        Menu(
            titre=donnees['titre'],
            description=donnees['description'],
            theme=themes[donnees['theme']],
            regime=regimes[donnees['regime']],
            nb_personnes_min=donnees['nb_personnes_min'],
            prix_base=donnees['prix_base'],
            conditions=donnees['conditions'],
            stock=donnees['stock'],
            actif=True,
            plats=[plats[t] for t in donnees['plats']],
        ).save()
        menus_crees += 1
    return plats_crees, menus_crees
