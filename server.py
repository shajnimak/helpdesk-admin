import os
import aiohttp
from flask import Flask, request
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import UserToken
from app.utils.database import AsyncSessionLocal
from datetime import datetime, timedelta

app = Flask(__name__)

# OAuth Configuration
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID = os.getenv("TENANT_ID")
REDIRECT_URI = "https://helpdesk-admin-r0n0.onrender.com/callback"

# Async function to get the access token
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

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(token_url, data=token_data, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None
    except Exception as e:
        print(f"Error during token retrieval: {e}")
        return None

# Save token to PostgreSQL database
async def save_token_to_db(user_id: str, access_token: str):
    expires_at = datetime.utcnow() + timedelta(hours=1)
    async with AsyncSessionLocal() as session:
        try:
            async with session.begin():  # Safe transaction
                token = UserToken(user_id=user_id, token=access_token, expires_at=expires_at)
                session.add(token)
                await session.commit()  # Ensure commit is done
        except Exception as e:
            print(f"Error saving token to DB: {e}")
            await session.rollback()  # Rollback on error

# Callback route for handling the OAuth callback
@app.route('/callback')
async def callback():
    code = request.args.get('code')
    state = request.args.get('state')  # Telegram user ID

    if not code or not state:
        return "Error: missing code or user ID", 400

    token_data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }

    # Get access token and handle errors gracefully
    result = await get_access_token(code, state)
    if result is None:
        return "Error during authorization", 400

    access_token = result.get("access_token")
    if access_token:
        # Securely save the token to DB
        await save_token_to_db(state, access_token)
        return "Authorization successful! You can now use /inbox."
    else:
        return f"Authorization failed: {result}", 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
