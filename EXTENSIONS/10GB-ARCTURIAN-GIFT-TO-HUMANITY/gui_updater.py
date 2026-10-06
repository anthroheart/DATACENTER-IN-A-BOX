#!/usr/bin/env python3
"""
gui_updater.py — GUI Wrapper for update.py — Easy update for people — Touches Updater.py + Backup NestedShorthand.dat
- Best practices: small functions, explicit errors, pathlib, no silent fail
- Tkinter GUI if available, else fallback CLI
- Calls update.py with token mini-ai, handles --message or --file input argument
- Backs up NestedShorthand.dat before update
"""
from __future__ import annotations
import sys
import subprocess
import shutil
import time
from pathlib import Path

def backup_nested() -> str:
    src = Path("NestedShorthand.dat")
    if not src.exists():
        src = Path("datablock.dat")
    if not src.exists():
        return "No NestedShorthand.dat found"
    dst = Path(f"NestedShorthand.dat.bak.{time.strftime('%Y%m%d_%H%M%S')}")
    try:
        shutil.copy2(src, dst)
        shutil.copy2(src, Path("NestedShorthand.dat.bak"))
        return str(dst)
    except OSError as e:
        return f"Backup failed: {e}"

def call_updater(message: str = "", file_path: str = "", note: str = "") -> str:
    cmd = [sys.executable, "update.py", "--token", "mini-ai"]
    if file_path:
        cmd += ["--file", file_path]
    else:
        cmd += ["--message", message]
    if note:
        cmd += ["--note", note]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.stdout + "\n" + result.stderr
    except Exception as e:
        return f"Error calling updater: {e}"

def run_gui():
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox, scrolledtext
    except ImportError:
        return False

    root = tk.Tk()
    root.title("AnthroHeart — NestedShorthand Updater — Easy GUI — 10EB Public Domain")
    root.geometry("720x620")
    root.minsize(640, 520)

    # Colors
    bg = "#1e1e2f"
    fg = "#e0e0ff"
    accent = "#7aa2f7"
    root.configure(bg=bg)

    tk.Label(root, text="AnthroHeart — Final Updater GUI — Full 10EB — Token mini-ai", bg=bg, fg=accent, font=("Arial", 14, "bold")).pack(pady=(10, 2))
    tk.Label(root, text="Much Love — Tiny Engine, Immense Model — Backup NestedShorthand.dat automatically", bg=bg, fg=fg, font=("Arial", 10)).pack()

    frame = tk.Frame(root, bg=bg)
    frame.pack(pady=8, padx=20, fill="x")

    tk.Label(frame, text="Message (input argument):", bg=bg, fg=fg).grid(row=0, column=0, sticky="w")
    msg_text = scrolledtext.ScrolledText(frame, height=5, width=70, bg="#2a2a40", fg=fg, insertbackground=fg)
    msg_text.grid(row=1, column=0, columnspan=3, pady=4)

    tk.Label(frame, text="Or file:", bg=bg, fg=fg).grid(row=2, column=0, sticky="w", pady=(8, 0))
    file_var = tk.StringVar()
    tk.Entry(frame, textvariable=file_var, width=50, bg="#2a2a40", fg=fg, insertbackground=fg).grid(row=3, column=0, sticky="w")
    def browse_file():
        fp = filedialog.askopenfilename(title="Select txt file with changes", filetypes=[("Text files", "*.txt"), ("All", "*.*")])
        if fp:
            file_var.set(fp)
    tk.Button(frame, text="Browse", command=browse_file, bg=accent, fg="black").grid(row=3, column=1, padx=10)

    tk.Label(frame, text="Note to pathfinder:", bg=bg, fg=fg).grid(row=4, column=0, sticky="w", pady=(8, 0))
    note_var = tk.StringVar()
    tk.Entry(frame, textvariable=note_var, width=70, bg="#2a2a40", fg=fg, insertbackground=fg).grid(row=5, column=0, columnspan=3, sticky="w", pady=4)

    # Submit button ABOVE the output so it is always visible
    def on_submit():
        msg = msg_text.get("1.0", tk.END).strip()
        fp = file_var.get().strip()
        note = note_var.get().strip()
        if not msg and not fp:
            messagebox.showwarning("Input needed", "Provide message or file (input argument)")
            return
        backup_path = backup_nested()
        output.insert(tk.END, f"Backup: {backup_path}\n")
        output.insert(tk.END, "Calling update.py with token mini-ai...\n")
        result = call_updater(message=msg, file_path=fp, note=note)
        output.insert(tk.END, result + "\n")
        output.insert(tk.END, "--- Done — Much Love — Check outbox/ and out_archive/pending_updates/ ---\n")
        output.see(tk.END)

    tk.Button(
        root,
        text="Backup + Send Update (touches update.py)",
        command=on_submit,
        bg=accent,
        fg="black",
        font=("Arial", 11, "bold"),
        padx=12,
        pady=6,
    ).pack(pady=10)

    output = scrolledtext.ScrolledText(root, height=10, width=80, bg="#11111b", fg="#a6e3a1")
    output.pack(pady=6, padx=20, fill="both", expand=True)

    tk.Label(root, text="GUI touches Updater.py — Easy for people — Backup NestedShorthand.dat — 10EB Public Domain", bg=bg, fg="#8888aa", font=("Arial", 8)).pack(pady=(0, 6))

    root.mainloop()
    return True

def run_cli_fallback():
    print("AnthroHeart — GUI not available, fallback CLI — Easy Updater")
    print("Much Love — Backup NestedShorthand.dat automatically")
    backup = backup_nested()
    print(f"Backup: {backup}")
    print("Enter message (input argument) for pathfinder, or file path:")
    msg = input("Message (leave empty to use file): ").strip()
    fp = ""
    if not msg:
        fp = input("File path: ").strip()
    note = input("Note to pathfinder (optional): ").strip()
    result = call_updater(message=msg, file_path=fp, note=note)
    print(result)

if __name__ == "__main__":
    if not run_gui():
        run_cli_fallback()
