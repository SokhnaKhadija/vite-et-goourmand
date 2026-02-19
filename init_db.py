#!/usr/bin/env python3
"""
Script d'initialisation de la base de données Vite & Gourmand.
- Crée la base PostgreSQL si elle n'existe pas encore
- Exécute database.sql (schéma + données de démo)

Fonctionne via le conteneur Docker PostgreSQL (docker exec).

Usage :
    python init_db.py
"""

import os
import sys
import subprocess

from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost/vite_et_gourmand"
)

SQL_FILE = os.path.join(os.path.dirname(__file__), "database.sql")

# Nom du conteneur Docker PostgreSQL
DOCKER_CONTAINER = "postgres-servicesgal-dev"


def parse_url(url: str) -> dict:
    """Décompose l'URL PostgreSQL en ses composants."""
    parsed = urlparse(url)
    return {
        "user":     parsed.username or "postgres",
        "password": parsed.password or "",
        "host":     parsed.hostname or "localhost",
        "port":     str(parsed.port or 5432),
        "dbname":   parsed.path.lstrip("/"),
    }


def run_docker_psql(params: dict, command: str = None, sql_content: str = None,
                    dbname: str = None) -> int:
    """Exécute une commande psql dans le conteneur Docker."""
    db = dbname or params["dbname"]
    env = {"PGPASSWORD": params["password"]} if params["password"] else {}

    env_args = []
    for k, v in env.items():
        env_args += ["-e", f"{k}={v}"]

    psql_cmd = [
        "psql",
        "-U", params["user"],
        "-d", db,
    ]

    if command:
        psql_cmd += ["-c", command]

    docker_cmd = ["docker", "exec", "-i"] + env_args + [DOCKER_CONTAINER] + psql_cmd

    if sql_content is not None:
        result = subprocess.run(docker_cmd, input=sql_content, text=True)
    else:
        result = subprocess.run(docker_cmd)

    return result.returncode


def create_database_if_missing(params: dict) -> None:
    """Crée la base de données si elle n'existe pas."""
    env_args = []
    if params["password"]:
        env_args = ["-e", f"PGPASSWORD={params['password']}"]

    check = subprocess.run(
        [
            "docker", "exec", "-i"
        ] + env_args + [
            DOCKER_CONTAINER,
            "psql", "-U", params["user"], "-d", "postgres",
            "-tAc",
            f"SELECT 1 FROM pg_database WHERE datname='{params['dbname']}'",
        ],
        capture_output=True,
        text=True,
    )

    if check.returncode != 0:
        print("Erreur : impossible de se connecter au conteneur PostgreSQL.")
        print(check.stderr.strip())
        sys.exit(1)

    if check.stdout.strip() == "1":
        print(f"Base de données '{params['dbname']}' déjà existante.")
    else:
        print(f"Création de la base de données '{params['dbname']}'...")
        code = run_docker_psql(
            params,
            command=f"CREATE DATABASE {params['dbname']};",
            dbname="postgres"
        )
        if code != 0:
            print("Erreur lors de la création de la base de données.")
            sys.exit(1)
        print("Base de données créée avec succès.")


def import_sql(params: dict) -> None:
    """Importe le fichier database.sql dans la base via docker exec."""
    if not os.path.isfile(SQL_FILE):
        print(f"Fichier introuvable : {SQL_FILE}")
        sys.exit(1)

    print(f"Import de 'database.sql' dans '{params['dbname']}'...")

    with open(SQL_FILE, "r", encoding="utf-8") as f:
        sql_content = f.read()

    code = run_docker_psql(params, sql_content=sql_content)
    if code != 0:
        print("Erreur lors de l'import du fichier SQL.")
        sys.exit(1)
    print("Import réussi. La base de données est prête.")


if __name__ == "__main__":
    params = parse_url(DATABASE_URL)

    print("=" * 50)
    print("  Initialisation — Vite & Gourmand")
    print("=" * 50)
    print(f"  Conteneur : {DOCKER_CONTAINER}")
    print(f"  Base      : {params['dbname']}")
    print(f"  Utilisateur : {params['user']}")
    print("=" * 50)

    create_database_if_missing(params)
    import_sql(params)

    print()
    print("Démarrez maintenant l'application avec : python run.py")
