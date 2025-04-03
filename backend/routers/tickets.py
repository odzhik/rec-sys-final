from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.schemas import TicketCreate, TicketOut
from backend.models import Ticket, Event, User
from backend.config import get_db
from datetime import datetime

router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"]
)

# 🔹 Покупка билета
@router.post("/", response_model=TicketOut)
def buy_ticket(ticket: TicketCreate, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == ticket.event_id).first()
    user = db.query(User).filter(User.id == ticket.user_id).first()
    
    if not event or not user:
        raise HTTPException(status_code=404, detail="Событие или пользователь не найдены")
    
    new_ticket = Ticket(user_id=ticket.user_id, event_id=ticket.event_id, purchase_date=datetime.utcnow())
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)
    return new_ticket

# 🔹 Получение всех билетов пользователя
@router.get("/{user_id}", response_model=list[TicketOut])
def get_tickets(user_id: int, db: Session = Depends(get_db)):
    print(f"📢 Получен запрос на билеты для user_id={user_id}")
    tickets = db.query(Ticket).filter(Ticket.user_id == user_id).all()
    print(f"🎟 Найдено билетов: {len(tickets)}")
    return tickets

