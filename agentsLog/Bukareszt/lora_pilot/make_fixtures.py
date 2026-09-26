"""Deterministic ORIGINAL synthetic serving fixtures (no exam/benchmark content).

Writes fixtures/synthetic_text.json, fixtures/synthetic_image.png and
fixtures/synthetic_image.json. The PNG is drawn in pure Python (zlib), so its bytes are reproducible.
"""
import json, struct, zlib
from pathlib import Path

OUT = Path(__file__).resolve().parent / 'fixtures'


def png(w, h, px):
    raw = b''.join(b'\x00' + bytes(c for x in range(w) for c in px(x, y)) for y in range(h))
    chunk = lambda t, d: struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b'')


def pixel(x, y):
    if 40 <= x < 200 and 60 <= y < 220:  # red square, left
        return (220, 30, 30)
    if (x - 400) ** 2 + (y - 140) ** 2 <= 80 ** 2:  # blue circle, right
        return (30, 60, 220)
    return (255, 255, 255)


def main():
    OUT.mkdir(exist_ok=True)
    (OUT / 'synthetic_image.png').write_bytes(png(560, 280, pixel))
    common = {'max_tokens': 512, 'temperature': 0.0, 'top_k': 1, 'seed': 42, 'enable_thinking': False}
    (OUT / 'synthetic_text.json').write_text(json.dumps({**common, 'kind': 'text',
        'prompt': 'Napisz trzy krótkie zdania o tym, jak działa zegar słoneczny.'}, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    (OUT / 'synthetic_image.json').write_text(json.dumps({**common, 'kind': 'image', 'image': 'synthetic_image.png',
        'prompt': 'Jakie kształty i kolory widać na tym obrazku? Odpowiedz jednym zdaniem.'}, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
