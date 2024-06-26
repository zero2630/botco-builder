import requests
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api import models

__all__ = [
    "check_bot_and_user",
    "check_token",
    "get_all_bots",
    "get_bot_info",
    "get_user_info",
    "return_answer",
]


async def check_token(token: str):
    data = requests.get(
        f"https://api.telegram.org/bot{token}/getMe",
        timeout=1,
    ).json()

    if data["ok"]:
        return True

    return False


async def get_user_info(user_token: str, session: AsyncSession):
    user_query = select(models.user).where(models.user.c.token == user_token)
    result = await session.execute(user_query)

    return result.one_or_none()


async def get_bot_info(bot_uid: str, session: AsyncSession):
    bot_query = select(models.bot).where(models.bot.c.uid == bot_uid)
    result = await session.execute(bot_query)

    return result.one_or_none()


async def check_bot_and_user(
    user_token: str,
    bot_uid: str,
    session: AsyncSession,
):
    user_res = await get_user_info(user_token, session)
    bot_res = await get_bot_info(bot_uid, session)
    errors = []

    if not user_res:
        errors.append("user with this token doesn't exist")

    if not bot_res:
        errors.append("bot with this token doesn't exist")

    if bot_res and user_res:
        if bot_res.user_id != user_res.id:
            errors.append("no roots")

    return errors


async def return_answer(messages: list[str] = None, errors: list[str] = None):
    messages = messages or []
    errors = errors or []

    return {
        "messages": messages,
        "errors": errors,
    }


async def get_all_bots(user_id: int, session: AsyncSession):
    bot_query = select(models.bot).where(models.bot.c.user_id == user_id)
    result = await session.execute(bot_query)
    return [bot.uid for bot in result]
