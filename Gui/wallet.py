from pathlib import Path

from embit.psbt import PSBT
from embit.bip32 import HDKey
from embit.networks import NETWORKS


# Location of wallet private key
KEY_FILE = Path(__file__).with_name("wallet_key.txt")


def load_wallet():
    """
    Load the local Bitcoin wallet.

    Private key stays on the user's computer.
    """

    if not KEY_FILE.exists():
        raise RuntimeError("Wallet key file not found.")

    raw = KEY_FILE.read_text().strip()

    if raw.startswith("tprv"):
        root = HDKey.from_base58(raw)

    elif raw.startswith("xprv"):
        raise ValueError(
            "Mainnet xprv keys are not allowed in this Regtest wallet."
        )

    else:
        try:
            seed = bytes.fromhex(raw)
        except ValueError:
            raise ValueError("Invalid hexadecimal wallet seed.")

        if len(seed) < 16 or len(seed) > 64:
            raise ValueError("Seed must be between 16 and 64 bytes.")

        root = HDKey.from_seed(
            seed,
            version=NETWORKS["regtest"]["xprv"]
        )

    return root


def sign_psbt(psbt_b64: str) -> str:
    """
    Sign a Bitcoin PSBT locally.

    Args:
        psbt_b64: Unsigned PSBT in Base64 format.

    Returns:
        Signed PSBT in Base64 format.
    """

    if not psbt_b64:
        raise ValueError("PSBT cannot be empty.")

    # 1. Load wallet
    root = load_wallet()

    # 2. Decode PSBT
    psbt = PSBT.from_string(psbt_b64)

    # 3. Sign transaction
    signatures_added = psbt.sign_with(root)

    # 4. Verify signing result
    if signatures_added == 0:
        raise RuntimeError(
            "Wallet key did not match any input in this PSBT."
        )

    # 5. Return signed PSBT
    return psbt.to_base64()