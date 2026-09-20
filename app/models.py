from datetime import datetime

import bcrypt
from bson import ObjectId
from flask import abort
from flask_login import UserMixin
from mongoengine import (
    Document, EmbeddedDocument,
    StringField, IntField, FloatField, BooleanField, DateTimeField, DateField,
    ListField, ReferenceField, EmbeddedDocumentListField, ObjectIdField,
    DENY, PULL, CASCADE, ValidationError,
)

# Modèle de données MongoDB (MongoEngine)
#
#  - Les tables de jointure SQL (menu_plat, plat_allergene) deviennent des listes
#    de références dans `Menu.plats` et `Plat.allergenes`.
#  - Les entités qui n'existent que pour leur parent sont *embarquées* :
#    `Menu.images` et `Commande.suivis`.
#  - Le rôle n'est plus une table : c'est un champ `Utilisateur.role`.
#  - Les clés étrangères deviennent des `ReferenceField` ; `reverse_delete_rule`
#    remplace les ON DELETE de PostgreSQL (DENY = refuser, PULL = retirer de la liste,
#    CASCADE = supprimer aussi les documents liés).


# ─────────────────────────────────────────────
# Utilitaires d'accès aux documents
# ─────────────────────────────────────────────

def charger(modele, identifiant):
    """Retourne le document dont l'id est `identifiant` (str ou ObjectId), ou None.

    Tolère les identifiants invalides (ex. URL bricolée) au lieu de lever une erreur.
    """
    if not identifiant:
        return None
    try:
        return modele.objects(id=identifiant).first()
    except (ValidationError, TypeError):
        return None


def charger_ou_404(modele, identifiant):
    document = charger(modele, identifiant)
    if document is None:
        abort(404)
    return document


def convertir_ids(valeurs):
    """Convertit une liste de chaînes en ObjectId en ignorant les valeurs invalides."""
    return [ObjectId(v) for v in valeurs if ObjectId.is_valid(v)]


# ─────────────────────────────────────────────
# Utilisateur
# ─────────────────────────────────────────────

ROLES = ('utilisateur', 'employe', 'administrateur')


class Utilisateur(Document, UserMixin):
    meta = {'collection': 'utilisateur'}

    nom = StringField(required=True, max_length=100)
    prenom = StringField(required=True, max_length=100)
    email = StringField(required=True, unique=True, max_length=150)
    mot_de_passe_hash = StringField(required=True, max_length=255)
    telephone = StringField(max_length=20)
    adresse = StringField(max_length=200)
    ville = StringField(max_length=100)
    code_postal = StringField(max_length=10)
    role = StringField(required=True, choices=ROLES, default='utilisateur')
    actif = BooleanField(required=True, default=True)
    created_at = DateTimeField(default=datetime.utcnow)

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
        return self.role == 'administrateur'

    @property
    def est_employe(self):
        return self.role in ('employe', 'administrateur')

    def get_id(self):
        return str(self.id)


# ─────────────────────────────────────────────
# Token de réinitialisation de mot de passe
# ─────────────────────────────────────────────

class TokenReinitialisation(Document):
    meta = {
        'collection': 'token_reinitialisation',
        'indexes': [
            # Index TTL : MongoDB supprime automatiquement le token à son expiration
            {'fields': ['expiration'], 'expireAfterSeconds': 0},
        ],
    }

    utilisateur = ReferenceField(Utilisateur, required=True, reverse_delete_rule=CASCADE)
    token = StringField(required=True, unique=True, max_length=200)
    expiration = DateTimeField(required=True)
    utilise = BooleanField(default=False)


# ─────────────────────────────────────────────
# Référentiels : Thème, Régime, Allergène
# ─────────────────────────────────────────────

class Theme(Document):
    meta = {'collection': 'theme'}
    libelle = StringField(required=True, unique=True, max_length=50)
    # 'Noël', 'Pâques', 'Classique', 'Événement'


class Regime(Document):
    meta = {'collection': 'regime'}
    libelle = StringField(required=True, unique=True, max_length=50)
    # 'Classique', 'Végétarien', 'Vegan', 'Sans gluten', 'Sans lactose', 'Halal'


class Allergene(Document):
    meta = {'collection': 'allergene'}
    libelle = StringField(required=True, unique=True, max_length=100)


# ─────────────────────────────────────────────
# Plat
# ─────────────────────────────────────────────

class Plat(Document):
    meta = {'collection': 'plat'}

    titre = StringField(required=True, max_length=200)
    type_plat = StringField(required=True, choices=('entree', 'plat', 'dessert'))
    description = StringField()
    photo = StringField(max_length=200)
    allergenes = ListField(ReferenceField(Allergene, reverse_delete_rule=PULL))


