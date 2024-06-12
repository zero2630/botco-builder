from aiogram.filters import Command
from aiogram.types import Message, FSInputFile
from aiogram import Bot
from aiogram import Router

router = Router()


@router.message(Command(commands=["document", "doc"]))
async def get_document(message: Message, bot: Bot):
    document = FSInputFile(path=r"путь до документа")
    await bot.send_document(
        message.chat.id, document=document, caption="подпись под файлом"
    )


@router.message(Command(commands=["audio", "aud"]))
async def get_audio(message: Message, bot: Bot):
    audio = FSInputFile(
        path=r"путь до аудио файла", filename="имя аудио файла"
    )
    await bot.send_audio(message.chat.id, audio=audio)


@router.message(Command(commands=["photo", "ph"]))
async def get_photo(message: Message, bot: Bot):
    photo = FSInputFile(path=r"путь до фото")
    await bot.send_photo(message.chat.id, photo, caption="подпись под фото")
