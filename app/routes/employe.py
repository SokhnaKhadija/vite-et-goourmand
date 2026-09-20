import os
import uuid
from flask import Blueprint, render_template, request, flash, redirect, url_for, abort, current_app
from flask_login import current_user
from mongoengine import Q
from mongoengine.errors import OperationError
from ..models import (Menu, Plat, ImageMenu, Theme, Regime, Allergene,
                      Horaire, Commande, SuiviCommande, Avis, Utilisateur,
                      STATUTS_COMMANDE, charger, charger_ou_404, convertir_ids)
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
    nb_commandes_attente = Commande.objects(statut='en_attente').count()
    nb_avis_attente = Avis.objects(statut='en_attente').count()
    return render_template('employe/dashboard.html',
                           nb_commandes_attente=nb_commandes_attente,
                           nb_avis_attente=nb_avis_attente)


# ─── Commandes ───────────────────────────────────────────────────────────────

@bp.route('/commandes')
@employe_requis
def commandes():
    statut = request.args.get('statut', '')
    client = request.args.get('client', '').strip()

    filtres = {}
    if statut:
        filtres['statut'] = statut
    if client:
        clients = Utilisateur.objects(
            Q(nom__icontains=client) | Q(prenom__icontains=client) | Q(email__icontains=client)
        ).only('id')
        filtres['utilisateur__in'] = list(clients)

    commandes_liste = list(Commande.objects(**filtres).order_by('-date_commande').select_related())
    return render_template('employe/commandes.html',
                           commandes=commandes_liste,
                           statuts=STATUTS_COMMANDE,
                           statut_filtre=statut,
                           client_filtre=client)


@bp.route('/commandes/<commande_id>/statut', methods=['POST'])
@employe_requis
def changer_statut(commande_id):
    commande = charger_ou_404(Commande, commande_id)
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
        if commande.statut != 'annulee':
            Menu.objects(id=commande.menu.id).update_one(inc__stock=1)

    commande.statut = nouveau_statut
    commande.suivis.append(SuiviCommande(statut=nouveau_statut))
    commande.save()

    # Notifications email selon statut
    if nouveau_statut == 'en_attente_materiel':
        envoyer_retour_materiel(commande)
    elif nouveau_statut == 'terminee':
        envoyer_commande_terminee(commande)

    flash("Statut de la commande mis à jour.", 'success')
    return redirect(url_for('employe.commandes'))


@bp.route('/commandes/<commande_id>')
@employe_requis
def detail_commande(commande_id):
    commande = charger_ou_404(Commande, commande_id)
    return render_template('employe/detail_commande.html',
                           commande=commande,
                           statuts=STATUTS_COMMANDE)


# ─── Menus ───────────────────────────────────────────────────────────────────

@bp.route('/menus')
@employe_requis
def gestion_menus():
    menus = list(Menu.objects.order_by('-created_at').select_related())
    return render_template('employe/menus/liste.html', menus=menus)


@bp.route('/menus/nouveau', methods=['GET', 'POST'])
@employe_requis
def nouveau_menu():
    return _form_menu()


@bp.route('/menus/<menu_id>/modifier', methods=['GET', 'POST'])
@employe_requis
def modifier_menu(menu_id):
    menu = charger_ou_404(Menu, menu_id)
    return _form_menu(menu)


def _form_menu(menu=None):
    themes = list(Theme.objects.order_by('libelle'))
    regimes = list(Regime.objects.order_by('libelle'))
    plats_disponibles = list(Plat.objects.order_by('type_plat', 'titre').select_related())

    if request.method == 'POST':
        titre = request.form.get('titre', '').strip()
        description = request.form.get('description', '').strip()
        theme = charger(Theme, request.form.get('theme_id', ''))
        regime = charger(Regime, request.form.get('regime_id', ''))
        nb_personnes_min = request.form.get('nb_personnes_min', type=int, default=1)
        prix_base = request.form.get('prix_base', type=float, default=0.0)
        conditions = request.form.get('conditions', '').strip()
        stock = request.form.get('stock', type=int, default=0)
        actif = request.form.get('actif') == 'on'
        plats_ids = convertir_ids(request.form.getlist('plats'))

        if not titre or not theme or not regime or nb_personnes_min < 1 or prix_base <= 0 or stock < 0:
            flash("Veuillez remplir tous les champs obligatoires.", 'danger')
        else:
            if menu is None:
                menu = Menu()

            menu.titre = titre
            menu.description = description
            menu.theme = theme
            menu.regime = regime
            menu.nb_personnes_min = nb_personnes_min
            menu.prix_base = prix_base
            menu.conditions = conditions
            menu.stock = stock
            menu.actif = actif
            menu.plats = list(Plat.objects(id__in=plats_ids))

            # Images
            images = request.files.getlist('images')
            for img in images:
                if img and img.filename and _extension_autorisee(img.filename):
                    chemin = _sauvegarder_image(img)
                    menu.images.append(ImageMenu(chemin=chemin))

            menu.save()
            flash("Menu enregistré avec succès.", 'success')
            return redirect(url_for('employe.gestion_menus'))

    return render_template('employe/menus/form.html',
                           menu=menu,
                           themes=themes,
                           regimes=regimes,
                           plats_disponibles=plats_disponibles)


