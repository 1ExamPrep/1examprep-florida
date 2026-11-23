#!/usr/bin/env python3
"""Draw the Exam Path logo set: icon, favicons, header wordmark and the 1200x630 social card.

The icon is a sun setting over Gulf water with a white exam path that ends in a check mark.
Run once (or after a color change): python3 tools/make_brand.py
"""
from PIL import Image, ImageDraw, ImageFont

NAVY, NAVY_D, SUN, SUN_L, TEAL, SAND = (20, 40, 75), (14, 29, 56), (74, 111, 165), (143, 170, 210), (29, 53, 97), (230, 235, 242)
GREEN, GREEN_D = (43, 182, 115), (26, 143, 85)
MONT = "/usr/share/fonts/truetype/google-fonts/ofl/montserrat/Montserrat[wght].ttf"
POP = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"


def mont(size, weight=800):
    f = ImageFont.truetype(MONT, size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


def icon(n=1024):
    s = n / 512
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, n - 1, n - 1], radius=int(112 * s), fill=NAVY)
    # sun
    d.ellipse([int(150 * s), int(118 * s), int(362 * s), int(330 * s)], fill=SUN)
    d.ellipse([int(196 * s), int(164 * s), int(316 * s), int(284 * s)], fill=SUN_L)
    # water
    d.rectangle([0, int(300 * s), n, n], fill=TEAL)
    # re-round the bottom corners after the water fill
    mask = Image.new("L", (n, n), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, n - 1, n - 1], radius=int(112 * s), fill=255)
    im.putalpha(mask)
    d = ImageDraw.Draw(im)
    # exam path: three steps rising to a check
    w = int(30 * s)
    pts = [(int(96 * s), int(452 * s)), (int(186 * s), int(452 * s)), (int(186 * s), int(392 * s)), (int(276 * s), int(392 * s))]
    d.line(pts, fill=GREEN, width=w, joint="curve")
    d.line([(int(262 * s), int(392 * s)), (int(316 * s), int(446 * s)), (int(430 * s), int(296 * s))], fill=GREEN, width=w, joint="curve")
    for x, y in [pts[0], (int(430 * s), int(296 * s))]:
        d.ellipse([x - w // 2, y - w // 2, x + w // 2, y + w // 2], fill=GREEN)
    return im


def wordmark(height=112, light=True):
    ic = icon(height * 4).resize((height, height), Image.LANCZOS)
    top, big = mont(int(height * 0.24), 700), mont(int(height * 0.40), 800)
    fg = (255, 255, 255) if light else NAVY
    sub = SAND if light else (85, 101, 126)
    tw = max(top.getlength("PASS YOUR"), big.getlength("FLORIDA") + 0, mont(int(height * 0.2), 700).getlength("CONTRACTOR EXAM"))
    W = int(height + height * 0.18 + tw + 8)
    im = Image.new("RGBA", (W, height), (0, 0, 0, 0))
    im.paste(ic, (0, 0), ic)
    d = ImageDraw.Draw(im)
    x = int(height * 1.18)
    d.text((x, int(height * 0.02)), "PASS YOUR", font=top, fill=sub)
    d.text((x, int(height * 0.22)), "FLORIDA", font=big, fill=GREEN if light else GREEN_D)
    d.text((x, int(height * 0.70)), "CONTRACTOR EXAM", font=mont(int(height * 0.2), 700), fill=fg)
    return im


def social():
    W, H = 1200, 630
    im = Image.new("RGB", (W, H), NAVY_D)
    d = ImageDraw.Draw(im)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(NAVY_D[i] + (20 * t if i == 2 else 10 * t)) for i in range(3)))
    
    [d.line([(x, 0), (x, H)], fill=(30, 52, 92)) for x in range(0, W, 48)]
    [d.line([(0, y), (W, y)], fill=(30, 52, 92)) for y in range(0, H, 48)]
    im.paste(wm := wordmark(150), (70, 110), wm)
    d.rectangle([0, 520, W, H], fill=GREEN_D)
    wm = wordmark(150)
    im.paste(wm, (70, 110), wm)
    d.text((72, 320), "Books, courses and Business and Finance", font=mont(40, 700), fill="white")
    d.text((72, 372), "prep for every Florida license exam", font=mont(40, 700), fill="white")
    d.text((72, 545), "passyourfloridacontractorexam.com", font=mont(30, 600), fill="white")
    return im


if __name__ == "__main__":
    big = icon(1024)
    big.resize((512, 512), Image.LANCZOS).save("assets/icon-512.png")
    big.resize((192, 192), Image.LANCZOS).save("assets/icon-192.png")
    big.resize((180, 180), Image.LANCZOS).convert("RGB").save("assets/apple-touch-icon.png")
    big.resize((48, 48), Image.LANCZOS).save("assets/favicon-48.png")
    big.resize((64, 64), Image.LANCZOS).save("assets/favicon.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
    wm = wordmark(112)
    wm.save("assets/logo-nav.png")
    wordmark(112, light=False).save("brand/logo-on-light.png")
    social().save("assets/logo.png", optimize=True)
    print("logo-nav", wm.size)
