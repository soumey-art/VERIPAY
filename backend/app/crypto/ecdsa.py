"""ECDSA / secp256k1 verification of a P2WPKH input, using only a plain ECDSA library.

Bitcoin Core remains the consensus authority. This independent check lets VeriPay show
(and test) exactly what a signature proves.
"""
from ecdsa import SECP256k1, BadSignatureError, VerifyingKey
from ecdsa.util import sigdecode_der
from embit.hashes import hash160

from .sighash import SIGHASH_ALL, sighash_p2wpkh


def verify_p2wpkh_input(tx, index: int, prev_script_pubkey: bytes, amount_sat: int, witness_items: list) -> tuple[bool, str]:
    """Return (valid, reason)."""
    if not (len(prev_script_pubkey) == 22 and prev_script_pubkey[:2] == b"\x00\x14"):
        return False, "Input is not P2WPKH"
    if len(witness_items) != 2:
        return False, "Witness must be [signature, pubkey]"
    sig_with_type, pubkey = witness_items
    if not sig_with_type:
        return False, "Empty signature"
    der, sighash_type = sig_with_type[:-1], sig_with_type[-1]
    if sighash_type != SIGHASH_ALL:
        return False, f"Unsupported sighash type 0x{sighash_type:02x} (only SIGHASH_ALL accepted)"
    if hash160(pubkey) != prev_script_pubkey[2:]:
        return False, "Public key does not match the output being spent"
    digest = sighash_p2wpkh(tx, index, amount_sat, prev_script_pubkey[2:], sighash_type)
    try:
        VerifyingKey.from_string(pubkey, curve=SECP256k1).verify_digest(der, digest, sigdecode=sigdecode_der)
    except (BadSignatureError, ValueError):
        return False, "Signature does not verify for this transaction"
    return True, "ECDSA signature valid for this exact transaction"
