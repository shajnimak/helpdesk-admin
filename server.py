import os
import aiohttp
from flask import Flask, request
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import UserToken
from app.utils.database import AsyncSessionLocal
from datetime import datetime, timedelta

app = Flask(__name__)

# Конфигурация OAuth
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID = os.getenv("TENANT_ID")
REDIRECT_URI = "https://helpdesk-admin-r0n0.onrender.com/callback"

# Асинхронная функция для получения токена
async def get_access_token(code, state):
    token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    token_data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    async with aiohttp.ClientSession() as session:
        async with session.post(token_url, data=token_data, headers=headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                return None

# Сохранение токена в базу данных PostgreSQL
async def save_token_to_db(user_id: str, access_token: str):
    expires_at = datetime.utcnow() + timedelta(hours=1)
    async with AsyncSessionLocal() as session:
        async with session.begin():  # безопасная транзакция
            token = UserToken(user_id=user_id, token=access_token, expires_at=expires_at)
            session.add(token)

# Маршрут callback
@app.route('/callback')
async def callback():
    code = request.args.get('code')
    state = request.args.get('state')  # Telegram user ID

    if not code or not state:
        return "Ошибка: отсутствует код или ID пользователя", 400

    token_data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token", data=token_data) as response:
            if response.status == 200:
                result = await response.json()
                access_token = result.get("access_token")

                # 🔐 Безопасное сохранение токена
                await save_token_to_db(state, access_token)

                return "Авторизация успешна! Теперь можете использовать /inbox."
            else:
                return f"Ошибка при авторизации: {await response.text()}", 400

if __name__ == '__main__':
    app.run(host='0.0.0.0')




