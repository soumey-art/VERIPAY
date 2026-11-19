import os

NETWORK = os.getenv("NETWORK", "regtest")
RPC_URL = os.getenv("RPC_URL", "http://127.0.0.1:18443")
RPC_USER = os.getenv("RPC_USER", "veripay")
RPC_PASS = os.getenv("RPC_PASS", "change-me")
MERCHANT_WALLET = os.getenv("MERCHANT_WALLET", "merchant")
CUSTOMER_WALLET = os.getenv("CUSTOMER_WALLET", "customer")
REQUIRED_CONFS = int(os.getenv("REQUIRED_CONFS","3"))
INVOICE_TTL_MIN = int(os.getenv("INVOICE_TTL_MIN", "60"))
JWT_SECRET = os.getenv("JWT_SECRET", "dev-only-change-me")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///veripay.db")

HRP = {"main": "bc", "test": "tb", "signet": "tb", "regtest": "bcrt"}
CHAIN = {"regtest": "regtest", "signet": "signet"}[NETWORK]