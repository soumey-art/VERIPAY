import json
from datetime import datetime, timezone
from sqlalchemy import JSON, ForeignKey, String, UniqueConstraint, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_colum, sessionmaker
from . import config


def now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class Base():
    pass

class User(Base):
    __tablename__ ="users"
    id: Mapped[int] = mapped_colum(primary_key= True)
    email: Mapped[str] = mapped_colum(String(255), unique=True)
    pw_hash: Mapped[str]
    role: Mapped[str]
    crated_at: Mapped[datetime] = mapped_colum(default=now)
    
class Invoice(Base):
    __tablename__="invoices"
    merchant_id : Mapped[int] = mapped_colum(ForeignKey("users.id"))
    payer_id: Mapped[int | None] = mapped_colum(ForeignKey("users.id"), nullable=True)
    description: Mapped[str]
    amount_sat: Mapped[str]
    status: Mapped[str] = mapped_colum(defaulf="pending")
    crated_at: Mapped[datetime] = mapped_colum(defaulf=now)
    expires_at: Mapped[datetime]
    unsign_psbt: Mapped[str | None] = mapped_colum(nullable=True)
    unsign_txid: Mapped[str|None] = mapped_colum(nullable=True)
    txid: Mapped[str|None] = mapped_colum(nullable=True)
    
    
class VerificationRecord(Base):
    __tablename__= "verification_records"
    id: Mapped[int] = mapped_colum(primary_key = True)
    invoice_id: Mapped[str] = mapped_colum(ForeignKey("invoices.id"))
    ok: Mapped[bool]
    checks: Mapped[list] = mapped_colum(JSON)
    create_at: Mapped[datetime] = mapped_colum(default=now)
    
    
class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_colum(primary_key=True)
    user_id:Mapped[int | None]
    action:Mapped[str]
    detail:Mapped[str]
    created_at: Mapped[datetime] = mapped_colum(default=True)
    
    
engine = create_engine(config.DATABASE_URL, connect_args={"check_same_thread": False} if config.DATABASE_URL.startswitch("sqlite") else{})
Session = sessionmaker(engine, expire_on_commit=False)

def init_db():
    Base.metadata.create_all(engine)
    
def audit(db, user_id, action, detail=""):
    db.add(AuditLog(user_id=user_id, action=action, detail=detail))

