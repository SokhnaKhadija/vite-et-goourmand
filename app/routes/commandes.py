import uuid
from datetime import date
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import current_user, login_required
from ..models import db, Commande, SuiviCommande, Menu
from ..utils.email import envoyer_confirmation_commande

bp = Blueprint('commandes', __name__)

BORDEAUX_KEYWORDS = {'bordeaux', 'bordeaux cedex', 'bordeaux-cedex'}


def _calculer_livraison(ville: str) -> float:
    """Retourne 0€ si la ville est Bordeaux, sinon 15€ (forfait simplifié)."""
    if ville.strip().lower() in BORDEAUX_KEYWORDS:
        return 0.0
    return 15.0


def _generer_numero() -> str:
    return 'VG-' + uuid.uuid4().hex[:8].upper()


@bp.route('/commander', methods=['GET', 'POST'])
@login_required
def commander():
    menus_actifs = Menu.query.filter_by(actif=True).filter(Menu.stock > 0).order_by(Menu.titre).all()
    menu_preselectionne_id = request.args.get('menu_id', type=int)

    if request.method == 'POST':
        menu_id = request.form.get('menu_id', type=int)
        menu = Menu.query.get(menu_id)

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

        commande = Commande(
            numero=_generer_numero(),
            utilisateur_id=current_user.id,
            menu_id=menu.id,
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
            pret_materiel=pret_materiel
        )
        db.session.add(commande)
        db.session.flush()

        suivi = SuiviCommande(commande_id=commande.id, statut='en_attente')
        db.session.add(suivi)

        # Décrémentation du stock
        menu.stock -= 1

        # Mise à jour stats MongoDB
        try:
            from flask import current_app
            from pymongo import MongoClient
            client = MongoClient(current_app.config['MONGO_URI'])
            mongo_db = client[current_app.config['MONGO_DBNAME']]
            mongo_db.stats_commandes.update_one(
                {'menu_id': menu.id},
                {
                    '$inc': {'count': 1, 'chiffre_affaires': prix_total},
                    '$set': {'menu_titre': menu.titre}
                },
                upsert=True
            )
            client.close()
        except Exception:
            pass  # MongoDB non critique

        db.session.commit()
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
    menu_id = request.args.get('menu_id', type=int)
    nb_personnes = request.args.get('nb_personnes', type=int, default=0)
    ville = request.args.get('ville', '')

    menu = Menu.query.get(menu_id)
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
