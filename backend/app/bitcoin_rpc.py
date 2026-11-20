from decimal import Decimal

import requests

from . import config



class RpcError(Exception):
    pass


class BitcoinRpc:
    def _call(self, method, params=None, wallet=None):
        url = config.RPC_URL + (f"/wallet/{wallet}" if wallet else "")
        try:
            r = requests.post(
                url,
                json={"jsonrpc": "1.0", "id": "veripay", "method": method, "params": params or []},
                auth=(config.RPC_USER, config.RPC_PASS),
                timeout=15,
            )
        except requests.RequestException as e:
            raise RpcError(f"Bitcoin Core unreachable ({e.__class__.__name__})")
        try:
            body = r.json() if r.content else {}
        except ValueError:
            raise RpcError(f"Bitcoin Core returned a non-JSON response (HTTP {r.status_code})")
        if not isinstance(body, dict) or "result" not in body:
            if isinstance(body, dict) and body.get("error"):
                raise RpcError(body["error"].get("message", "RPC error"))
            raise RpcError(f"Unexpected RPC response (HTTP {r.status_code})")
        if body.get("error"):
            raise RpcError(body["error"].get("message", "RPC error"))
        return body["result"]

    def get_chain(self) -> str:
        return self._call("getblockchaininfo")["chain"]

    def get_new_address(self) -> str:
        return self._call("getnewaddress", ["", "bech32"], wallet=config.MERCHANT_WALLET)

    def create_funded_psbt(self, address: str, amount_sat: int) -> str:
        amount_btc = format(Decimal(amount_sat) / Decimal(10 ** 8), ".8f")
        res = self._call(
            "walletcreatefundedpsbt",
            [[], [{address: amount_btc}], 0, {"includeWatching": False}, True],
            wallet=config.MERCHANT_WALLET,
        )
        return res["psbt"]

    def send_raw(self, tx_hex: str) -> str:
        return self._call("sendrawtransaction", [tx_hex])

    def test_mempool_accept(self, tx_hex: str) -> tuple[bool, str]:
        res = self._call("testmempoolaccept", [[tx_hex]])[0]
        return bool(res["allowed"]), res.get("reject-reason", "")

    def confirmation(self, txid: str):
        try:
            return self._call("getrawtransaction", [txid, True]).get("confirmations", 0)
        except RpcError:
            return None