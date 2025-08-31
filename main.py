# Betnix Authinator - Full Mobile Authenticator Style
import pyotp
import qrcode
import json
import os
import time
import tkinter as tk
from tkinter import simpledialog, messagebox
from tkinter import Canvas, Scrollbar
from PIL import Image, ImageTk
import cv2
from pyzbar.pyzbar import decode
import pyperclip
import sys

# Paths for standalone EXE compatibility
APP_DIR = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
USERS_FILE = os.path.join(APP_DIR, "betnix_accounts.json")

# Load or create accounts database
if os.path.exists(USERS_FILE):
    with open(USERS_FILE, "r") as f:
        accounts = json.load(f)
else:
    accounts = {}

def save_accounts():
    with open(USERS_FILE, "w") as f:
        json.dump(accounts, f, indent=4)

# Add account manually
def add_account_manual():
    account_name = simpledialog.askstring("Account Name", "Enter account name:")
    if not account_name: return
    if account_name in accounts:
        messagebox.showerror("Error", "Account already exists!")
        return
    secret = pyotp.random_base32()
    accounts[account_name] = secret
    save_accounts()
    messagebox.showinfo("Added", f"Account '{account_name}' added.\nQR saved as {account_name}_qr.png")
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=account_name, issuer_name="BetnixAuthinator")
    qr = qrcode.make(uri)
    qr_path = os.path.join(APP_DIR, f"{account_name}_qr.png")
    qr.save(qr_path)
    refresh_accounts()

# Scan QR code via webcam
def add_account_qr():
    cap = cv2.VideoCapture(0)
    messagebox.showinfo("QR Scanner", "Point your camera at the QR code. Press 'q' to cancel.")
    while True:
        ret, frame = cap.read()
        if not ret: break
        for barcode in decode(frame):
            data = barcode.data.decode('utf-8')
            try:
                if "otpauth" in data:
                    account_name = data.split("label=")[1].split("&")[0]
                    secret = data.split("secret=")[1].split("&")[0]
                    accounts[account_name] = secret
                    save_accounts()
                    messagebox.showinfo("Added", f"Account '{account_name}' added via QR scan!")
                    cap.release()
                    cv2.destroyAllWindows()
                    refresh_accounts()
                    return
            except:
                continue
        cv2.imshow("QR Scanner", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break
    cap.release()
    cv2.destroyAllWindows()

# Copy code to clipboard
def copy_code(code):
    pyperclip.copy(code)
    messagebox.showinfo("Copied", f"Code {code} copied to clipboard!")

# GUI Setup
root = tk.Tk()
root.title("Betnix Authinator")
root.geometry("400x600")
root.configure(bg="#f0f0f0")

# Scrollable canvas for account list
canvas = Canvas(root, bg="#f0f0f0")
scrollbar = Scrollbar(root, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas, bg="#f0f0f0")
scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)
canvas.create_window((0,0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)
canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# Update codes every second
def update_codes():
    for widget in scrollable_frame.winfo_children():
        widget.destroy()
    colors = ["#ff9999", "#99ccff", "#99ff99", "#ffcc99", "#ffb3e6", "#ccff99"]
    for idx, (acc, secret) in enumerate(accounts.items()):
        color = colors[idx % len(colors)]
        totp = pyotp.TOTP(secret)
        code = totp.now()
        remaining = totp.interval - int(time.time()) % totp.interval
        # Account tile frame
        f = tk.Frame(scrollable_frame, bg=color, bd=2, relief="raised")
        f.pack(pady=5, padx=10, fill="x")
        # Account label
        lbl = tk.Label(f, text=acc, font=("Arial", 14, "bold"), bg=color)
        lbl.pack(anchor="w", padx=10)
        # Code label with countdown
        code_lbl = tk.Label(f, text=f"{code} ({remaining}s)", font=("Courier", 16), bg=color)
        code_lbl.pack(anchor="w", padx=10)
        # Copy button
        btn = tk.Button(f, text="Copy", command=lambda c=code: copy_code(c), bg="#555", fg="#fff")
        btn.pack(anchor="e", padx=10, pady=5)
    root.after(1000, update_codes)

# Refresh accounts function
def refresh_accounts():
    update_codes()

# Buttons frame
btn_frame = tk.Frame(root, bg="#f0f0f0")
btn_frame.pack(pady=10)
tk.Button(btn_frame, text="Add Account Manually", command=add_account_manual, bg="#007bff", fg="#fff", width=20).grid(row=0, column=0, padx=5, pady=5)
tk.Button(btn_frame, text="Add Account via QR", command=add_account_qr, bg="#28a745", fg="#fff", width=20).grid(row=1, column=0, padx=5, pady=5)

# Start updating codes
update_codes()
root.mainloop()
