import os
import uuid
from flask import Blueprint, render_template, request, flash, redirect, url_for, abort, current_app
from flask_login import current_user
from ..models import (db, Menu, Plat, ImageMenu, Theme, Regime, Allergene,
                      Horaire, Commande, SuiviCommande, Avis, STATUTS_COMMANDE)
from ..utils.decorateurs import employe_requis
from ..utils.email import envoyer_retour_materiel, envoyer_commande_terminee

bp = Blueprint('employe', __name__)

EXTENSIONS_AUTORISEES = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def _extension_autorisee(nom_fichier: str) -> bool:
    return '.' in nom_fichier and nom_fichier.rsplit('.', 1)[1].lower() in EXTENSIONS_AUTORISEES


def _sauvegarder_image(fichier) -> str:
    ext = fichier.filename.rsplit('.', 1)[1].lower()
    nom_fichier = uuid.uuid4().hex + '.' + ext
    chemin = os.path.join(current_app.config['UPLOAD_FOLDER'], nom_fichier)
    fichier.save(chemin)
    return 'uploads/' + nom_fichier


# ─── Tableau de bord ─────────────────────────────────────────────────────────

@bp.route('/')
@employe_requis
def dashboard():
    nb_commandes_attente = Commande.query.filter_by(statut='en_attente').count()
    nb_avis_attente = Avis.query.filter_by(statut='en_attente').count()
    return render_template('employe/dashboard.html',
                           nb_commandes_attente=nb_commandes_attente,
                           nb_avis_attente=nb_avis_attente)


# ─── Commandes ───────────────────────────────────────────────────────────────

@bp.route('/commandes')
@employe_requis
def commandes():
    statut = request.args.get('statut', '')
    client = request.args.get('client', '').strip()

    query = Commande.query

    if statut:
        query = query.filter_by(statut=statut)
    if client:
        from ..models import Utilisateur
        sous_query = Utilisateur.query.filter(
            (Utilisateur.nom.ilike(f'%{client}%')) |
            (Utilisateur.prenom.ilike(f'%{client}%')) |
            (Utilisateur.email.ilike(f'%{client}%'))
        ).with_entities(Utilisateur.id)
        query = query.filter(Commande.utilisateur_id.in_(sous_query))

    commandes_liste = query.order_by(Commande.date_commande.desc()).all()
    return render_template('employe/commandes.html',
                           commandes=commandes_liste,
                           statuts=STATUTS_COMMANDE,
                           statut_filtre=statut,
                           client_filtre=client)


@bp.route('/commandes/<int:commande_id>/statut', methods=['POST'])
@employe_requis
def changer_statut(commande_id):
    commande = Commande.query.get_or_404(commande_id)
    nouveau_statut = request.form.get('statut')

    statuts_valides = [s[0] for s in STATUTS_COMMANDE]
    if nouveau_statut not in statuts_valides:
        flash("Statut invalide.", 'danger')
        return redirect(url_for('employe.commandes'))

    # Annulation : motif obligatoire
    if nouveau_statut == 'annulee':
        motif = request.form.get('motif_annulation', '').strip()
        mode_contact = request.form.get('mode_contact', '').strip()
        if not motif or not mode_contact:
            flash("Pour annuler, vous devez indiquer le motif et le mode de contact avec le client.", 'danger')
            return redirect(url_for('employe.detail_commande', commande_id=commande_id))
        commande.motif_annulation = motif
        commande.mode_contact_annulation = mode_contact
        commande.menu.stock += 1

    commande.statut = nouveau_statut
    suivi = SuiviCommande(commande_id=commande.id, statut=nouveau_statut)
    db.session.add(suivi)

    # Notifications email selon statut
    if nouveau_statut == 'en_attente_materiel':
        envoyer_retour_materiel(commande)
    elif nouveau_statut == 'terminee':
        envoyer_commande_terminee(commande)

    db.session.commit()
    flash("Statut de la commande mis à jour.", 'success')
    return redirect(url_for('employe.commandes'))


