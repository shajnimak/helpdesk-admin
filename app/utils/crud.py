# crud.py
from sqlalchemy.future import select
from app.models import UserToken
from app.utils.database import AsyncSession
from datetime import datetime, timedelta

async def get_token(session: AsyncSession, user_id: str):
    result = await session.execute(select(UserToken).where(UserToken.user_id == user_id))
    token = result.scalar_one_or_none()

    if token:
        if token.expires_at and token.expires_at < datetime.utcnow():
            await session.delete(token)
            await session.commit()
            return None
        return token.token

    return None


async def save_token(session: AsyncSession, user_id: str, access_token: str, expires_in: int = 3600):
    expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
    token = await session.get(UserToken, user_id)
    if token:
        token.token = access_token
        token.expires_at = expires_at
    else:
        token = UserToken(user_id=user_id, token=access_token, expires_at=expires_at)
        session.add(token)
    await session.commit()

