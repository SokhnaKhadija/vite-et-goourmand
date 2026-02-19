from flask import Blueprint, render_template, request, flash, redirect, url_for
from ..models import db, Avis, Horaire
from ..utils.email import envoyer_contact

bp = Blueprint('main', __name__)


@bp.route('/')
def accueil():
    avis_valides = Avis.query.filter_by(statut='valide').order_by(Avis.created_at.desc()).limit(6).all()
    horaires = Horaire.query.order_by(Horaire.id).all()
    return render_template('index.html', avis=avis_valides, horaires=horaires)


@bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        titre = request.form.get('titre', '').strip()
        description = request.form.get('description', '').strip()
        email = request.form.get('email', '').strip()

        erreurs = []
        if not titre:
            erreurs.append("Le titre est obligatoire.")
        if not description:
            erreurs.append("La description est obligatoire.")
        if not email:
            erreurs.append("L'adresse e-mail est obligatoire.")

        if erreurs:
            for e in erreurs:
                flash(e, 'danger')
        else:
            envoyer_contact(titre, description, email)
            flash("Votre message a bien été envoyé. Nous vous répondrons dans les meilleurs délais.", 'success')
            return redirect(url_for('main.contact'))

    return render_template('contact.html')


@bp.route('/mentions-legales')
def mentions_legales():
    return render_template('mentions_legales.html')


@bp.route('/conditions-generales-de-vente')
def cgv():
    return render_template('cgv.html')


@bp.app_errorhandler(403)
def erreur_403(e):
    return render_template('erreurs/403.html'), 403


@bp.app_errorhandler(404)
def erreur_404(e):
    return render_template('erreurs/404.html'), 404


@bp.app_errorhandler(500)
def erreur_500(e):
    return render_template('erreurs/500.html'), 500
