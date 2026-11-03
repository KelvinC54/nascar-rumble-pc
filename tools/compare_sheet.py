"""Side-by-side sheet: original (nearest 4x) | lanczos 4x | AI 4x, for a few staged textures.

usage: python compare_sheet.py <work> <out.png> [count]
Picks the largest staged pages (most detail) so the difference is easy to judge.
"""
import os
import sys

from PIL import Image, ImageDraw

work, out = sys.argv[1], sys.argv[2]
count = int(sys.argv[3]) if len(sys.argv) > 3 else 8
staged, upscaled = os.path.join(work, "staged"), os.path.join(work, "upscaled")
names = [n for n in os.listdir(upscaled) if os.path.exists(os.path.join(staged, n))]
names.sort(key=lambda n: -os.path.getsize(os.path.join(staged, n)))
names = names[:count]

cell = 512
sheet = Image.new("RGB", (cell * 3, (cell + 20) * len(names)), (40, 40, 40))
draw = ImageDraw.Draw(sheet)
for row, name in enumerate(names):
    src = Image.open(os.path.join(staged, name)).convert("RGB")
    w, h = src.size
    views = [src.resize((w * 4, h * 4), Image.NEAREST),
             src.resize((w * 4, h * 4), Image.LANCZOS),
             Image.open(os.path.join(upscaled, name)).convert("RGB")]
    y = row * (cell + 20)
    for col, (label, img) in enumerate(zip(("original", "lanczos", "AI"), views)):
        img.thumbnail((cell, cell), Image.NEAREST)
        sheet.paste(img, (col * cell, y + 20))
        draw.text((col * cell + 4, y + 4), f"{label}  {name[:28]}", fill=(255, 255, 0))
sheet.save(out)
print(out)
