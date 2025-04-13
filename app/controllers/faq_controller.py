from flask import Blueprint, jsonify
from app.models import FAQ

faq_bp = Blueprint('faq', __name__)

@faq_bp.route('/api/faq', methods=['GET'])
def get_faq():
    faq_items = FAQ.query.all()  # Получаем все FAQ из базы данных
    faq_list = [
        {
            "id": faq.id,
            "question_ru": faq.question_ru,
            "question_en": faq.question_en,
            "question_kk": faq.question_kk,
            "answer_ru": faq.answer_ru,
            "answer_en": faq.answer_en,
            "answer_kk": faq.answer_kk
        }
        for faq in faq_items
    ]
    return jsonify(faq_list)
