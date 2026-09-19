#!/usr/bin/env python3
"""
Script d'initialisation de la base de données MongoDB de Vite & Gourmand.

- Se connecte à MongoDB avec MONGO_URI / MONGO_DBNAME (fichier .env)
- Crée les collections et leurs index (uniques, TTL, recherche)
- Alimente la base : thèmes, régimes, allergènes, horaires, compte administrateur
  et données de démonstration (plats + menus)

Le script est relançable sans risque : les éléments déjà présents ne sont pas dupliqués.

Usage :
    python init_db.py              # initialise / complète la base
    python init_db.py --reset      # SUPPRIME la base puis la recrée (confirmation demandée)
    python init_db.py --reset -y   # idem, sans confirmation
    python init_db.py --sans-demo  # sans les plats/menus de démonstration
"""

import argparse
import re
import sys

from mongoengine import connect
from mongoengine.connection import get_connection
from pymongo.errors import PyMongoError

try:
    from config import Config
except RuntimeError as erreur:  # variable .env obligatoire manquante
    sys.exit(f"Erreur de configuration : {erreur}")

from app.models import DOCUMENTS
from app import seed


def masquer_identifiants(uri: str) -> str:
    """Masque 'utilisateur:motdepasse@' dans une URI MongoDB avant affichage."""
    return re.sub(r'//[^@/]+@', '//***@', uri)


def se_connecter():
    """Ouvre la connexion et vérifie que le serveur répond."""
    connect(db=Config.MONGO_DBNAME, host=Config.MONGO_URI, serverSelectionTimeoutMS=5000)
    try:
        get_connection().admin.command('ping')
    except PyMongoError as erreur:
        print("Erreur : impossible de se connecter à MongoDB.")
        print("Vérifiez que le serveur est démarré et que MONGO_URI est correct dans .env.")
        print(f"Détail : {erreur}")
        sys.exit(1)


def reinitialiser_base(confirme: bool) -> None:
    """Supprime toute la base (équivalent des DROP TABLE de l'ancien database.sql)."""
    if not confirme:
        reponse = input(
            f"⚠ Toutes les données de la base '{Config.MONGO_DBNAME}' vont être SUPPRIMÉES. "
            "Tapez le nom de la base pour confirmer : "
        )
        if reponse.strip() != Config.MONGO_DBNAME:
            print("Annulé : la base n'a pas été modifiée.")
            sys.exit(0)
    get_connection().drop_database(Config.MONGO_DBNAME)
    print(f"Base '{Config.MONGO_DBNAME}' supprimée.")


def creer_index() -> None:
    """Crée explicitement les index déclarés dans les modèles."""
    for modele in DOCUMENTS:
        modele.ensure_indexes()
    print(f"Collections et index créés ({len(DOCUMENTS)} collections).")


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialisation de la base MongoDB.")
    parser.add_argument('--reset', action='store_true',
                        help="supprime la base avant de la recréer")
    parser.add_argument('-y', '--yes', action='store_true',
                        help="ne pas demander de confirmation pour --reset")
    parser.add_argument('--sans-demo', action='store_true',
                        help="ne pas charger les plats et menus de démonstration")
    args = parser.parse_args()

    print("=" * 50)
    print("  Initialisation — Vite & Gourmand")
    print("=" * 50)
    print(f"  Serveur : {masquer_identifiants(Config.MONGO_URI)}")
    print(f"  Base    : {Config.MONGO_DBNAME}")
    print("=" * 50)

    se_connecter()

    if args.reset:
        reinitialiser_base(confirme=args.yes)

    creer_index()

    seed.initialiser_references()
    print("Données de référence prêtes (thèmes, régimes, allergènes, horaires).")

    if seed.creer_admin(Config.ADMIN_EMAIL, Config.ADMIN_PASSWORD):
        print(f"Compte administrateur créé : {Config.ADMIN_EMAIL}")
    else:
        print(f"Compte administrateur déjà existant : {Config.ADMIN_EMAIL}")

    if not args.sans_demo:
        plats, menus = seed.charger_demo()
        print(f"Données de démonstration : {plats} plat(s) et {menus} menu(s) ajouté(s).")

    print()
    print("Base de données prête. Démarrez l'application avec : python run.py")


if __name__ == "__main__":
    main()
