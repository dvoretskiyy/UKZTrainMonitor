from aiogram.fsm.state import State, StatesGroup


class RouteCreationStates(StatesGroup):
    waiting_for_departure_station = State()
    selecting_departure_station = State()
    
    waiting_for_arrival_station = State()
    selecting_arrival_station = State()
    
    selecting_dates = State()
    
    selecting_wagon_classes = State()
    
    confirmation = State()
