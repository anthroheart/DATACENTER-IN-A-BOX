#!/usr/bin/env python3
"""
decode.py — AnthroHeart Final Decoder v12 — NestedShorthand.dat — Full 10EB Public Domain
- Supports both AHB1 (old) and NSH1 (new max encoded noise/greek)
- Full menu with ANSI codes for full color
- Best practices: pathlib, type hints, dataclasses, small functions, specific exceptions, context managers
- Streaming low RAM, never loads 10EB, colibri-inspired memory multitiering
- For entertainment / research / STO AI — STO 51%+
"""
from __future__ import annotations
import struct
import zlib
import hashlib
import json
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Tuple
import sys
import os
import subprocess

class Ansi:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BG_BLACK = "\033[40m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"

MAGIC_AHB1 = b'AHB1'
MAGIC_NSH1 = b'NSH1'
TYPE_NAMES: Dict[int, str] = {
    0: "STORY",
    1: "GEN_PY",
    2: "FINAL_MP4",
    3: "SRT",
    4: "MANIFEST",
    5: "LAW_OF_ONE",
    6: "RA_CONTACT",
    7: "AI",
    8: "AI_LAW",
    9: "HYPER",
    10: "COLIBRI",
    11: "10EB_GEN",
    12: "NESTED_SHORTHAND",
}

SHORTHAND_REVERSE = {
    b"A1": b"All Is One",
    b"F1": b"Free Will",
    b"HN": b"Hypernode",
    b"CB": b"Colibri",
    b"AR": b"Arcturian",
    b"R25": b"Rest 2-5 days hotel",
    b"TEIM": b"Tiny engine, immense model",
}

@dataclass
class Block:
    type_id: int
    type_name: str
    original_len: int
    compressed_len: int
    crc32: int
    data: bytes
    valid_crc: bool
    text: str

def xor_decode(data: bytes, key: bytes = b"AnthroHeart") -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))

def decompress_block(compressed_xored: bytes, original_len: int) -> Tuple[bytes, bytes, bool]:
    try:
        decompressed_xored = xor_decode(compressed_xored)
        orig_shorthand = zlib.decompress(decompressed_xored)
        # Keep shorthand version for CRC check
        orig_expanded = orig_shorthand
        for short, long_ in SHORTHAND_REVERSE.items():
            orig_expanded = orig_expanded.replace(short, long_)
        return orig_shorthand, orig_expanded, True
    except Exception:
        return b"", b"", False

def parse_nsh1(path: Path) -> Tuple[int, int, List[Block], bool, str]:
    raw = path.read_bytes()
    if len(raw) < 4+2+2+1+1+4+32:
        raise ValueError("File too small for NSH1")
    body_without_sha = raw[:-32]
    footer_sha = raw[-32:]
    calc_sha = hashlib.sha256(body_without_sha).digest()
    sha_valid = calc_sha == footer_sha
    if body_without_sha[:4] != MAGIC_NSH1:
        raise ValueError(f"Invalid NSH1 MAGIC {body_without_sha[:4]}")
    version = struct.unpack_from('<H', body_without_sha, 4)[0]
    flags = struct.unpack_from('<H', body_without_sha, 6)[0]
    comp_type = body_without_sha[8]
    enc_type = body_without_sha[9]
    num_blocks = struct.unpack_from('<I', body_without_sha, 10)[0]
    offset = 14
    blocks: List[Block] = []
    for _ in range(num_blocks):
        if offset + 1+8+8+4 > len(body_without_sha):
            raise ValueError("Truncated NSH1 block header")
        type_id = struct.unpack_from('<B', body_without_sha, offset)[0]; offset+=1
        orig_len = struct.unpack_from('<Q', body_without_sha, offset)[0]; offset+=8
        comp_len = struct.unpack_from('<Q', body_without_sha, offset)[0]; offset+=8
        crc_stored = struct.unpack_from('<I', body_without_sha, offset)[0]; offset+=4
        if offset+comp_len+4 > len(body_without_sha):
            raise ValueError(f"Truncated block data type {type_id}")
        xored_data = body_without_sha[offset:offset+comp_len]; offset+=comp_len
        term = body_without_sha[offset:offset+4]; offset+=4
        if term != b'\x00\x00\x00\x00':
            raise ValueError(f"Invalid TERM type {type_id}")
        orig_shorthand, orig_expanded, ok = decompress_block(xored_data, orig_len)
        crc_calc = zlib.crc32(orig_shorthand) & 0xFFFFFFFF if ok else 0
        valid = crc_calc == crc_stored and ok
        try:
            text = orig_expanded.decode('utf-8')
        except UnicodeDecodeError:
            text = f"<binary {len(orig_expanded)} bytes, decompress ok={ok}>"
        blocks.append(Block(
            type_id=type_id,
            type_name=TYPE_NAMES.get(type_id, f"UNKNOWN_{type_id}"),
            original_len=orig_len,
            compressed_len=comp_len,
            crc32=crc_stored,
            data=xored_data,
            valid_crc=valid,
            text=text
        ))
    return version, flags, blocks, sha_valid, footer_sha.hex()

