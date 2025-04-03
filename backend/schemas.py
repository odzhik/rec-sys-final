from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr

# 🔹 Вывод пользователя (без пароля)
class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_admin: bool

    class Config:
        from_attributes = True  # Позволяет работать с SQLAlchemy-моделями

# 🔹 Обновление данных пользователя
class UserUpdate(BaseModel):
    username: str
    email: EmailStr  # Теперь email корректно валидируется

# 🔹 Смена пароля
class PasswordChange(BaseModel):
    old_password: str
    new_password: str

# 🔹 Создание пользователя
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

# 🔹 Создание события
class EventCreate(BaseModel):
    name: str
    description: Optional[str] = None
    location: str
    date: datetime
    price: int

# 🔹 Отображение события
class EventOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    location: str
    date: datetime
    price: int
    category: str  # Добавляем категорию
    available_tickets: int  # Добавляем количество доступных билетов
    total_tickets: int 
    class Config:
        from_attributes = True

# 🔹 Создание билета
class TicketCreate(BaseModel):
    user_id: int
    event_id: int

# 🔹 Отображение билета
class TicketOut(BaseModel):
    id: int
    user_id: int
    event_id: int
    purchase_date: datetime

    class Config:
        from_attributes = True

# 🔹 Токен
class Token(BaseModel):
    access_token: str
    token_type: str

# 🔹 Логин пользователя
class UserLogin(BaseModel):
    email: str
    password: str