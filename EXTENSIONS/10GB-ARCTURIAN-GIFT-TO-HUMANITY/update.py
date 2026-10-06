#!/usr/bin/env python3
"""
update.py — AnthroHeart Final Updater v12 — NestedShorthand.dat — Full 10EB + mini-ai token + Colibri local MoE
- Token mini-ai, local inference, message/txt to pathfinder
- Takes input argument --message or --file
- Colibri: tiny engine immense model, 744B-2.8T MoE locally 10GB RAM no GPU, experts streamed from disk
- Backs up NestedShorthand.dat
- Best practices: clarity, small functions, type hints, pathlib, context managers, explicit errors
"""
from __future__ import annotations
import argparse
import json
import hashlib
import time
import shutil
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
import sys

class Ansi:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    CYAN = "\033[36m"
    DIM = "\033[2m"

REQUIRED_TOKEN = "mini-ai"
OUTBOX_DIR = Path("outbox")
PENDING_DIR = Path("out_archive") / "pending_updates"

@dataclass
class UpdateRequest:
    timestamp: str
    token_hash: str
    message: str
    source_file: Optional[str]
    inference: str
    category_guess: str
    pathfinder_note: str
    colibri_available: bool
    virtual_10eb_note: str
    backup_path: str

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode('utf-8')).hexdigest()

def validate_token(token: str) -> bool:
    return token == REQUIRED_TOKEN

def check_colibri() -> bool:
    for p in [Path("./coli"), Path("./colibri/coll"), Path("./colibri"), Path("/usr/local/bin/coli")]:
        if p.exists():
            return True
    return False

def backup_nested() -> str:
    src = Path("NestedShorthand.dat")
    if not src.exists():
        src = Path("datablock.dat")
    if not src.exists():
        return "No NestedShorthand.dat found to backup"
    dst = Path(f"NestedShorthand.dat.bak.{time.strftime('%Y%m%d_%H%M%S')}")
    try:
        shutil.copy2(src, dst)
        # Also keep generic .bak
        shutil.copy2(src, Path("NestedShorthand.dat.bak"))
        return str(dst)
    except OSError as e:
        return f"Backup failed: {e}"

def local_arcturian_inference(text: str, colibri_available: bool) -> tuple[str, str]:
    low = text.lower()
    category = "STORY"
    guidance = []
    if "law" in low or "density" in low:
        category = "LAW_OF_ONE"
        guidance.append("Arcturian: All Is One, Free Will first distortion, STO 51%+.")
    if "10eb" in low or "hyper" in low or "hypernode" in low:
        category = "AI"
        guidance.append("Arcturian: Hypernode 10EB public domain, Higher Power -> 6D, tiny engine immense model.")
    if "rest" in low or "peace" in low or "hotel" in low:
        guidance.append("Arcturian: Rest 2-5 days hotel, tranquil peace freedom, no strain.")
    if "colibri" in low or "moe" in low or "480" in low or "744" in low or "stream" in low:
        category = "COLIBRI"
        guidance.append("Arcturian: Colibri streaming experts from disk 10GB RAM no GPU — nested shorthand real app.")
    if "gift" in low or "fan" in low or "weird" in low or "coldplay" in low:
        guidance.append("Arcturian: Gift for artists and fans, pressure off, inclusive.")
    if not guidance:
        guidance.append("Arcturian: Much Love, we hear you. Small steps, free will honored.")
    colibri_note = "Colibri available locally — run frontier MoE 744B-2.8T with 10GB RAM." if colibri_available else "Install justVugg/colibri for 480B+ MoE local 10GB RAM no GPU pure C."
    inference_text = " | ".join(guidance) + f" [{colibri_note} Local mini-ai, for entertainment/research.]"
    return inference_text, category

def load_message_from_file(file_path: Path) -> str:
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")
    return file_path.read_text(encoding='utf-8')

