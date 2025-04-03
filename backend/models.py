from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from backend.config import Base
from datetime import datetime


# Таблица пользователей
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    
    tickets = relationship("Ticket", back_populates="user")

# Таблица событий
class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    location = Column(String, nullable=False)
    date = Column(DateTime, nullable=False)
    price = Column(Integer, nullable=False)
    category = Column(String, nullable=True)  # Категория
    available_tickets = Column(Integer, nullable=False)  # Доступные билеты
    total_tickets = Column(Integer, nullable=False)
    tickets = relationship("Ticket", back_populates="event")

# Таблица билетов
class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    event_id = Column(Integer, ForeignKey("events.id"))
    purchase_date = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="tickets")
    event = relationship("Event", back_populates="tickets")
