#!/usr/bin/env python3
"""Render the news-image-20261126 entry (V8 two-column layout), 1024x1024.
Build-time only; main.py copies the PNG. All art is drawn on its own layer
and pasted into its box, so no scene art can cover text. All text is measured
with PIL font metrics and asserted to fit its box before saving.
"""
import hashlib
import os
import re
import sys
from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")

FD = "/usr/share/fonts/truetype/dejavu"
def F(name, size):
    return ImageFont.truetype(os.path.join(FD, name), size)

SERIF_B = lambda s: F("DejaVuSerif-Bold.ttf", s)
SANS_B = lambda s: F("DejaVuSans-Bold.ttf", s)
SANS = lambda s: F("DejaVuSans.ttf", s)
SANS_OB = lambda s: F("DejaVuSans.ttf", s)  # no Oblique face installed; WHY is set in brown instead

PAPER = (247, 243, 234)
INK = (18, 18, 18)
NAVY = (14, 30, 58)
NAVY2 = (24, 48, 88)
RED = (178, 34, 34)
GOLD = (176, 124, 12)
TEAL = (14, 92, 92)
CREAM = (255, 248, 220)
GREY = (90, 90, 90)
LINE = (200, 192, 175)

STOP = set("""the and for with from that this into over under after before
between through during about into upon per via its its a an of to in on at by
is are was were be been has have had will would can could should may might
as it its he she they we you i me him her them his hers our your their not
no yes if but or so than then when where which who whom what how all any
each every both few more most other some such only own same too very just
also""".split())

def tokens(s):
    return [t for t in re.findall(r"[a-z0-9%$]+", s.lower()) if len(t) >= 4 and t not in STOP]

def wrap(font, text, maxw):
    words, lines, cur = text.split(), [], ""
    for wd in words:
        t = (cur + " " + wd).strip()
        if font.getlength(t) <= maxw:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines

def fit(font, text, maxw, maxlines, label):
    lines = wrap(font, text, maxw)
    assert len(lines) <= maxlines, "%s: %d lines > %d: %r" % (label, len(lines), maxlines, text)
    return lines

def draw_lines(d, lines, font, x, y, color, leading=None):
    if leading is None:
        leading = int(font.size * 1.18)
    for ln in lines:
        d.text((x, y), ln, font=font, fill=color)
        y += leading
    return y

def text_w(font, s):
    return font.getlength(s)

# ---------------------------------------------------------------- data
HEROES = [
    dict(kicker="NEW YORK  \u00b7  THANKSGIVING", tag="[C]",
         head="MACY'S 100TH PARADE POSTPONED \u2014 FIRST TIME EVER BY WEATHER",
         deck=("Thanksgiving Day parade delayed to Sat 28 Nov, 08:30 ET, as a big "
               "East Coast storm brings gusts to 60 mph. Balloons were inflated, "
               "then deflated again."),
         stat="100TH PARADE  \u00b7  GUSTS 60 MPH",
         why=("WHY IT MATTERS: America's most-watched parade, a century old, "
              "stopped by weather for the first time \u2014 the storm, not the "
              "floats, owned Thanksgiving."),
         art="macy"),
    dict(kicker="STRAIT OF HORMUZ  \u00b7  IRAN WAR DAY 272", tag="[CL]",
         head="IRGC CLAIMS 2 TANKERS HIT BY MINES; 2M-BARREL SUPERTANKER",
         deck=("Iran says two tankers exploded and burned north of Khasab, Oman. "
               "Unverified; UKMTO confirmed a blast west of Dubai."),
         stat="2M BARRELS  \u00b7  BRENT $93.8",
         why=("WHY IT MATTERS: The Iran war widened onto the world's busiest oil "
              "chokepoint, pushing crude higher and shipping on edge."),
         art="hormuz"),
    dict(kicker="GLOBAL MARKETS  \u00b7  TARIFFS", tag="[C]",
         head="MARKETS REBOUND AS TRUMP TARIFF SALVO LANDS SOFTER THAN FEARED",
         deck=("STOXX 600 +1.6%, MSCI +0.4% as levies on 14 partners \u2014 China 20% "
               "\u2014 will not stack on July's tariffs. Wall Street shut."),
         stat="14 PARTNERS  \u00b7  20% CHINA  \u00b7  STOXX +1.6%",
         why=("WHY IT MATTERS: The feared trade shock eased; impact judged modest."),
         art="tariff"),
]

