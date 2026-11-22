"""Sum up 22 November 2026's world news in one image.

Draws a 1024x1024 newspaper front page with the standard library only and
writes it to /output/entry.png (MAKEFUN_OUTPUT_DIR overrides the folder).
Everything is integer or plain IEEE arithmetic with no clock, randomness or
network, so every run writes the same bytes.
"""

import math
import os
import struct
import zlib

W = H = 1024

PAPER = (246, 241, 228)
INK = (24, 24, 24)
WHITE = (255, 255, 255)
GREY = (120, 120, 120)
LIGHT_GREY = (190, 190, 190)

# 5x7 bitmap font, upper case only. "~" draws as a space that never wraps.
FONT = {
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "C": [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "F": ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    "G": [".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".####"],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "I": [".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "J": ["..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."],
    "K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    "N": ["#...#", "#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "P": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    "Q": [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "V": ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."],
    "X": ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
    "Y": ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    "Z": ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
    "0": [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
    "1": ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "2": [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    "3": ["####.", "....#", "....#", ".###.", "....#", "....#", "####."],
    "4": ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    "5": ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    "6": [".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."],
    "7": ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
    "8": [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    "9": [".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."],
    "-": [".....", ".....", ".....", ".###.", ".....", ".....", "....."],
    ",": [".....", ".....", ".....", ".....", ".##..", "..#..", ".#..."],
    ".": [".....", ".....", ".....", ".....", ".....", ".##..", ".##.."],
    "%": ["##..#", "##..#", "...#.", "..#..", ".#...", "#..##", "#..##"],
    "&": [".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"],
    "'": ["..#..", "..#..", ".#...", ".....", ".....", ".....", "....."],
    " ": ["....."] * 7,
}
FONT["~"] = FONT[" "]


class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.rows = [bytearray(bytes(bg) * w) for _ in range(h)]

    def span(self, y, x0, x1, c):
        """Fill pixels x0..x1-1 of row y."""
        if y < 0 or y >= self.h:
            return
        x0 = max(0, x0)
        x1 = min(self.w, x1)
        if x1 > x0:
            self.rows[y][x0 * 3:x1 * 3] = bytes(c) * (x1 - x0)

    def rect(self, x0, y0, x1, y1, c):
        for y in range(max(0, y0), min(self.h, y1)):
            self.span(y, x0, x1, c)

    def frame(self, x0, y0, x1, y1, t, c):
        self.rect(x0, y0, x1, y0 + t, c)
        self.rect(x0, y1 - t, x1, y1, c)
        self.rect(x0, y0, x0 + t, y1, c)
        self.rect(x1 - t, y0, x1, y1, c)

    def circle(self, cx, cy, r, c):
        for dy in range(-r, r + 1):
            dx = isqrt_floor(r * r - dy * dy)
            self.span(cy + dy, cx - dx, cx + dx + 1, c)

    def ring(self, cx, cy, r_out, r_in, c):
        for dy in range(-r_out, r_out + 1):
            do = isqrt_floor(r_out * r_out - dy * dy)
            if abs(dy) < r_in:
                di = isqrt_floor(r_in * r_in - dy * dy)
                self.span(cy + dy, cx - do, cx - di, c)
                self.span(cy + dy, cx + di + 1, cx + do + 1, c)
            else:
                self.span(cy + dy, cx - do, cx + do + 1, c)

    def polygon(self, pts, c):
        """Even-odd scanline fill, sampled at pixel centres."""
        ys = [p[1] for p in pts]
        n = len(pts)
        for y in range(max(0, int(min(ys))), min(self.h, int(max(ys)) + 1)):
            sy = y + 0.5
            xs = []
            for i in range(n):
                xa, ya = pts[i]
                xb, yb = pts[(i + 1) % n]
                if (ya <= sy < yb) or (yb <= sy < ya):
                    xs.append(xa + (sy - ya) * (xb - xa) / (yb - ya))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.span(y, int(xs[i] + 0.5), int(xs[i + 1] + 0.5), c)

    def line(self, x0, y0, x1, y1, t, c):
        """Thick segment with round ends."""
        dx = x1 - x0
        dy = y1 - y0
        ln = (dx * dx + dy * dy) ** 0.5
        nx = -dy / ln * t / 2
        ny = dx / ln * t / 2
        self.polygon([(x0 + nx, y0 + ny), (x1 + nx, y1 + ny),
                      (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)], c)
        self.circle(int(x0), int(y0), t // 2, c)
        self.circle(int(x1), int(y1), t // 2, c)

    def png(self):
        raw = b"".join(b"\x00" + bytes(r) for r in self.rows)

        def chunk(kind, data):
            return (struct.pack(">I", len(data)) + kind + data
                    + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF))

        ihdr = struct.pack(">IIBBBBB", self.w, self.h, 8, 2, 0, 0, 0)
        return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
                + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def isqrt_floor(v):
    return math.isqrt(v) if v > 0 else 0


# ---------- text ----------

def text_width(s, scale, bold):
    if not s:
        return 0
    return len(s) * 6 * scale - scale + (scale // 2 if bold else 0)


def draw_text(cv, s, x, y, scale, c, bold=True):
    extra = scale // 2 if bold else 0
    for ch in s:
        glyph = FONT[ch]
        for gy, row in enumerate(glyph):
            for gx, bit in enumerate(row):
                if bit == "#":
                    px = x + gx * scale
                    py = y + gy * scale
                    cv.rect(px, py, px + scale + extra, py + scale, c)
        x += 6 * scale


def draw_centered(cv, s, cx, y, scale, c, bold=True):
    draw_text(cv, s, cx - text_width(s, scale, bold) // 2, y, scale, c, bold)


def wrap(s, scale, max_w, bold=True):
    lines = []
    cur = ""
    for word in s.split(" "):
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale, bold) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------- icons (each drawn in a 480x150 box at x, y) ----------

def icon_climate(cv, x, y):
    # Earth
    gx, gy = x + 150, y + 75
    cv.circle(gx, gy, 66, INK)
    cv.circle(gx, gy, 62, (58, 124, 196))
    cv.circle(gx - 22, gy - 20, 22, (70, 160, 80))
    cv.circle(gx - 4, gy - 30, 16, (70, 160, 80))
    cv.circle(gx + 26, gy + 18, 20, (70, 160, 80))
    cv.circle(gx + 10, gy + 34, 12, (70, 160, 80))
    cv.circle(gx - 30, gy + 30, 9, (70, 160, 80))
    # "stalled" pause sign
    px, py = x + 330, y + 75
    cv.circle(px, py, 62, INK)
    cv.circle(px, py, 58, (214, 96, 36))
    cv.rect(px - 26, py - 32, px - 8, py + 33, WHITE)
    cv.rect(px + 8, py - 32, px + 26, py + 33, WHITE)


def icon_strike(cv, x, y):
    # factory
    fx, base = x + 270, y + 140
    cv.rect(fx + 120, y + 40, fx + 146, base, (90, 90, 90))
    for i in range(3):  # saw-tooth roof
        cv.polygon([(fx + i * 45, y + 86), (fx + i * 45 + 45, y + 60),
                    (fx + i * 45 + 45, y + 86)], (105, 105, 105))
    cv.rect(fx, y + 85, fx + 180, base, (105, 105, 105))
    cv.rect(fx + 20, y + 100, fx + 45, y + 120, (230, 200, 90))
    cv.rect(fx + 70, y + 100, fx + 95, y + 120, (230, 200, 90))
    cv.rect(fx + 120, y + 100, fx + 145, y + 120, (230, 200, 90))
    # explosion on the roof
    ex, ey = fx + 70, y + 62
    star(cv, ex, ey, 58, 30, (226, 60, 30))
    star(cv, ex, ey, 38, 20, (250, 170, 30))
    cv.circle(ex, ey, 14, (255, 232, 120))
    # missile coming in from the upper left
    tail = (x + 112, y + 34)
    d = (0.9701425, 0.2425356)   # unit vector (4, 1) / sqrt(17), aimed at the blast
    n = (-d[1], d[0])
    L, hw = 110, 10

    def at(a, b):
        return (tail[0] + d[0] * a + n[0] * b, tail[1] + d[1] * a + n[1] * b)

    for i, r in enumerate((6, 8, 10, 12)):
        sx, sy = at(-96 + i * 22, 0)
        cv.circle(int(sx), int(sy), r, (200, 200, 200))

    cv.polygon([at(-14, -6), at(0, -4), at(0, 4), at(-14, 6)], (250, 150, 30))
    cv.polygon([at(0, -hw), at(L, -hw), at(L + 30, 0), at(L, hw), at(0, hw)],
               (60, 60, 60))
    cv.polygon([at(0, -hw), at(22, -hw), at(4, -hw - 16), at(-6, -hw - 16)],
               (170, 30, 30))
    cv.polygon([at(0, hw), at(22, hw), at(4, hw + 16), at(-6, hw + 16)],
               (170, 30, 30))
    cv.polygon([at(L - 4, -hw), at(L, -hw), at(L + 30, 0), at(L, hw),
                at(L - 4, hw)], (170, 30, 30))


STAR_DIRS = [(1.0, 0.0), (0.8660254, 0.5), (0.5, 0.8660254), (0.0, 1.0),
             (-0.5, 0.8660254), (-0.8660254, 0.5), (-1.0, 0.0),
             (-0.8660254, -0.5), (-0.5, -0.8660254), (0.0, -1.0),
             (0.5, -0.8660254), (0.8660254, -0.5)]
HALF_DIRS = [(0.9659258, 0.2588190), (0.7071068, 0.7071068),
             (0.2588190, 0.9659258), (-0.2588190, 0.9659258),
             (-0.7071068, 0.7071068), (-0.9659258, 0.2588190),
             (-0.9659258, -0.2588190), (-0.7071068, -0.7071068),
             (-0.2588190, -0.9659258), (0.2588190, -0.9659258),
             (0.7071068, -0.7071068), (0.9659258, -0.2588190)]


def star(cv, cx, cy, r_out, r_in, c):
    pts = []
    for (ox, oy), (ix, iy) in zip(STAR_DIRS, HALF_DIRS):
        pts.append((cx + ox * r_out, cy + oy * r_out))
        pts.append((cx + ix * r_in, cy + iy * r_in))
    cv.polygon(pts, c)


def icon_capture(cv, x, y):
    steel = (80, 88, 100)
    hi = (150, 160, 175)
    lx, rx, cy = x + 150, x + 330, y + 85
    for cx in (lx, rx):
        cv.ring(cx, cy, 52, 36, steel)
        cv.ring(cx, cy, 44, 40, hi)
        cv.rect(cx - 20, cy - 66, cx + 20, cy - 40, steel)
    # chain links between the cuffs
    for i in range(8):
        cx = lx + 28 + i * 18
        cv.ring(cx, cy - 53, 10, 5, steel)
    # police badge star
    bx, by = x + 240, y + 105
    pts = []
    for i in range(5):
        o = STAR5[i]
        n = STAR5_IN[i]
        pts.append((bx + o[0] * 34, by + o[1] * 34))
        pts.append((bx + n[0] * 15, by + n[1] * 15))
    cv.polygon(pts, (212, 170, 40))
    cv.circle(bx, by, 8, (160, 120, 20))


STAR5 = [(0.0, -1.0), (0.9510565, -0.3090170), (0.5877853, 0.8090170),
         (-0.5877853, 0.8090170), (-0.9510565, -0.3090170)]
STAR5_IN = [(0.5877853, -0.8090170), (0.9510565, 0.3090170), (0.0, 1.0),
            (-0.9510565, 0.3090170), (-0.5877853, -0.8090170)]


def icon_markets(cv, x, y):
    red = (200, 30, 30)
    ax, ay = x + 40, y + 10
    cv.rect(ax, ay, ax + 6, y + 140, INK)
    cv.rect(ax, y + 134, x + 280, y + 140, INK)
    for gy in (y + 40, y + 75, y + 110):
        cv.rect(ax + 8, gy, x + 280, gy + 2, LIGHT_GREY)
    pts = [(ax + 20, y + 24), (ax + 70, y + 40), (ax + 110, y + 32),
           (ax + 160, y + 78), (ax + 200, y + 100)]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        cv.line(x0, y0, x1, y1, 10, red)
    # arrow head pointing down-right along the last segment
    tx, ty = ax + 228, y + 116
    cv.polygon([(tx, ty), (ax + 186, y + 116), (ax + 214, y + 82)], red)
    draw_text(cv, "-3.7%", x + 284, y + 50, 6, red)


# ---------- page ----------

PANELS = [
    ("COP31 CLIMATE TALKS STALL", "NO FOSSIL-FUEL DEAL IN TURKEY",
     (30, 110, 60), icon_climate),
    ("IRAN STRIKES BAHRAIN", "MISSILES HIT INDUSTRIAL SITE, 2~HURT",
     (150, 25, 25), icon_strike),
    ("MEXICO CAPTURES EL CHAPO ISIDRO", "CARTEL BOSS CAUGHT, 11~DEAD",
     (25, 60, 130), icon_capture),
    ("MARKETS FALL", "S&P~500 DOWN 3.7% IN AI SELL-OFF",
     (40, 40, 40), icon_markets),
]


def draw_panel(cv, x, y, w, h, title, line, color, icon):
    cv.rect(x, y, x + w, y + h, (252, 249, 240))
    band = 104
    cv.rect(x, y, x + w, y + band, color)
    lines = wrap(title, 5, w - 24)
    ty = y + (band - (len(lines) * 42 - 7)) // 2
    for i, s in enumerate(lines):
        draw_centered(cv, s.replace("~", " "), x + w // 2, ty + i * 42, 5, WHITE)
    icon(cv, x, y + band + 6)
    sub = wrap(line, 4, w - 24)
    area_top = y + band + 160
    area_h = h - band - 160
    sy = area_top + (area_h - (len(sub) * 38 - 10)) // 2
    for i, s in enumerate(sub):
        draw_centered(cv, s.replace("~", " "), x + w // 2, sy + i * 38, 4, INK)
    cv.frame(x, y, x + w, y + h, 4, INK)


def render():
    cv = Canvas(W, H, PAPER)
    m = 24
    cv.rect(m, 14, W - m, 20, INK)
    draw_centered(cv, "22 NOVEMBER 2026", W // 2, 32, 9, INK)
    cv.rect(m, 106, W - m, 111, INK)
    cv.rect(m, 115, W - m, 117, INK)
    draw_centered(cv, "WORLD NEWS IN ONE IMAGE", W // 2, 130, 5, (150, 25, 25))
    cv.rect(m, 178, W - m, 184, INK)

    gap = 16
    pw = (W - 2 * m - gap) // 2
    top = 198
    ph = (H - m + 4 - top - gap) // 2
    for i, (title, line, color, icon) in enumerate(PANELS):
        px = m + (i % 2) * (pw + gap)
        py = top + (i // 2) * (ph + gap)
        draw_panel(cv, px, py, pw, ph, title, line, color, icon)
    return cv.png()


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    data = render()
    with open(path, "wb") as f:
        f.write(data)
    os.chmod(path, 0o644)


if __name__ == "__main__":
    main()
