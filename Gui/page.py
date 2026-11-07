from venv import create

import customtkinter as ctk
from tkinter import messagebox
from api import ApiError, sats_to_btc
import wallet
PINE, PINE_D = "#1f5c4a", "#154235"
STATUS_COLORS = {"pending": "#8a9490", "underpaid": "#b7791f", "paid": "#2f7d63", "confirmed": PINE, "expired": "#a63d2f"}
MONO = ("Courier New", 12)


def badge(parent, status):
    return ctk.CTkLabel(parent, text=status, fg_color=STATUS_COLORS.get(status, "#888"),
                        text_color= "white", corner_radius=4, padx=8, pady= 2, font=("Segeo UI", 12, "bold"))
    
    
def title(parent, text):
    return ctk.CTkLabel(parent, text=text, font=("Segeo UI", 24, "bold"))

def button(parent, text, cmd, **kw):
    return ctk.CTkButton(parent, text=text, command=cmd, fg_color=PINE, hover_color=PINE_D, **kw)

class LoginPage(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app, self.mode = app, "login"
        box = ctk.CTkFrame(self, width=380)
        box.place(relx=0.5, rely=0.4, anchor="center")
        self.h = title(box, "Login in"); self.h.pack(padx=30, pady=(24, 2), anchor= "w")
        ctk.CTkLabel(box, text="Your private keys never leave your own wallet.",
text_color="grey").pack(padx=30, anchor="w")
        self.pw = ctk.CTkEntry(box, placeholder_text="Email", width=320)
        self.email.pack(padx=30, pady=(18,8))
        self.pw.pack(padx=30, pady=8)
        self.role = ctk.CTkOptionMenu(box, values=["merchant", "customer"], width=320, fg_color=PINE, button_color=PINE_D)
        self.err= ctk.CTkLabel(box, text= "", text_color="#a63d2f", wraplength=320)
        self.err.pack(padx=30)
        self.go = button(box, "log in", self.submit, width=320); self.go.pack(padx=30, pady=8)
        self.tg = ctk.CTkButton(box, text="Need an account? Register", fg_color="transparent",
                                text_color=("black", "white"), hover=False, command=self.toggle)
        self.tg.pack(pady=(0, 18))
        
    def toggle(self):
        self.mode = "register" if self.mode == "login" else "login"
        reg = self.mode == "register"
        self.h.configure(text="Create account" if reg else "Log in")
        self.go.configure(text="Create account" if reg else "Log in")
        self.tg.configure(text="Already registerd? Log in" if reg else "Need an account? Register")
        if reg: self.role.pack(padx= 30, pady=8, before= self.err)
        else: self.role.pack(padx=30, pady=8, before=self.err)
        self.err.configure(text="")
        
        
    def submit(self):
        
        try: 
            a,e,p= self.app.api, self.email.get().strip(), self.pw.get()
            a.login(e,p) if self.mode == "login" else a.register(e, p,self.role.get())
            self.app.show("invoices")
        except ApiError as ex:
            self.err.configure(text=str(ex))
            

class InvoicesPage(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.form = ctk.CTkFrame(self); self.form.pack(fill="x", pady=(0,16))
        title(self.form, "Create invoice").grid(row=0, column=0, columnspan=3, sticky="w", padx=16, pady=(12, 6))
        self.amt = ctk.CTkEntry(self.form, placeholder_text="Amount (sats)", width=150); 
        self.amt.grid(row=1, column=0, padx=16, pady=(0,14))
        self.desc = ctk.CTkEntry(self.form, placeholder_text="Description", width=320);
        self.desc.grid(column=1, padx=4, pady= (0,14))
        button(self.form, "Create invoice", self.create).grid(row=1, column=2, padx=16, pady=(0,14))
        self.err = ctk.CTkLabel(self, text="", font=("Segeo UI", 18, "bold"));
        self.heading = ctk.CTkLabel(self, text="", font=("Segoe UI", 18, "bold")); self.heading.pack(anchor="w", pady=(4, 6))
        self.list = ctk.CTkScrollableFrame(self); self.list.pack(fill="both", expand=True)
        self._job = None
    
    def on_show(self):
        merchant = self.app.api.role == "merchant"
        (self.form.pack if merchant else self.form.pack_forget)(**({"fill":"x", "pady": (0,16), "before": self.err} if merchant else{}))
        self.heading.configure(text="Your invoices" if merchant else "Your payments")
        self.refresh()
        
    def on_hide(self):
        if self._job: self.after_cancel(self._job)
    
    def create(self):
        try:
            self.app.api.create_invoice(int(self.amt.get()), self.desc.get().strip())
            self.amt.delete(0,"end"); self.desc.delel(0,"end"); self.err,self.configure(text="")
            self.refresh()
        except (ValueError, ApiError) as ex:
            self.err.configure(text=str(ex) if isinstance(ex, ApiError) else "Amount must be a whole number of satoshis.")
            
    def refresh(self):
        try:
            rows = self.app.api.list_invoices(); self.err.configure(text="")
        except ApiError as ex:
            rows = []; self.err.configure(text=str(ex))
        for w in self.list.winfo_children(): w.destroy()
        if not rows:
            ctk.CTkLabel(self.list, text="No invoices yet. Create one above to get a payment address.", text_color="gray").pack(pady=20)
        for i, inv in enumerate(rows):
            r = ctk.CTkFrame(self.list, fg_color="transparent"); r.pack(fill="x", pady=3)
            ctk.CTkLabel(r, text=inv["description"], width=240, anchor="w").pack(side="left", padx=8)
            ctk.CTkLabel(r, text=sats_to_btc(inv["amount_sat"]), font=MONO, width=120).pack(side="left")
            badge(r, inv["status"]).pack(side="left", padx=12)
            ctk.CTkButton(r, text="Pay", width=60, fg_color="transparent", border_width=1, text_color=("black", "white"),
                          command=lambda x=inv["id"]: self.app.show("pay", x)).pack(side="right", padx=4)
            ctk.CTkButton(r, text="Status", width=60, fg_color="transparent", border_width=1, text_color=("black", "white"),
                          command=lambda x=inv["id"]: self.app.show("status", x)).pack(side="right")
        self._job = self.after(5000, self.refresh)
 
 
class PayPage(ctk.CTkScrollableFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        
    def on_show(self, invoice_id):
        for w in self.winfo_children(): w.destroy()
        self.invoice_id = invoice_id
        try:
            
            inv = self.inv = self.app.api.get_invoice(invoice_id)
        except ApiError as ex:
            ctk.CTkLabel(self, text=str(ex), text_color="#a63d2f").pack(); return
        top = ctk.CTkFrame(self, fg_color="transparent"); top.pack(fill="x")
        left = ctk.CTkFrame(top, fg_color="transparent"); left.pack(side="left")
        title(left, inv["description"]).pack(anchor="w")
        ctk.CTkLabel(left, text=f"{sats_to_btc(inv['amount_sat'])} BTC", font=("Courier New", 16)).pack(anchor="w")
        badge(top, inv["status"]).pack(side="right")
     
     
        c1 = self.card("1. Review what you will sign")
        ctk.CTkLabel(c1, text="Check that these outputs match the invoice before signing.", text_color="gray").pack(anchor="w", padx=14)
        for o in inv["psbt_summary"]["outputs"]:
            ctk.CTkLabel(c1, text=f"{o['address']}   {sats_to_btc(o['amount_sat'])} BTC", font=MONO).pack(anchor="w", padx=14, pady=2)
        ctk.CTkLabel(c1, text=f"Network fee: {inv['psbt_summary']['fee_sat']} sats", text_color="gray").pack(anchor="w", padx=14, pady=(2, 12))
 
        c2 = self.card("2. Sign in your own wallet")
        box = ctk.CTkTextbox(c2, height=70, font=MONO); box.pack(fill="x", padx=14)
        box.insert("1.0", inv["psbt"]); box.configure(state="disabled")
        row = ctk.CTkFrame(c2, fg_color="transparent"); row.pack(fill="x", padx=14, pady=10)
        ctk.CTkButton(row, text="Copy PSBT", fg_color="transparent", border_width=1, text_color=("black", "white"),
                      command=lambda: (self.clipboard_clear(), self.clipboard_append(inv["psbt"]))).pack(side="left")
        button(row, "Sign with local wallet", self.sign_local).pack(side="left", padx=10)
        ctk.CTkLabel(c2, text="The key stays on this computer. VeriPay never sees it.", text_color="gray").pack(anchor="w", padx=14, pady=(0, 12))
 
        c3 = self.card("3. Submit the signed PSBT")
        self.signed = ctk.CTkTextbox(c3, height=90, font=MONO); self.signed.pack(fill="x", padx=14)
        self.err = ctk.CTkLabel(c3, text="", text_color="#a63d2f", wraplength=600); self.err.pack(anchor="w", padx=14)
        button(c3, "Verify and broadcast", self.submit).pack(anchor="w", padx=14, pady=(4, 14))
        
    def card(self, heading):
        f = ctk.CTkFrame(self); f.pack(fill="x", pady=(14, 0))
        ctk.CTkLabel(f, text=heading, font=("Segoe UI", 15, "bold")).pack(anchor="w", padx=14, pady=(12, 6))
        return f
 
    def sign_local(self):
        try:
            out = wallet.sign_psbt(self.inv["psbt"])
            self.signed.delete("1.0", "end"); self.signed.insert("1.0", out); self.err.configure(text="")
        except Exception as ex:
            messagebox.showerror("Wallet", str(ex))
 
    def submit(self):
        text = self.signed.get("1.0", "end").strip()
        if not text:
            self.err.configure(text="Paste or sign a PSBT first."); return
        try:
            self.app.api.verify_payment(self.invoice_id, text)
            self.app.show("status", self.invoice_id)
        except ApiError as ex:
            self.err.configure(text=str(ex))
 
 
class StatusPage(ctk.CTkScrollableFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app, self._job = app, None
 
    def on_show(self, invoice_id):
        self.invoice_id = invoice_id
        self.refresh()
 
    def on_hide(self):
        if self._job: self.after_cancel(self._job)
 
    def refresh(self):
        for w in self.winfo_children(): w.destroy()
        try:
            inv = self.app.api.get_invoice(self.invoice_id)
        except ApiError as ex:
            ctk.CTkLabel(self, text=str(ex), text_color="#a63d2f").pack(); return
        top = ctk.CTkFrame(self, fg_color="transparent"); top.pack(fill="x")
        left = ctk.CTkFrame(top, fg_color="transparent"); left.pack(side="left")
        title(left, inv["description"]).pack(anchor="w")
        ctk.CTkLabel(left, text=f"{sats_to_btc(inv['amount_sat'])} BTC", font=("Courier New", 16)).pack(anchor="w")
        badge(top, inv["status"]).pack(side="right")
 
        c = ctk.CTkFrame(self); c.pack(fill="x", pady=(14, 0))
        ctk.CTkLabel(c, text="Verification checks", font=("Segoe UI", 15, "bold")).pack(anchor="w", padx=14, pady=(12, 6))
        if not inv["checks"]:
            ctk.CTkLabel(c, text="No payment submitted yet.", text_color="gray").pack(anchor="w", padx=14, pady=(0, 12))
        for k in inv["checks"]:
            r = ctk.CTkFrame(c, fg_color="transparent"); r.pack(fill="x", padx=14, pady=3)
            ctk.CTkLabel(r, text="✓" if k["passed"] else "✕", width=22, height=22, corner_radius=11, text_color="white",
                         fg_color=PINE if k["passed"] else "#a63d2f").pack(side="left", anchor="n")
            col = ctk.CTkFrame(r, fg_color="transparent"); col.pack(side="left", padx=10)
            ctk.CTkLabel(col, text=k["name"], font=("Segoe UI", 13, "bold")).pack(anchor="w")
            if k.get("detail"): ctk.CTkLabel(col, text=k["detail"], text_color="gray", font=("Segoe UI", 11)).pack(anchor="w")
 
        c2 = ctk.CTkFrame(self); c2.pack(fill="x", pady=(14, 0))
        n, need = inv["confirmations"], inv["required_confirmations"]
        h = ctk.CTkFrame(c2, fg_color="transparent"); h.pack(fill="x", padx=14, pady=(12, 6))
        ctk.CTkLabel(h, text="Confirmations", font=("Segoe UI", 15, "bold")).pack(side="left")
        ctk.CTkLabel(h, text=f"{n} / {need}", font=MONO).pack(side="right")
        bar = ctk.CTkProgressBar(c2, progress_color=PINE); bar.pack(fill="x", padx=14); bar.set(min(1, n / need))
        if inv.get("txid"):
            ctk.CTkLabel(c2, text=f"txid {inv['txid']}", font=("Courier New", 10), wraplength=640, justify="left").pack(anchor="w", padx=14, pady=10)
        ctk.CTkLabel(c2, text="Updates every 5 seconds.", text_color="gray", font=("Segoe UI", 11)).pack(anchor="w", padx=14, pady=(4, 12))
        self._job = self.after(5000, self.refresh)
 