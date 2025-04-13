from flask import Blueprint, jsonify
from app.models import Instruction

instructions_bp = Blueprint('instructions', __name__)

@instructions_bp.route('/api/instructions', methods=['GET'])
def get_instructions():
    instructions = Instruction.query.all()  # Получаем все инструкции из базы данных
    instructions_list = [
        {
            "id": instruction.id,
            "title_ru": instruction.title_ru,
            "title_en": instruction.title_en,
            "title_kk": instruction.title_kk,
            "text_ru": instruction.text_ru,
            "text_en": instruction.text_en,
            "text_kk": instruction.text_kk
        }
        for instruction in instructions
    ]
    return jsonify(instructions_list)
