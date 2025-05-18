from flask import Blueprint, request, jsonify
from app.models import MedicalRequest, User, db
from app.utils.telegram_notify import send_telegram_message

medical_requests_bp = Blueprint('medical_requests', __name__)


@medical_requests_bp.route('/api/medical_requests', methods=['POST'])
def create_medical_request():
    data = request.get_json()
    user_id = data.get('user_id')  # это Telegram ID
    reason = data.get('reason')
    date = data.get('date')

    if not user_id or not reason or not date:
        return jsonify({"message": "Missing required fields"}), 400

    new_request = MedicalRequest(user_id=user_id, reason=reason, date=date)
    db.session.add(new_request)
    db.session.commit()

    return jsonify({"message": "Medical request created successfully", "id": new_request.id}), 201


@medical_requests_bp.route('/api/medical_requests/<user_id>', methods=['GET'])
def get_medical_requests_by_user(user_id):
    requests = MedicalRequest.query.filter_by(user_id=str(user_id)).all()
    if not requests:
        return jsonify({"message": "No requests found for this user"}), 404

    requests_list = [
        {
            "id": request.id,
            "reason": request.reason,
            "status": request.status,
            "date": request.date.strftime('%Y-%m-%d %H:%M')
        }
        for request in requests
    ]
    return jsonify(requests_list)

@medical_requests_bp.route('/api/medical_requests/<int:request_id>/upload_file', methods=['POST'])
def upload_medical_file(request_id):
    medical_request = MedicalRequest.query.get(request_id)
    if not medical_request:
        return jsonify({"message": "Medical request not found"}), 404

    if 'file' not in request.files:
        return jsonify({"message": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400

    medical_request.file_name = file.filename
    medical_request.file_data = file.read()
    medical_request.file_mime = file.mimetype

    db.session.commit()

    return jsonify({"message": "File uploaded successfully", "file_name": file.filename})

from flask import send_file
import io

@medical_requests_bp.route('/api/medical_requests/<int:request_id>/download', methods=['GET'])
def download_medical_file(request_id):
    medical_request = MedicalRequest.query.get(request_id)
    if not medical_request or not medical_request.file_data:
        return jsonify({"message": "File not found"}), 404

    return send_file(
        io.BytesIO(medical_request.file_data),
        mimetype=medical_request.file_mime or 'application/octet-stream',
        as_attachment=True,
        download_name=medical_request.file_name or 'file.bin'
    )

@medical_requests_bp.route('/admin/medical_request/<int:request_id>/download')
def download_file_from_admin(request_id):
    req = MedicalRequest.query.get(request_id)
    if not req or not req.file_data:
        return jsonify({"message": "File not found"}), 404

    return send_file(
        io.BytesIO(req.file_data),
        mimetype=req.file_mime or 'application/octet-stream',
        as_attachment=True,
        download_name=req.file_name or 'file.bin'
    )

@medical_requests_bp.route('/api/medical_requests/<int:request_id>/status', methods=['PUT'])
def update_request_status(request_id):
    data = request.get_json()
    new_status = data.get('status')

    medical_request = MedicalRequest.query.get(request_id)
    if not medical_request:
        return jsonify({"message": "Request not found"}), 404

    old_status = medical_request.status
    medical_request.status = new_status
    db.session.commit()

    # Уведомление в Telegram
    message = f"📢 Статус вашей заявки в медпункт обновлён:\n<b>{new_status}</b>"
    send_telegram_message(medical_request.user_id, message)

    return jsonify({"message": "Status updated", "old_status": old_status, "new_status": new_status})
