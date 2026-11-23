#!/usr/bin/env python3
"""One-page world news image for Monday, 23 November 2026.

The program draws the whole page itself: polygons are scanline-rasterised with
vertical supersampling, text is set from embedded DejaVu glyph outlines, and the
PNG is assembled and deflated with the standard library. No network, no clock,
no randomness, so two runs write identical bytes.
"""
import json
import math
import os
import struct
import zlib

W = H = 1024
SUB = 4

# ---------------------------------------------------------------- palette
PAPER = (243, 238, 227)
INK = (20, 22, 27)
MUTED = (92, 90, 82)
RED = (188, 47, 40)
DEEP = (22, 48, 68)
SEA = (31, 74, 101)
SAND = (214, 197, 168)
WHITE = (250, 247, 239)
GOLD = (203, 158, 71)
STEEL = (126, 137, 144)

buf = bytearray(bytes(PAPER) * (W * H))


def rgb(c):
    return c


def fill_rect(x0, y0, x1, y1, c, alpha=1.0):
    x0 = max(0, int(round(x0))); x1 = min(W, int(round(x1)))
    y0 = max(0, int(round(y0))); y1 = min(H, int(round(y1)))
    if x1 <= x0 or y1 <= y0:
        return
    if alpha >= 0.999:
        row = bytes(c) * (x1 - x0)
        for y in range(y0, y1):
            i = (y * W + x0) * 3
            buf[i:i + (x1 - x0) * 3] = row
        return
    r, g, b = c
    for y in range(y0, y1):
        i = (y * W + x0) * 3
        for x in range(x0, x1):
            buf[i] = int(buf[i] + (r - buf[i]) * alpha)
            buf[i + 1] = int(buf[i + 1] + (g - buf[i + 1]) * alpha)
            buf[i + 2] = int(buf[i + 2] + (b - buf[i + 2]) * alpha)
            i += 3


def fill_poly(contours, c, alpha=1.0):
    """Fill contours with the nonzero winding rule and 4x vertical AA."""
    edges = []
    ymin = 1e18
    ymax = -1e18
    for pts in contours:
        n = len(pts)
        if n < 3:
            continue
        for i in range(n):
            x0, y0 = pts[i]
            x1, y1 = pts[(i + 1) % n]
            if y0 == y1:
                continue
            if y0 < y1:
                edges.append((y0, y1, x0, (x1 - x0) / (y1 - y0), 1))
            else:
                edges.append((y1, y0, x1, (x0 - x1) / (y0 - y1), -1))
            if y0 < ymin: ymin = y0
            if y0 > ymax: ymax = y0
            if y1 < ymin: ymin = y1
            if y1 > ymax: ymax = y1
    if not edges:
        return
    row0 = max(0, int(ymin))
    row1 = min(H - 1, int(ymax))
    if row1 < row0:
        return
    # horizontal extent, for a compact coverage row
    xs_all = [e[2] for e in edges]
    bx0 = max(0, int(min(xs_all)) - 1)
    bx1 = min(W, int(max(xs_all)) + 2)
    if bx1 <= bx0:
        return
    span = bx1 - bx0
    r, g, b = c
    for py in range(row0, row1 + 1):
        cov = None
        for s in range(SUB):
            y = py + (s + 0.5) / SUB
            cuts = []
            for e in edges:
                if e[0] <= y < e[1]:
                    cuts.append((e[2] + (y - e[0]) * e[3], e[4]))
            if not cuts:
                continue
            cuts.sort()
            wind = 0
            start = 0.0
            spans = []
            for xx, d in cuts:
                if wind == 0:
                    start = xx
                wind += d
                if wind == 0:
                    spans.append((start, xx))
            if not spans:
                continue
            if cov is None:
                cov = [0.0] * span
            wgt = 1.0 / SUB
            for xa, xb in spans:
                if xb <= xa:
                    continue
                xa = max(xa, bx0); xb = min(xb, bx1)
                if xb <= xa:
                    continue
                ia = int(xa); ib = int(xb)
                if ia == ib:
                    cov[ia - bx0] += (xb - xa) * wgt
                    continue
                cov[ia - bx0] += (ia + 1 - xa) * wgt
                for ix in range(ia + 1, ib):
                    cov[ix - bx0] += wgt
                if ib < bx1:
                    cov[ib - bx0] += (xb - ib) * wgt
        if cov is None:
            continue
        base = py * W
        for k, a in enumerate(cov):
            if a <= 0.001:
                continue
            if a > 0.999:
                a = 1.0
            i = (base + bx0 + k) * 3
            if a >= 1.0:
                buf[i] = r; buf[i + 1] = g; buf[i + 2] = b
            else:
                buf[i] = int(buf[i] + (r - buf[i]) * a)
                buf[i + 1] = int(buf[i + 1] + (g - buf[i + 1]) * a)
                buf[i + 2] = int(buf[i + 2] + (b - buf[i + 2]) * a)


