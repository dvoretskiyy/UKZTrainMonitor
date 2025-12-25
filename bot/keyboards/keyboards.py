from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict, Any
from config import config


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Додати маршрут моніторингу")],
            [KeyboardButton(text="📋 Мої маршрути")]
        ],
        resize_keyboard=True
    )
    return keyboard


def get_stations_keyboard(stations: List[Dict[str, Any]], prefix: str = "station") -> InlineKeyboardMarkup:
    buttons = []
    
    max_stations = min(len(stations), config.MAX_STATIONS_TO_SHOW)
    for station in stations[:max_stations]:
        station_id = station.get("id")
        station_name = station.get("name")
        buttons.append([
            InlineKeyboardButton(
                text=station_name, 
                callback_data=f"{prefix}:{station_id}:{station_name}"
            )
        ])
    
    buttons.append([InlineKeyboardButton(text="« Назад", callback_data="back_to_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_dates_keyboard(
    dates: List[str], 
    selected_dates: List[str], 
    page: int = 0
) -> InlineKeyboardMarkup:
    dates_per_page = config.DATES_PER_PAGE
    total_pages = (len(dates) + dates_per_page - 1) // dates_per_page
    
    start_idx = page * dates_per_page
    end_idx = min(start_idx + dates_per_page, len(dates))
    page_dates = dates[start_idx:end_idx]
    
    buttons = []
    
    for i in range(0, len(page_dates), 3):
        row = []
        for date in page_dates[i:i+3]:
            icon = "🟢" if date in selected_dates else "⚪"
            row.append(
                InlineKeyboardButton(
                    text=f"{icon} {date[5:]}", 
                    callback_data=f"date:{date}"
                )
            )
        buttons.append(row)
    
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️", callback_data=f"date_page:{page-1}"))
    
    nav_row.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="noop"))
    
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton(text="➡️", callback_data=f"date_page:{page+1}"))
    
    buttons.append(nav_row)
    
    buttons.append([
        InlineKeyboardButton(text="« Назад", callback_data="back_to_arrival"),
        InlineKeyboardButton(text="Далі »»", callback_data="confirm_dates")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_wagon_classes_keyboard(selected_classes: List[str]) -> InlineKeyboardMarkup:
    buttons = []
    
    for class_code, class_name in config.WAGON_CLASSES.items():
        icon = "🟢" if class_code in selected_classes else "🔴"
        buttons.append([
            InlineKeyboardButton(
                text=f"{icon} {class_name} ({class_code})",
                callback_data=f"wagon:{class_code}"
            )
        ])
    
    buttons.append([
        InlineKeyboardButton(text="« Назад", callback_data="back_to_dates"),
        InlineKeyboardButton(text="Підтвердити", callback_data="confirm_route")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_routes_list_keyboard(routes: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    buttons = []
    
    for route in routes:
        route_id = route.get("id")
        from_name = route.get("station_from_name")
        to_name = route.get("station_to_name")
        is_active = route.get("is_active", True)
        
        status_icon = "✅" if is_active else "⏸"
        
        buttons.append([
            InlineKeyboardButton(
                text=f"{status_icon} {from_name} → {to_name}",
                callback_data=f"route_details:{route_id}"
            )
        ])
    
    buttons.append([InlineKeyboardButton(text="« Назад", callback_data="back_to_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_route_details_keyboard(route_id: int, is_active: bool) -> InlineKeyboardMarkup:
    buttons = []
    
    if is_active:
        buttons.append([InlineKeyboardButton(text="⏸ Призупинити", callback_data=f"pause_route:{route_id}")])
    else:
        buttons.append([InlineKeyboardButton(text="▶️ Відновити", callback_data=f"resume_route:{route_id}")])
    
    buttons.append([InlineKeyboardButton(text="🗑 Видалити", callback_data=f"delete_route:{route_id}")])
    buttons.append([InlineKeyboardButton(text="« Назад до списку", callback_data="my_routes")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="« Назад", callback_data="back_to_menu")]
        ]
    )