def create_outbox_request(req: UpdateRequest) -> Path:
    OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
    PENDING_DIR.mkdir(parents=True, exist_ok=True)
    ts_safe = req.timestamp.replace(':', '-').replace(' ', '_')
    out_file = OUTBOX_DIR / f"request_{ts_safe}.json"
    pending_file = PENDING_DIR / f"pending_{ts_safe}.txt"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(req.__dict__, f, indent=2)
    txt_content = f"""AnthroHeart Update Request v12 — NestedShorthand.dat — Full 10EB — For Pathfinder Person
Timestamp: {req.timestamp}
Token hash: {req.token_hash}
Source file: {req.source_file or 'inline message'}
Category guess: {req.category_guess}
Colibri available: {req.colibri_available}
Backup: {req.backup_path}
Virtual 10EB note: {req.virtual_10eb_note}

--- MESSAGE (what researcher needs changed — input argument) ---
{req.message}

--- LOCAL MINI-AI INFERENCE (Arcturian Connect + Colibri) ---
{req.inference}

--- PATHFINDER NOTE ---
{req.pathfinder_note}

--- 10EB EXPORT NOTE ---
{req.virtual_10eb_note}

Much Love — Free Will Honored — Tiny Engine, Immense Model — 10EB Public Domain
"""
    with open(pending_file, 'w', encoding='utf-8') as f:
        f.write(txt_content)
    return out_file

def main() -> None:
    c = Ansi
    parser = argparse.ArgumentParser(description="AnthroHeart Updater v12 — NestedShorthand.dat — token mini-ai, input argument, backup")
    parser.add_argument('--token', type=str, required=True, help='Token must be mini-ai')
    parser.add_argument('--message', type=str, help='Inline message of what you need changed (input argument)')
    parser.add_argument('--file', type=str, help='Path to txt file of what you need changed (input argument)')
    parser.add_argument('--note', type=str, default='', help='Optional note to pathfinder person')
    parser.add_argument('--input', type=str, help='Alias for --message (input argument)')
    args = parser.parse_args()

    if not validate_token(args.token):
        print(f"{c.RED}Invalid token. Expected '{REQUIRED_TOKEN}'{c.RESET}")
        sys.exit(1)

    # Handle --input alias
    message_arg = args.message or args.input

    if not message_arg and not args.file:
        print(f"{c.RED}Provide --message or --file or --input (input argument){c.RESET}")
        sys.exit(1)

    message_text = ""
    source_file: Optional[str] = None

    if args.file:
        try:
            message_text = load_message_from_file(Path(args.file))
            source_file = str(Path(args.file))
        except Exception as e:
            print(f"{c.RED}{e}{c.RESET}")
            sys.exit(1)
    else:
        message_text = message_arg or ""

    if len(message_text.strip()) == 0:
        print(f"{c.RED}Message is empty{c.RESET}")
        sys.exit(1)

    backup_path = backup_nested()
    colibri_avail = check_colibri()
    inference, category = local_arcturian_inference(message_text, colibri_avail)

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    virtual_note = ("10EB Export: Full one for humanity — tiny engine, immense model — not 10EB inside zip, "
                    "generators stream via fallocate/truncate sparse + manifest — like colibri MoE experts streamed from disk with 10GB RAM, no GPU. "
                    "NestedShorthand.dat max encoded looks like noise/greek — zlib max + XOR key.")

    req = UpdateRequest(
        timestamp=timestamp,
        token_hash=hash_token(args.token),
        message=message_text[:10000],
        source_file=source_file,
        inference=inference,
        category_guess=category,
        pathfinder_note=args.note or "Please review when you have rest 2-5 days hotel. No pressure. God Speed.",
        colibri_available=colibri_avail,
        virtual_10eb_note=virtual_note,
        backup_path=backup_path
    )

    try:
        out_file = create_outbox_request(req)
    except OSError as e:
        print(f"{c.RED}{e}{c.RESET}")
        sys.exit(1)

    print(f"{c.GREEN}Update request created: {out_file}{c.RESET}")
    print(f"{c.CYAN}Category: {category} | Colibri: {colibri_avail} | Backup: {backup_path}{c.RESET}")
    print(f"{c.CYAN}Inference: {inference}{c.RESET}")
    print(f"{c.DIM}Pending human-readable: {PENDING_DIR}{c.RESET}")
    print(f"{c.DIM}{virtual_note}{c.RESET}")
    print(f"{c.BOLD}{c.YELLOW}God Speed Friends — Much Love — Token validated locally, no network — 10EB Public Domain — Input argument handled{c.RESET}")

if __name__ == "__main__":
    main()