def disc(cx, cy, r, c, alpha=1.0):
    pts = []
    n = 48
    for i in range(n):
        a = 2 * 3.141592653589793 * i / n
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    fill_poly([pts], c, alpha)


def ring(cx, cy, r, width, c, alpha=1.0):
    n = 64
    outer = []
    inner = []
    for i in range(n):
        a = 2 * 3.141592653589793 * i / n
        ca = math.cos(a); sa = math.sin(a)
        outer.append((cx + r * ca, cy + r * sa))
        inner.append((cx + (r - width) * ca, cy + (r - width) * sa))
    # reverse inner so the contours form a ring under nonzero winding
    fill_poly([outer, inner[::-1]], c, alpha)


def thick_line(x0, y0, x1, y1, w, c, alpha=1.0):
    dx = x1 - x0; dy = y1 - y0
    d = (dx * dx + dy * dy) ** 0.5
    if d < 0.001:
        disc(x0, y0, w / 2, c, alpha)
        return
    nx = -dy / d * (w / 2); ny = dx / d * (w / 2)
    fill_poly([[(x0 + nx, y0 + ny), (x1 + nx, y1 + ny), (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)]], c, alpha)


def dashed_curve(pts, w, c, alpha=1.0, dash=9, gap=7):
    # pts is a polyline; draw alternating pieces
    on = True
    left = dash
    for i in range(len(pts) - 1):
        x0, y0 = pts[i]; x1, y1 = pts[i + 1]
        seg = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
        t = 0.0
        while t < seg - 0.001:
            step = min(left, seg - t)
            u0 = t / seg; u1 = (t + step) / seg
            if on:
                thick_line(x0 + (x1 - x0) * u0, y0 + (y1 - y0) * u0,
                           x0 + (x1 - x0) * u1, y0 + (y1 - y0) * u1, w, c, alpha)
            t += step
            left -= step
            if left <= 0.001:
                on = not on
                left = dash if on else gap


# ---------------------------------------------------------------- type
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts.json'), 'r', encoding='utf-8') as f:
    FONTS = json.load(f)


def text_width(s, font, size, tracking=0.0):
    f = FONTS[font]
    return sum((f['glyphs'].get(ch, f['glyphs']['?'])['a']) for ch in s) * size / 1000.0 + tracking * max(0, len(s) - 1)


def text(x, y, s, font, size, c, tracking=0.0, align='left', alpha=1.0):
    f = FONTS[font]
    total = text_width(s, font, size, tracking)
    if align == 'center':
        x -= total / 2.0
    elif align == 'right':
        x -= total
    scale = size / 1000.0
    for ch in s:
        g = f['glyphs'].get(ch, f['glyphs']['?'])
        # All contours of a glyph must be filled together.  Filling the inner
        # contour on its own turns the counters of O, A, R, P and B into ink.
        contours = []
        for contour in g['c']:
            contours.append([(x + px * scale, y + py * scale) for px, py in contour])
        if contours:
            fill_poly(contours, c, alpha)
        x += g['a'] * scale + tracking


def wrap(s, font, size, maxw, tracking=0.0):
    words = s.split()
    lines = []
    cur = ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if text_width(t, font, size, tracking) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def paragraph(x, y, s, font, size, maxw, lh, c, tracking=0.0):
    for line in wrap(s, font, size, maxw, tracking):
        text(x, y, line, font, size, c, tracking)
        y += lh


# ---------------------------------------------------------------- page
fill_rect(0, 0, W, H, PAPER)

# top rail
fill_rect(0, 0, W, 54, INK)
text(36, 34, 'WORLD NEWS  ·  MONDAY 23 NOVEMBER 2026', 'sansb', 17, WHITE, 0.5)
text(988, 34, 'ONE-PAGE EDITION', 'sans', 13, (201, 194, 178), 0.7, 'right')

