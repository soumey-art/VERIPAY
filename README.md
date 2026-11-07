# VERIPAY
A non-custodial Bitcoin payment service provider (Crypto PSP) built as an academic cryptography project. Merchants create invoices, customers sign payments in their own wallet, and VeriPay independently verifies the signed transaction before it is accepted. VeriPay never sees a private key.

Network: Bitcoin regtest (Signet-ready via config)
Wallet type: native SegWit (P2WPKH)
Cryptography: ECDSA on secp256k1, SHA-256, BIP-143 signature hash, PSBT (BIP-174)
Stack: Python (FastAPI backend, CustomTkinter desktop GUI), SQLite (swappable), Bitcoin Core

Academic proof of concept. Test networks only. Do not use real funds or real keys.

How it works
 Customer GUI ──► FastAPI backend ──► Bitcoin Core (regtest)
 (signs locally)    │  verification      (consensus authority)
                    ▼
                 Database
A merchant creates an invoice. The backend asks Bitcoin Core for a fresh address, one per invoice.
A customer opens the invoice. The backend issues an unsigned PSBT for exactly that payment.
The customer reviews the outputs and signs in their own wallet. The key stays on their machine.
The customer submits the signed PSBT. The backend runs the checks below.
If every check passes, the transaction is broadcast and the invoice becomes paid.
As blocks arrive the invoice moves to confirmed. If a reorg removes the transaction, it is recalculated.
What the verification engine checks
Check	What it proves
Signature valid	Our own BIP-143 + ECDSA code verifies every input's signature for this exact transaction
Transaction not modified	The signed transaction's txid equals the PSBT VeriPay issued (segwit txids ignore witnesses, so any other change shows)
Destination matches	An output pays the invoice's address
Amount matches	That output pays at least the invoice amount (overpayment accepted, shortfall marked underpaid)
Correct network	The invoice address and the node's chain agree
Not a duplicate	The (txid, vout) outpoint has not been credited before (database UNIQUE constraint)
Accepted by Bitcoin Core	testmempoolaccept passes. Core stays the authority on consensus rules

If Bitcoin Core is unreachable, verification fails closed.

Project structure
veripay/
├── README.md
├── backend/
│   ├── requirements.txt
│   ├── .env.example
│   ├── app/
│   │   ├── main.py            # FastAPI routes
│   │   ├── services.py        # process payment, refresh status (confirmations, expiry, reorg)
│   │   ├── verifier.py        # the verification checks (pure logic, no DB/HTTP)
│   │   ├── bitcoin_rpc.py     # Bitcoin Core JSON-RPC wrapper
│   │   ├── db.py              # all database access (models + session)
│   │   ├── security.py        # scrypt password hashing, JWT
│   │   ├── config.py          # settings from environment variables
│   │   └── crypto/
│   │       ├── sighash.py       # BIP-143 signature hash
│   │       ├── ecdsa_verify.py  # ECDSA / secp256k1 verification
│   │       └── psbt_policy.py   # PSBT parsing, txid, output summary
│   └── tests/                 # TC01-TC10 plus API tests (no Bitcoin node needed)
└── gui/
    ├── requirements.txt
    ├── main.py                # window and navigation
    ├── pages.py               # Login, Invoices, Pay, Status screens
    ├── api.py                 # HTTP client for the backend
    └── wallet.py              # local demo wallet (signs a PSBT; key never leaves the machine)
Setup (Windows, PowerShell)

Requires Python 3.10+ (tick Add python.exe to PATH when installing).

1. Backend
powershell
cd backend
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest -q                         # expect: 16 passed
python -m uvicorn app.main:app --reload     # API docs at http://localhost:8000/docs

If PowerShell blocks the activate script, run once: Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

2. GUI (in a second terminal, with its own venv)
powershell
cd gui
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
3. Bitcoin Core on regtest (needed for real payments)

Install Bitcoin Core, then in bitcoin.conf:

regtest=1
server=1
txindex=1
rpcuser=veripay
rpcpassword=change-me

Start bitcoind, then create the two demo wallets and fund the customer:

powershell
bitcoin-cli -regtest createwallet merchant
bitcoin-cli -regtest createwallet customer
bitcoin-cli -regtest -rpcwallet=customer -generate 101

Set the backend environment variables to match (see backend/.env.example), for example:

powershell
$env:RPC_USER="veripay"; $env:RPC_PASS="change-me"

To advance confirmations during a demo, mine blocks:

powershell
bitcoin-cli -regtest -rpcwallet=customer -generate 1
Configuration

Set as environment variables. Defaults suit local regtest.

Variable	Default	Purpose
NETWORK	regtest	regtest or signet
RPC_URL	http://127.0.0.1:18443	Bitcoin Core RPC
RPC_USER / RPC_PASS	veripay / change-me	RPC credentials
MERCHANT_WALLET / CUSTOMER_WALLET	merchant / customer	Node wallets used by the demo
REQUIRED_CONFS	3	Confirmations before an invoice is confirmed
INVOICE_TTL_MIN	60	Invoice lifetime in minutes
JWT_SECRET	dev value	Change this for anything beyond local testing
DATABASE_URL	sqlite:///veripay.db	SQLAlchemy URL (PostgreSQL works by changing this)
API

Base path /api/v1. All routes except register and login need Authorization: Bearer <token>.

Method	Path	Who	Purpose
POST	/auth/register	anyone	{email, password, role} where role is merchant or customer
POST	/auth/login	anyone	Returns a JWT and the role
POST	/invoices	merchant	{amount_sat, description}; assigns a unique address
GET	/invoices	both	Merchant: own invoices. Customer: invoices they paid
GET	/invoices/{id}	both	Detail with PSBT, output summary, checks, txid, confirmations
POST	/payments/verify	customer	{invoice_id, signed_psbt}; verifies and broadcasts
POST	/verification/psbt	both	Inspect any PSBT (outputs, fee, txid, signed inputs)

Amounts are integer satoshis everywhere. Interactive docs: http://localhost:8000/docs.

Tests
powershell
cd backend
python -m pytest -q

The suite builds real regtest transactions signed by an independent library (embit) and runs them through the verification engine, with a fake Bitcoin node standing in for Core.

Case	Scenario	Result
TC01	Valid payment	Accepted
TC02	Corrupted or missing signature	Rejected
TC03	Output amount edited after signing	Signature and "not modified" checks fail
TC04	Payment to the wrong address	Rejected
TC05	Insufficient amount	Marked underpaid, not broadcast
TC06	Same payment submitted twice	Second one not credited or broadcast
TC07	Expired invoice	Rejected
TC08	Input UTXO does not exist	Rejected by the node check
TC09	Wrong network	Rejected
TC10	Transaction reorged out	Status recalculated to pending
Security notes
Private keys and seed phrases are never sent to or stored by the backend.
Passwords are hashed with scrypt; sessions use signed JWTs.
Only SIGHASH_ALL signatures are accepted, since other types let a third party alter outputs.
Payment state changes happen in database transactions; UNIQUE(txid, vout) blocks double credit.
Verification attempts and security events are written to append-only tables (application level).
wallet_key.txt (GUI demo wallet) must hold a regtest key only. Never put a real key in it.

References
Nakamoto, S. (2008). Bitcoin: A Peer-to-Peer Electronic Cash System
BIP-32, BIP-84, BIP-143 (SegWit signature hash), BIP-174 (PSBT), BIP-340 (Schnorr, future work)
Bitcoin Core, FastAPI, SQLAlchemy documentation
