from fastapi import FastAPI, Depends, HTTPException, APIRouter
from sqlalchemy.orm import Session
from backend.config import engine, Base, SessionLocal
from backend import models, schemas, crud, auth
from datetime import timedelta
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from backend.auth import router as auth_router
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import users, events, tickets
from backend.auth import get_current_user
from backend.models import User
from fastapi.middleware.cors import CORSMiddleware
from backend.auth import router as auth_router  
from pydantic import BaseModel
from backend.models import User  # Убедись, что модель User импортирована
from backend.auth import get_current_user  # Функция для аутентификации
import psycopg2
import os
import time
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
# Создаем приложение FastAPI
app = FastAPI()

router = APIRouter()
DATABASE_URL = "postgresql://postgres:1234@db:5432/event_platform"
# Подключаем маршруты авторизации

app.include_router(auth_router, prefix="/auth")
# Перемещаем это ниже после вызова wait_for_db()
# Base.metadata.create_all(bind=engine)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app.include_router(auth_router, prefix="/auth")
app.include_router(users.router)
app.include_router(events.router)
print("Маршрут /tickets загружается...")
app.include_router(tickets.router)

def wait_for_db():
    retries = 30  # Увеличиваем количество попыток подключения до 30
    while retries > 0:
        try:
            engine = create_engine(DATABASE_URL)
            with engine.connect():
                print("✅ Database is ready!")
                return engine  # Возвращаем успешное подключение к БД
        except OperationalError:
            print(f"⏳ Waiting for database to start... {retries} retries left")
            time.sleep(2)  # Подождать 2 секунды между попытками
            retries -= 1
    print("❌ Could not connect to the database!")
    exit(1)  # Завершаем процесс, если БД так и не поднялась

# Дожидаемся готовности БД и создаем таблицы
wait_for_db()
# Теперь, когда БД готова, создаем таблицы
Base.metadata.create_all(bind=engine)
print("✅ Database tables created successfully")

# Функция для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  #  Разрешаем ВСЁ для разработки
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Маршрут: Главная страница
@app.get("/")
def read_root():
    return {"message": "Добро пожаловать в Event Platform!"}

# ------------- РАБОТА С ПОЛЬЗОВАТЕЛЯМИ -------------

# Создание пользователя
@app.post("/users/", response_model=schemas.UserOut)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email уже используется")
    return crud.create_user(db, user)

# Получение списка пользователей
@app.get("/users/", response_model=list[schemas.UserOut])
def get_users(db: Session = Depends(get_db)):
    return crud.get_users(db)

# Получение пользователя по ID
@app.get("/users/{user_id}", response_model=schemas.UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user

# Функция получения текущего пользователя по токену
def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Не удалось подтвердить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = auth.decode_access_token(token)
    if payload is None:
        raise credentials_exception
    user = crud.get_user_by_email(db, payload.get("sub"))
    if user is None:
        raise credentials_exception
    return user

#  Получение профиля пользователя
@app.get("/users/me", response_model=schemas.UserOut)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

#  Обновление профиля пользователя
@app.put("/users/me", response_model=schemas.UserOut)
def update_user_profile(
    user_update: schemas.UserUpdate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    return crud.update_user(db, current_user.id, user_update)

# 🔹 Смена пароля пользователя
@app.patch("/users/me/password")
def change_password(
    password_data: schemas.PasswordChange, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    success = crud.change_user_password(db, current_user.id, password_data)
    if not success:
        raise HTTPException(status_code=400, detail="Старый пароль не верен")
    return {"message": "Пароль успешно обновлен"}

# ------------- РАБОТА С СОБЫТИЯМИ -------------

# Создание события
@app.post("/events/", response_model=schemas.EventOut)
def create_event(event: schemas.EventCreate, db: Session = Depends(get_db)):
    return crud.create_event(db, event)

# Получение списка событий
@app.get("/events/", response_model=list[schemas.EventOut])
def get_events(db: Session = Depends(get_db)):
    return crud.get_events(db)

# Получение события по ID
@app.get("/events/{event_id}", response_model=schemas.EventOut)
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = crud.get_event(db, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Событие не найдено")
    return event

# Авторизация и получение токена
@app.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Неверный email или пароль")
    access_token = auth.create_access_token({"sub": user.email}, expires_delta=timedelta(minutes=30))
    return {"access_token": access_token, "token_type": "bearer"}


# origins = [
#     "http://localhost:4200",  
# ]

from fastapi.middleware.cors import CORSMiddleware




@router.get("/users/me")
def get_current_user_data(current_user: User = Depends(get_current_user)):
    return current_user





class LoginRequest(BaseModel):
    email: str
    password: str

    

@app.post("/login")
def login(request: LoginRequest):
    return {"access_token": "example_token"}

@app.get("/profile", response_model=schemas.UserOut)
def get_profile(current_user: models.User = Depends(get_current_user)):
    return current_user


@app.get("/auth/profile")
def get_profile(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,  # Добавляем ID
        "email": current_user.email,
        "name": current_user.username
    }
 # Покупка билета
conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME", "event_platform"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD", "1234"),
    host=os.getenv("DB_HOST", "db"),  # Используем "db" вместо "localhost"
    port=os.getenv("DB_PORT", "5432")
)
cursor = conn.cursor()
class TicketRequest(BaseModel):
    user_id: int
    event_id: int

@app.post("/buy_ticket")
async def buy_ticket(request: TicketRequest, db: Session = Depends(get_db)):
    # Проверяем наличие билетов
    cursor.execute("SELECT available_tickets FROM events WHERE id = %s", (request.event_id,))
    result = cursor.fetchone()

    if not result:
        raise HTTPException(status_code=404, detail="Событие не найдено!")

    available_tickets = result[0]

    if available_tickets <= 0:
        raise HTTPException(status_code=400, detail="Билеты закончились!")

    # Обновляем количество билетов
    cursor.execute(
        "UPDATE events SET available_tickets = available_tickets - 1 WHERE id = %s",
        (request.event_id,)
    )
    conn.commit()

    # 🔥 ВАЖНО: добавляем запись в таблицу Ticket
    new_ticket = models.Ticket(
        user_id=request.user_id,
        event_id=request.event_id,
    )
    db.add(new_ticket)
    db.commit()

    return {"message": f"Билет на событие {request.event_id} куплен пользователем {request.user_id}"}


# Эндпоинт для получения всех забронированных событий пользователя
@app.get("/reservations/{user_id}", response_model=list[schemas.EventOut])
def get_user_reservations(user_id: int, db: Session = Depends(get_db)):
    tickets = db.query(models.Ticket).filter(models.Ticket.user_id == user_id).all()

    if not tickets:
        raise HTTPException(status_code=404, detail="Нет забронированных событий")

    events = []
    for ticket in tickets:
        event = db.query(models.Event).filter(models.Event.id == ticket.event_id).first()
        if event:
            events.append(event)

    return events


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