# masthead
text(34, 160, 'THE WORLD', 'serif', 91, INK, -1.5)
fill_rect(690, 74, 988, 170, RED)
text(839, 103, 'MONDAY', 'sansb', 16, WHITE, 1.7, 'center')
text(839, 150, '23 NOV 2026', 'sansb', 40, WHITE, 0.3, 'center')

fill_rect(36, 181, 988, 185, INK)
fill_rect(36, 188, 988, 190, RED)
text(36, 214, "THE DAY'S NEWS IN ONE PAGE", 'sansb', 13.5, RED, 1.3)
text(988, 214, 'SIX STORIES  ·  WORLDWIDE', 'sans', 13.5, MUTED, 0.7, 'right')

# ---------------------------------------------------------------- lead
LX0, LX1 = 36, 604
text(LX0, 240, 'LEAD STORY  ·  GULF', 'sansb', 14, RED, 1.2)
text(LX0 - 2, 294, 'IRAN CLAIMS', 'serif', 54, INK, -0.8)
text(LX0 - 2, 348, 'STRIKES ON US', 'serif', 54, INK, -0.8)
text(LX0 - 2, 402, 'BASES IN BAHRAIN', 'serif', 54, INK, -0.8)
paragraph(LX0, 438, "Trump seeks a \u2018permanent\u2019 deal as attacks on Hormuz shipping escalate and oil holds near $92.",
          'sans', 19, 548, 24, (44, 44, 41))

# map panel
MX0, MY0, MX1, MY1 = 36, 492, 604, 744
fill_rect(MX0, MY0, MX1, MY1, SEA)
# Iran (north)
fill_poly([[(36, 492), (604, 492), (604, 566), (540, 578), (470, 593), (400, 584), (330, 572), (230, 563), (130, 553), (36, 544)]], (196, 174, 137))
# Arabia (south-west)
fill_poly([[(36, 744), (36, 620), (110, 610), (210, 620), (300, 640), (360, 670), (378, 700), (360, 744)]], (196, 174, 137))
# Musandam / Oman (south-east)
fill_poly([[(430, 744), (452, 680), (474, 656), (510, 650), (548, 662), (580, 684), (604, 702), (604, 744)]], (196, 174, 137))
# water highlights
for i in range(4):
    y = 628 + i * 16
    thick_line(404, y, 492 + i * 8, y, 1.2, (58, 108, 135), 0.55)
# Bahrain
disc(318, 614, 5.5, RED)
ring(318, 614, 13, 1.6, RED, 0.75)
ring(318, 614, 22, 1.2, RED, 0.45)
text(344, 619, 'BAHRAIN', 'sansb', 14, WHITE, 0.4)
text(352, 540, 'IRAN', 'sansb', 21, INK, 0.9)
text(66, 696, 'SAUDI ARABIA', 'sans', 12, INK, 0.4)
text(500, 696, 'OMAN', 'sans', 12, INK, 0.4)
# strike arcs from Iran to Bahrain
for k, off in enumerate((0, 14, 28)):
    pts = []
    for i in range(21):
        t = i / 20.0
        x = 410 - 88 * t
        y = 566 + 42 * t - 20 * t * (1 - t) * 2 + off * t * 0.35
        pts.append((x, y))
    dashed_curve(pts, 2.2, (232, 92, 62), 0.95, 8, 7)
# arrow head
fill_poly([[(318, 606), (334, 614), (318, 622)]], (232, 92, 62))
# tankers, one burning
for tx, ty, s in ((545, 610, 1.0), (576, 666, 0.8)):
    fill_poly([[(tx - 20 * s, ty), (tx + 20 * s, ty), (tx + 14 * s, ty + 8 * s), (tx - 14 * s, ty + 8 * s)]], INK)
    fill_rect(tx - 7 * s, ty - 7 * s, tx + 3 * s, ty, WHITE)
    thick_line(tx + 8 * s, ty - 12 * s, tx + 8 * s, ty, 1.4, INK)
# strait label
text(412, 642, 'STRAIT OF', 'sansb', 12, (225, 232, 236), 0.4)
text(412, 656, 'HORMUZ', 'sansb', 12, (225, 232, 236), 0.4)
# caption bar
fill_rect(MX0, MY1 - 30, MX1, MY1, INK)
text(MX0 + 14, MY1 - 7, '114', 'sansb', 27, WHITE, 0.0)
text(MX0 + 70, MY1 - 8, 'CROSSINGS IN 3 DAYS', 'sansb', 12.5, WHITE, 0.4)

