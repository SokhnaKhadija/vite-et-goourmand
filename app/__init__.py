import os
from datetime import date, datetime

from flask import Flask
from flask_login import LoginManager
from mongoengine import connect
from pymongo.errors import PyMongoError

from .models import Utilisateur, Horaire, charger
from . import seed
from config import Config


login_manager = LoginManager()
login_manager.login_view = 'auth.connexion'
login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."
login_manager.login_message_category = 'warning'


@login_manager.user_loader
def load_user(user_id):
    return charger(Utilisateur, user_id)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Créer le dossier d'uploads si nécessaire
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Connexion à MongoDB (paresseuse : l'erreur ne survient qu'au premier accès)
    connect(
        db=app.config['MONGO_DBNAME'],
        host=app.config['MONGO_URI'],
        serverSelectionTimeoutMS=5000,
    )

    # Initialiser les extensions
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
            horaires = list(Horaire.objects)
        except Exception:
            pass
        return {
            'horaires_footer': horaires,
            'now': datetime.utcnow,
            'today': date.today().isoformat(),
        }

    # Données de référence et compte administrateur initial
    try:
        seed.initialiser_references()
        seed.creer_admin(app.config['ADMIN_EMAIL'], app.config['ADMIN_PASSWORD'])
    except PyMongoError as e:
        raise RuntimeError(
            "Impossible de joindre MongoDB. Vérifiez que le serveur est démarré "
            f"et que MONGO_URI est correct dans .env. Détail : {e}"
        ) from e

    return app