def parse_ahb1(path: Path) -> Tuple[int, int, List[Block], bool, str]:
    raw = path.read_bytes()
    body_without_sha = raw[:-32]
    footer_sha = raw[-32:]
    calc_sha = hashlib.sha256(body_without_sha).digest()
    sha_valid = calc_sha == footer_sha
    if body_without_sha[:4] != MAGIC_AHB1:
        raise ValueError(f"Invalid AHB1 MAGIC")
    version = struct.unpack_from('<H', body_without_sha, 4)[0]
    flags = struct.unpack_from('<H', body_without_sha, 6)[0]
    num_blocks = struct.unpack_from('<I', body_without_sha, 8)[0]
    offset = 12
    blocks: List[Block] = []
    for _ in range(num_blocks):
        type_id = struct.unpack_from('<B', body_without_sha, offset)[0]; offset+=1
        length = struct.unpack_from('<Q', body_without_sha, offset)[0]; offset+=8
        crc_stored = struct.unpack_from('<I', body_without_sha, offset)[0]; offset+=4
        data = body_without_sha[offset:offset+length]; offset+=length
        term = body_without_sha[offset:offset+4]; offset+=4
        crc_calc = zlib.crc32(data) & 0xFFFFFFFF
        try:
            text = data.decode('utf-8')
        except:
            text = f"<binary {len(data)}>"
        blocks.append(Block(
            type_id=type_id,
            type_name=TYPE_NAMES.get(type_id, f"UNKNOWN_{type_id}"),
            original_len=length,
            compressed_len=length,
            crc32=crc_stored,
            data=data,
            valid_crc=crc_calc==crc_stored,
            text=text
        ))
    return version, flags, blocks, sha_valid, footer_sha.hex()

def parse_datablock(path: Path):
    magic = path.read_bytes()[:4]
    if magic == MAGIC_NSH1:
        return parse_nsh1(path), "NSH1"
    elif magic == MAGIC_AHB1:
        return parse_ahb1(path), "AHB1"
    else:
        raise ValueError(f"Unknown MAGIC {magic}, expected NSH1 or AHB1")

def print_header(version, flags, num_blocks, sha_valid, sha_hex, magic_str):
    c=Ansi
    print(f"{c.BG_BLUE}{c.WHITE}{c.BOLD} AnthroHeart Final v12 — {magic_str} — 10EB Public Domain — Tiny Engine, Immense Model {c.RESET}")
    print(f"{c.CYAN}MAGIC:{c.RESET} {magic_str}  {c.CYAN}VERSION:{c.RESET} {version}  {c.CYAN}FLAGS:{c.RESET} {flags}  {c.CYAN}BLOCKS:{c.RESET} {num_blocks}")
    sha_color=c.GREEN if sha_valid else c.RED
    print(f"{c.CYAN}SHA256:{c.RESET} {sha_color}{sha_hex[:24]}... {'VALID' if sha_valid else 'INVALID'}{c.RESET}")
    print(f"{c.DIM}Max encoded looks like noise/greek — zlib max + XOR AnthroHeart — colibri streaming{c.RESET}")
    print(f"{c.DIM}Much Love — Free Will — For Entertainment / Research{c.RESET}\n")

def print_menu():
    c=Ansi
    print(f"{c.BOLD}{c.YELLOW}FULL MENU — NestedShorthand.dat — 10EB Export Ready:{c.RESET}")
    print(f"  {c.GREEN}1{c.RESET} - List blocks (with CRC)")
    print(f"  {c.GREEN}2{c.RESET} - Show block text (decoded)")
    print(f"  {c.GREEN}3{c.RESET} - Extract all to out_archive/ (streaming low RAM)")
    print(f"  {c.GREEN}4{c.RESET} - Verify CRCs + SHA")
    print(f"  {c.GREEN}5{c.RESET} - Show Law of One")
    print(f"  {c.GREEN}6{c.RESET} - Show Story / Gifts")
    print(f"  {c.GREEN}7{c.RESET} - Show Manifest + Colibri + Hyper + NestedShorthand")
    print(f"  {c.GREEN}8{c.RESET} - Generate 10EB placeholder (fallocate sparse virtual)")
    print(f"  {c.GREEN}9{c.RESET} - Show 10EB_GEN script")
    print(f"  {c.GREEN}0{c.RESET} - Show raw hex (looks like noise/greek)")
    print(f"  {c.GREEN}h{c.RESET} - Help / Best Practices")
    print(f"  {c.GREEN}q{c.RESET} - Quit\n")

