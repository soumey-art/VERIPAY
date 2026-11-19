"""Payment-level verification of a signed PSBT. Pure logic: no database, no HTTP."""
from dataclasses import dataclass, field

from .crypto.ecdsa_verify import verify_p2wpkh_input
from .crypto.psbt_policy import address_matches_chain, finalize_p2wpkh, parse_psbt, spk_of, txid_of
from .bitcoin_rpc import RpcError


@dataclass
class Result:
    checks: list = field(default_factory=list)
    ok: bool = False
    outcome: str = "rejected"        # paid | underpaid | rejected
    txid: str | None = None
    vout: int | None = None
    received_sat: int = 0
    tx_hex: str | None = None

    def add(self, name, passed, detail=""):
        self.checks.append({"name": name, "passed": bool(passed), "detail": detail})
        return passed


def verify_signed_psbt(psbt_b64, *, invoice_address, amount_sat, unsigned_txid, rpc, already_credited) -> Result:
    r = Result()

    # 0. Parse + finalize
    try:
        psbt = parse_psbt(psbt_b64)
        tx, inputs = finalize_p2wpkh(psbt)
    except Exception as e:
        r.add("Valid signed PSBT", False, str(e) or "Could not parse PSBT")
        return r
    r.txid, r.tx_hex = txid_of(tx), tx.serialize().hex()

    # 1. Our own ECDSA / secp256k1 verification of every input
    sig_ok, why = True, "ECDSA signature valid for this exact transaction"
    for i, (spk, amt, items) in enumerate(inputs):
        ok, why_i = verify_p2wpkh_input(tx, i, spk, amt, items)
        if not ok:
            sig_ok, why = False, f"Input {i}: {why_i}"
            break
    r.add("Signature valid", sig_ok, why)

    # 2. The signed transaction is the one we issued (segwit txid ignores witnesses)
    if unsigned_txid is None:
        r.add("Transaction not modified", False, "No PSBT was issued for this invoice")
    else:
        same = unsigned_txid == r.txid
        r.add("Transaction not modified", same, "Matches the PSBT VeriPay issued" if same else "Differs from the PSBT VeriPay issued")

    # 3. Destination
    try:
        expected_spk = spk_of(invoice_address)
    except Exception:
        expected_spk = None
    vout = next((n for n, o in enumerate(tx.vout) if expected_spk and o.script_pubkey.data == expected_spk), None)
    r.add("Destination matches", vout is not None,
          "An output pays the invoice address" if vout is not None else "No output pays the invoice address")
    if vout is not None:
        r.vout, r.received_sat = vout, tx.vout[vout].value

    # 4. Amount
    if vout is None:
        r.add("Amount matches", False, "Not checked: no payment output")
    elif r.received_sat >= amount_sat:
        extra = f" (overpaid by {r.received_sat - amount_sat} sats)" if r.received_sat > amount_sat else ""
        r.add("Amount matches", True, f"Output pays {r.received_sat} sats, invoice needs {amount_sat}{extra}")
    else:
        r.add("Amount matches", False, f"Output pays {r.received_sat} sats, invoice needs {amount_sat}")

    # 5. Network
    try:
        chain = rpc.chain()
        net_ok = address_matches_chain(invoice_address, chain)
        r.add("Correct network", net_ok, f"Node is on {chain}" if net_ok else f"Address is not valid for {chain}")
    except RpcError as e:
        r.add("Correct network", False, str(e))

    # 6. Duplicate
    dup = vout is not None and already_credited(r.txid, vout)
    r.add("Not a duplicate", not dup, "Outpoint not credited before" if not dup else "This payment was already credited")

    # 7. Bitcoin Core consensus + mempool policy (authoritative)
    try:
        allowed, reason = rpc.test_mempool_accept(r.tx_hex)
        r.add("Accepted by Bitcoin Core", allowed, "testmempoolaccept: allowed" if allowed else f"Rejected: {reason}")
    except RpcError as e:
        r.add("Accepted by Bitcoin Core", False, str(e))

    by_name = {c["name"]: c["passed"] for c in r.checks}
    r.ok = all(by_name.values())
    if r.ok:
        r.outcome = "paid"
    elif not by_name["Amount matches"] and vout is not None and all(
            v for k, v in by_name.items() if k != "Amount matches"):
        r.outcome = "underpaid"
    return r
