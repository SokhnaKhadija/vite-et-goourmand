from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import bcrypt

db = SQLAlchemy()

# ─────────────────────────────────────────────
# Tables de jointure many-to-many
# ─────────────────────────────────────────────

menu_plat = db.Table(
    'menu_plat',
    db.Column('menu_id', db.Integer, db.ForeignKey('menu.id', ondelete='CASCADE'), primary_key=True),
    db.Column('plat_id', db.Integer, db.ForeignKey('plat.id', ondelete='CASCADE'), primary_key=True)
)

plat_allergene = db.Table(
    'plat_allergene',
    db.Column('plat_id', db.Integer, db.ForeignKey('plat.id', ondelete='CASCADE'), primary_key=True),
    db.Column('allergene_id', db.Integer, db.ForeignKey('allergene.id', ondelete='CASCADE'), primary_key=True)
)


# ─────────────────────────────────────────────
# Rôle
# ─────────────────────────────────────────────

class Role(db.Model):
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True)
    libelle = db.Column(db.String(50), unique=True, nullable=False)
    # 'utilisateur', 'employe', 'administrateur'


# ─────────────────────────────────────────────
# Utilisateur
# ─────────────────────────────────────────────

class Utilisateur(db.Model, UserMixin):
    __tablename__ = 'utilisateur'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    mot_de_passe_hash = db.Column(db.String(255), nullable=False)
    telephone = db.Column(db.String(20))
    adresse = db.Column(db.String(200))
    ville = db.Column(db.String(100))
    code_postal = db.Column(db.String(10))
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    role = db.relationship('Role', backref='utilisateurs')
    actif = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, mot_de_passe: str):
        self.mot_de_passe_hash = bcrypt.hashpw(
            mot_de_passe.encode('utf-8'), bcrypt.gensalt()
        ).decode('utf-8')

    def check_password(self, mot_de_passe: str) -> bool:
        return bcrypt.checkpw(
            mot_de_passe.encode('utf-8'),
            self.mot_de_passe_hash.encode('utf-8')
        )

    @property
    def est_admin(self):
        return self.role.libelle == 'administrateur'

    @property
    def est_employe(self):
        return self.role.libelle in ('employe', 'administrateur')

    def get_id(self):
        return str(self.id)


# ─────────────────────────────────────────────
# Token de réinitialisation de mot de passe
# ─────────────────────────────────────────────

class TokenReinitialisation(db.Model):
    __tablename__ = 'token_reinitialisation'
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)
    utilisateur = db.relationship('Utilisateur', backref='tokens')
    token = db.Column(db.String(200), unique=True, nullable=False)
    expiration = db.Column(db.DateTime, nullable=False)
    utilise = db.Column(db.Boolean, default=False)


# ─────────────────────────────────────────────
# Référentiels : Thème, Régime, Allergène
# ─────────────────────────────────────────────

class Theme(db.Model):
    __tablename__ = 'theme'
    id = db.Column(db.Integer, primary_key=True)
    libelle = db.Column(db.String(50), unique=True, nullable=False)
    # 'Noël', 'Pâques', 'Classique', 'Événement'


class Regime(db.Model):
    __tablename__ = 'regime'
    id = db.Column(db.Integer, primary_key=True)
    libelle = db.Column(db.String(50), unique=True, nullable=False)
    # 'Classique', 'Végétarien', 'Vegan', 'Sans gluten', 'Sans lactose'


class Allergene(db.Model):
    __tablename__ = 'allergene'
    id = db.Column(db.Integer, primary_key=True)
    libelle = db.Column(db.String(100), unique=True, nullable=False)


# ─────────────────────────────────────────────
# Plat
# ─────────────────────────────────────────────

class Plat(db.Model):
    __tablename__ = 'plat'
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False)
    type_plat = db.Column(db.String(20), nullable=False)  # 'entree', 'plat', 'dessert'
    description = db.Column(db.Text)
    photo = db.Column(db.String(200))
    allergenes = db.relationship('Allergene', secondary=plat_allergene, backref='plats')


# ─────────────────────────────────────────────
# Image de menu
# ─────────────────────────────────────────────

class ImageMenu(db.Model):
    __tablename__ = 'image_menu'
    id = db.Column(db.Integer, primary_key=True)
    menu_id = db.Column(db.Integer, db.ForeignKey('menu.id', ondelete='CASCADE'), nullable=False)
    chemin = db.Column(db.String(200), nullable=False)


# ─────────────────────────────────────────────
# Menu
# ─────────────────────────────────────────────

