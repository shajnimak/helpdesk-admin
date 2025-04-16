from flask import Blueprint, request, jsonify
from app import db
from app.models import TelegramToken

telegram_token_bp = Blueprint('telegram_token', __name__)

@telegram_token_bp.route('/api/telegram-token', methods=['POST'])
def save_token():
    data = request.json
    telegram_id = data.get('telegram_id')
    token = data.get('token')

    if not telegram_id or not token:
        return jsonify({"error": "telegram_id and token are required"}), 400

    existing = TelegramToken.query.filter_by(telegram_id=telegram_id).first()
    if existing:
        existing.token = token  # Обновляем токен
    else:
        new_token = TelegramToken(telegram_id=telegram_id, token=token)
        db.session.add(new_token)

    db.session.commit()
    return jsonify({"message": "Token saved"}), 200


@telegram_token_bp.route('/api/telegram-token/<telegram_id>', methods=['GET'])
def get_token(telegram_id):
    token_entry = TelegramToken.query.filter_by(telegram_id=telegram_id).first()
    if token_entry:
        return jsonify({"telegram_id": token_entry.telegram_id, "token": token_entry.token})
    else:
        return jsonify({"error": "Token not found"}), 404
