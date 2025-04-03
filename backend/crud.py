from sqlalchemy.orm import Session
from backend import models, schemas
from passlib.context import CryptContext
from fastapi import HTTPException

# Создание пользователя
def create_user(db: Session, user: schemas.UserCreate):
    # Проверяем, есть ли пользователь с таким email
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")

    try:
        hashed_password = hash_password(user.password)
        db_user = models.User(username=user.username, email=user.email, password=hashed_password)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка создания пользователя: {str(e)}")

# Получение пользователя по ID
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

# Получение пользователя по email
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

# Получение всех пользователей
def get_users(db: Session):
    return db.query(models.User).all()

# Создание события
def create_event(db: Session, event: schemas.EventCreate):
    db_event = models.Event(
        name=event.name,
        description=event.description,
        location=event.location,
        date=event.date,
        price=event.price
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

# Получение всех событий
def get_events(db: Session):
    return db.query(models.Event).all()

# Получение события по ID
def get_event(db: Session, event_id: int):
    return db.query(models.Event).filter(models.Event.id == event_id).first()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Функция хеширования пароля
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Проверка пароля
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Создание пользователя с хешированием пароля
def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = hash_password(user.password)
    db_user = models.User(username=user.username, email=user.email, password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Проверка пользователя по email
def authenticate_user(db: Session, email: str, password: str):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not verify_password(password, user.password):
        return None
    return user

# 🔹 Обновление данных пользователя
def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # Проверяем, не занят ли новый email
    existing_user = db.query(models.User).filter(models.User.email == user_update.email, models.User.id != user_id).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Этот email уже используется другим пользователем")

    user.username = user_update.username
    user.email = user_update.email
    db.commit()
    db.refresh(user)
    return user

# 🔹 Смена пароля пользователя
def change_user_password(db: Session, user_id: int, old_password: str, new_password: str):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # Проверяем старый пароль
    if not verify_password(old_password, user.password):
        raise HTTPException(status_code=400, detail="Неверный старый пароль")

    # Хешируем новый пароль и сохраняем
    user.password = hash_password(new_password)
    db.commit()
    db.refresh(user)
    return {"message": "Пароль успешно изменен"}

def get_user_by_email(db: Session, email: str):
    print(f"Поиск пользователя с email: {email}")
    return db.query(models.User).filter(models.User.email == email).first()
