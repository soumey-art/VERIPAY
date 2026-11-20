"""BIP-143 signature hash for native SegWit (P2WPKH) inputs, written out by hand.

This is the message a wallet signs. It commits to every input outpoint, every sequence,
every output (value + script), the amount being spent, version and locktime. Change any
of those after signing and the hash changes, so the original signature stops verifying.
"""

import hashlib

SIGHASH_ALL = 0x01


def sha256d(b: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(b).digest()).digest()


def p2wpkh_script_code(pubkey_hash: bytes) -> bytes:
    # OP_DUP OP_HASH160 <20-byte pubkey hash> OP_EQUALVERIFY OP_CHECKSIG
    return b"\x76\xa9\x14" + pubkey_hash + b"\x88\xac"


def sighash_p2wpkh(tx, index: int, amount_sat: int, pubkey_hash: bytes, sighash_type: int = SIGHASH_ALL) -> bytes:
    hash_prevouts = sha256d(b"".join(vin.serialize()[:36] for vin in tx.vin))
    hash_sequence = sha256d(b"".join(vin.sequence.to_bytes(4, "little") for vin in tx.vin))
    hash_outputs = sha256d(b"".join(vout.serialize() for vout in tx.vout))
    vin = tx.vin[index]
    script_code = p2wpkh_script_code(pubkey_hash)
    preimage = (
        tx.version.to_bytes(4, "little")
        + hash_prevouts
        + hash_sequence
        + vin.serialize()[:36]                      # outpoint (txid + vout)
        + bytes([len(script_code)]) + script_code
        + amount_sat.to_bytes(8, "little")
        + vin.sequence.to_bytes(4, "little")
        + hash_outputs
        + tx.locktime.to_bytes(4, "little")
        + sighash_type.to_bytes(4, "little")
    )
    return sha256d(preimage)