@bp.route('/menus/<menu_id>/supprimer', methods=['POST'])
@employe_requis
def supprimer_menu(menu_id):
    menu = charger_ou_404(Menu, menu_id)
    if Commande.objects(menu=menu, statut='en_attente').count() > 0:
        flash("Impossible de supprimer un menu ayant des commandes en attente.", 'warning')
        return redirect(url_for('employe.gestion_menus'))
    try:
        menu.delete()
    except OperationError:
        # reverse_delete_rule=DENY : le menu est référencé par des commandes existantes
        flash("Impossible de supprimer un menu ayant déjà été commandé. "
              "Désactivez-le plutôt (case « actif »).", 'warning')
        return redirect(url_for('employe.gestion_menus'))
    flash("Menu supprimé.", 'info')
    return redirect(url_for('employe.gestion_menus'))


@bp.route('/menus/<menu_id>/images/<image_id>/supprimer', methods=['POST'])
@employe_requis
def supprimer_image(menu_id, image_id):
    menu = charger_ou_404(Menu, menu_id)
    image = next((i for i in menu.images if str(i.id) == image_id), None)
    if image is None:
        abort(404)
    try:
        chemin_complet = os.path.join(current_app.root_path, 'static', image.chemin)
        if os.path.exists(chemin_complet):
            os.remove(chemin_complet)
    except Exception:
        pass
    menu.images.remove(image)
    menu.save()
    flash("Image supprimée.", 'info')
    return redirect(url_for('employe.modifier_menu', menu_id=menu_id))


# ─── Plats ───────────────────────────────────────────────────────────────────

@bp.route('/plats')
@employe_requis
def gestion_plats():
    plats = list(Plat.objects.order_by('type_plat', 'titre').select_related())
    return render_template('employe/plats/liste.html', plats=plats)


@bp.route('/plats/nouveau', methods=['GET', 'POST'])
@employe_requis
def nouveau_plat():
    return _form_plat()


@bp.route('/plats/<plat_id>/modifier', methods=['GET', 'POST'])
@employe_requis
def modifier_plat(plat_id):
    plat = charger_ou_404(Plat, plat_id)
    return _form_plat(plat)


def _form_plat(plat=None):
    allergenes_liste = list(Allergene.objects.order_by('libelle'))

    if request.method == 'POST':
        titre = request.form.get('titre', '').strip()
        type_plat = request.form.get('type_plat', '').strip()
        description = request.form.get('description', '').strip()
        allergenes_ids = convertir_ids(request.form.getlist('allergenes'))

        if not titre or type_plat not in ('entree', 'plat', 'dessert'):
            flash("Veuillez remplir les champs obligatoires.", 'danger')
        else:
            if plat is None:
                plat = Plat()

            plat.titre = titre
            plat.type_plat = type_plat
            plat.description = description
            plat.allergenes = list(Allergene.objects(id__in=allergenes_ids))

            # Photo
            photo = request.files.get('photo')
            if photo and photo.filename and _extension_autorisee(photo.filename):
                chemin = _sauvegarder_image(photo)
                plat.photo = chemin

            plat.save()
            flash("Plat enregistré.", 'success')
            return redirect(url_for('employe.gestion_plats'))

    return render_template('employe/plats/form.html',
                           plat=plat,
                           allergenes_liste=allergenes_liste)


@bp.route('/plats/<plat_id>/supprimer', methods=['POST'])
@employe_requis
def supprimer_plat(plat_id):
    plat = charger_ou_404(Plat, plat_id)
    plat.delete()
    flash("Plat supprimé.", 'info')
    return redirect(url_for('employe.gestion_plats'))


# ─── Horaires ────────────────────────────────────────────────────────────────

@bp.route('/horaires', methods=['GET', 'POST'])
@employe_requis
def horaires():
    if request.method == 'POST':
        for horaire in Horaire.objects:
            ferme = request.form.get(f'ferme_{horaire.id}') == 'on'
            horaire.ferme = ferme
            if not ferme:
                horaire.heure_ouverture = request.form.get(f'ouverture_{horaire.id}', '').strip() or None
                horaire.heure_fermeture = request.form.get(f'fermeture_{horaire.id}', '').strip() or None
            horaire.save()
        flash("Horaires mis à jour.", 'success')
        return redirect(url_for('employe.horaires'))

    horaires_liste = list(Horaire.objects)
    return render_template('employe/horaires.html', horaires=horaires_liste)


# ─── Avis ────────────────────────────────────────────────────────────────────

@bp.route('/avis')
@employe_requis
def gestion_avis():
    statut = request.args.get('statut', 'en_attente')
    avis_liste = list(Avis.objects(statut=statut).order_by('-created_at').select_related())
    return render_template('employe/avis.html', avis=avis_liste, statut=statut)


@bp.route('/avis/<avis_id>/valider', methods=['POST'])
@employe_requis
def valider_avis(avis_id):
    avis = charger_ou_404(Avis, avis_id)
    avis.statut = 'valide'
    avis.save()
    flash("Avis validé et publié.", 'success')
    return redirect(url_for('employe.gestion_avis'))


@bp.route('/avis/<avis_id>/refuser', methods=['POST'])
@employe_requis
def refuser_avis(avis_id):
    avis = charger_ou_404(Avis, avis_id)
    avis.statut = 'refuse'
    avis.save()
    flash("Avis refusé.", 'info')
    return redirect(url_for('employe.gestion_avis'))
