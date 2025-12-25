from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.states.route_states import RouteCreationStates
from bot.keyboards.keyboards import (
    get_stations_keyboard,
    get_dates_keyboard,
    get_wagon_classes_keyboard,
    get_main_menu_keyboard
)
from uz_api.client import UZApiClient, UZApiException
from services.db_service import UserService, RouteService
from config import config
from datetime import datetime, timedelta
import logging

router = Router()
logger = logging.getLogger(__name__)
uz_client = UZApiClient()


@router.message(F.text == "➕ Додати маршрут моніторингу")
async def add_route_start(message: Message, state: FSMContext):
    await state.set_state(RouteCreationStates.waiting_for_departure_station)
    await message.answer(
        "🚉 Введіть назву станції відправлення:\n\n"
        "Наприклад: Київ, Львів, Одеса"
    )


@router.message(RouteCreationStates.waiting_for_departure_station)
async def process_departure_search(message: Message, state: FSMContext):
    search_query = message.text.strip()
    
    try:
        stations = await uz_client.search_stations(search_query)
        
        if not stations:
            await message.answer(
                "❌ Станції не знайдено. Спробуйте ще раз.\n\n"
                "Введіть назву станції:"
            )
            return
        
        await state.update_data(departure_search=search_query)
        await state.set_state(RouteCreationStates.selecting_departure_station)
        
        await message.answer(
            f"Знайдено станцій: {len(stations)}\n"
            "Оберіть станцію відправлення:",
            reply_markup=get_stations_keyboard(stations, "departure")
        )
        
    except UZApiException as e:
        logger.error(f"API error searching stations: {e}")
        await message.answer(
            "⚠️ Помилка при пошуку станцій. Спробуйте пізніше."
        )


@router.callback_query(F.data.startswith("departure:"))
async def select_departure_station(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":", 2)
    station_id = int(parts[1])
    station_name = parts[2]
    
    await state.update_data(
        departure_station_id=station_id,
        departure_station_name=station_name
    )
    
    await callback.message.edit_text(
        f"✅ Станція відправлення: {station_name}\n\n"
        f"🚉 Тепер введіть станцію прибуття:"
    )
    
    await state.set_state(RouteCreationStates.waiting_for_arrival_station)
    await callback.answer()


@router.message(RouteCreationStates.waiting_for_arrival_station)
async def process_arrival_search(message: Message, state: FSMContext):
    search_query = message.text.strip()
    
    try:
        stations = await uz_client.search_stations(search_query)
        
        if not stations:
            await message.answer(
                "❌ Станції не знайдено. Спробуйте ще раз.\n\n"
                "Введіть назву станції:"
            )
            return
        
        await state.update_data(arrival_search=search_query)
        await state.set_state(RouteCreationStates.selecting_arrival_station)
        
        await message.answer(
            f"Знайдено станцій: {len(stations)}\n"
            "Оберіть станцію прибуття:",
            reply_markup=get_stations_keyboard(stations, "arrival")
        )
        
    except UZApiException as e:
        logger.error(f"API error searching stations: {e}")
        await message.answer(
            "⚠️ Помилка при пошуку станцій. Спробуйте пізніше."
        )


@router.callback_query(F.data.startswith("arrival:"))
async def select_arrival_station(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":", 2)
    station_id = int(parts[1])
    station_name = parts[2]
    
    await state.update_data(
        arrival_station_id=station_id,
        arrival_station_name=station_name
    )
    
    today = datetime.now()
    dates = []
    for i in range(config.MAX_DATES_TO_SHOW):
        date = today + timedelta(days=i)
        dates.append(date.strftime("%Y-%m-%d"))
    
    await state.update_data(
        available_dates=dates,
        selected_dates=[],
        current_page=0
    )
    
    data = await state.get_data()
    await callback.message.edit_text(
        f"✅ Маршрут: {data['departure_station_name']} → {station_name}\n\n"
        f"📅 Оберіть дати для моніторингу:\n"
        f"(Натисніть на дату, щоб обрати. Для діапазону - натисніть +5 днів)\n\n"
        f"Доступно дат: {len(dates)}",
        reply_markup=get_dates_keyboard(dates, [], 0)
    )
    
    await state.set_state(RouteCreationStates.selecting_dates)
    await callback.answer()


@router.callback_query(F.data.startswith("date:"))
async def select_date(callback: CallbackQuery, state: FSMContext):
    date_str = callback.data.split(":", 1)[1]
    data = await state.get_data()
    
    selected_dates = data.get("selected_dates", [])
    available_dates = data.get("available_dates", [])
    current_page = data.get("current_page", 0)
    
    if date_str in selected_dates:
        selected_dates.remove(date_str)
    else:
        if len(selected_dates) == 0:
            selected_dates.append(date_str)
        else:
            last_date = selected_dates[-1]
            if last_date in available_dates and date_str in available_dates:
                idx_last = available_dates.index(last_date)
                idx_new = available_dates.index(date_str)
                
                if abs(idx_new - idx_last) <= 5:
                    start = min(idx_last, idx_new)
                    end = max(idx_last, idx_new)
                    for i in range(start, end + 1):
                        if available_dates[i] not in selected_dates:
                            selected_dates.append(available_dates[i])
                else:
                    selected_dates.append(date_str)
            else:
                selected_dates.append(date_str)
    
    await state.update_data(selected_dates=selected_dates)
    
    await callback.message.edit_reply_markup(
        reply_markup=get_dates_keyboard(available_dates, selected_dates, current_page)
    )
    await callback.answer(f"Обрано дат: {len(selected_dates)}")


