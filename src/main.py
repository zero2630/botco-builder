import datetime
import subprocess

from fastapi import Depends, FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import delete, insert, update
from sqlalchemy.ext.asyncio import AsyncSession
import uvicorn

from src import builder
from src import functions
from src import models
from src import schemas
from src.config import SECRET_KEY, DATA_FOLDER
from src.database import get_async_session

__all__ = [
    "activate",
    "bot_add_media",
    "bot_all",
    "bot_archive",
    "bot_delete",
    "bot_info",
    "build_bot",
    "create_bot",
    "create_user",
    "deactivate_bot",
    "delete_user",
    "get_user",
    "set_bot_token",
]


app = FastAPI()


origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


processes = {}


@app.get("/api/bot/{bot_uid}/")
async def bot_info(
    bot_uid: str,
    user_token: str,
    session: AsyncSession = Depends(get_async_session),
):
    errors = await functions.check_bot_and_user(user_token, bot_uid, session)
    if errors:
        return await functions.return_answer(errors=errors)

    status = "stopped"
    if bot_uid in processes:
        status = "running"

    bot_res = await functions.get_bot_info(bot_uid, session)
    result = {
        "id": bot_res.id,
        "user_id": bot_res.user_id,
        "uid": bot_res.uid,
        "blueprint": bot_res.blueprint,
        "last_start": bot_res.last_start,
        "created_at": bot_res.created_at.strftime("%B %d %Y - %H:%M:%S"),
        "updated_at": bot_res.updated_at.strftime("%B %d %Y - %H:%M:%S"),
        "status": status,
    }
    if result["last_start"]:
        result["last_start"] = (
            bot_res.last_start.strftime("%B %d %Y - %H:%M:%S"),
        )

    if bot_res:
        return result

    return "bot with this uid doesn't exists"


@app.get("/api/user/allbots/")
async def bot_all(
    user_token: str,
    session: AsyncSession = Depends(get_async_session),
):
    user_info = await functions.get_user_info(user_token, session)
    if not user_info:
        return await functions.return_answer(
            errors=["user with this uid doesn't exists"],
        )

    return await functions.get_all_bots(user_info.id, session)


@app.post("/api/bot/{bot_uid}/activate/")
async def activate(
    bot_uid: str,
    user_token: str,
    session: AsyncSession = Depends(get_async_session),
):
    errors = await functions.check_bot_and_user(user_token, bot_uid, session)
    if errors:
        return await functions.return_answer(errors=errors)

    if bot_uid not in processes:
        processes[bot_uid] = subprocess.Popen(
            ["python", DATA_FOLDER + f"bots/{bot_uid}/bot.py"],
        )
        bot_query = (
            update(models.bot)
            .where(models.bot.c.uid == bot_uid)
            .values(last_start=datetime.datetime.utcnow())
        )
        await session.execute(bot_query)
        await session.commit()
        return await functions.return_answer(messages=["bot activated"])

    return await functions.return_answer(messages=["bot already activated"])


@app.post("/api/bot/{bot_uid}/deactivate/")
async def deactivate_bot(
    bot_uid: str,
    user_token: str,
    session: AsyncSession = Depends(get_async_session),
):
    errors = await functions.check_bot_and_user(user_token, bot_uid, session)

    if errors:
        return await functions.return_answer(errors=errors)

    if bot_uid in processes:
        processes[bot_uid].terminate()
        processes.pop(bot_uid)
        bot_query = (
            update(models.bot)
            .where(models.bot.c.uid == bot_uid)
            .values(last_start=datetime.datetime.utcnow())
        )
        await session.execute(bot_query)
        await session.commit()
        return await functions.return_answer(messages=["bot deactivated"])

    return await functions.return_answer(messages=["bot already deactivated"])


@app.post("/api/bot/{bot_uid}/set_token/")
async def set_bot_token(
    bot_uid: str,
    user_token: str,
    new_token: str,
    session: AsyncSession = Depends(get_async_session),
):
    user_res = await functions.get_user_info(user_token, session)
    bot_res = await functions.get_bot_info(bot_uid, session)
    errors = []

    if not user_res:
        errors.append("user with this token doesn't exist")

    if not bot_res:
        errors.append("bot with this uid doesn't exist")

    if not await functions.check_token(new_token):
        errors.append("your token isn't valid")

    if errors:
        return await functions.return_answer(errors=errors)

    if bot_uid in processes:
        processes[bot_uid].terminate()
        processes.pop(bot_uid)

    await builder.set_token(new_token=new_token, bot_uid=bot_uid)

    return await functions.return_answer(messages=["token was changed"])


