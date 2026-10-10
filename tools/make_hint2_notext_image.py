import math
import random
from PIL import Image, ImageDraw, ImageFilter
from pathlib import Path

W, H = 1920, 1080
img = Image.new("RGB", (W, H), (8, 6, 12))
draw = ImageDraw.Draw(img)

# 1. Deep atmospheric radial background with war fire glow
for r in range(1200, 0, -4):
    f = r / 1200.0
    cr = int(55 * (1 - f)**2.0 + 8 * f)
    cg = int(30 * (1 - f)**2.0 + 5 * f)
    cb = int(10 * (1 - f)**2.0 + 12 * f)
    draw.ellipse([W//2 - int(r*1.4), H//2 - r, W//2 + int(r*1.4), H//2 + r], fill=(cr, cg, cb))

# 2. Concentric Chakravyuha & Cipher Wheel Rings (Pure visual geometry, 0 text)
overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
odraw = ImageDraw.Draw(overlay)
cx, cy = W // 2, H // 2

# 18 Sacred Radiating Spokes from the core
for i in range(18):
    ang = math.radians(i * (360 / 18))
    x2 = cx + 850 * math.cos(ang)
    y2 = cy + 850 * math.sin(ang)
    odraw.line([(cx, cy), (x2, y2)], fill=(240, 185, 75, 45), width=3)
    # Highlight notches on the 18 spokes
    for r_mark in [180, 300, 440, 600]:
        mx = cx + r_mark * math.cos(ang)
        my = cy + r_mark * math.sin(ang)
        odraw.ellipse([mx - 6, my - 6, mx + 6, my + 6], fill=(255, 220, 110, 180), outline=(255, 240, 180, 230))

# 4 Main Cipher Rotor Rings (Visual representation of the 4 wheels)
wheel_radii = [180, 300, 440, 600]
for idx, rad in enumerate(wheel_radii):
    # Ring track
    odraw.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], outline=(230, 180, 70, 200), width=4)
    odraw.ellipse([cx - rad + 8, cy - rad + 8, cx + rad - 8, cy + rad - 8], outline=(140, 100, 35, 120), width=2)
    odraw.ellipse([cx - rad - 8, cy - rad - 8, cx + rad + 8, cy + rad + 8], outline=(140, 100, 35, 120), width=2)
    
    # Outer gear teeth / notches (30 divisions per wheel)
    for deg in range(0, 360, 12):
        ang = math.radians(deg)
        x1 = cx + (rad - 12) * math.cos(ang)
        y1 = cy + (rad - 12) * math.sin(ang)
        x2 = cx + (rad + 12) * math.cos(ang)
        y2 = cy + (rad + 12) * math.sin(ang)
        odraw.line([(x1, y1), (x2, y2)], fill=(255, 210, 90, 150), width=2)

# Outer 5th Protective Vyuha Circle
odraw.ellipse([cx - 760, cy - 760, cx + 760, cy + 760], outline=(255, 195, 65, 160), width=3)

# Glowing Lotus / Chakra Core
odraw.ellipse([cx - 70, cy - 70, cx + 70, cy + 70], fill=(255, 215, 100, 220), outline=(255, 245, 200, 255), width=4)
odraw.ellipse([cx - 30, cy - 30, cx + 30, cy + 30], fill=(255, 255, 220, 240))

# 3. Floating Embers & Fire Dust
random.seed(181818)
for _ in range(160):
    ex = random.randint(20, W - 20)
    ey = random.randint(20, H - 20)
    erad = random.randint(2, 7)
    ealpha = random.randint(70, 230)
    odraw.ellipse([ex - erad, ey - erad, ex + erad, ey + erad], fill=(255, random.randint(130, 210), 30, ealpha))

# Composite layers
img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
draw = ImageDraw.Draw(img)

# 4. Outer Filigree Frame (Pure Visual, NO TEXT)
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
out_brain = Path(r"C:\Users\Rohan\.gemini\antigravity-ide\brain\272b7099-9390-4886-a8d4-1f6cbbfe09ed\hint_two_notext.jpg")
out_proj = Path(r"d:\Kurukshetra\codebase C3\HINT 2.jpg")
out_public = Path(r"d:\Kurukshetra\codebase C3\public_artifacts\HINT 2.jpg")

img.save(out_brain, quality=95)
img.save(out_proj, quality=95)
img.save(out_public, quality=95)

print(f"Successfully generated pure visual Hint 2 image (NO TEXT) to:\n- {out_brain}\n- {out_proj}\n- {out_public}")
