from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.keyboards.keyboards import (
    get_routes_list_keyboard,
    get_route_details_keyboard,
    get_main_menu_keyboard
)
from services.db_service import RouteService
from config import config

router = Router()


@router.message(F.text == "📋 Мої маршрути")
async def show_my_routes(message: Message, state: FSMContext):
    await state.clear()
    
    routes = await RouteService.get_user_routes(message.from_user.id)
    
    if not routes:
        await message.answer(
            "У вас поки немає збережених маршрутів.\n\n"
            "Додайте перший маршрут для моніторингу!",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    routes_data = [
        {
            "id": r['id'],
            "station_from_name": r['station_from_name'],
            "station_to_name": r['station_to_name'],
            "is_active": r['is_active']
        }
        for r in routes
    ]
    
    await message.answer(
        f"📋 Ваші маршрути ({len(routes)}):\n\n"
        "Оберіть маршрут для перегляду деталей:",
        reply_markup=get_routes_list_keyboard(routes_data)
    )


@router.callback_query(F.data == "my_routes")
async def show_my_routes_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    
    routes = await RouteService.get_user_routes(callback.from_user.id)
    
    if not routes:
        await callback.message.edit_text(
            "У вас поки немає збережених маршрутів.\n\n"
            "Додайте перший маршрут для моніторингу!"
        )
        await callback.answer()
        return
    
    routes_data = [
        {
            "id": r['id'],
            "station_from_name": r['station_from_name'],
            "station_to_name": r['station_to_name'],
            "is_active": r['is_active']
        }
        for r in routes
    ]
    
    await callback.message.edit_text(
        f"📋 Ваші маршрути ({len(routes)}):\n\n"
        "Оберіть маршрут для перегляду деталей:",
        reply_markup=get_routes_list_keyboard(routes_data)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("route_details:"))
async def show_route_details(callback: CallbackQuery, state: FSMContext):
    route_id = int(callback.data.split(":", 1)[1])
    
    route = await RouteService.get_route_by_id(route_id)
    
    if not route:
        await callback.answer("❌ Маршрут не знайдено", show_alert=True)
        return
    
    status = "✅ Активний" if route['is_active'] else "⏸ Призупинено"
    classes_str = ", ".join([config.WAGON_CLASSES.get(c, c) for c in route['wagon_classes']])
    
    dates_preview = route['dates'][:5]
    dates_str = ", ".join([d[5:] for d in dates_preview])
    if len(route['dates']) > 5:
        dates_str += f" ... (всього {len(route['dates'])})"
    
    await callback.message.edit_text(
        f"🚉 Маршрут #{route['id']}\n\n"
        f"Від: {route['station_from_name']}\n"
        f"До: {route['station_to_name']}\n\n"
        f"📅 Дати: {dates_str}\n"
        f"🚂 Класи вагонів: {classes_str}\n\n"
        f"Статус: {status}\n"
        f"Створено: {route['created_at'].strftime('%Y-%m-%d %H:%M')}",
        reply_markup=get_route_details_keyboard(route['id'], route['is_active'])
    )
    await callback.answer()


@router.callback_query(F.data.startswith("pause_route:"))
async def pause_route(callback: CallbackQuery):
    route_id = int(callback.data.split(":", 1)[1])
    
    success = await RouteService.toggle_route_status(route_id)
    
    if success:
        route = await RouteService.get_route_by_id(route_id)
        await callback.answer("⏸ Маршрут призупинено")
        
        status = "✅ Активний" if route['is_active'] else "⏸ Призупинено"
        classes_str = ", ".join([config.WAGON_CLASSES.get(c, c) for c in route['wagon_classes']])
        
        dates_preview = route['dates'][:5]
        dates_str = ", ".join([d[5:] for d in dates_preview])
        if len(route['dates']) > 5:
            dates_str += f" ... (всього {len(route['dates'])})"
        
        await callback.message.edit_text(
            f"🚉 Маршрут #{route['id']}\n\n"
            f"Від: {route['station_from_name']}\n"
            f"До: {route['station_to_name']}\n\n"
            f"📅 Дати: {dates_str}\n"
            f"🚂 Класи вагонів: {classes_str}\n\n"
            f"Статус: {status}\n"
            f"Створено: {route['created_at'].strftime('%Y-%m-%d %H:%M')}",
            reply_markup=get_route_details_keyboard(route['id'], route['is_active'])
        )
    else:
        await callback.answer("❌ Помилка", show_alert=True)


@router.callback_query(F.data.startswith("resume_route:"))
async def resume_route(callback: CallbackQuery):
    route_id = int(callback.data.split(":", 1)[1])
    
    success = await RouteService.toggle_route_status(route_id)
    
    if success:
        route = await RouteService.get_route_by_id(route_id)
        await callback.answer("▶️ Маршрут відновлено")
        
        status = "✅ Активний" if route['is_active'] else "⏸ Призупинено"
        classes_str = ", ".join([config.WAGON_CLASSES.get(c, c) for c in route['wagon_classes']])
        
        dates_preview = route['dates'][:5]
        dates_str = ", ".join([d[5:] for d in dates_preview])
        if len(route['dates']) > 5:
            dates_str += f" ... (всього {len(route['dates'])})"
        
        await callback.message.edit_text(
            f"🚉 Маршрут #{route['id']}\n\n"
            f"Від: {route['station_from_name']}\n"
            f"До: {route['station_to_name']}\n\n"
            f"📅 Дати: {dates_str}\n"
            f"🚂 Класи вагонів: {classes_str}\n\n"
            f"Статус: {status}\n"
            f"Створено: {route['created_at'].strftime('%Y-%m-%d %H:%M')}",
            reply_markup=get_route_details_keyboard(route['id'], route['is_active'])
        )
    else:
        await callback.answer("❌ Помилка", show_alert=True)


@router.callback_query(F.data.startswith("delete_route:"))
async def delete_route(callback: CallbackQuery):
    route_id = int(callback.data.split(":", 1)[1])
    
    success = await RouteService.delete_route(route_id)
    
    if success:
        await callback.answer("🗑 Маршрут видалено")
        
        routes = await RouteService.get_user_routes(callback.from_user.id)
        
        if not routes:
            await callback.message.edit_text(
                "У вас більше немає збережених маршрутів.\n\n"
                "Додайте новий маршрут для моніторингу!"
            )
            return
        
        routes_data = [
            {
                "id": r['id'],
                "station_from_name": r['station_from_name'],
                "station_to_name": r['station_to_name'],
                "is_active": r['is_active']
            }
            for r in routes
        ]
        
        await callback.message.edit_text(
            f"📋 Ваші маршрути ({len(routes)}):\n\n"
            "Оберіть маршрут для перегляду деталей:",
            reply_markup=get_routes_list_keyboard(routes_data)
        )
    else:
        await callback.answer("❌ Помилка", show_alert=True)
