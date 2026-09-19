import re
from datetime import date, datetime, time, timedelta

from bson import ObjectId
from flask import Blueprint, render_template, request, flash, redirect, url_for
from ..models import Utilisateur, Menu, Commande, charger_ou_404
from ..utils.decorateurs import admin_requis
from ..utils.email import envoyer_compte_employe

bp = Blueprint('admin', __name__)

REGEX_MOT_DE_PASSE = re.compile(
    r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z\d]).{10,}$'
)


def _stats_par_menu(filtre: dict = None) -> list:
    """CA et nombre de commandes par menu, calculés par agrégation sur la collection `commande`.

    Retourne une liste de dicts {titre, nb_commandes, ca}, triée par titre.
    """
    pipeline = [
        {'$match': filtre or {}},
        {'$group': {'_id': '$menu',
                    'nb_commandes': {'$sum': 1},
                    'ca': {'$sum': '$prix_total'}}},
        {'$lookup': {'from': 'menu', 'localField': '_id',
                     'foreignField': '_id', 'as': 'menu'}},
        {'$unwind': '$menu'},
        {'$project': {'_id': 0, 'titre': '$menu.titre', 'nb_commandes': 1, 'ca': 1}},
        {'$sort': {'titre': 1}},
    ]
    return list(Commande.objects.aggregate(pipeline))


@bp.route('/')
@admin_requis
def dashboard():
    return render_template('admin/dashboard.html',
                           nb_commandes=Commande.objects.count(),
                           nb_utilisateurs=Utilisateur.objects(role='utilisateur').count(),
                           stats_menus=_stats_par_menu())


# ─── Gestion des employés ────────────────────────────────────────────────────

@bp.route('/employes')
@admin_requis
def employes():
    employes_liste = list(Utilisateur.objects(role='employe').order_by('nom'))
    return render_template('admin/employes.html', employes=employes_liste)


@bp.route('/employes/nouveau', methods=['GET', 'POST'])
@admin_requis
def nouvel_employe():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        prenom = request.form.get('prenom', '').strip()
        nom = request.form.get('nom', '').strip()
        mot_de_passe = request.form.get('mot_de_passe', '')

        erreurs = []
        if not email:
            erreurs.append("L'adresse e-mail est obligatoire.")
        elif Utilisateur.objects(email=email).first():
            erreurs.append("Cette adresse e-mail est déjà utilisée.")
        if not nom or not prenom:
            erreurs.append("Le nom et le prénom sont obligatoires.")
        if not REGEX_MOT_DE_PASSE.match(mot_de_passe):
            erreurs.append(
                "Le mot de passe doit contenir au minimum 10 caractères, "
                "une majuscule, une minuscule, un chiffre et un caractère spécial."
            )

        if erreurs:
            for e in erreurs:
                flash(e, 'danger')
        else:
            employe = Utilisateur(
                nom=nom,
                prenom=prenom,
                email=email,
                role='employe',
                actif=True
            )
            employe.set_password(mot_de_passe)
            employe.save()
            envoyer_compte_employe(employe)
            flash(f"Compte employé créé pour {prenom} {nom}.", 'success')
            return redirect(url_for('admin.employes'))

    return render_template('admin/form_employe.html', employe=None)


@bp.route('/employes/<employe_id>/activer', methods=['POST'])
@admin_requis
def activer_employe(employe_id):
    employe = charger_ou_404(Utilisateur, employe_id)
    if employe.role != 'employe':
        flash("Action non autorisée.", 'danger')
        return redirect(url_for('admin.employes'))
    employe.actif = True
    employe.save()
    flash(f"Compte de {employe.prenom} {employe.nom} activé.", 'success')
    return redirect(url_for('admin.employes'))


@bp.route('/employes/<employe_id>/desactiver', methods=['POST'])
@admin_requis
def desactiver_employe(employe_id):
    employe = charger_ou_404(Utilisateur, employe_id)
    if employe.role != 'employe':
        flash("Action non autorisée.", 'danger')
        return redirect(url_for('admin.employes'))
    employe.actif = False
    employe.save()
    flash(f"Compte de {employe.prenom} {employe.nom} désactivé.", 'info')
    return redirect(url_for('admin.employes'))


# ─── Statistiques ────────────────────────────────────────────────────────────

@bp.route('/statistiques')
@admin_requis
def statistiques():
    menus = list(Menu.objects(actif=True).order_by('titre'))

    menu_id = request.args.get('menu_id', '')
    date_debut = request.args.get('date_debut', '')
    date_fin = request.args.get('date_fin', '')

    filtre = {}
    if ObjectId.is_valid(menu_id):
        filtre['menu'] = ObjectId(menu_id)
    periode = {}
    try:
        if date_debut:
            periode['$gte'] = datetime.combine(date.fromisoformat(date_debut), time.min)
        if date_fin:
            # Jour de fin inclus : borne exclusive au lendemain 00:00
            periode['$lt'] = datetime.combine(date.fromisoformat(date_fin) + timedelta(days=1), time.min)
    except ValueError:
        periode = {}
    if periode:
        filtre['date_commande'] = periode

    resultats = _stats_par_menu(filtre)

    return render_template('admin/statistiques.html',
                           menus=menus,
                           resultats_ca=resultats,
                           menu_id_filtre=menu_id,
                           date_debut=date_debut,
                           date_fin=date_fin)


# L'administrateur hérite aussi des fonctionnalités employé via les blueprints
# (il peut accéder à /employe/* grâce au décorateur employe_requis qui accepte admin)
