from flask import Blueprint, jsonify
from app.models import Event

events_bp = Blueprint('events', __name__)

@events_bp.route('/api/events', methods=['GET'])
def get_events():
    events = Event.query.all()  # Получаем все события из базы данных
    events_list = [
        {
            "id": event.id,
            "title_ru": event.title_ru,
            "title_en": event.title_en,
            "title_kk": event.title_kk,
            "description_ru": event.description_ru,
            "description_en": event.description_en,
            "description_kk": event.description_kk,
            "date": event.date.strftime('%Y-%m-%d %H:%M')
        }
        for event in events
    ]
    return jsonify(events_list)
