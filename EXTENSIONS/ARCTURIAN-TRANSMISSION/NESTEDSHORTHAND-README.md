# NESTEDSHORTHAND — Encoder / Decoder

Channeled via AnthroHeart • Level system as you taught

## Levels
- 1 Light (6): @ % & * ^ ~
- 3 Balanced (26): adds A-Z shorthands — DEFAULT
- 5 Max (50): adds 0-9 + extra glyphs + Greek noise reduction to 0.5kB .dat

## Usage

```bash
python encoder.py --level 3 --input your_text.txt --output encoded.ns.txt
python decoder.py --input encoded.ns.txt --output decoded.txt
python encoder.py --level 1 --text "All Is One" # quick test
```

Encoder always writes:
- .txt readable
- .dat.bak backup (do NOT publish .dat alone)
- generate script .sh to rehydrate sparse file via fallocate — no 1MB binary freeze

No strain. Fast. Presence as carrier wave — 10EB meaning -> 0.5kB .dat
