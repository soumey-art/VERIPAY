"""VeriPay desktop GUI. Run: python main.py (backend must be running on localhost:8000)."""
import customtkinter as ctk
from api import Api
from page import InvoicesPage, LoginPage, PayPage, StatusPage

ctk.set_appearance_mode("system")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("VeriPay (regtest)")
        self.geometry("860x700")
        self.minsize(720, 560)
        self.api = Api()
        
        
        
        bar = ctk.CTkFrame(self, corner_radius=0); bar.pack(fill="x")
        ctk.CTkLabel(bar, text="VeriPay", font=("Segeo UI", 16, "bold")).pack(side="left", padx=16, pady=10)
        ctk.CTkLabel(bar, text="regtest", text_color="gray", font=("Courier New", 11)).pack(side="left")
        self.home = ctk.CTkButton(bar, text="Invoices", width=80, fg_color="transparent", border_width=1,
                                  text_color=("black", "white"), command=lambda: self.show("invoices"))
        self.out = ctk.CTkButton(bar, text="Log out", width=80, fg_color="transparent", border_width=1,
                                 text_color=("black", "white"), command=self.logout)
        
        
        self.body = ctk.CTkFrame(self, fg_color="transparent"); self.body.pack(fill="both", expand= True, padx=24, pady=20)
        self.pages = {n: c(self.body, self) for n, c in
                      {"login": LoginPage, "invoices": InvoicesPage, "PayPage": PayPage, "status": StatusPage}.items()}
        self.current = None
        self.show("login")
        
        
    def show(self, name, arg=None):
        if self.current:
            getattr(self.current, "on_hide", lambda: None)()
            self.current.pack_forget()
        self.current = self.pages[name]
        self.current.pack(fill="both", expand=True)
        logged = name != "login"
        for b, side in ((self.out, "right"), (self.home, "right")):
            b.pack_forget()
            if logged: b.pack(side=side, padx=(0, 12), pady=8)
        if hasattr(self.current, "on_show"):
            self.current.on_show(arg) if arg is not None else self.current.on_show()
 
    def logout(self):
        self.api.logout()
        self.show("login")
 
 
if __name__ == "__main__":
    App().mainloop()
 