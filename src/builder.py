import json
from pathlib import Path
import shutil

import aiofiles
from jinja2 import Environment, FileSystemLoader

from src.config import DATA_FOLDER

__all__ = [
    "archive_bot",
    "build",
    "build_base",
    "build_command_blocks",
    "build_default",
    "build_media_blocks",
    "build_reply_keyboard",
    "build_states",
    "build_text_blocks",
    "check_media",
    "load_media",
    "rebuild_blueprint",
    "remove",
    "set_token",
]


file_loader = FileSystemLoader("templates")
env = Environment(loader=file_loader)


# Обрабатывает json для создания бота
async def rebuild_blueprint(blueprint):
    # Создаем словарь для цепей состояний
    # и сохраняем блок из запроса в список для их изменения
    states = {}
    blocks = blueprint["blocks"]
    text_blocks = []
    command_blocks = []
    media_blocks = {"audio": [], "document": [], "image": []}
    start_block = {}

    # пробегаемся по каждому блоку и обрабатываем его
    for block in blocks:
        if "trigger" in block["parameters"]:
            block["parameters"]["trigger"] = block["parameters"][
                "trigger"
            ].lower()

        # Если блок является основой древа то создаем новую цепочку состояний
        if block["father"] is None and len(block["children"]) > 0:
            states[block["id"]] = ["first_state"]
            block["state"] = "first_state"
            block["father_state"] = None
            block["root_block"] = block["id"]

        # Если блок является частью или
        # окончанием цепочки то находим корень, родителя и ветку
        elif block["father"] is not None:
            branches = []

            # Находим родителя и определяем
            # номер ветки по порядку детей родителя
            cur_block = list(
                filter(
                    lambda x: x["id"] == block["father"],
                    blueprint["blocks"],
                ),
            )[0]
            block_id = cur_block["children"].index(block["id"]) + 1
            branches.append(f"B{block_id}")

            # Ищем начало цепи и составляем путь ветвлений к нашему блоку
            while cur_block["father"] is not None:
                prev_block = cur_block
                cur_block = list(
                    filter(
                        lambda x: x["id"] == prev_block["father"],
                        blueprint["blocks"],
                    ),
                )[0]
                block_id = cur_block["children"].index(prev_block["id"]) + 1
                branches.append(f"B{block_id}")

            # Сейчас цепочка записана с конца, но логичнее
            # записывать ветвоения от начала
            # цепи (переворачиваем родословную)
            branches = branches[::-1]

            # Если у блока есть дети то записываем его
            # в цепь состояний, но если у него их нет,
            # то он будет только завершать состояние родителя
            if len(block["children"]) > 0:
                cur_branch = "".join(branches)
                states[cur_block["id"]].append(cur_branch)
                block["state"] = cur_branch
            else:
                block["state"] = None

            # Так как у корневого блока нету номера
            # ветки то мы обрабатываем это исключение
            if len(branches) > 1:
                block["father_state"] = "".join(branches[:-1])
            else:
                block["father_state"] = "first_state"

            block["root_block"] = cur_block["id"]

    for block in blocks:
        if block["type"] == "command":
            command_blocks.append(block)
        elif block["type"] == "answer":
            text_blocks.append(block)
        elif block["type"] == "media":
            media_blocks[block["parameters"]["media-type"]].append(block)
        elif block["type"] == "start":
            start_block = block

    return {
        "keyboards": blueprint["keyboards"],
        "states": states,
        "text_blocks": text_blocks,
        "command_blocks": command_blocks,
        "media_blocks": media_blocks,
        "start_block": start_block,
    }


# Создает директории для частей бота и генерирует конфиг
async def build_default(bot_uid):
    if not Path(DATA_FOLDER + f"bots/{bot_uid}").exists():
        Path(DATA_FOLDER + f"bots/{bot_uid}").mkdir()
        Path(DATA_FOLDER + f"bots/{bot_uid}/keyboards").mkdir()
        Path(DATA_FOLDER + f"bots/{bot_uid}/handlers").mkdir()
        Path(DATA_FOLDER + f"bots/{bot_uid}/media").mkdir()

    with Path(DATA_FOLDER + f"bots/{bot_uid}/conf.json").open(
        mode="w",
        encoding="utf-8",
    ) as f:
        json.dump({"token": None}, f)


