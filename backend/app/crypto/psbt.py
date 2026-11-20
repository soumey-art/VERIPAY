import hashlib

from embit.compact import to_bytes
from embit.networks import NETWORKS
from embit.psbt import PSBT
from embit.script import Witness, address_to_scriptpubkey

from .. import config


def txid_of(tx) -> str:
    """txid = double SHA-256 of the transaction WITHOUT witness data, byte-reversed for display.
    Witness data is excluded, so signing never changes it. Any other change does."""
    legacy = tx.version.to_bytes(4, "little")
    legacy += to_bytes(len(tx.vin)) + b"".join(v.serialize() for v in tx.vin)
    legacy += to_bytes(len(tx.vout)) + b"".join(o.serialize() for o in tx.vout)
    legacy += tx.locktime.to_bytes(4, "little")
    return hashlib.sha256(hashlib.sha256(legacy).digest()).digest()[::-1].hex()


def parse_psbt(b64: str) -> PSBT:
    return PSBT.from_string(b64.strip())


def finalize_p2wpkh(psbt: PSBT):
    """Attach [signature, pubkey] witnesses to the transaction. Returns (tx, inputs) where inputs holds
    (prev_script_pubkey_bytes, amount_sat, witness_items) per input, or raises ValueError."""
    tx, inputs = psbt.tx, []
    for i, inp in enumerate(psbt.inputs):
        utxo = inp.utxo
        if utxo is None:
            raise ValueError(f"Input {i} has no UTXO data")
        final = getattr(inp, "final_scriptwitness", None)
        if final is not None:
            items = list(final.items)
        elif inp.partial_sigs:
            pub, sig = next(iter(inp.partial_sigs.items()))
            items = [sig, pub.sec()]
        else:
            raise ValueError(f"Input {i} is not signed")
        tx.vin[i].witness = Witness(items)
        inputs.append((utxo.script_pubkey.data, utxo.value, items))
    return tx, inputs


def summarize(psbt: PSBT) -> dict:
    net = NETWORKS[config.NETWORK]
    outs = [{"address": o.script_pubkey.address(net), "amount_sat": o.value} for o in psbt.tx.vout]
    total_in = sum(i.utxo.value for i in psbt.inputs if i.utxo is not None)
    return {"outputs": outs, "fee_sat": total_in - sum(o["amount_sat"] for o in outs)}


def address_matches_chain(address: str, chain: str) -> bool:
    hrp = config.HRP[chain]
    return address.lower().startswith(hrp + "1")


def spk_of(address: str) -> bytes:
    return address_to_scriptpubkey(address).data
