import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-changez-en-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'postgresql://postgres:password@localhost/vite_et_gourmand'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # MongoDB pour les statistiques
    MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
    MONGO_DBNAME = 'vite_et_gourmand_stats'

    # Upload d'images
    UPLOAD_FOLDER = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'app', 'static', 'uploads'
    )
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 Mo
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # Email (simulé : écriture dans le fichier de logs)
    MAIL_SUPPRESS_SEND = True
    MAIL_LOG_FILE = 'emails.log'

    # Compte administrateur initial (créé au premier démarrage)
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'jose@viteetsourmand.fr')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Admin@VG2025!')

    # Frais de livraison hors Bordeaux
    FRAIS_LIVRAISON_BASE = 5.0
    FRAIS_LIVRAISON_KM = 0.59
    FRAIS_LIVRAISON_FIXE_HORS_BORDEAUX = 15.0  # montant fixe simplifié