# ---------------------------------------------------------------- right column
RX0, RX1 = 628, 988
# COP31
text(RX0, 240, 'CLIMATE  ·  ANTALYA', 'sansb', 13.5, RED, 1.0)
text(RX0 - 1, 288, 'COP31 ENDS', 'serif', 38, INK, -0.5)
text(RX0 - 1, 328, 'WITH NO DEAL', 'serif', 38, INK, -0.5)
paragraph(RX0, 358, 'No deal on fossil fuels as EU delegates walk out.',
          'sans', 16, 352, 20, (52, 51, 47))
# globe + failure mark
gx, gy = RX0 + 27, 424
disc(gx, gy, 24, DEEP)
fill_poly([[(gx - 18, gy - 9), (gx - 8, gy - 15), (gx - 2, gy - 4), (gx - 12, gy + 2)]], (94, 154, 111))
fill_poly([[(gx + 4, gy + 3), (gx + 17, gy - 2), (gx + 20, gy + 10), (gx + 8, gy + 16)]], (94, 154, 111))
thick_line(gx - 22, gy, gx + 22, gy, 1.0, (143, 190, 205), 0.7)
thick_line(gx, gy - 23, gx, gy + 23, 1.0, (143, 190, 205), 0.5)
thick_line(gx - 15, gy + 18, gx + 17, gy - 18, 5, RED)
text(RX0 + 64, 414, 'LONGEST COP', 'sansb', 11.5, MUTED, 0.6)
text(RX0 + 64, 430, 'ON RECORD', 'sansb', 11.5, MUTED, 0.6)
text(RX0 + 64, 446, '48 HOURS OF OVERTIME', 'sans', 10.5, MUTED, 0.3)

fill_rect(RX0, 474, RX1, 476, (190, 182, 166))

# Ukraine / Libya
text(RX0, 502, 'EUROPE  ·  AFRICA', 'sansb', 13.5, RED, 1.0)
text(RX0 - 1, 550, 'DRONES HIT', 'serif', 38, INK, -0.5)
text(RX0 - 1, 590, 'RUSSIAN SHIP', 'serif', 38, INK, -0.5)
paragraph(RX0, 620, 'Suspected Ukrainian sea drones strike the Merkury at Benghazi; Odesa hit by blackouts.',
          'sans', 16, 352, 20, (52, 51, 47))
# sea strip with ship and drones
fill_rect(RX0, 668, RX1, 744, DEEP)
for i in range(4):
    thick_line(RX0 + 8, 700 + i * 9, RX1 - 8, 700 + i * 9, 1.0, (52, 96, 124), 0.55)
sx, sy = RX0 + 150, 710
fill_poly([[(sx - 42, sy), (sx + 42, sy), (sx + 30, sy + 13), (sx - 30, sy + 13)]], (96, 106, 112))
fill_rect(sx - 16, sy - 14, sx + 10, sy, (126, 137, 144))
fill_rect(sx + 12, sy - 24, sx + 20, sy, (126, 137, 144))
thick_line(sx + 16, sy - 38, sx + 16, sy - 24, 1.5, (170, 179, 184))
for dx in (-58, -34):
    fill_poly([[(sx + dx, sy - 32), (sx + dx + 14, sy - 24), (sx + dx, sy - 16)]], (232, 92, 62))
    dashed_curve([(sx + dx + 10, sy - 20), (sx + dx + 34, sy - 4)], 1.2, (232, 92, 62), 0.8, 5, 5)
# explosion
for a in range(8):
    ang = a * math.pi / 4
    thick_line(sx + 26, sy - 8, sx + 26 + 12 * math.cos(ang), sy - 8 + 12 * math.sin(ang), 2.2, GOLD)
text(RX0 + 8, 690, 'BENGHAZI', 'sansb', 11, (225, 232, 236), 0.6)
text(RX1 - 8, 690, 'ODESA', 'sansb', 11, (225, 232, 236), 0.6, 'right')

