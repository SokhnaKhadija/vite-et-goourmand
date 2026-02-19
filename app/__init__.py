import os
from datetime import datetime
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from .models import db, Utilisateur, Role, Horaire, Theme, Regime, Allergene
from config import Config


login_manager = LoginManager()
login_manager.login_view = 'auth.connexion'
login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."
login_manager.login_message_category = 'warning'


@login_manager.user_loader
def load_user(user_id):
    return Utilisateur.query.get(int(user_id))


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Créer le dossier d'uploads si nécessaire
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialiser les extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Enregistrer les blueprints
    from .routes.main import bp as main_bp
    from .routes.auth import bp as auth_bp
    from .routes.menus import bp as menus_bp
    from .routes.commandes import bp as commandes_bp
    from .routes.utilisateur import bp as utilisateur_bp
    from .routes.employe import bp as employe_bp
    from .routes.admin import bp as admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(menus_bp, url_prefix='/menus')
    app.register_blueprint(commandes_bp, url_prefix='/commandes')
    app.register_blueprint(utilisateur_bp, url_prefix='/utilisateur')
    app.register_blueprint(employe_bp, url_prefix='/employe')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # Context processor global : injecter les horaires dans tous les templates
    @app.context_processor
    def injecter_contexte():
        horaires = []
        try:
            horaires = Horaire.query.order_by(Horaire.id).all()
        except Exception:
            pass
        from datetime import date
        return {
            'horaires_footer': horaires,
            'now': datetime.utcnow,
            'today': date.today().isoformat(),
        }

    # Créer les tables et données initiales
    with app.app_context():
        db.create_all()
        _initialiser_donnees()

    return app


def _initialiser_donnees():
    """Crée les données de référence si elles n'existent pas."""
    # Rôles
    roles = ['utilisateur', 'employe', 'administrateur']
    for libelle in roles:
        if not Role.query.filter_by(libelle=libelle).first():
            db.session.add(Role(libelle=libelle))
    db.session.flush()

    # Thèmes
    themes = ['Noël', 'Pâques', 'Classique', 'Événement']
    for libelle in themes:
        if not Theme.query.filter_by(libelle=libelle).first():
            db.session.add(Theme(libelle=libelle))

    # Régimes
    regimes = ['Classique', 'Végétarien', 'Vegan', 'Sans gluten', 'Sans lactose', 'Halal']
    for libelle in regimes:
        if not Regime.query.filter_by(libelle=libelle).first():
            db.session.add(Regime(libelle=libelle))

    # Allergènes
    allergenes = [
        'Gluten', 'Crustacés', 'Œufs', 'Poissons', 'Arachides', 'Soja',
        'Lait', 'Fruits à coque', 'Céleri', 'Moutarde', 'Graines de sésame',
        'Anhydride sulfureux et sulfites', 'Lupin', 'Mollusques'
    ]
    for libelle in allergenes:
        if not Allergene.query.filter_by(libelle=libelle).first():
            db.session.add(Allergene(libelle=libelle))

    # Horaires (lundi–dimanche)
    jours = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
    for jour in jours:
        if not Horaire.query.filter_by(jour=jour).first():
            ferme = jour == 'Dimanche'
            db.session.add(Horaire(
                jour=jour,
                heure_ouverture='09:00' if not ferme else None,
                heure_fermeture='18:00' if not ferme else None,
                ferme=ferme
            ))

    db.session.flush()

    # Compte administrateur initial
    role_admin = Role.query.filter_by(libelle='administrateur').first()
    from config import Config
    if not Utilisateur.query.filter_by(email=Config.ADMIN_EMAIL).first():
        admin = Utilisateur(
            nom='Vite',
            prenom='José',
            email=Config.ADMIN_EMAIL,
            telephone='0600000000',
            adresse='1 rue des Saveurs',
            ville='Bordeaux',
            code_postal='33000',
            role_id=role_admin.id,
            actif=True
        )
        admin.set_password(Config.ADMIN_PASSWORD)
        db.session.add(admin)

    db.session.commit()
