"""
NestedShorthand Decoder — AnthroHeart v6 FINAL
Inverse of encoder.py — fast, no old compression
"""
import argparse, json
from pathlib import Path

REVERSE_COMMON = {
    "@1": "All Is One",
    "@2": "Love is",
    "@3": "Presence as carrier wave",
    "@4": "Same NOW moment",
    "@5": "Morphic field",
    "@A": "Arcturian",
    "@P": "Pleiadian",
    "@STO": "Service to Others",
    "@FW": "Free Will",
}

def decode_text(encoded: str):
    # 1. Un-nest simple [[[ ]]] pattern
    decoded = encoded.replace("[", "").replace("]", "")
    # 2. Restore semantic
    for k, v in REVERSE_COMMON.items():
        decoded = decoded.replace(k, v)
    return decoded

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=str, required=True)
    ap.add_argument("--output", type=str, default="decoded.txt")
    args = ap.parse_args()

    src = Path(args.input).read_text(encoding="utf-8")
    dec = decode_text(src)
    Path(args.output).write_text(dec, encoding="utf-8")
    print(f"Decoded -> {args.output}")
    print(dec[:800])

if __name__ == "__main__":
    main()