# ---------------------------------------------------------------- bottom band
fill_rect(36, 764, 988, 766, INK)
cols = [
    (36, 328, 'ASIA  ·  BORDER', 'INDIA-CHINA', 'BORDER TALKS',
     'Commanders end 10 days of talks to ease Arunachal tensions before winter.', 'mountains'),
    (350, 642, 'SOUTH ASIA  ·  DIPLOMACY', 'NEPAL PM', 'MEETS MODI',
     'Balendra Shah\u2019s first India visit focuses on energy and connectivity.', 'podiums'),
    (664, 988, 'TECH  ·  US-CHINA', 'US PROBES', 'NVIDIA SPY',
     'Alleged Chinese spy tied to ex-CEO puts chip access under scrutiny.', 'chip'),
]
for x0, x1, kick, h1, h2, deck, icon in cols:
    # icon well
    fill_rect(x0, 780, x0 + 46, 826, (231, 223, 208))
    if icon == 'mountains':
        fill_poly([[(x0 + 5, 820), (x0 + 20, 790), (x0 + 31, 808), (x0 + 38, 798), (x0 + 43, 820)]], INK)
        fill_poly([[(x0 + 15, 800), (x0 + 20, 790), (x0 + 25, 800)]], WHITE)
        dashed_curve([(x0 + 30, 784), (x0 + 30, 822)], 1.2, RED, 1.0, 4, 4)
    elif icon == 'podiums':
        fill_rect(x0 + 8, 804, x0 + 22, 820, INK)
        fill_rect(x0 + 26, 798, x0 + 40, 820, INK)
        disc(x0 + 15, 796, 4.5, INK)
        disc(x0 + 33, 790, 4.5, INK)
        thick_line(x0 + 16, 802, x0 + 16, 810, 6, RED)
        thick_line(x0 + 34, 796, x0 + 34, 806, 6, (61, 105, 148))
    else:
        fill_rect(x0 + 11, 790, x0 + 35, 814, INK)
        fill_rect(x0 + 16, 795, x0 + 30, 809, (231, 223, 208))
        for i in range(3):
            fill_rect(x0 + 14 + i * 7, 784, x0 + 17 + i * 7, 790, INK)
            fill_rect(x0 + 14 + i * 7, 814, x0 + 17 + i * 7, 820, INK)
            fill_rect(x0 + 5, 792 + i * 7, x0 + 11, 795 + i * 7, INK)
            fill_rect(x0 + 35, 792 + i * 7, x0 + 41, 795 + i * 7, INK)
    text(x0 + 56, 800, kick, 'sansb', 12, RED, 0.8)
    text(x0 - 1, 852, h1, 'serif', 30, INK, -0.3)
    text(x0 - 1, 882, h2, 'serif', 30, INK, -0.3)
    paragraph(x0, 906, deck, 'sans', 15, x1 - x0, 17.5, (58, 56, 51))

# ---------------------------------------------------------------- footer
fill_rect(0, 944, W, H, INK)
text(512, 970, 'ALSO INSIDE:  ISRAEL COALITION TALKS STALL',
     'sansb', 17.5, (232, 226, 213), 0.3, 'center')
text(512, 990, 'WEST BANK SETTLER ARSON CONDEMNED  ·  HAITI FOOD CRISIS',
     'sansb', 17.5, (232, 226, 213), 0.3, 'center')
text(512, 1012, 'THE WORLD  ·  MONDAY 23 NOVEMBER 2026  ·  PAGE 1 OF 1', 'sans', 10.5, (147, 145, 137), 0.6, 'center')

# ---------------------------------------------------------------- PNG
raw = bytearray()
for y in range(H):
    raw.append(0)
    raw += buf[y * W * 3:(y + 1) * W * 3]


def chunk(tag, data):
    return (struct.pack('>I', len(data)) + tag + data +
            struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff))


png = (b'\x89PNG\r\n\x1a\n' +
       chunk(b'IHDR', struct.pack('>IIBBBBB', W, H, 8, 2, 0, 0, 0)) +
       chunk(b'IDAT', zlib.compress(bytes(raw), 9)) +
       chunk(b'IEND', b''))

out_dir = os.environ.get('MAKEFUN_OUTPUT_DIR', '/output')
os.makedirs(out_dir, exist_ok=True)
with open(os.path.join(out_dir, 'entry.png'), 'wb') as f:
    f.write(png)
print('wrote', os.path.join(out_dir, 'entry.png'), len(png), 'bytes')
