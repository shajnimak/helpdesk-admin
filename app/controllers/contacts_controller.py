# app/controllers/contacts_controller.py
from flask import Blueprint, jsonify
from app.models import Contact

contacts_bp = Blueprint('contacts', __name__)

@contacts_bp.route('/api/contacts', methods=['GET'])
def get_contacts():
    contacts = Contact.query.all()  # Получаем все контакты из базы данных
    contacts_list = [
        {
            "id": contact.id,
            "department": contact.department,
            "phone": contact.phone,
            "email": contact.email,
            "category": contact.category
        }
        for contact in contacts
    ]
    return jsonify(contacts_list)