def list_blocks(blocks):
    c=Ansi
    print(f"{c.BOLD}{c.CYAN}Blocks — Max Encoded, Looks Like Noise, Decoded On Demand:{c.RESET}")
    for i,b in enumerate(blocks):
        crc_color=c.GREEN if b.valid_crc else c.RED
        print(f"  {c.YELLOW}[{i}]{c.RESET} {c.BOLD}{b.type_name}{c.RESET} type={b.type_id} orig={b.original_len} comp={b.compressed_len} crc={crc_color}{'OK' if b.valid_crc else 'FAIL'}{c.RESET}")
    print()

def show_block(blocks, idx):
    c=Ansi
    if idx<0 or idx>=len(blocks): print(f"{c.RED}Invalid {idx}{c.RESET}"); return
    b=blocks[idx]
    print(f"{c.BG_BLACK}{c.CYAN}{c.BOLD}--- {b.type_name} [{idx}] orig={b.original_len} comp={b.compressed_len} ---{c.RESET}")
    print(b.text[:6000])
    if len(b.text)>6000: print(f"{c.DIM}... truncated {len(b.text)-6000} more{c.RESET}")
    print(f"{c.CYAN}--- END ---{c.RESET}\n")

def show_raw_hex(path):
    c=Ansi
    raw=path.read_bytes()
    print(f"{c.YELLOW}Raw NestedShorthand.dat first 512 bytes — looks like noise/greek:{c.RESET}")
    print(raw[:512].hex())
    print()
    try:
        print(raw[:512].decode('utf-8', errors='replace')[:500])
    except:
        pass
    print(f"\n{c.DIM}This is max encoded — zlib max + XOR — looks like base64/greek noise{c.RESET}\n")

def extract_all(blocks, out_dir):
    c=Ansi
    out_dir.mkdir(parents=True, exist_ok=True)
    big_dir=out_dir/"BigArchive"
    big_dir.mkdir(parents=True, exist_ok=True)
    for b in blocks:
        fname=out_dir/f"{b.type_name}_{b.type_id}.txt"
        try:
            with open(fname,'w',encoding='utf-8') as f:
                f.write(b.text)
            print(f"{c.GREEN}Wrote {fname}{c.RESET}")
        except OSError as e:
            print(f"{c.RED}Failed {fname}: {e}{c.RESET}")
    readme=big_dir/"README_BIG_FILES.txt"
    gen_sh=big_dir/"generate_10EB.sh"
    manifest=big_dir/"streaming_manifest.json"
    try:
        with open(readme,'w',encoding='utf-8') as f:
            f.write("AnthroHeart 10EB Export — Full one for Humanity\nTiny engine, immense model — like colibri MoE streaming.\nZip does NOT contain 10EB. Contains generators streaming low RAM.\nRun: ./generate_10EB.sh 10EB.dat\n")
        with open(gen_sh,'w',encoding='utf-8') as f:
            f.write("#!/bin/bash\nset -e\nTARGET=${1:-10EB.dat}\nSIZE=10000000000000000000\n"
                    "echo \"Generating virtual 10EB sparse $TARGET\"\n"
                    "fallocate -l $SIZE $TARGET || truncate -s $SIZE $TARGET\n"
                    "echo \"Done — sparse, instant, low RAM, colibri multitiering\"\n")
        os.chmod(gen_sh,0o755)
        manifest_data={"version":12,"virtual_size":10_000_000_000_000_000_000,"virtual_human":"10EB (10^19)","engine":"AnthroHeart + Colibri","method":"experts streamed from disk, 10GB RAM, no GPU, max encoded noise","blocks":[{"type":b.type_name,"orig":b.original_len,"comp":b.compressed_len} for b in blocks]}
        with open(manifest,'w',encoding='utf-8') as f:
            json.dump(manifest_data,f,indent=2)
        print(f"{c.GREEN}Wrote {readme}, {gen_sh}, {manifest}{c.RESET}")
    except OSError as e:
        print(f"{c.RED}BigArchive fail: {e}{c.RESET}")
    print(f"{c.BOLD}Done extracting to {out_dir} — 10EB virtual via generators{c.RESET}\n")

