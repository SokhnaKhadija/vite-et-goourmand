from bson import ObjectId
from flask import Blueprint, render_template, request, jsonify, abort
from ..models import Menu, Theme, Regime, charger_ou_404

bp = Blueprint('menus', __name__)


@bp.route('/')
def liste():
    themes = list(Theme.objects.order_by('libelle'))
    regimes = list(Regime.objects.order_by('libelle'))
    return render_template('menus/liste.html', themes=themes, regimes=regimes)


@bp.route('/api/filtrer')
def api_filtrer():
    """API JSON pour le filtrage dynamique sans rechargement de page."""
    prix_max = request.args.get('prix_max', type=float)
    prix_min = request.args.get('prix_min', type=float)
    theme_id = request.args.get('theme_id', '')
    regime_id = request.args.get('regime_id', '')
    nb_personnes = request.args.get('nb_personnes', type=int)

    filtres = {'actif': True}

    if prix_max is not None:
        filtres['prix_base__lte'] = prix_max
    if prix_min is not None:
        filtres['prix_base__gte'] = prix_min
    if ObjectId.is_valid(theme_id):
        filtres['theme'] = ObjectId(theme_id)
    if ObjectId.is_valid(regime_id):
        filtres['regime'] = ObjectId(regime_id)
    if nb_personnes:
        filtres['nb_personnes_min__lte'] = nb_personnes

    menus = Menu.objects(**filtres).order_by('-created_at').select_related()

    resultats = []
    for m in menus:
        premiere_image = m.images[0].chemin if m.images else None
        resultats.append({
            'id': str(m.id),
            'titre': m.titre,
            'description': m.description[:150] + '...' if m.description and len(m.description) > 150 else m.description,
            'theme': m.theme.libelle,
            'regime': m.regime.libelle,
            'nb_personnes_min': m.nb_personnes_min,
            'prix_base': m.prix_base,
            'stock': m.stock,
            'image': premiere_image,
            'url_detail': f'/menus/{m.id}',
        })

    return jsonify(resultats)


@bp.route('/<menu_id>')
def detail(menu_id):
    menu = charger_ou_404(Menu, menu_id)
    if not menu.actif:
        abort(404)
    return render_template('menus/detail.html', menu=menu)
