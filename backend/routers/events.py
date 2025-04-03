from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.schemas import EventCreate, EventOut
from backend.models import Event
from backend.config import get_db

router = APIRouter(
    prefix="/events",
    tags=["Events"]
)

# 🔹 Создание события
@router.post("/", response_model=EventOut)
def create_event(event: EventCreate, db: Session = Depends(get_db)):
    new_event = Event(**event.dict())
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    return new_event

# 🔹 Получение всех событий
@router.get("/", response_model=list[EventOut])
def get_events(db: Session = Depends(get_db)):
    return db.query(Event).all()

# 🔹 Получение события по ID
@router.get("/{event_id}", response_model=EventOut)
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Событие не найдено")
    return event

# 🔹 Удаление события
@router.delete("/{event_id}")
def delete_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Событие не найдено")
    
    db.delete(event)
    db.commit()
    return {"message": "Событие удалено"}
