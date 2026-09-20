import os
from dotenv import load_dotenv

load_dotenv()


def _requis(nom: str) -> str:
    """Lit une variable d'environnement obligatoire (aucune valeur par défaut dans le code)."""
    valeur = os.environ.get(nom)
    if not valeur:
        raise RuntimeError(
            f"Variable d'environnement obligatoire manquante : {nom}. "
            f"Copiez .env.example en .env et renseignez-la."
        )
    return valeur


def _booleen(nom: str, defaut: bool) -> bool:
    valeur = os.environ.get(nom)
    if valeur is None:
        return defaut
    return valeur.strip().lower() in ('1', 'true', 'vrai', 'oui', 'yes', 'on')


class Config:
    # ── Sécurité ─────────────────────────────────────────────
    SECRET_KEY = _requis('SECRET_KEY')

    # ── MongoDB (base de données unique de l'application) ────
    MONGO_URI = _requis('MONGO_URI')
    MONGO_DBNAME = os.environ.get('MONGO_DBNAME', 'vite_et_gourmand')

    # ── Serveur de développement (run.py) ────────────────────
    FLASK_HOST = os.environ.get('FLASK_HOST', '127.0.0.1')
    FLASK_PORT = int(os.environ.get('FLASK_PORT', '5001'))
    FLASK_DEBUG = _booleen('FLASK_DEBUG', True)

    # URL publique de l'application (utilisée dans les liens des e-mails)
    APP_BASE_URL = os.environ.get('APP_BASE_URL', 'http://localhost:5001').rstrip('/')

    # ── Upload d'images ──────────────────────────────────────
    UPLOAD_FOLDER = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'app', 'static', 'uploads'
    )
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_UPLOAD_MB', '16')) * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # ── E-mails (simulés : écriture dans le fichier de logs) ─
    MAIL_SUPPRESS_SEND = True
    MAIL_LOG_FILE = os.environ.get('MAIL_LOG_FILE', 'emails.log')
    CONTACT_EMAIL = os.environ.get('CONTACT_EMAIL', 'contact@viteetsourmand.fr')

    # ── Compte administrateur initial (créé au premier démarrage) ─
    ADMIN_EMAIL = _requis('ADMIN_EMAIL')
    ADMIN_PASSWORD = _requis('ADMIN_PASSWORD')

    # ── Livraison ────────────────────────────────────────────
    # Livraison gratuite dans la ville ci-dessous, forfait fixe ailleurs (simplifié)
    VILLE_LIVRAISON_GRATUITE = os.environ.get('VILLE_LIVRAISON_GRATUITE', 'Bordeaux')
    FRAIS_LIVRAISON_HORS_ZONE = float(os.environ.get('FRAIS_LIVRAISON_HORS_ZONE', '15'))