# ─────────────────────────────────────────────
# Menu (avec ses images embarquées)
# ─────────────────────────────────────────────

class ImageMenu(EmbeddedDocument):
    # Identifiant propre : nécessaire pour supprimer une image précise depuis l'interface
    id = ObjectIdField(default=ObjectId)
    chemin = StringField(required=True, max_length=200)


class Menu(Document):
    meta = {
        'collection': 'menu',
        'indexes': ['actif', 'theme', 'regime', '-created_at'],
    }

    titre = StringField(required=True, max_length=200)
    description = StringField()
    theme = ReferenceField(Theme, required=True, reverse_delete_rule=DENY)
    regime = ReferenceField(Regime, required=True, reverse_delete_rule=DENY)
    nb_personnes_min = IntField(required=True, min_value=1)
    prix_base = FloatField(required=True, min_value=0)   # prix pour nb_personnes_min personnes
    conditions = StringField()
    # Pas de min_value : MongoEngine l'appliquerait aussi à l'opérande de dec__stock.
    # Le stock reste >= 0 grâce au filtre `stock__gt=0` des décrémentations atomiques.
    stock = IntField(default=0)
    actif = BooleanField(required=True, default=True)
    created_at = DateTimeField(default=datetime.utcnow)

    plats = ListField(ReferenceField(Plat, reverse_delete_rule=PULL))
    images = EmbeddedDocumentListField(ImageMenu)

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
# Commande (avec son historique de statuts embarqué)
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


class SuiviCommande(EmbeddedDocument):
    statut = StringField(required=True, max_length=50)
    date_modification = DateTimeField(default=datetime.utcnow)

    @property
    def statut_libelle(self):
        return dict(STATUTS_COMMANDE).get(self.statut, self.statut)


class Commande(Document):
    meta = {
        'collection': 'commande',
        'indexes': ['statut', 'utilisateur', '-date_commande'],
    }

    numero = StringField(required=True, unique=True, max_length=50)
    utilisateur = ReferenceField(Utilisateur, required=True, reverse_delete_rule=DENY)
    menu = ReferenceField(Menu, required=True, reverse_delete_rule=DENY)
    date_commande = DateTimeField(default=datetime.utcnow)
    date_prestation = DateField(required=True)
    heure_livraison = StringField(required=True, max_length=10)
    adresse_livraison = StringField(required=True, max_length=200)
    ville_livraison = StringField(required=True, max_length=100)
    code_postal_livraison = StringField(max_length=10)
    nb_personnes = IntField(required=True, min_value=1)
    prix_menu = FloatField(required=True)
    prix_livraison = FloatField(default=0.0)
    prix_total = FloatField(required=True)
    statut = StringField(required=True, default='en_attente', max_length=50)
    pret_materiel = BooleanField(default=False)
    motif_annulation = StringField()
    mode_contact_annulation = StringField(max_length=20)  # 'gsm' ou 'mail'

    suivis = EmbeddedDocumentListField(SuiviCommande)

    @property
    def statut_libelle(self):
        return dict(STATUTS_COMMANDE).get(self.statut, self.statut)

    @property
    def peut_etre_modifiee(self):
        return self.statut == 'en_attente'

    @property
    def avis_donne(self):
        return Avis.objects(commande=self).count() > 0


# ─────────────────────────────────────────────
# Avis
# ─────────────────────────────────────────────

class Avis(Document):
    meta = {
        'collection': 'avis',
        'indexes': [('statut', '-created_at')],
    }

    utilisateur = ReferenceField(Utilisateur, required=True, reverse_delete_rule=DENY)
    # Unique : un seul avis par commande
    commande = ReferenceField(Commande, required=True, unique=True, reverse_delete_rule=DENY)
    note = IntField(required=True, min_value=1, max_value=5)
    commentaire = StringField()
    statut = StringField(required=True, default='en_attente',
                         choices=('en_attente', 'valide', 'refuse'))
    created_at = DateTimeField(default=datetime.utcnow)


# ─────────────────────────────────────────────
# Horaire
# ─────────────────────────────────────────────

class Horaire(Document):
    meta = {'collection': 'horaire', 'ordering': ['ordre']}

    ordre = IntField(required=True, unique=True)   # 0 = lundi … 6 = dimanche
    jour = StringField(required=True, unique=True, max_length=20)
    # 'Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'
    heure_ouverture = StringField(max_length=10)
    heure_fermeture = StringField(max_length=10)
    ferme = BooleanField(default=False)


# Toutes les collections de l'application (utilisé par init_db.py)
DOCUMENTS = (Utilisateur, TokenReinitialisation, Theme, Regime, Allergene,
             Plat, Menu, Commande, Avis, Horaire)
