from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from backend.config import SECRET_KEY, ALGORITHM, SessionLocal
from backend.models import User
from dotenv import load_dotenv
import os
from passlib.context import CryptContext
from . import models, schemas, security
from .models import User
from . import schemas
from . import models
from . import auth
from . import crud

router = APIRouter()

# Загружаем переменные окружения
load_dotenv()


# Время жизни токена (30 минут)
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Используем OAuth2 для авторизации
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_db():
    """Функция для создания сессии базы данных"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Создает JWT-токен с заданным временем жизни."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Расшифровывает JWT-токен и возвращает данные."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def authenticate_user(db: Session, username: str, password: str):
    """Проверяет пользователя по базе данных."""
    user = db.query(User).filter(User.username == username).first()
    if not user or password != user.password:
        return None
    return user


@router.post("/register")
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    """Регистрация нового пользователя"""
    existing_user = db.query(models.User).filter(models.User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email уже используется")

    new_user = models.User(username=user_data.username, email=user_data.email, password=user_data.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "Регистрация успешна"}

@router.post("/login")
def login(user_data: schemas.UserLogin, db: Session = Depends(get_db)):
    print("Email из запроса:", user_data.email)
    user = db.query(models.User).filter(models.User.email.ilike(user_data.email.strip())).first()
    
    # ЛОГ ДЛЯ ОТЛАДКИ
    print("Пользователь в БД:", user.email if user else "Не найден")
    print("Введённый пароль:", user_data.password)
    print("Пароль в БД:", user.password if user else "Нет пароля")

    if not user or user_data.password != user.password:
        raise HTTPException(status_code=400, detail="Неверный email или пароль")

    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}



@router.get("/me")
def get_me(user: models.User = Depends(security.get_current_user)):
    """Получение данных о текущем пользователе"""
    return {"username": user.username, "email": user.email}

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Функция для получения текущего пользователя по токену"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Не удалось подтвердить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = auth.decode_access_token(token)
    if payload is None:
        print("Ошибка: payload пустой")
        raise credentials_exception
    user = crud.get_user_by_email(db, payload.get("sub"))
    if user is None:
        print("Ошибка: пользователь не найден")
        raise credentials_exception
    return user