# Создает главный скрипт бота
async def build_base(bot_uid, handlers):
    with Path(DATA_FOLDER + f"bots/{bot_uid}/bot.py").open(mode="w", encoding="utf-8") as f:
        template = env.get_template("base")
        f.write(template.render(bot_uid=bot_uid, handlers=handlers))


# Создает хэндлер для обработки текстовых сообщений
async def build_text_blocks(blocks, bot_uid):
    with Path(DATA_FOLDER + f"bots/{bot_uid}/handlers/default.py").open(
        mode="w",
        encoding="utf-8",
    ) as f:
        template = env.get_template("text_blocks")
        f.write(
            template.render(
                blocks=blocks,
            ),
        )


async def build_media_blocks(blocks, bot_uid):
    with Path(DATA_FOLDER + f"bots/{bot_uid}/handlers/media.py").open(
        mode="w",
        encoding="utf-8",
    ) as f:
        template = env.get_template("media_blocks")
        f.write(
            template.render(
                blocks=blocks,
                bot_uid=bot_uid,
            ),
        )


async def load_media(in_files, bot_uid):
    for in_file in in_files:
        async with aiofiles.open(
            DATA_FOLDER + f"bots/{bot_uid}/media/" + in_file.filename,
            "wb",
        ) as out_file:
            while content := await in_file.read(1024):  # async read chunk
                await out_file.write(content)  # async write chunk


async def check_media(media_blocks, bot_uid):
    filenames = list(Path(DATA_FOLDER + f"bots/{bot_uid}/media").glob("*"))
    blueprint_files = []
    for elem in ["audio", "document", "image"]:
        blueprint_files += [
            file["parameters"]["filename"] for file in media_blocks[elem]
        ]

    for file in filenames:
        if file.name not in blueprint_files:
            Path(DATA_FOLDER + f"bots/{bot_uid}/media/{file.name}").unlink(missing_ok=True)


# Создает хэндлер для обработки команд
async def build_command_blocks(start_block, command_blocks, bot_uid):
    with Path(DATA_FOLDER + f"bots/{bot_uid}/handlers/commands.py").open(
        mode="w",
        encoding="utf-8",
    ) as f:
        template = env.get_template("command_blocks")
        f.write(
            template.render(
                start_block=start_block,
                command_blocks=command_blocks,
            ),
        )


# Создает файл с клавиатурами-меню
async def build_reply_keyboard(keyboards, bot_uid):
    with Path(DATA_FOLDER + f"bots/{bot_uid}/keyboards/reply.py").open(
        mode="w",
        encoding="utf-8",
    ) as f:
        template = env.get_template("reply_keyboards")
        f.write(template.render(keyboards=keyboards))


async def build_states(states, bot_uid):
    with Path(DATA_FOLDER + f"bots/{bot_uid}/states.py").open(
        mode="w",
        encoding="utf-8",
    ) as f:
        template = env.get_template("states")
        f.write(template.render(states=states))


async def remove(bot_uid):
    shutil.rmtree(DATA_FOLDER + f"bots/{bot_uid}")
    if Path(DATA_FOLDER + f"archives/{bot_uid}").exists():
        shutil.rmtree(DATA_FOLDER + f"archives/{bot_uid}")


async def build(blueprint, bot_uid):
    new_dict = await rebuild_blueprint(blueprint)
    await check_media(new_dict["media_blocks"], bot_uid)
    await build_base(bot_uid, ["default", "commands", "media"])
    await build_states(new_dict["states"], bot_uid)
    await build_reply_keyboard(new_dict["keyboards"], bot_uid)
    await build_text_blocks(new_dict["text_blocks"], bot_uid)
    await build_media_blocks(new_dict["media_blocks"], bot_uid)
    await build_command_blocks(
        command_blocks=new_dict["command_blocks"],
        start_block=new_dict["start_block"],
        bot_uid=bot_uid,
    )


async def set_token(new_token, bot_uid):
    with Path(DATA_FOLDER + f"bots/{bot_uid}/conf.json").open(
        mode="w",
        encoding="utf-8",
    ) as f:
        json.dump({"token": new_token}, f)


async def archive_bot(bot_uid):
    shutil.make_archive(DATA_FOLDER + f"archives/{bot_uid}/bot", "zip", DATA_FOLDER + f"bots/{bot_uid}")


if __name__ == "__main__":
    pass
