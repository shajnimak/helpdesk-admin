from flask import Blueprint, redirect, request, jsonify, session
import requests
import os
from .models import db, User

oauth_bp = Blueprint("oauth", __name__)

MICROSOFT_AUTH_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
MICROSOFT_TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
MICROSOFT_USERINFO_URL = "https://graph.microsoft.com/v1.0/me"

client_id = os.getenv("MICROSOFT_CLIENT_ID")
client_secret = os.getenv("MICROSOFT_CLIENT_SECRET")
redirect_uri = os.getenv("MICROSOFT_REDIRECT_URI")


@oauth_bp.route("/api/telegram/oauth/login")
def microsoft_login():
    telegram_id = request.args.get("telegram_id")  # получаем из WebApp
    session["telegram_id"] = telegram_id
    return redirect(
        f"{MICROSOFT_AUTH_URL}?client_id={client_id}&response_type=code"
        f"&redirect_uri={redirect_uri}&response_mode=query"
        f"&scope=User.Read"
    )


@oauth_bp.route("/api/telegram/oauth/callback")
def microsoft_callback():
    code = request.args.get("code")

    token_response = requests.post(
        MICROSOFT_TOKEN_URL,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ).json()

    access_token = token_response.get("access_token")
    user_info = requests.get(
        MICROSOFT_USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"}
    ).json()

    # user_info содержит email, displayName, и т.д.
    email = user_info.get("mail") or user_info.get("userPrincipalName")
    name = user_info.get("displayName")

    # получаем telegram_id из сессии
    telegram_id = session.pop("telegram_id", None)

    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(email=email, name=name)

    user.telegram_id = telegram_id
    db.session.add(user)
    db.session.commit()

    return "Успешная авторизация! Можете закрыть это окно."

@oauth_bp.route("/api/telegram/me")
def get_user_info():
    # Получаем telegram_id из сессии
    telegram_id = request.args.get("telegram_id")

    if not telegram_id:
        return jsonify({"error": "Telegram ID is missing"}), 400

    user = User.query.filter_by(telegram_id=telegram_id).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    # Отправляем информацию о пользователе
    return jsonify({
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "telegram_id": user.telegram_id,
        "role": user.role,  # или другие данные, которые тебе нужны
    })
