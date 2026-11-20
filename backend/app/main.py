import uuid
from datetime import timedelta
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError

from . import config
from .bitcoin_rpc import BitcoinRpc, RpcError
from .crypto.psbt import address_matches_chain, parse_psbt, summarize, txid_of
from .db import Invoice, Session, User, VerificationRecord, audit, init_db, now
from .security import check_password, hash_password, make_token, read_token
from .services import process_payment, refresh_invoice

app = FastAPI(title="VeriPay", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
bearer = HTTPBearer(auto_error=False)
_rpc = BitcoinRpc()


@app.on_event("startup")
def _startup():
    init_db()


def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()


def get_rpc():
    return _rpc


def current_user(cred: HTTPAuthorizationCredentials | None = Depends(bearer), db=Depends(get_db)) -> User:
    try:
        user = db.get(User, int(read_token(cred.credentials)["sub"])) if cred else None
    except Exception:
        user = None
    if not user:
        raise HTTPException(401, "Not authenticated")
    return user


# ---------- auth ----------
class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class Registration(Credentials):
    role: Literal["merchant", "customer"]


@app.post("/api/v1/auth/register")
def register(body: Registration, db=Depends(get_db)):
    user = User(email=body.email.lower(), pw_hash=hash_password(body.password), role=body.role)
    db.add(user)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Email already registered")
    audit(db, user.id, "auth.register", body.role)
    db.commit()
    return {"access_token": make_token(user.id, user.role), "role": user.role}


@app.post("/api/v1/auth/login")
def login(body: Credentials, db=Depends(get_db)):
    user = db.query(User).filter_by(email=body.email.lower()).first()
    if not user or not check_password(body.password, user.pw_hash):
        audit(db, user.id if user else None, "auth.login_failed", body.email.lower())
        db.commit()
        raise HTTPException(401, "Wrong email or password")
    audit(db, user.id, "auth.login")
    db.commit()
    return {"access_token": make_token(user.id, user.role), "role": user.role}


# ---------- invoices ----------
class NewInvoice(BaseModel):
    amount_sat: int = Field(ge=546, le=21_000_000 * 100_000_000)     # 546 = dust limit
    description: str = Field(min_length=1, max_length=200)


def invoice_dict(i: Invoice) -> dict:
    return {"id": i.id, "description": i.description, "amount_sat": i.amount_sat, "address": i.address,
            "status": i.status, "created_at": i.created_at.isoformat()}


@app.post("/api/v1/invoices")
def create_invoice(body: NewInvoice, user=Depends(current_user), db=Depends(get_db), rpc=Depends(get_rpc)):
    if user.role != "merchant":
        raise HTTPException(403, "Only merchants can create invoices")
    try:
        address = rpc.get_new_address()                  # unique address per invoice
        if not address_matches_chain(address, rpc.get_chain()):
            raise HTTPException(502, "Node returned an address for the wrong network")
    except RpcError as e:
        raise HTTPException(502, str(e))
    inv = Invoice(id=uuid.uuid4().hex[:12], merchant_id=user.id, description=body.description, amount_sat=body.amount_sat,
                  address=address, expires_at=now() + timedelta(minutes=config.INVOICE_TTL_MIN))
    db.add(inv)
    audit(db, user.id, "invoice.create", inv.id)
    db.commit()
    return invoice_dict(inv)


@app.get("/api/v1/invoices")
def list_invoices(user=Depends(current_user), db=Depends(get_db), rpc=Depends(get_rpc)):
    q = db.query(Invoice)
    q = q.filter_by(merchant_id=user.id) if user.role == "merchant" else q.filter_by(payer_id=user.id)
    rows = q.order_by(Invoice.created_at.desc()).all()
    for inv in rows:
        refresh_invoice(db, inv, rpc)
    return [invoice_dict(i) for i in rows]


@app.get("/api/v1/invoices/{invoice_id}")
def get_invoice(invoice_id: str, user=Depends(current_user), db=Depends(get_db), rpc=Depends(get_rpc)):
    inv = db.get(Invoice, invoice_id)
    if not inv:
        raise HTTPException(404, "Invoice not found")
    confirmations = refresh_invoice(db, inv, rpc)

    if user.role == "customer" and inv.unsigned_psbt is None and inv.status == "pending":
        try:
            inv.unsigned_psbt = rpc.create_funded_psbt(inv.address, inv.amount_sat)
            inv.unsigned_txid = txid_of(parse_psbt(inv.unsigned_psbt).tx)
            db.commit()
        except RpcError as e:
            raise HTTPException(502, str(e))

    rec = db.query(VerificationRecord).filter_by(invoice_id=inv.id).order_by(VerificationRecord.id.desc()).first()
    summary = summarize(parse_psbt(inv.unsigned_psbt)) if inv.unsigned_psbt else {"outputs": [], "fee_sat": 0}
    return {**invoice_dict(inv), "psbt": inv.unsigned_psbt or "", "psbt_summary": summary,
            "checks": rec.checks if rec else [], "txid": inv.txid, "confirmations": confirmations,
            "required_confirmations": config.REQUIRED_CONFS}


# ---------- payments / verification ----------
class Submission(BaseModel):
    invoice_id: str
    signed_psbt: str = Field(min_length=20, max_length=200_000)


@app.post("/api/v1/payments/verify")
def verify_payment(body: Submission, user=Depends(current_user), db=Depends(get_db), rpc=Depends(get_rpc)):
    inv = db.get(Invoice, body.invoice_id)
    if not inv:
        raise HTTPException(404, "Invoice not found")
    if user.role != "customer":
        raise HTTPException(403, "Only customers can submit payments")
    return process_payment(db, inv, body.signed_psbt, user.id, rpc)


class PsbtOnly(BaseModel):
    psbt: str = Field(min_length=20, max_length=200_000)


@app.post("/api/v1/verification/psbt")
def inspect_psbt(body: PsbtOnly, user=Depends(current_user)):
    try:
        psbt = parse_psbt(body.psbt)
        return {"txid": txid_of(psbt.tx), **summarize(psbt), "signed_inputs": sum(1 for i in psbt.inputs if i.partial_sigs)}
    except Exception as e:
        raise HTTPException(400, f"Invalid PSBT: {e}")