@router.callback_query(F.data.startswith("date_page:"))
async def change_date_page(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split(":", 1)[1])
    data = await state.get_data()
    
    available_dates = data.get("available_dates", [])
    selected_dates = data.get("selected_dates", [])
    
    await state.update_data(current_page=page)
    
    await callback.message.edit_reply_markup(
        reply_markup=get_dates_keyboard(available_dates, selected_dates, page)
    )
    await callback.answer()


@router.callback_query(F.data == "confirm_dates")
async def confirm_dates(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected_dates = data.get("selected_dates", [])
    
    if not selected_dates:
        await callback.answer("⚠️ Оберіть хоча б одну дату!", show_alert=True)
        return
    
    await state.update_data(wagon_classes=list(config.DEFAULT_ACTIVE_CLASSES))
    
    await callback.message.edit_text(
        f"✅ Обрано дат: {len(selected_dates)}\n\n"
        f"🚂 Оберіть класи вагонів для моніторингу:\n"
        f"(Має бути обрано мінімум 1 клас)",
        reply_markup=get_wagon_classes_keyboard(list(config.DEFAULT_ACTIVE_CLASSES))
    )
    
    await state.set_state(RouteCreationStates.selecting_wagon_classes)
    await callback.answer()


@router.callback_query(F.data.startswith("wagon:"))
async def toggle_wagon_class(callback: CallbackQuery, state: FSMContext):
    wagon_class = callback.data.split(":", 1)[1]
    data = await state.get_data()
    
    wagon_classes = data.get("wagon_classes", [])
    
    if wagon_class in wagon_classes:
        if len(wagon_classes) > 1:
            wagon_classes.remove(wagon_class)
        else:
            await callback.answer("⚠️ Має залишитись хоча б один клас!", show_alert=True)
            return
    else:
        wagon_classes.append(wagon_class)
    
    await state.update_data(wagon_classes=wagon_classes)
    
    await callback.message.edit_reply_markup(
        reply_markup=get_wagon_classes_keyboard(wagon_classes)
    )
    await callback.answer(f"Обрано класів: {len(wagon_classes)}")


@router.callback_query(F.data == "confirm_route")
async def confirm_route_creation(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    user = await UserService.get_or_create_user(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
        last_name=callback.from_user.last_name
    )
    
    route = await RouteService.create_route(
        user_id=user["id"],
        station_from_id=data["departure_station_id"],
        station_from_name=data["departure_station_name"],
        station_to_id=data["arrival_station_id"],
        station_to_name=data["arrival_station_name"],
        dates=data["selected_dates"],
        wagon_classes=data["wagon_classes"]
    )
    
    classes_str = ", ".join([config.WAGON_CLASSES.get(c, c) for c in data["wagon_classes"]])
    
    await callback.message.edit_text(
        f"✅ Маршрут успішно додано!\n\n"
        f"🚉 Маршрут: {data['departure_station_name']} → {data['arrival_station_name']}\n"
        f"📅 Дат: {len(data['selected_dates'])}\n"
        f"🚂 Класи: {classes_str}\n\n"
        f"🔔 Моніторинг запущено!\n\n"
        f"💬 При появі квитків вам надійде повідомлення та груповий дзвінок.\n\n"
        f"📞 <b>Важливо!</b> Щоб отримувати дзвінки, напишіть будь-яке повідомлення боту {config.NOTIFICATION_ACCOUNT}",
        parse_mode="HTML"
    )
    
    await state.clear()
    await callback.answer("✅ Маршрут збережено!")


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(
        "Головне меню:",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.message.delete()
    await callback.answer()


@router.callback_query(F.data == "back_to_arrival")
async def back_to_arrival(callback: CallbackQuery, state: FSMContext):
    await state.set_state(RouteCreationStates.waiting_for_arrival_station)
    await callback.message.edit_text(
        "🚉 Введіть станцію прибуття:"
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_dates")
async def back_to_dates(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    available_dates = data.get("available_dates", [])
    selected_dates = data.get("selected_dates", [])
    current_page = data.get("current_page", 0)
    
    await state.set_state(RouteCreationStates.selecting_dates)
    
    await callback.message.edit_text(
        f"📅 Оберіть дати для моніторингу:",
        reply_markup=get_dates_keyboard(available_dates, selected_dates, current_page)
    )
    await callback.answer()
