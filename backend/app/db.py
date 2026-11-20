from datetime import datetime, timezone

from sqlalchemy import JSON, ForeignKey, String, UniqueConstraint, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from . import config


def now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    pw_hash: Mapped[str]
    role: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(default=now)


class Invoice(Base):
    __tablename__ = "invoices"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    payer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    description: Mapped[str]
    amount_sat: Mapped[int]
    address: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(default="pending")
    created_at: Mapped[datetime] = mapped_column(default=now)
    expires_at: Mapped[datetime]
    unsigned_psbt: Mapped[str | None] = mapped_column(nullable=True)
    unsigned_txid: Mapped[str | None] = mapped_column(nullable=True)
    txid: Mapped[str | None] = mapped_column(nullable=True)


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (UniqueConstraint("txid", "vout"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[str] = mapped_column(ForeignKey("invoices.id"))
    txid: Mapped[str]
    vout: Mapped[int]
    amount_sat: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(default=now)


class VerificationRecord(Base):
    __tablename__ = "verification_records"
    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[str] = mapped_column(ForeignKey("invoices.id"))
    ok: Mapped[bool]
    checks: Mapped[list] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(default=now)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None]
    action: Mapped[str]
    detail: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(default=now)


engine = create_engine(
    config.DATABASE_URL,
    connect_args={"check_same_thread": False} if config.DATABASE_URL.startswith("sqlite") else {},
)
Session = sessionmaker(engine, expire_on_commit=False)


def init_db():
    Base.metadata.create_all(engine)


def audit(db, user_id, action, detail=""):
    db.add(AuditLog(user_id=user_id, action=action, detail=detail))