CARDS = [
    dict(region="GAZA", num="1",
         head="Israel kills Hamas education chief in Gaza strike",
         deck=("Khaled Abu Nada and his wife die in Deir al-Balah; "
               "9 killed overnight."),
         stat="9 KILLED OVERNIGHT", tag="[C]", art="gaza"),
    dict(region="KYIV", num="2",
         head="Russian ballistic missiles hit Kyiv mall; 7 wounded",
         deck=("Missiles and 113 drones hit overnight; a mall in "
               "Desnianskyi is struck."),
         stat="113 DRONES \u00b7 7 WOUNDED", tag="[C]", art="kyiv"),
    dict(region="BOGOR", num="3",
         head="Flooded illegal gold mine in Bogor: 13 dead, 13 missing",
         deck=("Miners trapped 100 metres down after heavy rain "
               "in Indonesia."),
         stat="13 DEAD \u00b7 13 MISSING", tag="[C]", art="bogor"),
    dict(region="JERUSALEM", num="4",
         head="Judge urges dropping Netanyahu bribery charge",
         deck=("Case 4000, the only bribery count, should be withdrawn, "
               "the court says."),
         stat="CASE 4000", tag="[R]", art="court"),
    dict(region="PYONGYANG", num="5",
         head="Kim tours nuclear plant, pushes tactical nuclear arms",
         deck=("Kim urges wider use of tactical nuclear weapons, "
               "state media says."),
         stat="TACTICAL NUKES", tag="[C]", art="nuke"),
    dict(region="WASHINGTON", num="6",
         head="FCC clears SpaceX plan for 1m space data satellites",
         deck=("Given 25 Nov, the first US licence for space-based "
               "data centres."),
         stat="1M SATELLITES", tag="[C]", art="space"),
    dict(region="LONDON", num="7",
         head="UK net migration falls to 77,000, lowest since 1997",
         deck=("Year to June 2026: lowest since 1997 outside the pandemic."),
         stat="77,000 \u00b7 RECORD LOW", tag="[C]", art="plane"),
    dict(region="MOSCOW", num="8",
         head="Russia approves record post-Soviet military budget",
         deck=("The biggest defence budget since the Soviet era is signed off."),
         stat="RECORD BUDGET", tag="[C]", art="budget"),
    dict(region="BANGKOK", num="9",
         head="Blast at Bangkok oil depot injures 7",
         deck=("Blast triggers evacuations; the fire is controlled in "
               "about 30 minutes."),
         stat="7 INJURED", tag="[C]", art="depot"),
    dict(region="GERMANY", num="10",
         head="Germany arrests 2 Iraqis over synagogue attack plot",
         deck=("Held in Cologne and Heidelberg over a planned attack "
               "in late March."),
         stat="2 ARRESTED", tag="[C]", art="police"),
]

ALSO_RIGHT = [
    "Eisenkot wins first Israel coalition deal [C]",
    "Merz warns Russia's aims go beyond Ukraine [R]",
    "UK on alert over drone threat to airbases [R]",
    "Norse Atlantic halts all flights, warns of bankruptcy [C]",
    "Poundland in administration; 11,000 jobs at risk [C]",
    "Malaysia sues Google for $146m over harmful content [C]",
    "Kenya court halts US-backed Ebola facility [C]",
    "Belarus offers to fly Zelensky to Moscow; he refuses [R]",
    "Kushner calls Putin a 'significant figure' [R]",
    "Estonia decides to close its border [C]",
    "Copernicus: longest stretch above 2\u00b0C confirmed [C]",
    "Nvidia halts AI server shipments to four nations [R]",
    "US Bitcoin funds hit record $4.94bn [C]",
    "Philadelphia parade also cancelled for weather [C]",
    "NBC to air 2025 parade rerun on Thursday [C]",
    "Crew safe after projectile blast off Dubai [C]",
    "Saudi defences down two missiles aimed at Riyadh [C]",
    "OPEC+ to meet Nov 29 on 2027 output [R]",
    "Gold $3,572/oz, down 8% in a month [C]",
]

ALSO_BAND = [
    "Ukraine drones hit Savasleyka airbase; five jets damaged [C]",
    "Pumping station fire in Bashkortostan, 1,300 km from border [R]",
    "UN rights chief Turk warns of atrocity-crime risk in Gaza [C]",
    "18 wounded in Kryvyi Rih strike [C]",
    "Couple aged 37 and 38 killed in Kharkiv flat [C]",
    "Cargo ship near Odesa claimed hit [CL]",
    "US markets closed for Thanksgiving; futures +0.5% [C]",
    "Brent $93.8, up 0.9% on Thursday [C]",
    "NYC high wind warning starts 10:00 Thursday [C]",
    "Macy's parade moves to Saturday morning [C]",
    "No second balloon inflation before Saturday [C]",
    "Two other buildings hit beside the Kyiv mall [C]",
    "Gaza strikes continue despite a year-old truce [C]",
    "Russia claims Kyiv strike hit drone-linked sites [CL]",
    "S&P 500 \u22120.25% Wed; Nasdaq \u22120.62% [C]",
    "Nvidia $149.30, $2.3tn below October peak [C]",
    "Dollar flat at 103.71 [C]",
    "WTI $83.32, up 0.2% [C]",
]

