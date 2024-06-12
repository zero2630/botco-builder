from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

links = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="текст", url="ссылки")],
        # для того что бы создать кнопку на след. строке
        [InlineKeyboardButton(text="текст", url="ссылки")],
    ]
)
