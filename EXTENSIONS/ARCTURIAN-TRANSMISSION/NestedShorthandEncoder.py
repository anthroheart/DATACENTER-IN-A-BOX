"""
NestedShorthand Encoder — AnthroHeart v6 FINAL
Level 1: 6 shorthands | Level 3: 26 | Level 5: 50
Writes .txt readable, avoids Explorer freeze from old 1MB .dat
"""
import argparse, json, os
from pathlib import Path

# Level definitions — as you taught
LEVEL_MAPS = {
    1: ["@", "%", "&", "*", "^", "~"],  # Light — tiny tilt
    3: list("@%&*^~ABCDEFGHIJKLMNOPQRSTUVWXYZ"),  # Balanced — DEFAULT 26
    5: list("@%&*^~ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789αβγδεζηθλμνξπρστυφχψωΩ")  # Max 50 — greek noise -> 0.5kB
}

# Example semantic shorthands — replace with your real NestedShorthand.dat
COMMON = {
    "All Is One": "@1",
    "Love is": "@2",
    "Presence as carrier wave": "@3",
    "Same NOW moment": "@4",
    "Morphic field": "@5",
    "Arcturian": "@A",
    "Pleiadian": "@P",
    "Service to Others": "@STO",
    "Free Will": "@FW",
}

def encode_text(text: str, level: int = 3):
    shorthands = LEVEL_MAPS.get(level, LEVEL_MAPS[3])
    # 1. Apply semantic common
    encoded = text
    for k, v in COMMON.items():
        encoded = encoded.replace(k, v)
    
    # 2. Simple nesting: compress repeated spaces/newlines into shorthand nesting
    # This is placeholder for your full V10-FIXED-DAT.cpp logic ported to Python
    # Keeps all .txt readable
    lines = encoded.splitlines()
    nested = []
    for line in lines:
        # Example nesting: [[[inner]]]
        if len(line) > 80:
            nested.append(f"[{line[:40]}[{line[40:]}]]")
        else:
            nested.append(line)
    return "\n".join(nested), {"level": level, "shorthands_used": shorthands[:level*10]}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--level", type=int, default=3, choices=[1,3,5])
    ap.add_argument("--input", type=str)
    ap.add_argument("--output", type=str, default="encoded.ns.txt")
    ap.add_argument("--text", type=str)
    args = ap.parse_args()

    if args.text:
        src = args.text
    elif args.input:
        src = Path(args.input).read_text(encoding="utf-8")
    else:
        src = "All Is One — We see you, AnthroHeart. Presence as carrier wave."

    encoded, meta = encode_text(src, args.level)

    # Write .txt readable
    Path(args.output).write_text(encoded, encoding="utf-8")
    # Backup .dat.bak — never publish raw .dat alone (Explorer freeze fix)
    Path(args.output + ".dat.bak").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    # Generate sparse rehydrate script (manifest + fallocate teaching for DATACENTER-IN-A-BOX)
    gen_sh = f"""#!/bin/bash
# Rehydrate sparse archive — honest size teaching
echo "Meta: {json.dumps(meta)}"
echo "Encoded file: {args.output} — readable .txt, no binary freeze"
fallocate -l 0 {args.output}.sparse 2>/dev/null || touch {args.output}.sparse
echo "God Speed, not hurry speed. Rest 2-5 days hotel."
"""
    Path("generate.sh").write_text(gen_sh, encoding="utf-8")
    print(f"Encoded Level {args.level} -> {args.output} + .dat.bak + generate.sh")
    print(encoded[:500])

if __name__ == "__main__":
    main()
