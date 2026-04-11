from datetime import datetime

from app.extensions import db


class TicketNote(db.Model):
    __tablename__ = "ticket_notes"

    id = db.Column(db.Integer, primary_key=True)
    ticket_key = db.Column(db.String(64), unique=True, nullable=False, index=True)
    note = db.Column(db.Text, nullable=False, default="")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

