from flask import Blueprint, request, jsonify
from app.models import MedicalRequest, User, db

medical_requests_bp = Blueprint('medical_requests', __name__)


@medical_requests_bp.route('/api/medical_requests', methods=['POST'])
def create_medical_request():
    data = request.get_json()
    user_id = data.get('user_id')
    reason = data.get('reason')

    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    new_request = MedicalRequest(user_id=user_id, reason=reason)
    db.session.add(new_request)
    db.session.commit()

    return jsonify({"message": "Medical request created successfully", "id": new_request.id}), 201


@medical_requests_bp.route('/api/medical_requests/<int:user_id>', methods=['GET'])
def get_medical_requests_by_user(user_id):
    requests = MedicalRequest.query.filter_by(user_id=user_id).all()
    if not requests:
        return jsonify({"message": "No requests found for this user"}), 404

    requests_list = [
        {
            "id": request.id,
            "reason": request.reason,
            "status": request.status
        }
        for request in requests
    ]
    return jsonify(requests_list)
