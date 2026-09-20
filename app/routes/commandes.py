import uuid
from datetime import date
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app
from flask_login import current_user, login_required
from ..models import Commande, SuiviCommande, Menu, charger
from ..utils.email import envoyer_confirmation_commande

bp = Blueprint('commandes', __name__)

def _calculer_livraison(ville: str) -> float:
    """Livraison gratuite dans la ville configurée (Bordeaux), sinon forfait fixe (.env)."""
    ville_gratuite = current_app.config['VILLE_LIVRAISON_GRATUITE'].strip().lower()
    villes_gratuites = {ville_gratuite, f'{ville_gratuite} cedex', f'{ville_gratuite}-cedex'}
    if ville.strip().lower() in villes_gratuites:
        return 0.0
    return current_app.config['FRAIS_LIVRAISON_HORS_ZONE']


def _generer_numero() -> str:
    return 'VG-' + uuid.uuid4().hex[:8].upper()


@bp.route('/commander', methods=['GET', 'POST'])
@login_required
def commander():
    menus_actifs = list(Menu.objects(actif=True, stock__gt=0).order_by('titre'))
    menu_preselectionne_id = request.args.get('menu_id', '')

    if request.method == 'POST':
        menu_id = request.form.get('menu_id', '')
        menu = charger(Menu, menu_id)

        if not menu or not menu.actif:
            flash("Menu introuvable.", 'danger')
            return redirect(url_for('commandes.commander'))

        if menu.stock <= 0:
            flash("Ce menu n'est plus disponible (stock épuisé).", 'danger')
            return redirect(url_for('commandes.commander'))

        # Récupération des champs
        adresse = request.form.get('adresse_livraison', '').strip()
        ville = request.form.get('ville_livraison', '').strip()
        code_postal = request.form.get('code_postal_livraison', '').strip()
        date_prestation_str = request.form.get('date_prestation', '')
        heure = request.form.get('heure_livraison', '').strip()
        nb_personnes = request.form.get('nb_personnes', type=int, default=0)
        pret_materiel = request.form.get('pret_materiel') == 'on'
        conditions_acceptees = request.form.get('conditions_acceptees')

        erreurs = []
        if not adresse:
            erreurs.append("L'adresse de livraison est obligatoire.")
        if not ville:
            erreurs.append("La ville est obligatoire.")
        if not date_prestation_str:
            erreurs.append("La date de prestation est obligatoire.")
        if not heure:
            erreurs.append("L'heure de livraison est obligatoire.")
        if nb_personnes < menu.nb_personnes_min:
            erreurs.append(f"Le nombre minimum de personnes pour ce menu est {menu.nb_personnes_min}.")
        if not conditions_acceptees:
            erreurs.append("Vous devez accepter les conditions du menu avant de commander.")

        try:
            date_prest = date.fromisoformat(date_prestation_str)
            if date_prest < date.today():
                erreurs.append("La date de prestation doit être dans le futur.")
        except ValueError:
            erreurs.append("La date de prestation est invalide.")
            date_prest = None

        if erreurs:
            for e in erreurs:
                flash(e, 'danger')
            return render_template('commandes/commander.html',
                                   menus=menus_actifs,
                                   menu_preselectionne_id=menu_id)

        prix_menu = menu.calcul_prix(nb_personnes)
        prix_livraison = _calculer_livraison(ville)
        prix_total = round(prix_menu + prix_livraison, 2)

        # Réservation atomique du stock : évite la survente si deux clients
        # commandent le dernier exemplaire en même temps.
        if not Menu.objects(id=menu.id, stock__gt=0).update_one(dec__stock=1):
            flash("Ce menu n'est plus disponible (stock épuisé).", 'danger')
            return redirect(url_for('commandes.commander'))

        commande = Commande(
            numero=_generer_numero(),
            utilisateur=current_user._get_current_object(),
            menu=menu,
            date_prestation=date_prest,
            heure_livraison=heure,
            adresse_livraison=adresse,
            ville_livraison=ville,
            code_postal_livraison=code_postal,
            nb_personnes=nb_personnes,
            prix_menu=prix_menu,
            prix_livraison=prix_livraison,
            prix_total=prix_total,
            statut='en_attente',
            pret_materiel=pret_materiel,
            suivis=[SuiviCommande(statut='en_attente')],
        )
        try:
            commande.save()
        except Exception:
            # Échec de l'enregistrement : on rend le stock réservé
            Menu.objects(id=menu.id).update_one(inc__stock=1)
            raise

        envoyer_confirmation_commande(commande)
        flash(f"Votre commande n°{commande.numero} a bien été enregistrée !", 'success')
        return redirect(url_for('utilisateur.mes_commandes'))

    return render_template('commandes/commander.html',
                           menus=menus_actifs,
                           menu_preselectionne_id=menu_preselectionne_id)


@bp.route('/api/prix')
@login_required
def api_prix():
    """Calcule le prix en temps réel (AJAX)."""
    menu_id = request.args.get('menu_id', '')
    nb_personnes = request.args.get('nb_personnes', type=int, default=0)
    ville = request.args.get('ville', '')

    menu = charger(Menu, menu_id)
    if not menu:
        return jsonify({'erreur': 'Menu introuvable'}), 404

    if nb_personnes < menu.nb_personnes_min:
        nb_personnes = menu.nb_personnes_min

    prix_menu = menu.calcul_prix(nb_personnes)
    prix_livraison = _calculer_livraison(ville)
    reduction = nb_personnes >= menu.nb_personnes_min + 5

    return jsonify({
        'prix_menu': prix_menu,
        'prix_livraison': prix_livraison,
        'prix_total': round(prix_menu + prix_livraison, 2),
        'reduction_appliquee': reduction,
        'nb_personnes_min': menu.nb_personnes_min,
    })
