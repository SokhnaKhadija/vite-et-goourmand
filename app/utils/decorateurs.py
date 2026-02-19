from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user


def role_requis(*roles):
    """Décorateur qui vérifie que l'utilisateur connecté possède l'un des rôles indiqués."""
    def decorateur(f):
        @wraps(f)
        def enveloppe(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Vous devez être connecté pour accéder à cette page.", "warning")
                return redirect(url_for('auth.connexion'))
            if not current_user.actif:
                flash("Votre compte est désactivé. Contactez l'administrateur.", "danger")
                return redirect(url_for('main.accueil'))
            if current_user.role.libelle not in roles:
                abort(403)
            return f(*args, **kwargs)
        return enveloppe
    return decorateur


def employe_requis(f):
    """Raccourci : employé ou administrateur."""
    @wraps(f)
    def enveloppe(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Vous devez être connecté pour accéder à cette page.", "warning")
            return redirect(url_for('auth.connexion'))
        if not current_user.actif:
            flash("Votre compte est désactivé.", "danger")
            return redirect(url_for('main.accueil'))
        if not current_user.est_employe:
            abort(403)
        return f(*args, **kwargs)
    return enveloppe


def admin_requis(f):
    """Raccourci : administrateur uniquement."""
    @wraps(f)
    def enveloppe(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Vous devez être connecté pour accéder à cette page.", "warning")
            return redirect(url_for('auth.connexion'))
        if not current_user.actif:
            flash("Votre compte est désactivé.", "danger")
            return redirect(url_for('main.accueil'))
        if not current_user.est_admin:
            abort(403)
        return f(*args, **kwargs)
    return enveloppe