@app.post("/api/user/create/")
async def create_user(
    user_token: str,
    secret_key: str,
    session: AsyncSession = Depends(get_async_session),
):
    if secret_key == SECRET_KEY:
        if not await functions.get_user_info(user_token, session):
            user_stmt = insert(models.user).values(token=user_token)
            await session.execute(user_stmt)
            await session.commit()
            return "ok"

        return "user with this uid already exists"

    return "no roots"


@app.post("/api/user/delete/")
async def delete_user(
    user_token: str,
    secret_key: str,
    session: AsyncSession = Depends(get_async_session),
):
    if secret_key == SECRET_KEY:
        user_stmt = delete(models.user).where(
            models.user.c.token == user_token,
        )
        await session.execute(user_stmt)
        await session.commit()
        return "ok"

    return "no roots"


@app.get("/api/user/{user_token}/get/")
async def get_user(
    user_token: str,
    session: AsyncSession = Depends(get_async_session),
):
    user_res = await functions.get_user_info(user_token, session)

    return {
        "user_id": user_res.id,
        "user_token": user_res.token,
    }


@app.post("/api/bot/create/")
async def create_bot(
    bot_uid: str,
    user_token: str,
    session: AsyncSession = Depends(get_async_session),
):
    user_res = await functions.get_user_info(user_token, session)
    bot_res = await functions.get_bot_info(bot_uid, session)
    errors = []
    if not user_res:
        errors.append("user with this token doesn't exist")

    elif len(await functions.get_all_bots(user_res.id, session)) == 10:
        errors.append("you can't own more than 10 bots")

    if bot_res:
        errors.append("bot with this uid already exist")

    if errors:
        return await functions.return_answer(errors=errors)

    bot_stmt = insert(models.bot).values(user_id=user_res[0], uid=bot_uid)
    await session.execute(bot_stmt)
    await session.commit()
    await builder.build_default(bot_uid)
    return "ok"


@app.post("/api/bot/{bot_uid}/build/")
async def build_bot(
    bot_uid: str,
    user_token: str,
    blueprint: schemas.CreationBlueprint,
    session: AsyncSession = Depends(get_async_session),
):
    errors = await functions.check_bot_and_user(user_token, bot_uid, session)
    if errors:
        return await functions.return_answer(errors=errors)

    stmt = (
        update(models.bot)
        .where(models.bot.c.uid == bot_uid)
        .values(blueprint=blueprint.model_dump(mode="json"))
    )
    await session.execute(stmt)
    await session.commit()
    await builder.build(blueprint.model_dump(mode="python"), bot_uid)
    return await functions.return_answer(messages=["new bot was created"])


@app.post("/api/bot/{bot_uid}/add_media/")
async def bot_add_media(
    bot_uid: str,
    user_token: str,
    media_files: list[UploadFile],
    session: AsyncSession = Depends(get_async_session),
):
    errors = await functions.check_bot_and_user(user_token, bot_uid, session)
    if errors:
        return await functions.return_answer(errors=errors)

    await builder.load_media(media_files, bot_uid)
    return "ok"


@app.post("/api/bot/{bot_uid}/delete/")
async def bot_delete(
    bot_uid: str,
    user_token: str,
    session: AsyncSession = Depends(get_async_session),
):
    errors = await functions.check_bot_and_user(user_token, bot_uid, session)
    if errors:
        return await functions.return_answer(errors=errors)

    bot_stmt = delete(models.bot).where(models.bot.c.uid == bot_uid)
    await session.execute(bot_stmt)
    await session.commit()
    await builder.remove(bot_uid)
    return "ok"


@app.get("/api/bot/{bot_uid}/archive/")
async def bot_archive(
    bot_uid: str,
    user_token: str,
    session: AsyncSession = Depends(get_async_session),
):
    errors = await functions.check_bot_and_user(user_token, bot_uid, session)
    if errors:
        return await functions.return_answer(errors=errors)

    await builder.archive_bot(bot_uid)
    return FileResponse(
        path=DATA_FOLDER + f"archives/{bot_uid}/bot.zip",
        filename="bot.zip",
        media_type="multipart/form-data",
    )


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)
