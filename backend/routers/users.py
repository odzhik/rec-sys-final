from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.schemas import UserCreate, UserOut, UserLogin, Token
from backend.models import User
from backend.config import get_db
from datetime import timedelta
import jwt

# Секретный ключ для JWT (в будущем вынесем в .env)
SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

# 🔹 Создание токена
def create_access_token(data: dict):
    to_encode = data.copy()
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token

# 🔹 Регистрация пользователя (без хеширования пароля)
@router.post("/register", response_model=UserOut)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email уже используется")
    
    new_user = User(username=user.username, email=user.email, password=user.password)  # Просто сохраняем пароль без хеширования
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# 🔹 Логин пользователя (простая проверка пароля без хеширования)
@router.post("/login", response_model=Token)
def login_user(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or db_user.password != user.password:  # Простое сравнение строк
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    
    access_token = create_access_token({"sub": db_user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# 🔹 Получение списка пользователей (для теста)
@router.get("/", response_model=list[UserOut])
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users