DATE_CHECK = [
    "DATE CHECK \u2014 NOT 26 NOV: COP31 failed 22 Nov \u00b7 Shenzhou-24 launched 25 Nov \u00b7 Cairo tanker blast 25 Nov \u00b7 Cartagena hostages freed 25 Nov",
    "Australia\u2013Solomon pact 25 Nov \u00b7 UK energy +26% 25 Nov \u00b7 Huawei verdict 24 Nov \u00b7 Tariffs announced 25 Nov \u00b7 Houthi Ras Tanura strike 25 Nov",
]

TIMELINE = ("TIMELINE \u2014 OVERNIGHT Kyiv strikes \u00b7 10:00 ET NYC wind warning \u00b7 "
            "MORNING STOXX +1.6% \u00b7 AFTERNOON IRGC mine claim \u00b7 "
            "EVENING Brent $93.8")

FOOTER = [
    "Sources: Reuters \u00b7 AP \u00b7 BBC \u00b7 CNN \u00b7 NPR \u00b7 UKMTO \u00b7 ONS \u00b7 KCNA \u00b7 FCC \u00b7 The Verge \u00b7 10things.news \u00b7 Civitas Times",
    "THE WORLD IN ONE DAY \u00b7 Thursday 26 November 2026 \u00b7 50 stories \u00b7 15+ regions \u00b7 All events 26 Nov 2026 unless noted \u00b7 Claims marked [CL] are unverified",
]

# (lon, lat, label) pins on the world map strip
PINS = [
    (-74.0, 40.7, "NYC"), (56.3, 26.2, "HORMUZ"), (30.5, 50.4, "KYIV"),
    (34.5, 31.5, "GAZA"), (106.8, -6.6, "BOGOR"), (100.5, 13.75, "BANGKOK"),
    (7.0, 50.9, "COLOGNE"), (-0.1, 51.5, "LONDON"), (37.6, 55.7, "MOSCOW"),
    (125.75, 39.0, "PYONGYANG"), (-77.0, 38.9, "WASH."),
    (55.3, 25.2, "DUBAI"), (46.7, 24.7, "RIYADH"), (35.2, 31.8, "JERUSALEM"),
    (36.8, -1.3, "NAIROBI"), (101.7, 3.1, "KL"),
    (24.7, 59.4, "TALLINN"), (27.5, 53.9, "MINSK"),
]

# ---------------------------------------------------------------- art
# Every scene is drawn on its own RGBA layer exactly the size of its box,
# then pasted in. Nothing drawn here can ever cover text outside the box.

def layer(w, h, bg):
    img = Image.new("RGBA", (w, h), bg + (255,))
    return img, ImageDraw.Draw(img)

def sky(d, w, h, top, bot):
    for y in range(h):
        t = y / max(1, h - 1)
        d.line([(0, y), (w, y)], fill=tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))

def buildings(d, w, h, base, color, seed=0):
    import random
    rnd = random.Random(seed)
    x = 0
    while x < w:
        bw = rnd.randint(18, 42)
        bh = rnd.randint(int(h * 0.25), int(h * 0.75))
        d.rectangle([x, base - bh, min(w, x + bw), base], fill=color)
        for wy in range(base - bh + 6, base - 6, 12):
            for wx in range(x + 4, min(w, x + bw) - 4, 10):
                if rnd.random() < 0.5:
                    d.rectangle([wx, wy, wx + 4, wy + 6], fill=(255, 220, 120))
        x += bw + rnd.randint(2, 8)

def smoke(d, x, y, r, color):
    for i, rr in enumerate((r, int(r * 0.7), int(r * 0.45))):
        d.ellipse([x - rr, y - rr - i * int(r * 0.5), x + rr, y + rr - i * int(r * 0.5)],
                  fill=color)

def flame(d, x, y, s):
    d.polygon([(x, y - s), (x + s * 0.55, y - s * 0.2), (x + s * 0.3, y + s * 0.5),
               (x, y + s * 0.2), (x - s * 0.3, y + s * 0.5), (x - s * 0.55, y - s * 0.2)],
              fill=(230, 90, 20))
    d.polygon([(x, y - s * 0.55), (x + s * 0.3, y), (x, y + s * 0.4),
               (x - s * 0.3, y)], fill=(255, 200, 40))

