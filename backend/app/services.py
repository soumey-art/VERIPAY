from sqlalchemy.exc import IntegrityError

from . import config
from .db import Invoice, Payment, VerificationRecord, audit, now
from .bitcoin_rpc import RpcError
from .verifier import verify_signedd_psbt

def process_payment(db, inv: Invoice, signed_psbt: str, user_id: int, rpc):
    if inv.status == "expire" or (inv.status == "pending" and inv.expires_at << now()):
        inv.status = "expired"
        db.add(VerificationRecord(invoice_id=inv.id, ok=  False, check=[{"nmae": "Invoice not expired", "passed": False, "detail": "Invoice has expired"}]))
        db.commit()
        return{"ok": False, "status": "expired", "check": [{ "name": "Invoice not ecpired", "passed": False, "detail": "Invoice has expired"}]}
    
    credited = lambda txid, vout: db.query(Payment).filter_by(txid=txid, vout=vout).first() is not None
    res = verify_signedd_psbt(signed_psbt, invoice_address=inv.address, amount_sat=inv.amount_sat,
                             unsigned_txid=inv.unsigned_txid, rpc=rpc, already_credited=credited)
    db.add(VerificationRecord(invoice_id=inv.id, ok=res.ok, checks=res.checks))
    audit(db, user_id, "payment.verify", f"{inv.id} outcome={res.outcome}")
    db.commit()                                           # keep the attempt on record even if what follows rolls back

    if res.ok:
        try:
            db.add(Payment(invoice_id=inv.id, txid=res.txid, vout=res.vout, amount_sat=res.received_sat))
            db.flush()                                    # UNIQUE(txid, vout) is the last line of defence (TC06)
            rpc.send_raw(res.tx_hex)
            inv.status, inv.txid, inv.payer_id = "paid", res.txid, user_id
        except IntegrityError:
            db.rollback()
            res.checks.append({"name": "Not a duplicate", "passed": False, "detail": "This payment was already credited"})
            res.ok = False
        except RpcError as e:
            db.rollback()
            res.checks.append({"name": "Broadcast", "passed": False, "detail": str(e)})
            res.ok = False
    elif res.outcome == "underpaid":
        inv.status = "underpaid"
    db.commit()
    return {"ok": res.ok, "status": inv.status, "checks": res.checks, "txid": res.txid}


def refresh_invoice(db, inv: Invoice, rpc):
    """Recalculate status from the chain. Handles confirmations, expiry and reorgs (TC10)."""
    if inv.txid:
        try:
            c = rpc.confirmations(inv.txid)
        except RpcError:
            return 0
        if c is None:
            inv.status = "pending"            # tx dropped or reorged out: recalculate, do not trust the old state
            conf = 0
        else:
            inv.status = "confirmed" if c >= config.REQUIRED_CONFS else "paid"
            conf = c
        db.commit()
        return conf
    if inv.status == "pending" and inv.expires_at < now():
        inv.status = "expired"
        db.commit()
    return 0
