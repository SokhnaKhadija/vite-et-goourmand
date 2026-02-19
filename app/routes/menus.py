from flask import Blueprint, render_template, request, jsonify
from ..models import db, Menu, Theme, Regime

bp = Blueprint('menus', __name__)


@bp.route('/')
def liste():
    themes = Theme.query.order_by(Theme.libelle).all()
    regimes = Regime.query.order_by(Regime.libelle).all()
    return render_template('menus/liste.html', themes=themes, regimes=regimes)


@bp.route('/api/filtrer')
def api_filtrer():
    """API JSON pour le filtrage dynamique sans rechargement de page."""
    prix_max = request.args.get('prix_max', type=float)
    prix_min = request.args.get('prix_min', type=float)
    theme_id = request.args.get('theme_id', type=int)
    regime_id = request.args.get('regime_id', type=int)
    nb_personnes = request.args.get('nb_personnes', type=int)

    query = Menu.query.filter_by(actif=True)

    if prix_max is not None:
        query = query.filter(Menu.prix_base <= prix_max)
    if prix_min is not None:
        query = query.filter(Menu.prix_base >= prix_min)
    if theme_id:
        query = query.filter(Menu.theme_id == theme_id)
    if regime_id:
        query = query.filter(Menu.regime_id == regime_id)
    if nb_personnes:
        query = query.filter(Menu.nb_personnes_min <= nb_personnes)

    menus = query.order_by(Menu.created_at.desc()).all()

    resultats = []
    for m in menus:
        premiere_image = m.images[0].chemin if m.images else None
        resultats.append({
            'id': m.id,
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


@bp.route('/<int:menu_id>')
def detail(menu_id):
    menu = Menu.query.get_or_404(menu_id)
    if not menu.actif:
        from flask import abort
        abort(404)
    return render_template('menus/detail.html', menu=menu)
