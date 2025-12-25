from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from bot.keyboards.keyboards import get_main_menu_keyboard
from services.db_service import UserService

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    
    await UserService.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )
    
    await message.answer(
        "👋 Вітаю! Я бот для моніторингу квитків Укрзалізниці.\n\n"
        "Я допоможу вам відстежувати наявність квитків на потрібні маршрути "
        "та повідомлю, як тільки з'являться вільні місця!\n\n"
        "Оберіть дію:",
        reply_markup=get_main_menu_keyboard()
    )


@router.message(F.text == "« Назад")
async def back_to_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Головне меню:",
        reply_markup=get_main_menu_keyboard()
    )