@bp.route('/commandes/<int:commande_id>')
@employe_requis
def detail_commande(commande_id):
    commande = Commande.query.get_or_404(commande_id)
    return render_template('employe/detail_commande.html',
                           commande=commande,
                           statuts=STATUTS_COMMANDE)


# ─── Menus ───────────────────────────────────────────────────────────────────

@bp.route('/menus')
@employe_requis
def gestion_menus():
    menus = Menu.query.order_by(Menu.created_at.desc()).all()
    return render_template('employe/menus/liste.html', menus=menus)


@bp.route('/menus/nouveau', methods=['GET', 'POST'])
@employe_requis
def nouveau_menu():
    return _form_menu()


@bp.route('/menus/<int:menu_id>/modifier', methods=['GET', 'POST'])
@employe_requis
def modifier_menu(menu_id):
    menu = Menu.query.get_or_404(menu_id)
    return _form_menu(menu)


def _form_menu(menu=None):
    themes = Theme.query.order_by(Theme.libelle).all()
    regimes = Regime.query.order_by(Regime.libelle).all()
    plats_disponibles = Plat.query.order_by(Plat.type_plat, Plat.titre).all()

    if request.method == 'POST':
        titre = request.form.get('titre', '').strip()
        description = request.form.get('description', '').strip()
        theme_id = request.form.get('theme_id', type=int)
        regime_id = request.form.get('regime_id', type=int)
        nb_personnes_min = request.form.get('nb_personnes_min', type=int, default=1)
        prix_base = request.form.get('prix_base', type=float, default=0.0)
        conditions = request.form.get('conditions', '').strip()
        stock = request.form.get('stock', type=int, default=0)
        actif = request.form.get('actif') == 'on'
        plats_ids = request.form.getlist('plats', type=int)

        if not titre or not theme_id or not regime_id or nb_personnes_min < 1 or prix_base <= 0:
            flash("Veuillez remplir tous les champs obligatoires.", 'danger')
        else:
            if menu is None:
                menu = Menu()
                db.session.add(menu)

            menu.titre = titre
            menu.description = description
            menu.theme_id = theme_id
            menu.regime_id = regime_id
            menu.nb_personnes_min = nb_personnes_min
            menu.prix_base = prix_base
            menu.conditions = conditions
            menu.stock = stock
            menu.actif = actif
            menu.plats = Plat.query.filter(Plat.id.in_(plats_ids)).all()

            # Images
            images = request.files.getlist('images')
            for img in images:
                if img and img.filename and _extension_autorisee(img.filename):
                    chemin = _sauvegarder_image(img)
                    db.session.add(ImageMenu(menu=menu, chemin=chemin))

            db.session.commit()
            flash("Menu enregistré avec succès.", 'success')
            return redirect(url_for('employe.gestion_menus'))

    return render_template('employe/menus/form.html',
                           menu=menu,
                           themes=themes,
                           regimes=regimes,
                           plats_disponibles=plats_disponibles)


@bp.route('/menus/<int:menu_id>/supprimer', methods=['POST'])
@employe_requis
def supprimer_menu(menu_id):
    menu = Menu.query.get_or_404(menu_id)
    if Commande.query.filter_by(menu_id=menu_id, statut='en_attente').count() > 0:
        flash("Impossible de supprimer un menu ayant des commandes en attente.", 'warning')
        return redirect(url_for('employe.gestion_menus'))
    db.session.delete(menu)
    db.session.commit()
    flash("Menu supprimé.", 'info')
    return redirect(url_for('employe.gestion_menus'))


@bp.route('/menus/<int:menu_id>/images/<int:image_id>/supprimer', methods=['POST'])
@employe_requis
def supprimer_image(menu_id, image_id):
    image = ImageMenu.query.get_or_404(image_id)
    if image.menu_id != menu_id:
        abort(403)
    try:
        chemin_complet = os.path.join(current_app.root_path, 'static', image.chemin)
        if os.path.exists(chemin_complet):
            os.remove(chemin_complet)
    except Exception:
        pass
    db.session.delete(image)
    db.session.commit()
    flash("Image supprimée.", 'info')
    return redirect(url_for('employe.modifier_menu', menu_id=menu_id))


