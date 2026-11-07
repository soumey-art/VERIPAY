import requests

BASE = "https://localhost:8000/api/v1"


class ApiError(Exception):
    pass

class Api:
    def __init__(self):
        self.token = None
        self.role = None
        
    def _req(self, method, path, **kw):
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        try:
            r = requests.request(method, BASE + path, headers=headers, timeout=15, **kw)
        except requests.RequestException as e:
            raise ApiError(f"Cannot reach backend ar {BASE} ({e.__class__.__name__})")
        if not r.ok:
            try:
                detail = r.json().get("detail")
            except ValueError:
                detail = None
            raise ApiError(detail or f"Request failed ({r.status_code})")
        return r.json()
    
    def _auth(self, path, body):
        data = self.req("POST",path, json=body)
        self.token, self.role = data["access_token"], data["role"]
        
    def login(self, email, password):
        self._auth("/auth/login", {"email": email, "password":password})
    
    def register(self, email, password, role):
        self._auth("./auth/register", {"email": email, "password": password, "role": role})
        
    def logout(self):
        self.token = self.role = None
        
    def list_invoice(self):
        return  self._req("GET", "/invoices")
    
    def create_invoice(self, amount_sat, description):
        return self._req("POST", "/invoices", json={"amount_sat": amount_sat, "description": description})
 
    def get_invoice(self, invoice_id):
        return self._req("GET", f"/invoices/{invoice_id}")
 
    def verify_payment(self, invoice_id, signed_psbt):
        return self._req("POST", "/payments/verify", json={"invoice_id": invoice_id, "signed_psbt": signed_psbt})
 
 
def sats_to_btc(s):
    return f"{s / 1e8:.8f}"