import math
import random
from PIL import Image, ImageDraw, ImageFilter
from pathlib import Path

W, H = 1920, 1080
img = Image.new("RGB", (W, H), (10, 8, 14))
draw = ImageDraw.Draw(img)

# 1. Deep atmospheric radial background with war fire glow
for r in range(1200, 0, -4):
    f = r / 1200.0
    cr = int(58 * (1 - f)**2.0 + 9 * f)
    cg = int(32 * (1 - f)**2.0 + 6 * f)
    cb = int(10 * (1 - f)**2.0 + 13 * f)
    draw.ellipse([W//2 - int(r*1.4), H//2 - r, W//2 + int(r*1.4), H//2 + r], fill=(cr, cg, cb))

# 2. Concentric Chakravyuha Geometry in background
overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
odraw = ImageDraw.Draw(overlay)
cx, cy = W // 2, H // 2

for rad in [200, 340, 500, 680, 880]:
    alpha = max(15, int(55 - (rad / 1000) * 40))
    odraw.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], outline=(218, 165, 32, alpha), width=2)
    ticks = 24
    step = 360 / ticks
    for deg in range(0, 360, int(step)):
        ang = math.radians(deg)
        x1 = cx + (rad - 8) * math.cos(ang)
        y1 = cy + (rad - 8) * math.sin(ang)
        x2 = cx + (rad + 8) * math.cos(ang)
        y2 = cy + (rad + 8) * math.sin(ang)
        odraw.line([(x1, y1), (x2, y2)], fill=(255, 205, 90, alpha + 15), width=2)

# Floating embers
random.seed(1111)
for _ in range(140):
    ex = random.randint(20, W - 20)
    ey = random.randint(20, H - 20)
    erad = random.randint(2, 6)
    ealpha = random.randint(60, 220)
    odraw.ellipse([ex - erad, ey - erad, ex + erad, ey + erad], fill=(255, random.randint(140, 210), 40, ealpha))

img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
draw = ImageDraw.Draw(img)

# 3. Central Illuminated Scroll / Plaque (Pure visual, 0 text)
bx1, by1 = 380, 180
bx2, by2 = W - 380, H - 180

# Scroll Shadow
shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sdraw = ImageDraw.Draw(shadow)
sdraw.rectangle([bx1 + 12, by1 + 12, bx2 + 12, by2 + 12], fill=(0, 0, 0, 170))
img = Image.alpha_composite(img.convert("RGBA"), shadow).convert("RGB")
draw = ImageDraw.Draw(img)

# Scroll Body (Parchment & Bronze)
draw.rectangle([bx1, by1, bx2, by2], fill=(24, 19, 28), outline=(180, 130, 50), width=4)
draw.rectangle([bx1 + 8, by1 + 8, bx2 - 8, by2 - 8], outline=(80, 58, 25), width=2)
draw.rectangle([bx1 + 16, by1 + 16, bx2 - 16, by2 - 16], outline=(230, 185, 85), width=2)

# Scroll Handles / Rollers
draw.rectangle([bx1 - 30, by1 - 15, bx1 + 10, by2 + 15], fill=(45, 32, 15), outline=(220, 170, 70), width=3)
draw.rectangle([bx2 - 10, by1 - 15, bx2 + 30, by2 + 15], fill=(45, 32, 15), outline=(220, 170, 70), width=3)

# 4. Central Emblem: Divine Narrator Eye & Sacred Quill (Visual clue for opening crib)
em_cx, em_cy = cx, cy - 40

# Outer glowing emblem rings
for r_e in [140, 110, 80]:
    draw.ellipse([em_cx - r_e, em_cy - r_e, em_cx + r_e, em_cy + r_e], outline=(240, 190, 80), width=2)

# Divine Eye / Opening Salutation Emblem
# Eye outline
draw.arc([em_cx - 90, em_cy - 60, em_cx + 90, em_cy + 60], start=200, end=340, fill=(255, 215, 100), width=4)
draw.arc([em_cx - 90, em_cy - 60, em_cx + 90, em_cy + 60], start=20, end=160, fill=(255, 215, 100), width=4)
# Iris & Pupil
draw.ellipse([em_cx - 35, em_cy - 35, em_cx + 35, em_cy + 35], fill=(60, 40, 10), outline=(255, 225, 120), width=3)
draw.ellipse([em_cx - 15, em_cy - 15, em_cx + 15, em_cy + 15], fill=(255, 235, 150))

# Glowing Feather Quill touching the opening scroll position
qx1, qy1 = em_cx + 160, em_cy + 120
qx2, qy2 = em_cx + 40, em_cy + 150
draw.line([(qx1, qy1), (qx2, qy2)], fill=(255, 210, 90), width=5)
draw.polygon([(qx2, qy2), (qx2 + 25, qy2 - 15), (qx2 + 15, qy2 + 25)], fill=(255, 235, 140))

# 5. Outer Filigree Frame (Pure Visual, 0 Text)
pad = 35
draw.rectangle([pad, pad, W - pad, H - pad], outline=(170, 125, 45), width=4)
draw.rectangle([pad + 10, pad + 10, W - pad - 10, H - pad - 10], outline=(235, 190, 85), width=2)
draw.rectangle([pad + 18, pad + 18, W - pad - 18, H - pad - 18], outline=(100, 70, 25), width=1)

# Corner ornaments
for cx_c, cy_c in [(pad + 18, pad + 18), (W - pad - 18, pad + 18), 
                   (pad + 18, H - pad - 18), (W - pad - 18, H - pad - 18)]:
    draw.rectangle([cx_c - 20, cy_c - 20, cx_c + 20, cy_c + 20], fill=(18, 14, 22), outline=(240, 195, 90), width=2)
    draw.line([(cx_c - 12, cy_c), (cx_c + 12, cy_c)], fill=(255, 225, 120), width=2)
    draw.line([(cx_c, cy_c - 12), (cx_c, cy_c + 12)], fill=(255, 225, 120), width=2)

# Save image
out_brain = Path(r"C:\Users\Rohan\.gemini\antigravity-ide\brain\272b7099-9390-4886-a8d4-1f6cbbfe09ed\hint_one_notext.jpg")
out_proj = Path(r"d:\Kurukshetra\codebase C3\HINT 1.jpg")
out_public = Path(r"d:\Kurukshetra\codebase C3\public_artifacts\HINT 1.jpg")

img.save(out_brain, quality=95)
img.save(out_proj, quality=95)
img.save(out_public, quality=95)

print(f"Successfully generated pure visual Hint 1 image (NO TEXT) to:\n- {out_brain}\n- {out_proj}\n- {out_public}")
