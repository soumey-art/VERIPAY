# VERIPAY
# 🔐 VERIPAY
### Secure & Decentralized Bitcoin Payment Application

## 📌 Introduction

VERIPAY is a cryptography-based Bitcoin payment application designed to provide secure and decentralized digital transactions. It follows a non-custodial architecture, allowing users to maintain control over their private keys while preparing, reviewing, and signing Bitcoin transactions.

Developed using Python, VERIPAY integrates cryptographic mechanisms and Bitcoin transaction processing to improve payment security and user control over digital assets.

## 🎯 Project Objectives

- Develop a non-custodial Bitcoin payment application.
- Implement secure private-key management.
- Apply digital signatures for transaction authorization.
- Integrate Partially Signed Bitcoin Transactions (PSBT).
- Provide a user-friendly graphical interface.

## ✨ Key Features

- **Non-Custodial Wallet:** Users maintain control over their private keys.
- **ECDSA:** Implements elliptic curve digital signatures.
- **PSBT Integration:** Supports partially signed Bitcoin transactions.
- **Signature Verification:** Verifies transaction signatures.
- **Bitcoin RPC:** Supports communication with a Bitcoin node.
- **GUI:** Provides an interactive desktop interface.

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Main programming language |
| CustomTkinter | Graphical user interface |
| Embit | Bitcoin cryptographic operations |
| ECDSA | Digital signatures |
| PSBT | Transaction signing |
| Bitcoin RPC | Bitcoin node communication |
| Git & GitHub | Version control |

## 🔐 Cryptographic Concepts

1. **Asymmetric Cryptography:** Uses public and private key pairs.
2. **Digital Signatures:** Provides transaction authentication and integrity.
3. **SHA-256:** Cryptographic hashing used in Bitcoin.
4. **ECDSA:** Elliptic Curve Digital Signature Algorithm.
5. **PSBT:** Enables partially signed Bitcoin transactions.
6. **SIGHASH:** Defines which transaction data is covered by a signature.

## 📂 Project Structure

```text
VERIPAY/
├── backend/
│   ├── app/
│   │   ├── crypto/
│   │   │   ├── ecdsa.py
│   │   │   ├── psbt.py
│   │   │   └── sighash.py
│   │   ├── bitcoin_rpc.py
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── main.py
│   │   ├── security.py
│   │   ├── services.py
│   │   └── verifier.py
│   ├── test/
│   └── requirements.txt
│
├── Gui/
│   ├── api.py
│   ├── main.py
│   ├── page.py
│   └── wallet.py
│
├── requirements.txt
├── .gitignore
└── README.md
```

## ⚙️ Installation & Setup

### Prerequisites
- Python 3.10+
- Git
- pip

### 1. Clone the Repository

```bash
git clone https://github.com/soumey-art/VERIPAY.git
cd VERIPAY
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

### 3. Activate the Virtual Environment

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
.venv\Scripts\activate.bat
```

**Linux / macOS:**
```bash
source .venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Run the Application

Start the backend:

```bash
python backend/app/main.py
```

Start the GUI:

```bash
python Gui/main.py
```

### 6. Deactivate the Virtual Environment

When finished, run:

```bash
deactivate
```

**Note:** Ensure the Bitcoin node and backend configurations are properly configured before running the application.

## 🔄 System Workflow

1. User interacts with the GUI.
2. GUI communicates with the backend.
3. Backend processes Bitcoin transactions.
4. Cryptographic modules handle signing and verification.
5. PSBT facilitates transaction signing.
6. Bitcoin RPC communicates with the Bitcoin node.

## ⚠️ Security Notice

VERIPAY is an academic project developed for educational purposes. It has not necessarily undergone a professional security audit. Do not use real Bitcoin funds or production private keys without appropriate security testing.

## 📚 References

- [Bitcoin Developer Documentation](https://developer.bitcoin.org/)
- [BIP 174 – PSBT](https://bips.dev/174/)
- [Embit Library](https://github.com/diybitcoinhardware/embit)

---

**VERIPAY – Your Keys. Your Control. Your Bitcoin. 🔐**