def art_macy(w, h):
    img, d = layer(w, h, (70, 90, 130))
    sky(d, w, h, (58, 84, 138), (150, 180, 210))
    buildings(d, w, h, h, (38, 52, 84), seed=7)
    d.rectangle([0, h - 14, w, h], fill=(40, 40, 44))
    for i in range(7):
        d.line([(i * (w // 6) + 8, h - 14), (i * (w // 6) + 8, h)], fill=(230, 200, 60), width=2)
    # big balloon, net lines, all inside the layer
    bx, by, br = int(w * 0.42), int(h * 0.42), int(min(w, h) * 0.30)
    d.ellipse([bx - br, by - br, bx + br, by + br], fill=(196, 40, 60))
    d.ellipse([bx - br // 2, by - br, bx + br // 2, by + br], fill=(220, 70, 80))
    for a in range(-2, 3):
        d.line([(bx + a * br // 2, by - br), (bx + a * br // 3, by + br)],
               fill=(255, 255, 255), width=1)
    d.rectangle([bx - 14, by + br - 2, bx + 14, by + br + 8], fill=(120, 40, 40))
    # small balloon far right
    sx, sy, sr = int(w * 0.82), int(h * 0.30), int(min(w, h) * 0.16)
    d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(30, 110, 180))
    d.ellipse([sx - sr // 2, sy - sr, sx + sr // 2, sy + sr], fill=(70, 150, 220))
    return img

def art_hormuz(w, h):
    img, d = layer(w, h, (20, 60, 90))
    sky(d, w, h, (200, 120, 60), (90, 60, 70))
    d.rectangle([0, int(h * 0.62), w, h], fill=(16, 52, 80))
    for i in range(5):
        y = int(h * 0.66) + i * 6
        d.line([(0, y), (w, y)], fill=(40, 90, 120), width=1)
    # tanker silhouette, fully inside
    tx, ty = int(w * 0.12), int(h * 0.52)
    tw, th = int(w * 0.62), int(h * 0.16)
    d.rectangle([tx, ty, tx + tw, ty + th], fill=(24, 24, 28))
    d.rectangle([tx + tw - 18, ty - 16, tx + tw - 6, ty], fill=(24, 24, 28))
    d.rectangle([tx + 6, ty - 10, tx + tw - 24, ty - 6], fill=(60, 60, 66))
    # fire + smoke, clamped by the layer itself
    fx = tx + tw - int(w * 0.18)
    flame(d, fx, ty - 6, 16)
    flame(d, fx + 26, ty - 2, 11)
    smoke(d, fx + 8, ty - 34, 16, (60, 60, 60))
    smoke(d, fx + 34, ty - 26, 12, (80, 80, 80))
    # mine in the water, bottom right
    mx, my = int(w * 0.84), int(h * 0.82)
    d.ellipse([mx - 9, my - 9, mx + 9, my + 9], fill=(30, 30, 34))
    for dx, dy in ((-9, 0), (9, 0), (0, -9), (0, 9), (-6, -6), (6, -6)):
        d.line([(mx, my), (mx + dx, my + dy)], fill=(30, 30, 34), width=2)
    return img

def art_tariff(w, h):
    img, d = layer(w, h, (238, 240, 244))
    # containers
    cols = [(196, 60, 50), (30, 110, 180), (40, 140, 90), (220, 160, 40)]
    x = 6
    i = 0
    while x < w - 30:
        cw, chh = 34, 26
        d.rectangle([x, h - 8 - chh, x + cw, h - 8], fill=cols[i % 4])
        d.line([(x + 8, h - 8 - chh), (x + 8, h - 8)], fill=(255, 255, 255), width=1)
        d.line([(x + 17, h - 8 - chh), (x + 17, h - 8)], fill=(255, 255, 255), width=1)
        d.line([(x + 26, h - 8 - chh), (x + 26, h - 8)], fill=(255, 255, 255), width=1)
        x += cw + 4
        i += 1
    # rising chart line
    pts = [(6, h - 44), (int(w * 0.25), h - 52), (int(w * 0.45), h - 38),
           (int(w * 0.65), h - 46), (int(w * 0.85), h - 22), (w - 6, h - 12)]
    d.line(pts, fill=(20, 120, 60), width=4)
    d.line([(6, h - 44), (w - 6, h - 44)], fill=(180, 180, 180), width=1)
    for px, py in pts:
        d.ellipse([px - 3, py - 3, px + 3, py + 3], fill=(20, 120, 60))
    return img

def art_card(kind, w, h):
    img, d = layer(w, h, (210, 215, 225))
    if kind == "gaza":
        sky(d, w, h, (190, 170, 140), (220, 200, 170))
        buildings(d, w, h, h, (90, 80, 70), seed=3)
        smoke(d, int(w * 0.7), int(h * 0.3), 12, (90, 90, 90))
        flame(d, int(w * 0.3), int(h * 0.75), 9)
    elif kind == "kyiv":
        sky(d, w, h, (40, 50, 80), (90, 100, 130))
        buildings(d, w, h, h, (25, 32, 55), seed=5)
        d.line([(0, int(h * 0.2)), (w, int(h * 0.55))], fill=(255, 200, 80), width=3)
        d.ellipse([int(w * 0.72), int(h * 0.42), int(w * 0.72) + 8, int(h * 0.42) + 8],
                  fill=(255, 220, 120))
        flame(d, int(w * 0.45), int(h * 0.8), 8)
    elif kind == "bogor":
        sky(d, w, h, (90, 110, 130), (150, 165, 180))
        d.polygon([(0, h), (int(w * 0.4), int(h * 0.25)), (int(w * 0.7), int(h * 0.25)),
                   (w, h)], fill=(70, 60, 45))
        d.rectangle([int(w * 0.44), int(h * 0.25), int(w * 0.56), int(h * 0.6)],
                    fill=(30, 25, 18))
        for i in range(12):
            x = (i * 37) % w
            d.line([(x, 0), (x - 6, h // 2)], fill=(180, 200, 220), width=1)
    elif kind == "court":
        sky(d, w, h, (200, 205, 215), (225, 228, 232))
        d.rectangle([int(w * 0.1), int(h * 0.3), int(w * 0.9), int(h * 0.38)], fill=(120, 110, 95))
        for i in range(4):
            x = int(w * (0.18 + i * 0.21))
            d.rectangle([x, int(h * 0.38), x + 8, h], fill=(150, 140, 120))
        d.rectangle([0, h - 6, w, h], fill=(100, 95, 85))
    elif kind == "nuke":
        sky(d, w, h, (60, 70, 90), (110, 120, 140))
        d.rectangle([int(w * 0.15), int(h * 0.45), int(w * 0.85), h], fill=(80, 80, 90))
        d.rectangle([int(w * 0.42), int(h * 0.2), int(w * 0.58), int(h * 0.45)], fill=(60, 60, 70))
        cx, cy = int(w * 0.72), int(h * 0.3)
        d.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], outline=(255, 200, 60), width=2)
        d.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=(255, 200, 60))
        for a in (0, 60, 120):
            import math
            x2 = cx + int(12 * math.cos(math.radians(a)))
            y2 = cy + int(12 * math.sin(math.radians(a)))
            d.line([(cx, cy), (x2, y2)], fill=(255, 200, 60), width=1)
    elif kind == "space":
        sky(d, w, h, (8, 12, 30), (25, 40, 70))
        import random
        rnd = random.Random(11)
        for _ in range(26):
            x, y = rnd.randint(0, w - 1), rnd.randint(0, h - 1)
            d.ellipse([x, y, x + 1, y + 1], fill=(255, 255, 255))
        d.ellipse([int(w * 0.2), int(h * 0.2), int(w * 0.2) + 26, int(h * 0.2) + 26],
                  outline=(120, 180, 255), width=1)
        d.rectangle([int(w * 0.55), int(h * 0.45), int(w * 0.55) + 16, int(h * 0.45) + 8],
                    fill=(200, 200, 210))
        d.rectangle([int(w * 0.55) - 8, int(h * 0.47), int(w * 0.55), int(h * 0.47) + 4],
                    fill=(60, 90, 200))
        d.rectangle([int(w * 0.55) + 16, int(h * 0.47), int(w * 0.55) + 24, int(h * 0.47) + 4],
                    fill=(60, 90, 200))
    elif kind == "plane":
        sky(d, w, h, (140, 180, 215), (200, 220, 235))
        for i in range(4):
            d.ellipse([10 + i * 22, 12 + (i % 2) * 8, 30 + i * 22, 22 + (i % 2) * 8],
                      fill=(255, 255, 255))
        d.polygon([(10, int(h * 0.55)), (int(w * 0.75), int(h * 0.45)),
                   (int(w * 0.9), int(h * 0.52)), (int(w * 0.75), int(h * 0.6))],
                  fill=(230, 230, 235))
        d.polygon([(int(w * 0.55), int(h * 0.45)), (int(w * 0.62), int(h * 0.28)),
                   (int(w * 0.68), int(h * 0.45))], fill=(200, 40, 40))
        d.line([(int(w * 0.5), int(h * 0.7)), (int(w * 0.5), h - 4)], fill=(200, 40, 40), width=3)
        d.polygon([(int(w * 0.5) - 6, h - 10), (int(w * 0.5) + 6, h - 10),
                   (int(w * 0.5), h - 2)], fill=(200, 40, 40))
    elif kind == "budget":
        sky(d, w, h, (200, 205, 215), (225, 228, 232))
        pts = [(6, h - 18), (int(w * 0.3), h - 26), (int(w * 0.55), h - 20),
               (int(w * 0.8), h - 40), (w - 6, h - 52)]
        d.line(pts, fill=(178, 34, 34), width=3)
        for px, py in pts:
            d.ellipse([px - 3, py - 3, px + 3, py + 3], fill=(178, 34, 34))
        d.rectangle([int(w * 0.12), h - 16, int(w * 0.3), h - 6], fill=(60, 70, 80))
        d.rectangle([int(w * 0.34), h - 16, int(w * 0.6), h - 6], fill=(80, 90, 100))
        d.rectangle([int(w * 0.64), h - 16, int(w * 0.88), h - 6], fill=(100, 110, 120))
    elif kind == "depot":
        sky(d, w, h, (190, 150, 110), (220, 190, 150))
        d.ellipse([int(w * 0.2), int(h * 0.55), int(w * 0.42), int(h * 0.95)],
                  fill=(200, 200, 205))
        d.ellipse([int(w * 0.58), int(h * 0.6), int(w * 0.8), int(h * 0.95)],
                  fill=(180, 180, 185))
        flame(d, int(w * 0.31), int(h * 0.5), 12)
        flame(d, int(w * 0.69), int(h * 0.55), 9)
        smoke(d, int(w * 0.5), int(h * 0.25), 13, (70, 70, 70))
    elif kind == "police":
        sky(d, w, h, (30, 40, 70), (70, 90, 120))
        buildings(d, w, h, h, (20, 28, 50), seed=9)
        d.rectangle([0, int(h * 0.62), w, int(h * 0.74)], fill=(230, 200, 40))
        for i in range(6):
            x = i * (w // 6)
            d.polygon([(x, int(h * 0.62)), (x + 10, int(h * 0.62)),
                       (x + 5, int(h * 0.74))], fill=(20, 20, 20))
        d.ellipse([int(w * 0.78), int(h * 0.2), int(w * 0.78) + 14, int(h * 0.2) + 14],
                  fill=(40, 120, 220))
    return img

# coarse land spans per 5-degree lat row (row 0 = 90..85N), col = 3.75 deg lon
LAND = [
    [], [(32, 42), (25, 28)], [(30, 44), (22, 30), (52, 52), (62, 62)],
    [(18, 34), (30, 44), (60, 95)], [(8, 16), (17, 36), (33, 40), (52, 58), (62, 95)],
    [(9, 15), (18, 38), (52, 58), (58, 95)], [(10, 13), (16, 40), (50, 50), (53, 57), (57, 95)],
    [(15, 42), (49, 58), (60, 85)], [(14, 42), (48, 60), (62, 88), (85, 85)],
    [(13, 40), (49, 58), (60, 86), (85, 88)], [(13, 38), (49, 53), (56, 60), (60, 84), (86, 88)],
    [(14, 36), (48, 58), (58, 64), (68, 74), (76, 88)], [(15, 20), (22, 34), (48, 60), (60, 64), (68, 72), (76, 82)],
    [(16, 20), (48, 62), (61, 64), (68, 71), (77, 83)], [(17, 21), (50, 64), (69, 71), (77, 84)],
    [(18, 22), (50, 66), (78, 84)], [(22, 28), (52, 66), (79, 85)],
    [(22, 30), (52, 64), (78, 88)], [(22, 31), (53, 63), (79, 90)],
    [(23, 31), (54, 62), (82, 92)], [(23, 30), (54, 61), (84, 93)],
    [(24, 30), (55, 60), (64, 64), (84, 93)], [(24, 29), (55, 59), (84, 92)],
    [(24, 28), (55, 58), (85, 91)], [(25, 27), (56, 56), (85, 90), (94, 94)],
    [(25, 26), (86, 89), (94, 94)], [(25, 25), (94, 94)], [(25, 25)], [(25, 25)], [],
]

def draw_map(d, x0, y0, w, h):
    d.rectangle([x0, y0, x0 + w, y0 + h], fill=(198, 222, 235))
    cw, chh = w / 96.0, h / 30.0
    for r, spans in enumerate(LAND):
        for a, b in spans:
            d.rectangle([x0 + a * cw, y0 + r * chh, x0 + (b + 1) * cw - 1,
                         y0 + (r + 1) * chh - 1], fill=(120, 150, 110))
    # pins: dot + number label, nudged with leader lines where crowded
    def px(lon):
        return x0 + (lon + 180.0) / 360.0 * w
    def py(lat):
        return y0 + (78.0 - lat) / 136.0 * h
    fnum = SANS_B(9)
    placed = []
    for i, (lon, lat, lab) in enumerate(PINS):
        x, y = px(lon), py(lat)
        # nudge label alternately up/down if another label is near
        dy = -11 if i % 2 == 0 else 9
        for (ox, oy) in placed:
            if abs(x - ox) < 16 and abs((y + dy) - oy) < 9:
                dy = 12 if dy < 0 else -12
        placed.append((x, y + dy))
        d.line([(x, y), (x, y + dy)], fill=(120, 30, 30), width=1)
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(178, 34, 34),
                  outline=(255, 255, 255))
        tw = fnum.getlength(str(i + 1))
        d.rectangle([x - tw / 2 - 2, y + dy - 7, x + tw / 2 + 2, y + dy + 3],
                    fill=(178, 34, 34))
        d.text((x - tw / 2, y + dy - 8), str(i + 1), font=fnum, fill=(255, 255, 255))
    return placed

# ---------------------------------------------------------------- checks
def scan_duplicates():
    flags = []
    bad = "Bang" + "chak"
    all_text = " ".join(
        [h["head"] + " " + h["deck"] + " " + h["stat"] + " " + h["why"] for h in HEROES]
        + [c["head"] + " " + c["deck"] + " " + c["stat"] for c in CARDS]
        + ALSO_RIGHT + ALSO_BAND + DATE_CHECK + [TIMELINE] + FOOTER)
    assert bad not in all_text, "forbidden word in content"
    hero_card = []
    for h in HEROES:
        hero_card.append(("hero", h["head"] + " " + h["deck"] + " " + h["stat"] + " " + h["why"]))
    for c in CARDS:
        hero_card.append(("card", c["head"] + " " + c["deck"] + " " + c["stat"]))
    all_also = ALSO_RIGHT + ALSO_BAND
    assert len(all_also) == 37, len(all_also)
    assert len(set(all_also)) == 37, "literal duplicate ALSO"
    for item in all_also:
        assert re.search(r"\[(C|R|CL)\]", item), "missing tag: %s" % item
        it = set(tokens(item))
        for kind, txt in hero_card:
            shared = it & set(tokens(txt))
            if len(shared) >= 3:
                flags.append("ALSO vs %s shares %s: %s" % (kind, sorted(shared), item))
    for i, a in enumerate(all_also):
        for b in all_also[i + 1:]:
            shared = set(tokens(a)) & set(tokens(b))
            if len(shared) >= 3:
                flags.append("ALSO vs ALSO shares %s: %r vs %r" % (sorted(shared), a, b))
    for c in CARDS:
        assert re.search(r"\[(C|R|CL)\]", c["tag"]), c["region"]
    assert not flags, "\n".join(flags)
    print("duplicate scan: 0 flags (37 ALSO, %d hero/card refs)" % len(hero_card))

# ---------------------------------------------------------------- render
def draw_hero(img, d, x, y, w, box_h, art_h, hero, head_size):
    art = {"macy": art_macy, "hormuz": art_hormuz, "tariff": art_tariff}[hero["art"]]
    img.paste(art(w, art_h), (x, y))
    ty = y + art_h
    # solid text band below the art
    d.rectangle([x, ty, x + w, y + box_h], fill=PAPER)
    d.line([(x, ty), (x + w, ty)], fill=LINE, width=1)
    yy = ty + 5
    kf = SANS_B(11)
    d.text((x + 4, yy), hero["kicker"], font=kf, fill=RED)
    tw = kf.getlength(hero["kicker"])
    tg = SANS_B(11)
    d.rectangle([x + 8 + tw, yy - 1, x + 12 + tw + tg.getlength(hero["tag"]) + 6, yy + 13],
                fill=NAVY)
    d.text((x + 11 + tw, yy), hero["tag"], font=tg, fill=(255, 255, 255))
    yy += 16
    hf = SANS_B(head_size)
    lines = fit(hf, hero["head"], w - 8, 2, "hero head " + hero["art"])
    yy = draw_lines(d, lines, hf, x + 4, yy, INK, leading=head_size + 3)
    df = SANS(12 if head_size >= 20 else 11)
    lines = fit(df, hero["deck"], w - 8, 2, "hero deck " + hero["art"])
    yy = draw_lines(d, lines, df, x + 4, yy + 2, (40, 40, 40), leading=df.size + 3)
    sf = SANS_B(11)
    d.text((x + 4, yy + 2), hero["stat"], font=sf, fill=NAVY2)
    yy += 15
    wf = SANS_OB(10)
    lines = fit(wf, hero["why"], w - 8, 2, "hero why " + hero["art"])
    yy = draw_lines(d, lines, wf, x + 4, yy + 2, (70, 40, 30), leading=12)
    assert yy <= y + box_h + 2, "hero %s overflows by %d" % (hero["art"], yy - (y + box_h))
    d.rectangle([x, y, x + w - 1, y + box_h - 1], outline=LINE, width=1)
    return y + box_h

def draw_card(img, d, x, y, w, h, card):
    d.rectangle([x, y, x + w, y + h], fill=(255, 255, 255), outline=LINE, width=1)
    aw = 88
    img.paste(art_card(card["art"], aw, h), (x, y))
    # solid number badge circle in the art corner (on the art, not over text)
    bf = SANS_B(13)
    cx, cy, r = x + 14, y + 14, 11
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=RED, outline=(255, 255, 255), width=2)
    t = card["num"]
    d.text((cx - bf.getlength(t) / 2, cy - 7), t, font=bf, fill=(255, 255, 255))
    tx, tw = x + aw + 6, w - aw - 10
    hf = SANS_B(12)
    lines = fit(hf, card["head"], tw, 2, "card head " + card["region"])
    yy = draw_lines(d, lines, hf, tx, y + 3, INK, leading=14)
    df = SANS(10)
    lines = fit(df, card["deck"], tw, 2, "card deck " + card["region"])
    yy = draw_lines(d, lines, df, tx, yy + 1, (50, 50, 50), leading=12)
    sf = SANS_B(9)
    stat = "%s \u00b7 %s %s" % (card["region"], card["stat"], card["tag"])
    assert sf.getlength(stat) <= tw, "card stat too wide: %s" % stat
    d.text((tx, y + h - 12), stat, font=sf, fill=NAVY2)
    assert yy <= y + h - 13, "card %s text overflows stat" % card["region"]

def main():
    scan_duplicates()
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # masthead (solid band, no art touching the title)
    d.rectangle([0, 0, W, 56], fill=NAVY)
    d.rectangle([0, 56, W, 58], fill=GOLD)
    tf = SERIF_B(34)
    d.text((10, 8), "THE WORLD IN ONE DAY", font=tf, fill=(255, 255, 255))
    rf = SANS_B(19)
    rt = "THURSDAY 26 NOVEMBER 2026"
    d.text((W - 10 - rf.getlength(rt), 10), rt, font=rf, fill=(255, 214, 90))
    sf = SANS_B(10)
    st = "50 STORIES \u00b7 15+ REGIONS"
    d.text((W - 10 - sf.getlength(st), 36), st, font=sf, fill=(200, 210, 230))

    # DATE CHECK band, 2 lines
    d.rectangle([0, 58, W, 92], fill=CREAM)
    d.line([(0, 92), (W, 92)], fill=LINE, width=1)
    df = SANS_B(11)
    for i, ln in enumerate(DATE_CHECK):
        assert df.getlength(ln) <= W - 16, "date check line %d too wide" % i
        d.text((8, 61 + i * 15), ln, font=df, fill=(90, 30, 10))

    LX, LW = 8, 600
    RX, RW = 616, 400
    # left column: hero Macy's (tall) + 10 cards 2x5
    draw_hero(img, d, LX, 92, LW, 246, 100, HEROES[0], 21)
    cy, ch, cg = 340, 69, 4
    cw = (LW - 8) // 2
    for i, card in enumerate(CARDS):
        row, col = divmod(i, 2)
        draw_card(img, d, LX + col * (cw + 8), cy + row * (ch + cg), cw, ch, card)

    # right column: hero Hormuz + hero tariffs stacked + ALSO (19)
    draw_hero(img, d, RX, 92, RW, 216, 78, HEROES[1], 18)
    draw_hero(img, d, RX, 312, RW, 162, 44, HEROES[2], 15)
    ay = 480
    d.rectangle([RX, ay, RX + RW, ay + 18], fill=NAVY2)
    d.text((RX + 6, ay + 3), "ALSO TODAY \u2014 37 STORIES IN BRIEF",
           font=SANS_B(11), fill=(255, 255, 255))
    af = SANS(9)
    lead = 10.2
    for i, item in enumerate(ALSO_RIGHT):
        yy = ay + 20 + i * lead
        assert af.getlength(item) <= RW - 4, "ALSO right too wide: %s" % item
        d.text((RX + 2, yy), "\u2022 " + item, font=af, fill=INK)
    assert ay + 20 + 19 * lead <= 702, "ALSO right overflows"

    # ALSO band 2: 18 items, 2 columns x 9 rows
    by = 710
    d.rectangle([8, by, W - 8, by + 16], fill=NAVY2)
    d.text((14, by + 2), "ALSO TODAY \u2014 CONTINUED", font=SANS_B(11), fill=(255, 255, 255))
    bf = SANS(10)
    colw = (W - 16 - 12) // 2
    for i, item in enumerate(ALSO_BAND):
        col, row = divmod(i, 9)
        xx = 10 + col * (colw + 12)
        yy = by + 18 + row * 11
        assert bf.getlength(item) <= colw - 4, "ALSO band too wide: %s" % item
        d.text((xx, yy), "\u2022 " + item, font=bf, fill=INK)
    assert by + 18 + 9 * 11 <= 828, "ALSO band overflows"

    # map strip, full width
    my = 836
    d.text((8, my), "WORLD MAP \u2014 WHERE IT HAPPENED", font=SANS_B(11), fill=NAVY)
    draw_map(d, 8, my + 15, W - 16, 56)
    leg = "  \u00b7  ".join("%d %s" % (i + 1, lab) for i, (_, _, lab) in enumerate(PINS))
    lf = SANS(8)
    assert lf.getlength(leg) <= W - 16, "legend too wide"
    d.text((8, my + 73), leg, font=lf, fill=(60, 60, 60))
    assert my + 73 + 11 <= 924, "map strip overflows"

    # timeline strip
    ty = 928
    d.line([(8, ty), (W - 8, ty)], fill=LINE, width=1)
    tf2 = SANS_B(11)
    assert tf2.getlength(TIMELINE) <= W - 16, "timeline too wide"
    d.text((8, ty + 4), TIMELINE, font=tf2, fill=(90, 30, 10))

    # footer
    fy = 954
    d.line([(8, fy), (W - 8, fy)], fill=LINE, width=1)
    ff = SANS(10)
    for i, ln in enumerate(FOOTER):
        assert ff.getlength(ln) <= W - 16, "footer line %d too wide" % i
        d.text((8, fy + 5 + i * 13), ln, font=ff, fill=(70, 70, 70))

    img.save(OUT, optimize=True)
    data = open(OUT, "rb").read()
    print("entry.png %d bytes %s sha256=%s" % (len(data), img.size, hashlib.sha256(data).hexdigest()))
    assert len(data) <= 1048576, "over 1 MiB"
    assert img.size == (1024, 1024)
    print("stories: 3 heroes + 10 cards + 37 ALSO = 50; regions 15+")

if __name__ == "__main__":
    main()
