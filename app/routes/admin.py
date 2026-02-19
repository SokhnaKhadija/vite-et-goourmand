import re
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import current_user
from ..models import db, Utilisateur, Role, Menu, Commande
from ..utils.decorateurs import admin_requis
from ..utils.email import envoyer_compte_employe

bp = Blueprint('admin', __name__)

REGEX_MOT_DE_PASSE = re.compile(
    r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z\d]).{10,}$'
)


@bp.route('/')
@admin_requis
def dashboard():
    # Statistiques globales PostgreSQL
    nb_commandes = Commande.query.count()
    nb_utilisateurs = Utilisateur.query.join(Role).filter(Role.libelle == 'utilisateur').count()

    # Statistiques MongoDB
    stats_menus = []
    try:
        from flask import current_app
        from pymongo import MongoClient
        client = MongoClient(current_app.config['MONGO_URI'])
        mongo_db = client[current_app.config['MONGO_DBNAME']]
        stats_menus = list(mongo_db.stats_commandes.find({}, {'_id': 0}))
        client.close()
    except Exception:
        pass

    return render_template('admin/dashboard.html',
                           nb_commandes=nb_commandes,
                           nb_utilisateurs=nb_utilisateurs,
                           stats_menus=stats_menus)


# ─── Gestion des employés ────────────────────────────────────────────────────

@bp.route('/employes')
@admin_requis
def employes():
    employes_liste = (Utilisateur.query
                      .join(Role)
                      .filter(Role.libelle == 'employe')
                      .order_by(Utilisateur.nom)
                      .all())
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
        elif Utilisateur.query.filter_by(email=email).first():
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
            role_employe = Role.query.filter_by(libelle='employe').first()
            employe = Utilisateur(
                nom=nom,
                prenom=prenom,
                email=email,
                role_id=role_employe.id,
                actif=True
            )
            employe.set_password(mot_de_passe)
            db.session.add(employe)
            db.session.commit()
            envoyer_compte_employe(employe)
            flash(f"Compte employé créé pour {prenom} {nom}.", 'success')
            return redirect(url_for('admin.employes'))

    return render_template('admin/form_employe.html', employe=None)


@bp.route('/employes/<int:employe_id>/activer', methods=['POST'])
@admin_requis
def activer_employe(employe_id):
    employe = Utilisateur.query.get_or_404(employe_id)
    if employe.role.libelle != 'employe':
        flash("Action non autorisée.", 'danger')
        return redirect(url_for('admin.employes'))
    employe.actif = True
    db.session.commit()
    flash(f"Compte de {employe.prenom} {employe.nom} activé.", 'success')
    return redirect(url_for('admin.employes'))


@bp.route('/employes/<int:employe_id>/desactiver', methods=['POST'])
@admin_requis
def desactiver_employe(employe_id):
    employe = Utilisateur.query.get_or_404(employe_id)
    if employe.role.libelle != 'employe':
        flash("Action non autorisée.", 'danger')
        return redirect(url_for('admin.employes'))
    employe.actif = False
    db.session.commit()
    flash(f"Compte de {employe.prenom} {employe.nom} désactivé.", 'info')
    return redirect(url_for('admin.employes'))


# ─── Statistiques (données MongoDB) ─────────────────────────────────────────

@bp.route('/statistiques')
@admin_requis
def statistiques():
    menus = Menu.query.filter_by(actif=True).order_by(Menu.titre).all()

    menu_id = request.args.get('menu_id', type=int)
    date_debut = request.args.get('date_debut', '')
    date_fin = request.args.get('date_fin', '')

    # Calcul du CA depuis PostgreSQL
    query = db.session.query(
        Menu.titre,
        db.func.count(Commande.id).label('nb_commandes'),
        db.func.sum(Commande.prix_total).label('ca')
    ).join(Menu).group_by(Menu.id, Menu.titre)

    if menu_id:
        query = query.filter(Commande.menu_id == menu_id)
    if date_debut:
        from datetime import date
        try:
            query = query.filter(Commande.date_commande >= date.fromisoformat(date_debut))
        except ValueError:
            pass
    if date_fin:
        from datetime import date
        try:
            query = query.filter(Commande.date_commande <= date.fromisoformat(date_fin))
        except ValueError:
            pass

    resultats_ca = query.all()

    # Données MongoDB pour le graphique
    stats_mongo = []
    try:
        from flask import current_app
        from pymongo import MongoClient
        client = MongoClient(current_app.config['MONGO_URI'])
        mongo_db = client[current_app.config['MONGO_DBNAME']]
        stats_mongo = list(mongo_db.stats_commandes.find({}, {'_id': 0}))
        client.close()
    except Exception:
        pass

    return render_template('admin/statistiques.html',
                           menus=menus,
                           resultats_ca=resultats_ca,
                           stats_mongo=stats_mongo,
                           menu_id_filtre=menu_id,
                           date_debut=date_debut,
                           date_fin=date_fin)


# L'administrateur hérite aussi des fonctionnalités employé via les blueprints
# (il peut accéder à /employe/* grâce au décorateur employe_requis qui accepte admin)
