import re
from flask import Blueprint, render_template, request, flash, redirect, url_for, abort
from flask_login import login_required, current_user
from ..models import db, Commande, SuiviCommande, Avis, Utilisateur
from ..utils.decorateurs import role_requis

bp = Blueprint('utilisateur', __name__)

REGEX_MOT_DE_PASSE = re.compile(
    r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z\d]).{10,}$'
)


@bp.route('/profil', methods=['GET', 'POST'])
@login_required
def profil():
    if request.method == 'POST':
        current_user.nom = request.form.get('nom', '').strip() or current_user.nom
        current_user.prenom = request.form.get('prenom', '').strip() or current_user.prenom
        current_user.telephone = request.form.get('telephone', '').strip()
        current_user.adresse = request.form.get('adresse', '').strip()
        current_user.ville = request.form.get('ville', '').strip()
        current_user.code_postal = request.form.get('code_postal', '').strip()

        nouveau_mdp = request.form.get('nouveau_mot_de_passe', '')
        if nouveau_mdp:
            ancien = request.form.get('ancien_mot_de_passe', '')
            if not current_user.check_password(ancien):
                flash("Ancien mot de passe incorrect.", 'danger')
                return redirect(url_for('utilisateur.profil'))
            if not REGEX_MOT_DE_PASSE.match(nouveau_mdp):
                flash(
                    "Le nouveau mot de passe doit contenir au minimum 10 caractères, "
                    "une majuscule, une minuscule, un chiffre et un caractère spécial.",
                    'danger'
                )
                return redirect(url_for('utilisateur.profil'))
            current_user.set_password(nouveau_mdp)

        db.session.commit()
        flash("Profil mis à jour.", 'success')
        return redirect(url_for('utilisateur.profil'))

    return render_template('utilisateur/profil.html')


@bp.route('/commandes')
@login_required
def mes_commandes():
    commandes = (Commande.query
                 .filter_by(utilisateur_id=current_user.id)
                 .order_by(Commande.date_commande.desc())
                 .all())
    return render_template('utilisateur/commandes.html', commandes=commandes)


@bp.route('/commandes/<int:commande_id>')
@login_required
def detail_commande(commande_id):
    commande = Commande.query.get_or_404(commande_id)
    if commande.utilisateur_id != current_user.id:
        abort(403)
    return render_template('utilisateur/detail_commande.html', commande=commande)


@bp.route('/commandes/<int:commande_id>/modifier', methods=['GET', 'POST'])
@login_required
def modifier_commande(commande_id):
    commande = Commande.query.get_or_404(commande_id)
    if commande.utilisateur_id != current_user.id:
        abort(403)
    if not commande.peut_etre_modifiee:
        flash("Cette commande ne peut plus être modifiée.", 'warning')
        return redirect(url_for('utilisateur.detail_commande', commande_id=commande_id))

    if request.method == 'POST':
        commande.adresse_livraison = request.form.get('adresse_livraison', commande.adresse_livraison).strip()
        commande.ville_livraison = request.form.get('ville_livraison', commande.ville_livraison).strip()
        commande.code_postal_livraison = request.form.get('code_postal_livraison', '').strip()
        commande.heure_livraison = request.form.get('heure_livraison', commande.heure_livraison).strip()

        from datetime import date
        date_str = request.form.get('date_prestation', '')
        try:
            commande.date_prestation = date.fromisoformat(date_str)
        except ValueError:
            flash("Date invalide.", 'danger')
            return redirect(url_for('utilisateur.modifier_commande', commande_id=commande_id))

        nb_personnes = request.form.get('nb_personnes', type=int, default=commande.nb_personnes)
        if nb_personnes < commande.menu.nb_personnes_min:
            flash(f"Minimum {commande.menu.nb_personnes_min} personnes requis.", 'danger')
            return redirect(url_for('utilisateur.modifier_commande', commande_id=commande_id))

        from .commandes import _calculer_livraison
        commande.nb_personnes = nb_personnes
        commande.prix_menu = commande.menu.calcul_prix(nb_personnes)
        commande.prix_livraison = _calculer_livraison(commande.ville_livraison)
        commande.prix_total = round(commande.prix_menu + commande.prix_livraison, 2)

        db.session.commit()
        flash("Commande modifiée avec succès.", 'success')
        return redirect(url_for('utilisateur.detail_commande', commande_id=commande_id))

    return render_template('utilisateur/modifier_commande.html', commande=commande)


@bp.route('/commandes/<int:commande_id>/annuler', methods=['POST'])
@login_required
def annuler_commande(commande_id):
    commande = Commande.query.get_or_404(commande_id)
    if commande.utilisateur_id != current_user.id:
        abort(403)
    if not commande.peut_etre_modifiee:
        flash("Cette commande ne peut plus être annulée.", 'warning')
        return redirect(url_for('utilisateur.detail_commande', commande_id=commande_id))

    commande.statut = 'annulee'
    commande.menu.stock += 1
    suivi = SuiviCommande(commande_id=commande.id, statut='annulee')
    db.session.add(suivi)
    db.session.commit()
    flash("Commande annulée.", 'info')
    return redirect(url_for('utilisateur.mes_commandes'))


@bp.route('/commandes/<int:commande_id>/avis', methods=['GET', 'POST'])
@login_required
def donner_avis(commande_id):
    commande = Commande.query.get_or_404(commande_id)
    if commande.utilisateur_id != current_user.id:
        abort(403)
    if commande.statut != 'terminee':
        flash("Vous ne pouvez laisser un avis que sur une commande terminée.", 'warning')
        return redirect(url_for('utilisateur.detail_commande', commande_id=commande_id))
    if commande.avis_donne:
        flash("Vous avez déjà laissé un avis pour cette commande.", 'info')
        return redirect(url_for('utilisateur.detail_commande', commande_id=commande_id))

    if request.method == 'POST':
        note = request.form.get('note', type=int)
        commentaire = request.form.get('commentaire', '').strip()

        if not note or note < 1 or note > 5:
            flash("La note doit être comprise entre 1 et 5.", 'danger')
        else:
            avis = Avis(
                utilisateur_id=current_user.id,
                commande_id=commande.id,
                note=note,
                commentaire=commentaire,
                statut='en_attente'
            )
            db.session.add(avis)
            db.session.commit()
            flash("Votre avis a bien été soumis et sera publié après validation.", 'success')
            return redirect(url_for('utilisateur.detail_commande', commande_id=commande_id))

    return render_template('utilisateur/avis.html', commande=commande)
