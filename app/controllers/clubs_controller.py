from flask import Blueprint, jsonify
from app.models import Club

clubs_bp = Blueprint('clubs', __name__)

@clubs_bp.route('/api/clubs', methods=['GET'])
def get_clubs():
    clubs = Club.query.all()  # Получаем все клубы из базы данных
    clubs_list = [
        {
            "id": club.id,
            "name": club.name,
            "description": club.description,
            "url": club.url
        }
        for club in clubs
    ]
    return jsonify(clubs_list)
