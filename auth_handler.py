import os
import json
import tkinter as tk
from tkinter import messagebox
import sys
import ctypes

CRED_FILE = ".spotify_credentials"

def save_credentials(client_id, client_secret):
    creds = {"client_id": client_id, "client_secret": client_secret}
    with open(".spotify_credentials", "w") as f:
        json.dump(creds, f)

    # Make file hidden on Windows
    try:
        if os.name == 'nt':  # Windows
            ctypes.windll.kernel32.SetFileAttributesW(".spotify_credentials", 2)
    except Exception as e:
        print(f"Failed to hide credentials file: {e}")


def load_credentials():
    if not os.path.exists(CRED_FILE):
        return None
    with open(CRED_FILE, "r") as f:
        return json.load(f)

def delete_credentials():
    if os.path.exists(CRED_FILE):
        os.remove(CRED_FILE)

def prompt_for_credentials():
    cred_win = tk.Tk()
    cred_win.title("Spotify API Login")
    cred_win.geometry("400x200")
    cred_win.resizable(False, False)

    tk.Label(cred_win, text="Enter your Spotify API credentials", font=("Arial", 11, "bold")).pack(pady=10)
    tk.Label(cred_win, text="(You can get them at https://developer.spotify.com)").pack()

    tk.Label(cred_win, text="Client ID:").pack()
    client_id_entry = tk.Entry(cred_win, width=40)
    client_id_entry.pack()

    tk.Label(cred_win, text="Client Secret:").pack()
    client_secret_entry = tk.Entry(cred_win, show="*", width=40)
    client_secret_entry.pack()

    def on_ok():
        cid = client_id_entry.get().strip()
        secret = client_secret_entry.get().strip()
        if not cid or not secret:
            messagebox.showerror("Error", "Both fields are required.")
            return
        save_credentials(cid, secret)
        cred_win.destroy()

    def on_cancel():
        cred_win.destroy()
        sys.exit()

    button_frame = tk.Frame(cred_win)
    button_frame.pack(pady=10)
    tk.Button(button_frame, text="OK", command=on_ok, width=10).pack(side=tk.LEFT, padx=10)
    tk.Button(button_frame, text="Cancel", command=on_cancel, width=10).pack(side=tk.LEFT, padx=10)

    cred_win.mainloop()