class Menu(db.Model):
    __tablename__ = 'menu'
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    theme_id = db.Column(db.Integer, db.ForeignKey('theme.id'), nullable=False)
    theme = db.relationship('Theme', backref='menus')
    regime_id = db.Column(db.Integer, db.ForeignKey('regime.id'), nullable=False)
    regime = db.relationship('Regime', backref='menus')
    nb_personnes_min = db.Column(db.Integer, nullable=False)
    prix_base = db.Column(db.Float, nullable=False)   # prix pour nb_personnes_min personnes
    conditions = db.Column(db.Text)
    stock = db.Column(db.Integer, default=0)
    actif = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    plats = db.relationship('Plat', secondary=menu_plat, backref='menus')
    images = db.relationship('ImageMenu', backref='menu', cascade='all, delete-orphan')

    @property
    def prix_par_personne(self):
        if self.nb_personnes_min and self.nb_personnes_min > 0:
            return self.prix_base / self.nb_personnes_min
        return 0

    def calcul_prix(self, nb_personnes: int) -> float:
        """Calcule le prix total pour un nombre de personnes donné."""
        prix = self.prix_par_personne * nb_personnes
        # Réduction de 10% si nb_personnes >= nb_personnes_min + 5
        if nb_personnes >= self.nb_personnes_min + 5:
            prix *= 0.90
        return round(prix, 2)

    @property
    def entrees(self):
        return [p for p in self.plats if p.type_plat == 'entree']

    @property
    def plats_principaux(self):
        return [p for p in self.plats if p.type_plat == 'plat']

    @property
    def desserts(self):
        return [p for p in self.plats if p.type_plat == 'dessert']


# ─────────────────────────────────────────────
# Commande
# ─────────────────────────────────────────────

STATUTS_COMMANDE = [
    ('en_attente', 'En attente'),
    ('accepte', 'Acceptée'),
    ('en_preparation', 'En préparation'),
    ('en_cours_livraison', 'En cours de livraison'),
    ('livre', 'Livrée'),
    ('en_attente_materiel', 'En attente du retour de matériel'),
    ('terminee', 'Terminée'),
    ('annulee', 'Annulée'),
]


class Commande(db.Model):
    __tablename__ = 'commande'
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(50), unique=True, nullable=False)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)
    utilisateur = db.relationship('Utilisateur', backref='commandes')
    menu_id = db.Column(db.Integer, db.ForeignKey('menu.id'), nullable=False)
    menu = db.relationship('Menu', backref='commandes')
    date_commande = db.Column(db.DateTime, default=datetime.utcnow)
    date_prestation = db.Column(db.Date, nullable=False)
    heure_livraison = db.Column(db.String(10), nullable=False)
    adresse_livraison = db.Column(db.String(200), nullable=False)
    ville_livraison = db.Column(db.String(100), nullable=False)
    code_postal_livraison = db.Column(db.String(10))
    nb_personnes = db.Column(db.Integer, nullable=False)
    prix_menu = db.Column(db.Float, nullable=False)
    prix_livraison = db.Column(db.Float, default=0.0)
    prix_total = db.Column(db.Float, nullable=False)
    statut = db.Column(db.String(50), default='en_attente', nullable=False)
    pret_materiel = db.Column(db.Boolean, default=False)
    motif_annulation = db.Column(db.Text)
    mode_contact_annulation = db.Column(db.String(20))  # 'gsm' ou 'mail'

    suivis = db.relationship('SuiviCommande', backref='commande',
                             cascade='all, delete-orphan', order_by='SuiviCommande.date_modification')

    @property
    def statut_libelle(self):
        return dict(STATUTS_COMMANDE).get(self.statut, self.statut)

    @property
    def peut_etre_modifiee(self):
        return self.statut == 'en_attente'

    @property
    def avis_donne(self):
        return len(self.avis) > 0


class SuiviCommande(db.Model):
    __tablename__ = 'suivi_commande'
    id = db.Column(db.Integer, primary_key=True)
    commande_id = db.Column(db.Integer, db.ForeignKey('commande.id', ondelete='CASCADE'), nullable=False)
    statut = db.Column(db.String(50), nullable=False)
    date_modification = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def statut_libelle(self):
        return dict(STATUTS_COMMANDE).get(self.statut, self.statut)


# ─────────────────────────────────────────────
# Avis
# ─────────────────────────────────────────────

class Avis(db.Model):
    __tablename__ = 'avis'
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)
    utilisateur = db.relationship('Utilisateur', backref='avis')
    commande_id = db.Column(db.Integer, db.ForeignKey('commande.id'), nullable=False)
    commande = db.relationship('Commande', backref='avis')
    note = db.Column(db.Integer, nullable=False)  # 1 à 5
    commentaire = db.Column(db.Text)
    statut = db.Column(db.String(20), default='en_attente', nullable=False)
    # 'en_attente', 'valide', 'refuse'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ─────────────────────────────────────────────
# Horaire
# ─────────────────────────────────────────────

class Horaire(db.Model):
    __tablename__ = 'horaire'
    id = db.Column(db.Integer, primary_key=True)
    jour = db.Column(db.String(20), nullable=False)
    # 'Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'
    heure_ouverture = db.Column(db.String(10))
    heure_fermeture = db.Column(db.String(10))
    ferme = db.Column(db.Boolean, default=False)