# ─── Plats ───────────────────────────────────────────────────────────────────

@bp.route('/plats')
@employe_requis
def gestion_plats():
    plats = Plat.query.order_by(Plat.type_plat, Plat.titre).all()
    return render_template('employe/plats/liste.html', plats=plats)


@bp.route('/plats/nouveau', methods=['GET', 'POST'])
@employe_requis
def nouveau_plat():
    return _form_plat()


@bp.route('/plats/<int:plat_id>/modifier', methods=['GET', 'POST'])
@employe_requis
def modifier_plat(plat_id):
    plat = Plat.query.get_or_404(plat_id)
    return _form_plat(plat)


def _form_plat(plat=None):
    allergenes_liste = Allergene.query.order_by(Allergene.libelle).all()

    if request.method == 'POST':
        titre = request.form.get('titre', '').strip()
        type_plat = request.form.get('type_plat', '').strip()
        description = request.form.get('description', '').strip()
        allergenes_ids = request.form.getlist('allergenes', type=int)

        if not titre or type_plat not in ('entree', 'plat', 'dessert'):
            flash("Veuillez remplir les champs obligatoires.", 'danger')
        else:
            if plat is None:
                plat = Plat()
                db.session.add(plat)

            plat.titre = titre
            plat.type_plat = type_plat
            plat.description = description
            plat.allergenes = Allergene.query.filter(Allergene.id.in_(allergenes_ids)).all()

            # Photo
            photo = request.files.get('photo')
            if photo and photo.filename and _extension_autorisee(photo.filename):
                chemin = _sauvegarder_image(photo)
                plat.photo = chemin

            db.session.commit()
            flash("Plat enregistré.", 'success')
            return redirect(url_for('employe.gestion_plats'))

    return render_template('employe/plats/form.html',
                           plat=plat,
                           allergenes_liste=allergenes_liste)


@bp.route('/plats/<int:plat_id>/supprimer', methods=['POST'])
@employe_requis
def supprimer_plat(plat_id):
    plat = Plat.query.get_or_404(plat_id)
    db.session.delete(plat)
    db.session.commit()
    flash("Plat supprimé.", 'info')
    return redirect(url_for('employe.gestion_plats'))


# ─── Horaires ────────────────────────────────────────────────────────────────

@bp.route('/horaires', methods=['GET', 'POST'])
@employe_requis
def horaires():
    if request.method == 'POST':
        for horaire in Horaire.query.all():
            ferme = request.form.get(f'ferme_{horaire.id}') == 'on'
            horaire.ferme = ferme
            if not ferme:
                horaire.heure_ouverture = request.form.get(f'ouverture_{horaire.id}', '').strip() or None
                horaire.heure_fermeture = request.form.get(f'fermeture_{horaire.id}', '').strip() or None
        db.session.commit()
        flash("Horaires mis à jour.", 'success')
        return redirect(url_for('employe.horaires'))

    horaires_liste = Horaire.query.order_by(Horaire.id).all()
    return render_template('employe/horaires.html', horaires=horaires_liste)


# ─── Avis ────────────────────────────────────────────────────────────────────

@bp.route('/avis')
@employe_requis
def gestion_avis():
    statut = request.args.get('statut', 'en_attente')
    avis_liste = Avis.query.filter_by(statut=statut).order_by(Avis.created_at.desc()).all()
    return render_template('employe/avis.html', avis=avis_liste, statut=statut)


@bp.route('/avis/<int:avis_id>/valider', methods=['POST'])
@employe_requis
def valider_avis(avis_id):
    avis = Avis.query.get_or_404(avis_id)
    avis.statut = 'valide'
    db.session.commit()
    flash("Avis validé et publié.", 'success')
    return redirect(url_for('employe.gestion_avis'))


@bp.route('/avis/<int:avis_id>/refuser', methods=['POST'])
@employe_requis
def refuser_avis(avis_id):
    avis = Avis.query.get_or_404(avis_id)
    avis.statut = 'refuse'
    db.session.commit()
    flash("Avis refusé.", 'info')
    return redirect(url_for('employe.gestion_avis'))