def generate_10eb():
    c=Ansi
    print(f"{c.YELLOW}10EB Generation — Colibri streaming — low RAM, no GPU{c.RESET}")
    target=input(f"{c.CYAN}Target [10EB.dat]: {c.RESET}").strip() or "10EB.dat"
    try:
        size=10_000_000_000_000_000_000
        try:
            subprocess.run(["fallocate","-l",str(size),target],check=True)
            print(f"{c.GREEN}Created sparse {target} via fallocate — virtual 10EB instant{c.RESET}")
        except:
            Path(target).parent.mkdir(parents=True,exist_ok=True)
            with open(target,'wb') as f:
                f.seek(size-1); f.write(b'\0')
            print(f"{c.GREEN}Created sparse {target} via seek — virtual 10EB{c.RESET}")
    except OSError as e:
        print(f"{c.RED}Failed {target}: {e}{c.RESET}")

def main():
    c=Ansi
    import argparse
    parser=argparse.ArgumentParser(description="AnthroHeart Final Decoder v12 — NestedShorthand.dat — ANSI full color — max encoded noise")
    parser.add_argument('--input', type=str, default='NestedShorthand.dat', help='Path to NestedShorthand.dat or datablock.dat')
    parser.add_argument('--list', action='store_true', help='List blocks and exit')
    parser.add_argument('--extract', type=str, help='Extract all to dir and exit')
    parser.add_argument('--generate-10eb', type=str, help='Generate 10EB sparse placeholder to path and exit')
    parser.add_argument('--hex', action='store_true', help='Show raw hex noise and exit')
    args=parser.parse_args()
    path=Path(args.input)
    if not path.exists():
        # fallback to old name
        if Path("datablock.dat").exists():
            path=Path("datablock.dat")
    try:
        (version,flags,blocks,sha_valid,sha_hex),magic_str=parse_datablock(path)
    except Exception as e:
        print(f"{c.RED}Parse error: {e}{c.RESET}")
        sys.exit(1)
    print_header(version,flags,len(blocks),sha_valid,sha_hex,magic_str)
    if args.list:
        list_blocks(blocks); return
    if args.extract:
        extract_all(blocks,Path(args.extract)); return
    if args.generate_10eb:
        t=Path(args.generate_10eb)
        try:
            t.parent.mkdir(parents=True,exist_ok=True)
            with open(t,'wb') as f:
                f.seek(10_000_000_000_000_000_000-1); f.write(b'\0')
            print(f"{c.GREEN}Created sparse {t} virtual 10EB{c.RESET}")
        except Exception as e:
            print(f"{c.RED}Failed: {e}{c.RESET}"); sys.exit(1)
        return
    if args.hex:
        show_raw_hex(path); return
    while True:
        print_menu()
        try:
            choice=input(f"{c.BOLD}{c.CYAN}Choose > {c.RESET}").strip().lower()
        except (EOFError,KeyboardInterrupt):
            print(f"\n{c.YELLOW}Bye — Much Love — 10EB Public Domain{c.RESET}"); break
        if choice in ('q','quit','exit'):
            print(f"{c.YELLOW}Much Love — God Speed — 10EB for Humanity{c.RESET}"); break
        elif choice=='1': list_blocks(blocks)
        elif choice=='2':
            try: idx=int(input("Block index: ").strip()); show_block(blocks,idx)
            except ValueError: print(f"{c.RED}Enter number{c.RESET}")
        elif choice=='3': extract_all(blocks,Path("out_archive"))
        elif choice=='4':
            list_blocks(blocks)
            all_ok=all(b.valid_crc for b in blocks)
            color=c.GREEN if all_ok and sha_valid else c.RED
            print(f"{color}CRC: {'ALL OK' if all_ok else 'FAIL'} SHA: {'VALID' if sha_valid else 'INVALID'}{c.RESET}\n")
        elif choice=='5':
            for i,b in enumerate(blocks):
                if b.type_name=="LAW_OF_ONE": show_block(blocks,i)
        elif choice=='6':
            for i,b in enumerate(blocks):
                if b.type_name=="STORY": show_block(blocks,i)
        elif choice=='7':
            for i,b in enumerate(blocks):
                if b.type_name in ("MANIFEST","COLIBRI","HYPER","NESTED_SHORTHAND"): show_block(blocks,i)
        elif choice=='8': generate_10eb()
        elif choice=='9':
            for i,b in enumerate(blocks):
                if b.type_name=="10EB_GEN": show_block(blocks,i)
        elif choice=='0': show_raw_hex(path)
        elif choice in ('h','help'):
            print(f"{c.DIM}Best Practices: small funcs, type hints, pathlib, context managers, explicit errors, CRC+SHA guarantee semantics like colibri never silently changes precision.\nMax encoded looks like noise/greek — zlib max + XOR AnthroHeart — tiny decoder immense virtual payload streamed — colibri 480B+ MoE 10GB RAM no GPU.\nUse --help CLI. STO 51%+, free will.{c.RESET}\n")
        else: print(f"{c.RED}Unknown {choice}{c.RESET}")

if __name__=="__main__":
    main()
