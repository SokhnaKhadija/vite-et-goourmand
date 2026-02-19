import re
import uuid
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, logout_user, current_user
from ..models import db, Utilisateur, Role, TokenReinitialisation
from ..utils.email import envoyer_bienvenue, envoyer_reinitialisation

bp = Blueprint('auth', __name__)

REGEX_MOT_DE_PASSE = re.compile(
    r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z\d]).{10,}$'
)


@bp.route('/connexion', methods=['GET', 'POST'])
def connexion():
    if current_user.is_authenticated:
        return redirect(url_for('main.accueil'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        mot_de_passe = request.form.get('mot_de_passe', '')

        utilisateur = Utilisateur.query.filter_by(email=email).first()
        if utilisateur and utilisateur.check_password(mot_de_passe):
            if not utilisateur.actif:
                flash("Votre compte est désactivé. Contactez l'administrateur.", 'danger')
            else:
                login_user(utilisateur, remember=request.form.get('se_souvenir') == 'on')
                flash(f"Bienvenue, {utilisateur.prenom} !", 'success')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('main.accueil'))
        else:
            flash("Identifiants incorrects.", 'danger')

    return render_template('auth/connexion.html')


@bp.route('/deconnexion')
def deconnexion():
    logout_user()
    flash("Vous avez été déconnecté.", 'info')
    return redirect(url_for('main.accueil'))


@bp.route('/inscription', methods=['GET', 'POST'])
def inscription():
    if current_user.is_authenticated:
        return redirect(url_for('main.accueil'))

    if request.method == 'POST':
        nom = request.form.get('nom', '').strip()
        prenom = request.form.get('prenom', '').strip()
        email = request.form.get('email', '').strip().lower()
        telephone = request.form.get('telephone', '').strip()
        adresse = request.form.get('adresse', '').strip()
        ville = request.form.get('ville', '').strip()
        code_postal = request.form.get('code_postal', '').strip()
        mot_de_passe = request.form.get('mot_de_passe', '')
        confirmation = request.form.get('confirmation', '')
        consentement = request.form.get('consentement')

        erreurs = []
        if not nom:
            erreurs.append("Le nom est obligatoire.")
        if not prenom:
            erreurs.append("Le prénom est obligatoire.")
        if not email:
            erreurs.append("L'adresse e-mail est obligatoire.")
        elif Utilisateur.query.filter_by(email=email).first():
            erreurs.append("Cette adresse e-mail est déjà utilisée.")
        if not telephone:
            erreurs.append("Le numéro de téléphone est obligatoire.")
        if not mot_de_passe:
            erreurs.append("Le mot de passe est obligatoire.")
        elif not REGEX_MOT_DE_PASSE.match(mot_de_passe):
            erreurs.append(
                "Le mot de passe doit contenir au minimum 10 caractères, "
                "une majuscule, une minuscule, un chiffre et un caractère spécial."
            )
        elif mot_de_passe != confirmation:
            erreurs.append("Les mots de passe ne correspondent pas.")
        if not consentement:
            erreurs.append("Vous devez accepter la politique de confidentialité.")

        if erreurs:
            for e in erreurs:
                flash(e, 'danger')
        else:
            role_utilisateur = Role.query.filter_by(libelle='utilisateur').first()
            nouvel_utilisateur = Utilisateur(
                nom=nom,
                prenom=prenom,
                email=email,
                telephone=telephone,
                adresse=adresse,
                ville=ville,
                code_postal=code_postal,
                role_id=role_utilisateur.id,
                actif=True
            )
            nouvel_utilisateur.set_password(mot_de_passe)
            db.session.add(nouvel_utilisateur)
            db.session.commit()
            envoyer_bienvenue(nouvel_utilisateur)
            flash("Votre compte a été créé avec succès. Vous pouvez maintenant vous connecter.", 'success')
            return redirect(url_for('auth.connexion'))

    return render_template('auth/inscription.html')


@bp.route('/mot-de-passe-oublie', methods=['GET', 'POST'])
def mot_de_passe_oublie():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        utilisateur = Utilisateur.query.filter_by(email=email).first()
        # On retourne toujours le même message pour ne pas divulguer les emails existants
        if utilisateur and utilisateur.actif:
            token = uuid.uuid4().hex
            expiration = datetime.utcnow() + timedelta(hours=1)
            t = TokenReinitialisation(
                utilisateur_id=utilisateur.id,
                token=token,
                expiration=expiration
            )
            db.session.add(t)
            db.session.commit()
            lien = url_for('auth.reinitialiser_mot_de_passe', token=token, _external=True)
            envoyer_reinitialisation(utilisateur, lien)
        flash("Si cette adresse e-mail est enregistrée, un lien de réinitialisation vous a été envoyé.", 'info')
        return redirect(url_for('auth.connexion'))

    return render_template('auth/mot_de_passe_oublie.html')


@bp.route('/reinitialiser-mot-de-passe/<token>', methods=['GET', 'POST'])
def reinitialiser_mot_de_passe(token):
    t = TokenReinitialisation.query.filter_by(token=token, utilise=False).first()
    if not t or t.expiration < datetime.utcnow():
        flash("Ce lien est invalide ou a expiré.", 'danger')
        return redirect(url_for('auth.mot_de_passe_oublie'))

    if request.method == 'POST':
        nouveau = request.form.get('mot_de_passe', '')
        confirmation = request.form.get('confirmation', '')

        if not REGEX_MOT_DE_PASSE.match(nouveau):
            flash(
                "Le mot de passe doit contenir au minimum 10 caractères, "
                "une majuscule, une minuscule, un chiffre et un caractère spécial.",
                'danger'
            )
        elif nouveau != confirmation:
            flash("Les mots de passe ne correspondent pas.", 'danger')
        else:
            t.utilisateur.set_password(nouveau)
            t.utilise = True
            db.session.commit()
            flash("Mot de passe réinitialisé avec succès.", 'success')
            return redirect(url_for('auth.connexion'))

    return render_template('auth/reinitialiser_mot_de_passe.html', token=token)
