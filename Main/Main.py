#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
4R022 Heart  -  Cinematic "I love you" scene in 30 languages
Sinematik kalp sahnesi - 30 dilde "Seni seviyorum"

Copyright (c) 2026 4R022 / Kaan Kross
Licensed under the 4R022 Heart License (see LICENSE and Docs/NOTICE.md).
The brand elements (name, "4R022 PRESENTS" opening, closing card, logo, credits) MUST be kept.
Marka unsurlari (isim, "4R022 PRESENTS" acilisi, kapanis karti, logo, kredi) SILINEMEZ.

Run / Calistir      :  python Main/Main.py
Window test         :  python Main/Main.py --windowed
Performance         :  python Main/Main.py --quality auto|high|balanced|low   (see README)
Screenshots / Self-test: --screenshot DIR   |   --selftest
Emergency exit      :  ESC

Timeline (~49 s)
   0.0 -  6.3  "4R022 PRESENTS": letters write in, light sweep, 3 s fully visible, graceful dissolve
   5.8 - 12.6  Heart outline is drawn (music starts at 5.8)
   6.5 - 13.6  Outer phrases are written on, right behind the light
  12.8 - 20.4  Inside of the heart fills with phrases
  20.4        Ignition: flash + shockwaves + heartbeat
  20.4 - 40.4 Stays on screen for exactly 20 s
  40.4 - 46.2 Phrases dissolve into embers, outline retracts (music fades from 41.0)
  45.3 - 47.4 Closing card "4R022 HEART"
  47.4 - 48.8 Fade to black, program exits
"""
import sys
import os
import math
import glob
import gc
import json
import random
import argparse
from time import perf_counter

from PySide6.QtCore import Qt, QTimer, QUrl, QPointF, QRectF, QRect, QElapsedTimer
from PySide6.QtGui import (QPainter, QColor, QFont, QPen, QPainterPath, QPixmap, QImage,
                           QRadialGradient, QFontMetricsF, QCursor, QBrush, QPolygonF, QIcon)
from PySide6.QtWidgets import QApplication, QWidget
# QtMultimedia is imported lazily (faster window start-up)

APP_NAME = "4R022 Heart"
__version__ = "1.2.0"
COPYRIGHT = "(c) 2026 4R022 / Kaan Kross - 4R022 Heart License"
SETTINGS_FILE = "4R022-Heart.settings.json"

PLUS = QPainter.CompositionMode.CompositionMode_Plus
SRC_OVER = QPainter.CompositionMode.CompositionMode_SourceOver

# ----------------------------------------------------------------------------
# TIMELINE (seconds)
# ----------------------------------------------------------------------------
T_INTRO_OUT = 4.9               # letters are all in at ~1.85 -> 3 s fully visible
T_INTRO_END = 6.3
T_DRAW_START = 5.8
T_OUTLINE_END = 12.6
T_INNER_START = 12.8
T_INNER_LAST = 19.2
WRITE_DUR = 1.2
T_COMPLETE = T_INNER_LAST + WRITE_DUR          # 20.4
T_HOLD_END = T_COMPLETE + 20.0                 # 40.4  (exactly 20 s on screen)
ERASE_DUR = 1.0
T_ERASE_INNER = (T_HOLD_END, T_HOLD_END + 3.2)
T_ERASE_OUTER = (T_HOLD_END + 2.0, T_HOLD_END + 3.6)
T_OUTLINE_ERASE = (43.8, 46.2)
T_ENDCARD = 45.3
T_FADE = (47.4, 48.8)
T_QUIT = 49.0

MUSIC_START = T_DRAW_START
MUSIC_LEAD = 0.12
MUSIC_FADE = (41.0, 48.4)
XFADE = 2.0
FALLBACK_LEN = 24.0

# ----------------------------------------------------------------------------
# PERFORMANCE PROFILES
# ----------------------------------------------------------------------------
PROFILES = {
    "high":     dict(name="high",     particles=46, sparkles=64, glow=4, fps=60, embers=5),
    "balanced": dict(name="balanced", particles=30, sparkles=36, glow=3, fps=60, embers=3),
    "low":      dict(name="low",      particles=14, sparkles=12, glow=2, fps=30, embers=0),
}
LEVELS = ["high", "balanced", "low"]

# ----------------------------------------------------------------------------
# LANGUAGES (code, text)
# ----------------------------------------------------------------------------
PHRASES = [
    ("tr", "Seni seviyorum"), ("en", "I love you"), ("ru", "Я тебя люблю"),
    ("fr", "Je t’aime"), ("de", "Ich liebe dich"), ("es", "Te amo"),
    ("it", "Ti amo"), ("pt", "Eu te amo"), ("zh", "我爱你"), ("ja", "愛してる"),
    ("ko", "사랑해"), ("el", "Σ’ αγαπώ"), ("ar", "أحبك"), ("uk", "Я тебе кохаю"),
    ("pl", "Kocham cię"), ("nl", "Ik hou van jou"), ("sv", "Jag älskar dig"),
    ("th", "ฉันรักคุณ"), ("vi", "Anh yêu em"), ("id", "Aku cinta kamu"),
    ("no", "Jeg elsker deg"), ("da", "Jeg elsker dig"), ("fi", "Rakastan sinua"),
    ("sk", "Ľúbim ťa"), ("hu", "Szeretlek"), ("sq", "Të dua"),
    ("lt", "Aš tave myliu"), ("lv", "Es tevi mīlu"), ("et", "Ma armastan sind"),
    ("sl", "Ljubim te"),
]
OUTER_IDX = [0, 1, 3, 5, 6, 8, 9, 10]
INNER_IDX = [i for i in range(len(PHRASES)) if i not in OUTER_IDX]
RTL_CODES = ("ar",)

DEFAULT_FONTS = ["Segoe UI", "Helvetica Neue", "Noto Sans", "DejaVu Sans", "Arial"]
SERIF_FONTS = ["Bodoni MT", "Didot", "Georgia", "Cambria", "Noto Serif", "DejaVu Serif", "Times New Roman"]
FONT_HINTS = {
    "zh": ["Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", "Segoe UI"],
    "ja": ["Yu Gothic UI", "Yu Gothic", "Meiryo", "Hiragino Sans", "Noto Sans CJK JP"],
    "ko": ["Malgun Gothic", "Apple SD Gothic Neo", "Noto Sans CJK KR"],
    "ar": ["Segoe UI", "Tahoma", "Noto Naskh Arabic", "Arial"],
    "th": ["Leelawadee UI", "Tahoma", "Noto Sans Thai", "Arial"],
}


# ----------------------------------------------------------------------------
# HELPERS
# ----------------------------------------------------------------------------
def clamp01(x):
    return 0.0 if x < 0 else (1.0 if x > 1 else x)


def smooth(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)


def ease_io(x):
    x = clamp01(x)
    return 0.5 - 0.5 * math.cos(math.pi * x)


def ease_out(x):
    x = clamp01(x)
    return 1 - (1 - x) ** 3


def ease_in(x):
    x = clamp01(x)
    return x * x


def lerp(a, b, f):
    return a + (b - a) * f


def heart_unit(t):
    x = 16 * math.sin(t) ** 3
    y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
    return (x, y)


def resample(pts, n):
    d = [0.0]
    for i in range(1, len(pts)):
        d.append(d[-1] + math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
    total = d[-1]
    out, j = [], 0
    for k in range(n):
        target = total * k / (n - 1)
        while j < len(d) - 2 and d[j + 1] < target:
            j += 1
        seg = d[j + 1] - d[j]
        f = 0.0 if seg == 0 else (target - d[j]) / seg
        out.append((pts[j][0] + (pts[j + 1][0] - pts[j][0]) * f,
                    pts[j][1] + (pts[j + 1][1] - pts[j][1]) * f))
    return out


ARM_N = 360
_dense = [heart_unit(math.pi - i * math.pi / 3000.0) for i in range(3001)]
ARM_R = resample(_dense, ARM_N)
ARM_L = [(-x, y) for (x, y) in ARM_R]
LOOP = resample(ARM_R + ARM_L[::-1][1:], 721)
C_UNIT_Y = -2.0


def loop_at(u):
    pos = (u % 1.0) * (len(LOOP) - 1)
    i = int(pos)
    f = pos - i
    if i >= len(LOOP) - 1:
        return LOOP[-1]
    a, b = LOOP[i], LOOP[i + 1]
    return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)


def scan(poly, y):
    xs = []
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 <= y < y2) or (y2 <= y < y1):
            xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
    xs.sort()
    return [(xs[i], xs[i + 1]) for i in range(0, len(xs) - 1, 2)]


def clip_ints(a, b):
    out = []
    for (a0, a1) in a:
        for (b0, b1) in b:
            lo, hi = max(a0, b0), min(a1, b1)
            if hi > lo:
                out.append((lo, hi))
    return out


def resource_path(*parts):
    """Finds bundled files both from source and from a PyInstaller build."""
    bases = []
    if getattr(sys, "frozen", False):
        bases.append(getattr(sys, "_MEIPASS", os.path.dirname(sys.executable)))
        bases.append(os.path.dirname(sys.executable))
    else:
        here = os.path.dirname(os.path.abspath(__file__))
        bases += [os.path.dirname(here), here]
    for b in bases:
        p = os.path.join(b, *parts)
        if os.path.exists(p):
            return p
    return None


def find_music(arg=None):
    if arg and os.path.isfile(arg):
        return os.path.abspath(arg)
    d = resource_path("Assets", "Music")
    if d and os.path.isdir(d):
        pref = os.path.join(d, "meaningful-love-instrumental.mp3")
        if os.path.isfile(pref):
            return pref
        found = sorted(glob.glob(os.path.join(d, "*.mp3")))
        if found:
            return found[0]
    return None


def settings_paths():
    paths = []
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        paths.append(exe_dir)
        if sys.platform == "darwin":                       # X.app/Contents/MacOS -> next to X.app
            paths.append(os.path.abspath(os.path.join(exe_dir, "..", "..", "..")))
    else:
        here = os.path.dirname(os.path.abspath(__file__))
        paths += [os.path.join(os.path.dirname(here), "Assets", "Config"), here]
    return [os.path.join(p, SETTINGS_FILE) for p in paths]


def load_settings():
    for f in settings_paths():
        try:
            if os.path.isfile(f):
                with open(f, encoding="utf-8") as fh:
                    d = json.load(fh)
                if isinstance(d, dict):
                    return d
        except Exception as ex:                               # a bad settings file must never stop the show
            print("Settings file ignored:", f, ex)
    return {}


def parse_args(argv):
    ap = argparse.ArgumentParser(prog="4R022-Heart", description=f"{APP_NAME} {__version__} - {COPYRIGHT}")
    ap.add_argument("--windowed", action="store_true", help="run in a 1280x720 window on the primary screen")
    ap.add_argument("--quality", choices=["auto", "high", "balanced", "low"], default=None,
                    help="performance profile (default: auto)")
    ap.add_argument("--fps", type=int, default=None, help="frame-rate cap (default: profile)")
    ap.add_argument("--no-music", action="store_true", help="run silently")
    ap.add_argument("--music", metavar="FILE", default=None, help="use a different audio file")
    ap.add_argument("--primary-only", action="store_true", help="use only the primary monitor")
    ap.add_argument("--full-repaint", action="store_true", help="disable dirty-rectangle optimisation")
    ap.add_argument("--screenshot", metavar="DIR", default=None, help="render preview PNGs offscreen and exit")
    ap.add_argument("--size", default="1920x1080", help="screenshot size, e.g. 1920x1080")
    ap.add_argument("--selftest", action="store_true", help="run an internal health check and exit")
    ap.add_argument("--log", metavar="FILE", default=None, help="write self-test log to FILE")
    ap.add_argument("--version", action="store_true", help="print the version and exit")
    o = ap.parse_known_args(argv)[0]
    s = load_settings()
    q = o.quality or s.get("quality", "auto")
    o.quality = q if q in ("auto", "high", "balanced", "low") else "auto"
    try:
        f = o.fps if o.fps is not None else int(s.get("fps", 0) or 0)
    except (TypeError, ValueError):
        f = 0
    o.fps = max(15, min(240, f)) if f else 0
    o.no_music = bool(o.no_music or (s.get("music", True) is False))
    o.primary_only = bool(o.primary_only or s.get("primary_only", False))
    try:
        o.volume = max(0.0, min(1.0, float(s.get("volume", 0.9))))
    except (TypeError, ValueError):
        o.volume = 0.9
    return o


class Headless:
    """Minimal controller used for screenshots and self-tests."""
    windowed = True

    def __init__(self, prof=None):
        self.prof = prof or PROFILES["high"]
        self.t = 0.0


# ----------------------------------------------------------------------------
# STAGE WIDGET (one per monitor)
# ----------------------------------------------------------------------------
class StageWidget(QWidget):
    def __init__(self, screen, ctl, size=None):
        super().__init__()
        self.ctl = ctl
        self.scr = screen
        self.dpr = screen.devicePixelRatio() if screen is not None else 1.0
        windowed = bool(getattr(ctl, "windowed", False)) or size is not None
        if not windowed:
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
            self.setCursor(QCursor(Qt.CursorShape.BlankCursor))
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setWindowTitle(f"{APP_NAME} {__version__}")
        if size is not None:
            self.W, self.H = size
        elif windowed:
            g = screen.geometry()
            self.W, self.H = 1280, 720
            self.setScreen(screen)
            self.setGeometry(g.x() + 40, g.y() + 60, self.W, self.H)
        else:
            g = screen.geometry()
            self.setScreen(screen)
            self.setGeometry(g)
            self.W, self.H = g.width(), g.height()
        W, H = self.W, self.H
        # geometry
        self.s = min(0.62 * H / 28.9, 0.5 * W / 32.0)
        self.ox = W / 2.0
        self.oy = H / 2.0 - 2.55 * self.s
        self.cpx, self.cpy = self.to_px((0, C_UNIT_Y))
        self.heart_h = 28.9 * self.s
        self.u = min(H, W * 9.0 / 16.0)
        self._mc = {}
        self.entries = []
        self.parts, self.sparks = [], []
        self._pprev = []
        self._last_full = 0.0
        self._poly_k = -1
        self.intro_ready = False
        self.ready = False
        self._gen = self._build_gen()

    # ---- window ----------------------------------------------------------
    def go(self):
        if getattr(self.ctl, "windowed", False):
            self.show()
        else:
            self.move(self.scr.geometry().topLeft())
            self.showFullScreen()
        self.update()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape and hasattr(self.ctl, "finish"):
            self.ctl.finish()

    # ---- geometry helpers -------------------------------------------------
    def to_px(self, u, k=1.0):
        x = k * u[0]
        y = C_UNIT_Y + k * (u[1] - C_UNIT_Y)
        return (self.ox + self.s * x, self.oy - self.s * y)

    def snap(self, v):
        return round(v * self.dpr) / self.dpr

    @staticmethod
    def _R(x, y, w, h):
        return QRect(int(math.floor(x)) - 3, int(math.floor(y)) - 3, int(math.ceil(w)) + 7, int(math.ceil(h)) + 7)

    # ---- incremental builder ----------------------------------------------
    def step_build(self, budget=0.006):
        if self.ready:
            return
        t0 = perf_counter()
        while True:
            try:
                next(self._gen)
            except StopIteration:
                self.ready = True
                return
            if perf_counter() - t0 >= budget:
                return

    def build_all_sync(self):
        while not self.ready:
            self.step_build(60.0)

    def _build_gen(self):
        self.make_background()
        yield
        self.build_intro()
        self.intro_ready = True
        yield
        self.make_sprites()
        yield
        self.make_particles()
        yield
        self.make_outline()
        yield
        outer = self.layout_outer()
        yield
        inner = yield from self.layout_inner_gen()
        yield
        glow = (255, 40, 85)
        dists = [math.hypot(cx - self.cpx, cy - self.cpy) for (_, cx, cy, _, _, _) in inner]
        order = sorted(range(len(inner)), key=lambda k: -dists[k])
        rank = {k: r for r, k in enumerate(order)}
        n_in = max(1, len(inner) - 1)
        maxd = max(dists) if dists else 1.0
        palette = [(255, 238, 242), (255, 196, 210), (255, 250, 246)]
        # outer ring
        for k, (idx, cx, cy, f, path, r, fs) in enumerate(outer):
            fr = clamp01(f)
            appear = (T_DRAW_START + (T_OUTLINE_END - T_DRAW_START) * (math.acos(1 - 2 * fr) / math.pi) + 0.15)
            erase = T_ERASE_OUTER[0] + (T_ERASE_OUTER[1] - T_ERASE_OUTER[0]) * k / max(1, len(outer) - 1)
            self.entries.append(self.make_entry(idx, cx, cy, path, r, fs, (255, 236, 241), glow,
                                                appear, erase, k * 1.3, 0.0, True))
            yield
        # inner fill
        for k, (idx, cx, cy, path, r, fs) in enumerate(inner):
            appear = T_INNER_START + (T_INNER_LAST - T_INNER_START) * rank[k] / n_in
            erase = T_ERASE_INNER[0] + (T_ERASE_INNER[1] - T_ERASE_INNER[0]) * (n_in - rank[k]) / n_in
            ign = 1.2 * (1 - dists[k] / maxd)
            self.entries.append(self.make_entry(idx, cx, cy, path, r, fs, palette[idx % 3], glow,
                                                appear, erase, idx * 0.9, ign, False))
            yield
        self.finalize()

    # ---- build steps ---------------------------------------------------------
    def make_background(self):
        W, H = self.W, self.H
        pm = QPixmap(int(W * self.dpr), int(H * self.dpr))
        pm.setDevicePixelRatio(self.dpr)
        q = QPainter(pm)
        q.fillRect(0, 0, W, H, QColor(3, 0, 2))
        g = QRadialGradient(QPointF(W / 2, H * 0.48), 0.78 * max(W, H))
        g.setColorAt(0.0, QColor(46, 6, 16))
        g.setColorAt(0.45, QColor(20, 2, 8))
        g.setColorAt(1.0, QColor(2, 0, 1))
        q.fillRect(0, 0, W, H, QBrush(g))
        q.end()
        self.bg = pm

    def make_word(self, text, font, color, glow, px):
        """Pre-renders every letter of a word (used for the opening and closing cards)."""
        fm = QFontMetricsF(font)
        total = fm.horizontalAdvance(text) - font.letterSpacing()
        asc, desc, pad = 1.1 * px, 0.4 * px, 0.45 * px
        letters = []
        for i, ch in enumerate(text):
            if ch.isspace():
                continue
            x = fm.horizontalAdvance(text[:i])
            path = QPainterPath()
            path.addText(x, 0.0, font, ch)
            r = path.boundingRect()
            w, h = r.width() + 2 * pad, asc + desc
            pm = QPixmap(int(math.ceil(w * self.dpr)), int(math.ceil(h * self.dpr)))
            pm.setDevicePixelRatio(self.dpr)
            pm.fill(Qt.GlobalColor.transparent)
            q = QPainter(pm)
            q.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            q.translate(pad - r.x(), asc)
            for wf, al in ((0.50, 14), (0.28, 34), (0.12, 70)):
                pen = QPen(QColor(glow[0], glow[1], glow[2], al), px * wf)
                pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
                q.setPen(pen)
                q.setBrush(Qt.BrushStyle.NoBrush)
                q.drawPath(path)
            q.setPen(Qt.PenStyle.NoPen)
            q.setBrush(QColor(*color))
            q.drawPath(path)
            q.end()
            letters.append(dict(pm=pm, w=pm.width() / self.dpr, h=pm.height() / self.dpr,
                                ox=r.x() - pad, oy=-asc, cx=r.x() + r.width() / 2.0))
        return dict(letters=letters, width=total, px=px)

    def build_intro(self):
        W, H, u = self.W, self.H, self.u
        f1 = QFont()
        f1.setFamilies(SERIF_FONTS)
        f1.setPixelSize(max(12, int(0.105 * u)))
        f1.setWeight(QFont.Weight.Normal)
        f1.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.018 * u)
        f2 = QFont()
        f2.setFamilies(DEFAULT_FONTS)
        f2.setPixelSize(max(8, int(0.030 * u)))
        f2.setWeight(QFont.Weight.Light)
        f2.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.020 * u)
        f3 = QFont()
        f3.setFamilies(SERIF_FONTS)
        f3.setPixelSize(max(10, int(0.062 * u)))
        f3.setWeight(QFont.Weight.Normal)
        f3.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.012 * u)
        f4 = QFont()
        f4.setFamilies(DEFAULT_FONTS)
        f4.setPixelSize(max(7, int(0.020 * u)))
        f4.setWeight(QFont.Weight.Light)
        f4.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.034 * u)
        glow = (255, 40, 85)
        self.w_title = self.make_word("4R022", f1, (255, 236, 240), glow, 0.105 * u)
        self.w_pres = self.make_word("PRESENTS", f2, (236, 176, 190), glow, 0.030 * u)
        self.w_end1 = self.make_word("4R022", f3, (255, 236, 240), glow, 0.062 * u)
        self.w_end2 = self.make_word("HEART", f4, (236, 176, 190), glow, 0.020 * u)
        cx = W / 2.0
        self.i_base1 = H / 2.0 + 0.02 * u
        self.i_base2 = self.i_base1 + 0.085 * u
        self.i_x1 = cx - self.w_title["width"] / 2.0
        self.i_x2 = cx - self.w_pres["width"] / 2.0
        self.e_base1 = H / 2.0 + 0.012 * u
        self.e_base2 = self.e_base1 + 0.060 * u
        self.e_x1 = cx - self.w_end1["width"] / 2.0
        self.e_x2 = cx - self.w_end2["width"] / 2.0
        # soft light behind the title
        hw = max(0.5 * self.w_title["width"], 0.5 * self.w_pres["width"]) + 0.30 * u
        eh = 0.55 * u
        pm = QPixmap(int(math.ceil(2 * hw * self.dpr)), int(math.ceil(eh * self.dpr)))
        pm.setDevicePixelRatio(self.dpr)
        pm.fill(Qt.GlobalColor.transparent)
        q = QPainter(pm)
        q.translate(hw, eh / 2.0)
        q.scale(1.0, (eh / 2.0) / hw)
        g = QRadialGradient(QPointF(0, 0), hw)
        g.setColorAt(0.0, QColor(210, 22, 64, 120))
        g.setColorAt(0.55, QColor(150, 10, 40, 40))
        g.setColorAt(1.0, QColor(120, 0, 30, 0))
        q.fillRect(QRectF(-hw, -hw, 2 * hw, 2 * hw), QBrush(g))
        q.end()
        self.i_glow = pm
        self.i_glow_pos = QPointF(cx - hw, (self.i_base1 + self.i_base2) / 2.0 - 0.05 * u - eh / 2.0)
        self.intro_rect = self._R(cx - hw, self.i_base1 - 0.32 * u, 2 * hw, 0.64 * u)
        wide = max(self.w_end1["width"], self.w_end2["width"])
        self.end_rect = self._R(cx - wide / 2.0 - 0.10 * u, self.e_base1 - 0.12 * u, wide + 0.20 * u, 0.24 * u)

    def make_sprites(self):
        self.heart_sprites = []
        size = 64
        tints = [((255, 70, 110), (255, 200, 215)), ((200, 20, 60), (255, 120, 150)),
                 ((255, 150, 175), (255, 235, 240))]
        pts = [heart_unit(i * 2 * math.pi / 90.0) for i in range(91)]
        sc = size * 0.78 / 29.0
        for base, light in tints:
            pm = QPixmap(int(size * self.dpr), int(size * self.dpr))
            pm.setDevicePixelRatio(self.dpr)
            pm.fill(Qt.GlobalColor.transparent)
            q = QPainter(pm)
            q.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            path = QPainterPath()
            for i, (x, y) in enumerate(pts):
                px, py = size / 2 + sc * x, size / 2 - sc * (y + 2.55)
                if i == 0:
                    path.moveTo(px, py)
                else:
                    path.lineTo(px, py)
            path.closeSubpath()
            for w, a in ((7, 30), (4, 60)):
                pen = QPen(QColor(base[0], base[1], base[2], a), w)
                pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
                q.setPen(pen)
                q.setBrush(Qt.BrushStyle.NoBrush)
                q.drawPath(path)
            g = QRadialGradient(QPointF(size * 0.42, size * 0.38), size * 0.5)
            g.setColorAt(0.0, QColor(*light))
            g.setColorAt(1.0, QColor(*base))
            q.setPen(Qt.PenStyle.NoPen)
            q.setBrush(QBrush(g))
            q.drawPath(path)
            q.end()
            self.heart_sprites.append(pm)
        gs = 96
        pm = QPixmap(int(gs * self.dpr), int(gs * self.dpr))
        pm.setDevicePixelRatio(self.dpr)
        pm.fill(Qt.GlobalColor.transparent)
        q = QPainter(pm)
        g = QRadialGradient(QPointF(gs / 2, gs / 2), gs / 2)
        g.setColorAt(0.0, QColor(255, 245, 248, 255))
        g.setColorAt(0.18, QColor(255, 120, 150, 190))
        g.setColorAt(0.5, QColor(230, 30, 70, 70))
        g.setColorAt(1.0, QColor(200, 0, 40, 0))
        q.fillRect(0, 0, gs, gs, QBrush(g))
        q.end()
        self.glow_sprite = pm
        self.glow_src = QRectF(0, 0, pm.width(), pm.height())

    def make_particles(self):
        rng = random.Random(4022)
        W, H, u = self.W, self.H, self.u
        for _ in range(46):
            self.parts.append(dict(
                x=rng.uniform(0.02, 0.98) * W, sz=rng.uniform(0.010, 0.026) * u,
                sp=rng.uniform(0.028, 0.085) * H, off=rng.uniform(0, 1000),
                amp=rng.uniform(0.004, 0.02) * H, fr=rng.uniform(0.4, 1.1),
                ph=rng.uniform(0, 6.28), al=rng.uniform(0.25, 0.75),
                spr=rng.randrange(len(self.heart_sprites))))
        for _ in range(64):
            s = rng.uniform(0.012, 0.034) * u
            x, y = rng.uniform(0.02, 0.98) * W, rng.uniform(0.04, 0.96) * H
            self.sparks.append(dict(x=x, y=y, s=s, ph=rng.uniform(0, 6.28), sp=rng.uniform(0.8, 2.6),
                                    rect=self._R(x - s / 2, y - s / 2, s, s)))

    def make_outline(self):
        self.arm_r = [QPointF(*self.to_px(u)) for u in ARM_R]
        self.arm_l = [QPointF(*self.to_px(u)) for u in ARM_L]
        outline = [self.to_px(u) for u in LOOP]
        path = QPainterPath()
        path.moveTo(*outline[0])
        for p in outline[1:]:
            path.lineTo(*p)
        path.closeSubpath()
        self.heart_path = path
        specs = ((0.020, (255, 40, 90, 22)), (0.011, (255, 40, 90, 50)),
                 (0.0055, (255, 70, 110, 120)), (0.0028, (255, 225, 232, 255)))
        self.pens = []
        for wf, col in specs:
            pen = QPen(QColor(*col), wf * self.u)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            self.pens.append((pen, wf))

    # ---- text measuring / layout -----------------------------------------
    def measure(self, i, fs):
        key = (i, fs)
        if key in self._mc:
            return self._mc[key]
        code, text = PHRASES[i]
        f = QFont()
        f.setFamilies(FONT_HINTS.get(code, DEFAULT_FONTS))
        f.setPixelSize(max(6, int(fs)))
        f.setWeight(QFont.Weight.Medium)
        path = QPainterPath()
        path.addText(0.0, 0.0, f, text)
        res = (path, path.boundingRect())
        self._mc[key] = res
        return res

    @staticmethod
    def rects_ok(rects, pad, W, H, margin):
        for r in rects:
            if r.left() < margin or r.right() > W - margin or r.top() < margin or r.bottom() > H - margin:
                return False
        for a in range(len(rects)):
            ra = rects[a].adjusted(-pad, -pad, pad, pad)
            for b in range(a + 1, len(rects)):
                if ra.intersects(rects[b]):
                    return False
        return True

    def layout_outer(self):
        W, H = self.W, self.H
        ref = self.heart_h / 0.62
        n = len(OUTER_IDX)
        fracs = []
        for j in range(n):
            u = (j + 0.5) / n
            f = 2 * u if u <= 0.5 else 2 * (1 - u)
            fracs.append((f, 0 if u <= 0.5 else 1, u))
        order = sorted(fracs)
        poly = [self.to_px(u) for u in LOOP[:-1]]
        gap = 0.022 * ref
        best = None
        fs = int(0.030 * ref)
        while fs >= 6:
            items, rects = [], []
            for slot, idx in enumerate(OUTER_IDX):
                f, side, u = order[slot]
                path, r = self.measure(idx, fs)
                px, py = self.to_px(loop_at(u))
                dx, dy = px - self.cpx, py - self.cpy
                L = math.hypot(dx, dy) or 1.0
                dx, dy = dx / L, dy / L
                w, h = r.width(), fs * 1.15
                cx = px + dx * (gap + w / 2.0)
                cy = py + dy * (gap + h / 2.0)
                for _ in range(16):
                    corners = ((cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2),
                               (cx - w / 2, cy + h / 2), (cx + w / 2, cy + h / 2))
                    if not any(any(a0 <= x <= b0 for a0, b0 in scan(poly, y)) for x, y in corners):
                        break
                    cx += dx * 0.15 * fs
                    cy += dy * 0.15 * fs
                rects.append(QRectF(cx - w / 2.0, cy - h / 2.0, w, h))
                items.append((idx, cx, cy, f, path, r, fs))
            best = items
            if self.rects_ok(rects, 0.5 * fs, W, H, 0.02 * min(W, H)):
                break
            fs -= 1
        return best

    def try_fit(self, idxs, fs, poly):
        ws = {i: self.measure(i, fs)[1].width() for i in idxs}
        hh, rh = 0.62 * fs, 1.95 * fs
        ys = [p[1] for p in poly]
        y0, y1 = min(ys), max(ys)
        nrows = int((y1 - y0) // rh)
        if nrows < 1:
            return None
        ystart = y0 + ((y1 - y0) - nrows * rh) / 2.0 + rh / 2.0
        m, gap = 0.55 * fs, 0.9 * fs
        min_w = min(ws.values())
        slots = []
        for r in range(nrows):
            cy = ystart + r * rh
            ints = scan(poly, cy)
            ints = clip_ints(ints, scan(poly, cy - hh))
            ints = clip_ints(ints, scan(poly, cy + hh))
            for (a, b) in ints:
                a, b = a + m, b - m
                if b - a >= min_w:
                    slots.append([cy, a, b, [], 0.0])
        for i in sorted(idxs, key=lambda k: -ws[k]):
            w = ws[i]
            best, bestr = None, 9.0
            for s in slots:
                need = s[4] + w + (gap if s[3] else 0.0)
                cap = s[2] - s[1]
                if need <= cap and need / cap < bestr:
                    best, bestr = s, need / cap
            if best is None:
                return None
            best[4] += w + (gap if best[3] else 0.0)
            best[3].append(i)
        return slots, ws

    def layout_inner_gen(self):
        poly = [self.to_px(u, 0.86) for u in LOOP[:-1]]
        ref = self.heart_h / 0.62
        fs = int(0.030 * ref)
        res = None
        while fs >= 5:
            res = self.try_fit(INNER_IDX, fs, poly)
            if res:
                break
            fs -= 1
            yield
        if not res:
            fs = 5
            res = self.try_fit(INNER_IDX, fs, poly)
        items = []
        if not res:
            return items
        slots, ws = res
        for cy, a, b, ids, used in slots:
            if not ids:
                continue
            ids = sorted(ids)
            total = sum(ws[i] for i in ids)
            g = (b - a - total) / (len(ids) + 1)
            x = a + g
            for i in ids:
                path, r = self.measure(i, fs)
                items.append((i, x + ws[i] / 2.0, cy, path, r, fs))
                x += ws[i] + g
        return items

    def make_entry(self, idx, cx, cy, path, r, fs, color, glow, appear, erase, ph, ign, outer):
        pad, asc, desc = 0.45 * fs, 1.5 * fs, 0.6 * fs
        w, h = r.width() + 2 * pad, asc + desc
        pm = QPixmap(int(math.ceil(w * self.dpr)), int(math.ceil(h * self.dpr)))
        pm.setDevicePixelRatio(self.dpr)
        pm.fill(Qt.GlobalColor.transparent)
        q = QPainter(pm)
        q.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        q.translate(pad - r.x(), asc)
        for wf, al in ((0.62, 12), (0.36, 28), (0.18, 60)):
            pen = QPen(QColor(glow[0], glow[1], glow[2], al), fs * wf)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            q.setPen(pen)
            q.setBrush(Qt.BrushStyle.NoBrush)
            q.drawPath(path)
        q.setPen(Qt.PenStyle.NoPen)
        q.setBrush(QColor(*color))
        q.drawPath(path)
        q.end()
        rng = random.Random(7000 + idx)
        embers = [(rng.random(), rng.random(), rng.uniform(0.035, 0.06), rng.uniform(0.004, 0.012), rng.uniform(0, 6.28))
                  for _ in range(5)]
        rw = r.width()
        return dict(pm=pm, w=pm.width() / self.dpr, h=pm.height() / self.dpr, cx=cx, cy=cy, fs=fs,
                    asc=asc, mid=0.32 * fs, a=appear, e=erase, ph=ph, ign=ign, outer=outer,
                    rtl=PHRASES[idx][0] in RTL_CODES, embers=embers,
                    rect=QRectF(cx - rw / 2.0, cy - fs * 0.575, rw, fs * 1.15))

    def finalize(self):
        r = self.heart_path.boundingRect()
        for e in self.entries:
            r = r.united(e["rect"])
        m = 0.08 * self.u + 0.02 * self.heart_h
        self.heart_rect = self._R(r.left() - m, r.top() - m, r.width() + 2 * m, r.height() + 2 * m)
        hh = self.heart_h
        self.shock_rect = self._R(self.cpx - 1.5 * hh, self.cpy - 1.5 * hh, 3 * hh, 3 * hh)

    # ---- repaint management ----------------------------------------------
    def part_state(self, q, t):
        D = self.H + 2 * q["sz"]
        pos = (t * q["sp"] + q["off"]) % D
        life = pos / D
        x = q["x"] + math.sin(t * q["fr"] + q["ph"]) * q["amp"]
        y = self.H + q["sz"] - pos
        al = q["al"] * smooth(life * 6) * (1 - smooth((life - 0.7) / 0.3))
        return x, y, al

    def compute_dirty(self, t):
        """Dirty rectangles for this frame, or None for a full repaint."""
        if t < 0.4 or t >= T_FADE[0] or (T_COMPLETE <= t < T_COMPLETE + 0.95):
            return None
        if t - self._last_full > 5.0:                       # periodic self-heal
            self._last_full = t
            return None
        prof = self.ctl.prof
        rects = []
        if t < T_INTRO_END + 0.25:
            rects.append(self.intro_rect)
        if t >= T_ENDCARD - 0.1:
            rects.append(self.end_rect)
        for s in self.sparks[:max(prof["sparkles"], 0)]:
            rects.append(s["rect"])
        if self.ready and t >= T_DRAW_START - 0.5:
            rects.append(self.heart_rect)
            cur = []
            for q in self.parts[:prof["particles"]]:
                x, y, al = self.part_state(q, t)
                sz = q["sz"] * 1.1
                cur.append(self._R(x - sz, y - sz, 2 * sz, 2 * sz))
            rects += cur
            rects += self._pprev
            self._pprev = cur
            if T_COMPLETE - 0.1 < t < T_COMPLETE + 2.7:
                rects.append(self.shock_rect)
        return rects

    def refresh(self, t, force_full=False):
        if force_full or getattr(self.ctl, "full_repaint", False):
            self.update()
            return
        rects = self.compute_dirty(t)
        if rects is None:
            self.update()
        else:
            for r in rects:
                self.update(r)

    # ---- painting ----------------------------------------------------------
    def paintEvent(self, ev):
        p = QPainter(self)
        self.paint_scene(p, self.ctl.t)
        p.end()

    def paint_scene(self, p, t):
        W, H = self.W, self.H
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        if t < 0 or not self.intro_ready:
            p.fillRect(0, 0, W, H, QColor(0, 0, 0))
            return
        prof = self.ctl.prof
        p.drawPixmap(0, 0, self.bg)
        self.draw_sparkles(p, t, prof)
        if self.ready and t >= T_DRAW_START - 0.3:
            self.draw_particles(p, t, prof)
            self.draw_heart(p, t, prof)
            self.draw_shockwave(p, t)
        self.draw_endcard(p, t)
        if t < T_INTRO_END + 0.1:
            self.draw_intro(p, t)
        fl = (t - T_COMPLETE) / 0.9
        if 0 < fl < 1:
            p.fillRect(0, 0, W, H, QColor(255, 110, 140, int(42 * (1 - fl))))
        fa = smooth((t - T_FADE[0]) / (T_FADE[1] - T_FADE[0]))
        if fa > 0.002:
            p.fillRect(0, 0, W, H, QColor(0, 0, 0, int(255 * fa)))

    def draw_word(self, p, word, x0, base, t, t_in, st_in, dur_in, t_out, st_out, dur_out,
                  sweep_x=None, sweep_w=1.0):
        u = self.u
        letters = word["letters"]
        n = len(letters)
        for i, L in enumerate(letters):
            a = smooth((t - (t_in + st_in * i)) / dur_in)
            o = smooth((t - (t_out + st_out * i)) / dur_out)
            al = a * (1.0 - o)
            if al <= 0.003:
                continue
            dy = (1.0 - ease_out(a)) * 0.035 * u - o * 0.012 * u
            dx = (i - (n - 1) / 2.0) * 0.010 * u * o
            x = self.snap(x0 + L["ox"] + dx)
            y = self.snap(base + L["oy"] + dy)
            p.setOpacity(al)
            p.drawPixmap(QPointF(x, y), L["pm"])
            fl = 0.45 * math.sin(math.pi * a) if a < 1.0 else 0.0
            if sweep_x is not None:
                d = (x0 + L["cx"] - sweep_x) / sweep_w
                fl = max(fl, 0.8 * math.exp(-d * d))
            if fl > 0.03:
                p.setCompositionMode(PLUS)
                p.setOpacity(min(1.0, fl) * (1.0 - o))
                p.drawPixmap(QPointF(x, y), L["pm"])
                p.setCompositionMode(SRC_OVER)
        p.setOpacity(1.0)

    def draw_intro(self, p, t):
        W, u = self.W, self.u
        ga = smooth((t - 0.1) / 1.2) * (1 - smooth((t - T_INTRO_OUT) / 1.3))
        if ga > 0.003:
            p.setCompositionMode(PLUS)
            p.setOpacity(0.55 * ga * (0.92 + 0.08 * math.sin(t * 1.3)))
            p.drawPixmap(self.i_glow_pos, self.i_glow)
            p.setCompositionMode(SRC_OVER)
            p.setOpacity(1.0)
        sweep_x, sweep_w = None, 0.12 * self.w_title["width"] + 1.0
        if 2.2 < t < 3.9:
            s = ease_io((t - 2.2) / 1.7)
            sweep_x = lerp(self.i_x1 - 0.15 * self.w_title["width"],
                           self.i_x1 + 1.15 * self.w_title["width"], s)
        self.draw_word(p, self.w_title, self.i_x1, self.i_base1, t, 0.25, 0.10, 0.8,
                       T_INTRO_OUT, 0.05, 0.9, sweep_x, sweep_w)
        sweep_p = None
        if sweep_x is not None:
            sweep_p = lerp(self.i_x2 - 0.1 * self.w_pres["width"], self.i_x2 + 1.1 * self.w_pres["width"],
                           ease_io((t - 2.2) / 1.7))
        self.draw_word(p, self.w_pres, self.i_x2, self.i_base2, t, 0.9, 0.05, 0.6,
                       T_INTRO_OUT, 0.05, 0.9, sweep_p, 0.10 * self.w_pres["width"] + 1.0)
        la = ease_out((t - 0.5) / 1.4) * (1 - smooth((t - T_INTRO_OUT) / 0.9))
        if la > 0.01:
            ln = 0.085 * u * la
            y = self.i_base2 - 0.0105 * u
            gap = 0.025 * u
            x_l = self.i_x2 - gap
            x_r = self.i_x2 + self.w_pres["width"] + gap
            p.setOpacity(0.9 * la)
            p.setPen(QPen(QColor(200, 30, 70), max(1.0, 0.0015 * u)))
            p.drawLine(QPointF(x_l - ln, y), QPointF(x_l, y))
            p.drawLine(QPointF(x_r, y), QPointF(x_r + ln, y))
            p.setCompositionMode(PLUS)
            gs = 0.03 * u
            for gx in (x_l - ln, x_r + ln):
                p.drawPixmap(QRectF(gx - gs / 2, y - gs / 2, gs, gs), self.glow_sprite, self.glow_src)
            p.setCompositionMode(SRC_OVER)
            p.setOpacity(1.0)

    def draw_endcard(self, p, t):
        if t < T_ENDCARD - 0.05 or not self.intro_ready:
            return
        never = 1e9
        self.draw_word(p, self.w_end1, self.e_x1, self.e_base1, t, T_ENDCARD, 0.07, 0.8, never, 0.0, 1.0)
        self.draw_word(p, self.w_end2, self.e_x2, self.e_base2, t, T_ENDCARD + 0.35, 0.06, 0.7, never, 0.0, 1.0)

    def draw_sparkles(self, p, t, prof):
        sr = smooth((t - 0.3) / 1.5) * (1 - smooth((t - 46.5) / 1.5))
        if sr < 0.01 or not self.sparks:
            return
        p.setCompositionMode(PLUS)
        gs = self.glow_sprite
        for s in self.sparks[:max(prof["sparkles"], 0)]:
            p.setOpacity(sr * (0.10 + 0.50 * (0.5 + 0.5 * math.sin(t * s["sp"] + s["ph"]))))
            sz = s["s"]
            p.drawPixmap(QRectF(s["x"] - sz / 2, s["y"] - sz / 2, sz, sz), gs, self.glow_src)
        p.setCompositionMode(SRC_OVER)
        p.setOpacity(1.0)

    def draw_particles(self, p, t, prof):
        ramp = smooth((t - (T_DRAW_START - 0.2)) / 2.0) * (1 - smooth((t - 46.0) / 1.8))
        if ramp <= 0.003:
            return
        for q in self.parts[:prof["particles"]]:
            x, y, al = self.part_state(q, t)
            al *= ramp
            if al <= 0.01:
                continue
            spr = self.heart_sprites[q["spr"]]
            sz = q["sz"]
            p.save()
            p.translate(x, y)
            p.rotate(14 * math.sin(t * q["fr"] * 0.8 + q["ph"]))
            p.setOpacity(al)
            p.drawPixmap(QRectF(-sz / 2, -sz / 2, sz, sz), spr, QRectF(0, 0, spr.width(), spr.height()))
            p.restore()
        p.setOpacity(1.0)

    @staticmethod
    def beat(t):
        ph = (t * 0.85) % 1.0
        b = math.exp(-((ph - 0.06) / 0.045) ** 2) + 0.65 * math.exp(-((ph - 0.24) / 0.055) ** 2)
        return min(1.0, b)

    def draw_heart(self, p, t, prof):
        u = self.u
        amp = smooth((t - (T_COMPLETE - 1.4)) / 2.0) * (1 - smooth((t - 44.0) / 2.0))
        bt = self.beat(t) * amp
        sc = 1.0 + 0.028 * bt

        p.save()
        p.translate(self.cpx, self.cpy)
        p.scale(sc, sc)
        p.translate(-self.cpx, -self.cpy)
        f = smooth((t - 14.0) / 6.0) * (1 - smooth((t - 41.0) / 4.5))
        if f > 0.01:
            f *= 0.75 + 0.25 * bt
            g = QRadialGradient(QPointF(self.cpx, self.cpy), 0.52 * self.heart_h)
            g.setColorAt(0.0, QColor(255, 40, 85, int(95 * f)))
            g.setColorAt(0.6, QColor(170, 10, 40, int(60 * f)))
            g.setColorAt(1.0, QColor(90, 0, 20, int(14 * f)))
            p.fillPath(self.heart_path, QBrush(g))

        frac = ease_io((t - T_DRAW_START) / (T_OUTLINE_END - T_DRAW_START))
        frac *= 1 - ease_in((t - T_OUTLINE_ERASE[0]) / (T_OUTLINE_ERASE[1] - T_OUTLINE_ERASE[0]))
        if frac > 0.002:
            k = max(2, int(frac * (ARM_N - 1)) + 1)
            if k != self._poly_k:
                self._poly_k = k
                self._pr = QPolygonF(self.arm_r[:k])
                self._pl = QPolygonF(self.arm_l[:k])
            boost = 0.0
            if t >= T_COMPLETE - 0.5:
                boost = 0.125 * math.sin(t * 2.2) + 0.5 * bt + 0.2
            p.setBrush(Qt.BrushStyle.NoBrush)
            for pen, wf in self.pens[-prof["glow"]:]:
                pen.setWidthF(wf * u * (1 + 0.35 * boost))
                p.setPen(pen)
                p.drawPolyline(self._pr)
                p.drawPolyline(self._pl)
            if 0.01 < frac < 0.995:
                p.setCompositionMode(PLUS)
                gs = 0.075 * u
                for pt in (self.arm_r[k - 1], self.arm_l[k - 1]):
                    p.drawPixmap(QRectF(pt.x() - gs / 2, pt.y() - gs / 2, gs, gs), self.glow_sprite, self.glow_src)
                p.setCompositionMode(SRC_OVER)
        p.restore()

        # texts keep pixel-perfect size: only their positions follow the heartbeat
        for e in self.entries:
            self.draw_phrase(p, e, t, sc)
        if prof["embers"] > 0 and t >= T_HOLD_END - 0.1:
            for e in self.entries:
                self.draw_embers(p, e, t, sc, prof["embers"])

    def draw_phrase(self, p, e, t, sc):
        a = clamp01((t - e["a"]) / WRITE_DUR)
        qe = clamp01((t - e["e"]) / ERASE_DUR)
        if a <= 0.0 or qe >= 1.0:
            return
        alpha = smooth(a * 2.2) * (1.0 - smooth(qe))
        if t > T_COMPLETE:
            alpha *= 0.93 + 0.07 * math.sin(t * 1.7 + e["ph"])
        if alpha <= 0.003:
            return
        if qe > 0.0:
            lo, hi = ease_io(qe), 1.0
        else:
            lo, hi = 0.0, ease_out(a)
        if e["rtl"]:
            lo, hi = 1.0 - hi, 1.0 - lo
        if hi - lo < 0.004:
            return
        w, h, pm = e["w"], e["h"], e["pm"]
        pw, ph_ = pm.width(), pm.height()
        u = self.u
        settle = (1.0 - ease_out(a)) * 0.006 * u - ease_in(qe) * 0.012 * u
        x = self.snap(self.cpx + (e["cx"] - self.cpx) * sc - w / 2.0)
        y = self.snap(self.cpy + (e["cy"] - self.cpy) * sc + e["mid"] - e["asc"] + settle)
        target = QRectF(x + w * lo, y, w * (hi - lo), h)
        source = QRectF(pw * lo, 0.0, pw * (hi - lo), ph_)
        p.setOpacity(alpha)
        p.drawPixmap(target, pm, source)
        fl = 0.35 * math.sin(math.pi * a) if a < 1.0 else 0.0
        ig = (t - T_COMPLETE - e["ign"]) / 0.8
        if 0.0 < ig < 1.0:
            fl = max(fl, 0.7 * math.sin(math.pi * ig))
        if fl > 0.02:
            p.setCompositionMode(PLUS)
            p.setOpacity(min(1.0, fl) * (1.0 - smooth(qe)))
            p.drawPixmap(target, pm, source)
            p.setCompositionMode(SRC_OVER)
        if 0.0 < a < 1.0 and qe == 0.0:
            hx = x + w * (lo if e["rtl"] else hi)
            gs = e["fs"] * 2.2
            p.setCompositionMode(PLUS)
            p.setOpacity(0.9 * math.sin(math.pi * a))
            p.drawPixmap(QRectF(hx - gs / 2, y + e["asc"] - e["mid"] - gs / 2, gs, gs),
                         self.glow_sprite, self.glow_src)
            p.setCompositionMode(SRC_OVER)
        p.setOpacity(1.0)

    def draw_embers(self, p, e, t, sc, count):
        q = t - e["e"]
        if q < 0.0 or q > ERASE_DUR + 0.9:
            return
        u = self.u
        cx = self.cpx + (e["cx"] - self.cpx) * sc
        cy = self.cpy + (e["cy"] - self.cpy) * sc
        p.setCompositionMode(PLUS)
        for (xf, dl, rise, sway, ph) in e["embers"][:count]:
            k = (q - dl * 0.7) / 0.9
            if not (0.0 < k < 1.0):
                continue
            x = cx + (xf - 0.5) * e["w"] + math.sin(t * 3.0 + ph) * sway * u
            y = cy - k * rise * u
            sz = (0.5 + 0.5 * (1.0 - k)) * 0.8 * e["fs"]
            p.setOpacity((1.0 - k) ** 1.4 * 0.8)
            p.drawPixmap(QRectF(x - sz / 2, y - sz / 2, sz, sz), self.glow_sprite, self.glow_src)
        p.setCompositionMode(SRC_OVER)
        p.setOpacity(1.0)

    def draw_shockwave(self, p, t):
        for delay in (0.0, 0.4, 0.8):
            k = (t - T_COMPLETE - delay) / 1.8
            if 0 < k < 1:
                r = self.heart_h * (0.2 + 1.2 * ease_out(k))
                p.setOpacity((1 - k) ** 1.5 * (0.7 - 0.2 * delay))
                p.setPen(QPen(QColor(255, 60, 100), max(2.0, 0.004 * self.u)))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawEllipse(QPointF(self.cpx, self.cpy), r, r)
        p.setOpacity(1.0)


# ----------------------------------------------------------------------------
# CONTROLLER (shared clock, audio, all monitors, adaptive performance)
# ----------------------------------------------------------------------------
class Controller:
    def __init__(self, app, opts):
        self.app = app
        self.opts = opts
        self.windowed = opts.windowed
        self.full_repaint = opts.full_repaint
        self.t = -1.0
        self.clock = QElapsedTimer()
        self.launch = QElapsedTimer()
        self.launch.start()
        self.started = False
        self.done = False
        self.a_on = self.b_on = False
        self.players = []
        self.force_full = False
        self._last_tick = None
        self._ema = None
        self._slow = 0
        self._cool = 0

        if opts.windowed or opts.primary_only:
            screens = [app.primaryScreen()]
        else:
            screens = app.screens()
        self.level = self.pick_level(screens)
        self.prof = PROFILES[LEVELS[self.level]]
        self.fps = self.pick_fps(screens)
        self.start_delay = 1500 if sys.platform == "darwin" and not opts.windowed else 0

        self.widgets = [StageWidget(scr, self) for scr in screens]
        for w in self.widgets:
            w.go()
        self.timer = QTimer()
        self.timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.timer.setInterval(max(4, int(round(1000.0 / self.fps))))
        self.timer.timeout.connect(self.tick)
        self.timer.start()
        if not opts.no_music:
            QTimer.singleShot(350, self.setup_audio)       # after the first frames are on screen

    # ---- performance ---------------------------------------------------------
    def pick_level(self, screens):
        q = self.opts.quality
        if q in LEVELS:
            return LEVELS.index(q)
        total = 0.0
        for s in screens:
            g = s.geometry()
            total += g.width() * g.height() * s.devicePixelRatio() ** 2
        cores = os.cpu_count() or 2
        lvl = 0
        if total > 14e6 or cores <= 2:
            lvl = 1
        if total > 26e6 or cores <= 1:
            lvl = 2
        return lvl

    def pick_fps(self, screens):
        cap = self.prof["fps"]
        if self.opts.fps:
            return self.opts.fps
        try:
            hz = float(screens[0].refreshRate())
            if hz >= 20:
                cap = min(cap, int(round(hz)))
        except Exception:
            pass
        return max(15, cap)

    def adapt(self, now, t):
        if self._last_tick is not None:
            dt = now - self._last_tick
            self._ema = dt if self._ema is None else 0.9 * self._ema + 0.1 * dt
        self._last_tick = now
        if self.opts.quality != "auto" or self._ema is None:
            return
        if self._cool > 0:
            self._cool -= 1
            return
        if T_DRAW_START + 0.5 < t < 45.0 and self._ema > 1.45 / self.fps and self.level < len(LEVELS) - 1:
            self._slow += 1
            if self._slow >= 60:                                  # ~1 s of struggling -> step down
                self.level += 1
                self.prof = PROFILES[LEVELS[self.level]]
                self.fps = min(self.fps, self.prof["fps"])
                self.timer.setInterval(max(4, int(round(1000.0 / self.fps))))
                self.force_full = True
                self._slow, self._cool, self._ema = 0, 120, None
        else:
            self._slow = max(0, self._slow - 1)

    # ---- audio -----------------------------------------------------------------
    def setup_audio(self):
        path = find_music(self.opts.music)
        if not path:
            print("Warning: no music file found, running silently / Muzik bulunamadi, sessiz calisacak.")
            return
        try:
            from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput, QMediaDevices
            if not QMediaDevices.audioOutputs():
                print("Warning: no audio output device, running silently / Ses cihazi yok, sessiz calisacak.")
                return
            players = []
            for _ in range(2):
                out = QAudioOutput()
                out.setVolume(0.0)
                pl = QMediaPlayer()
                pl.setAudioOutput(out)
                pl.setSource(QUrl.fromLocalFile(path))
                players.append((pl, out))
            self.players = players
        except Exception as ex:                                   # audio must never crash the show
            print("Audio disabled:", ex)
            self.players = []

    def update_audio(self, t):
        if not self.players:
            return
        (A, oa), (B, ob) = self.players
        tm = t - MUSIC_START
        if tm >= -MUSIC_LEAD and not self.a_on:
            A.setPosition(0)
            A.play()
            self.a_on = True
        if tm < 0:
            return
        dur = A.duration() / 1000.0
        L = dur if dur > 1.0 else FALLBACK_LEN
        gain = self.opts.volume
        master = 1 - smooth((t - MUSIC_FADE[0]) / (MUSIC_FADE[1] - MUSIC_FADE[0]))
        va = smooth(tm / 1.5)
        vb = 0.0
        xs = L - XFADE
        if tm >= xs:
            if not self.b_on:
                B.setPosition(0)
                B.play()
                self.b_on = True
            x = smooth((tm - xs) / XFADE)
            va *= (1 - x)
            vb = x
        oa.setVolume(max(0.0, min(1.0, va * master * gain)))
        ob.setVolume(max(0.0, min(1.0, vb * master * gain)))

    # ---- main loop -------------------------------------------------------------
    def tick(self):
        if self.done:
            return
        now = perf_counter()
        if not self.started:
            for w in self.widgets:
                w.step_build(0.006)
            if all(w.intro_ready for w in self.widgets) and self.launch.elapsed() >= self.start_delay:
                self.clock.start()
                self.started = True
                gc.collect()
                gc.freeze()
                gc.disable()                                       # no garbage-collector pauses mid-show
            else:
                return
        t = self.clock.nsecsElapsed() * 1e-9
        self.t = t
        if not all(w.ready for w in self.widgets):
            force = t > T_DRAW_START - 0.7
            for w in self.widgets:
                w.step_build(60.0 if force else 0.005)
        self.update_audio(t)
        self.adapt(now, t)
        ff = self.force_full
        for w in self.widgets:
            w.refresh(t, ff)
        self.force_full = False
        if t >= T_QUIT:
            self.finish()

    def finish(self):
        if self.done:
            return
        self.done = True
        self.timer.stop()
        for pl, out in self.players:
            pl.stop()
        gc.enable()
        keep_awake(False)
        QApplication.restoreOverrideCursor()
        self.app.quit()


def keep_awake(on):
    """Windows: keeps the display and system awake during the show."""
    if sys.platform.startswith("win"):
        try:
            import ctypes
            ES_CONTINUOUS, ES_SYSTEM, ES_DISPLAY = 0x80000000, 0x00000001, 0x00000002
            ctypes.windll.kernel32.SetThreadExecutionState(
                ES_CONTINUOUS | ES_SYSTEM | ES_DISPLAY if on else ES_CONTINUOUS)
        except Exception:
            pass


# ----------------------------------------------------------------------------
# SCREENSHOTS & SELF-TEST
# ----------------------------------------------------------------------------
def render_frame(widget, t):
    img = QImage(int(widget.W * widget.dpr), int(widget.H * widget.dpr), QImage.Format.Format_ARGB32_Premultiplied)
    img.setDevicePixelRatio(widget.dpr)
    img.fill(Qt.GlobalColor.black)
    p = QPainter(img)
    widget.paint_scene(p, t)
    p.end()
    return img


def run_screenshots(opts):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        sw, sh = [int(v) for v in opts.size.lower().split("x")]
    except Exception:
        sw, sh = 1920, 1080
    app = QApplication([sys.argv[0]])
    w = StageWidget(app.primaryScreen(), Headless(), size=(sw, sh))
    w.build_all_sync()
    os.makedirs(opts.screenshot, exist_ok=True)
    shots = [("01-intro", 3.2), ("02-drawing", 9.6), ("03-heart", 26.0), ("04-closing", 46.4)]
    for name, t in shots:
        f = os.path.join(opts.screenshot, name + ".png")
        render_frame(w, t).save(f)
        print("saved", f)
    return 0


def run_selftest(opts):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    lines, fails = [], [0]

    def out(s):
        print(s)
        lines.append(s)

    def check(name, ok, warn=False):
        if ok:
            out(f"[ OK ] {name}")
        elif warn:
            out(f"[WARN] {name}")
        else:
            fails[0] += 1
            out(f"[FAIL] {name}")

    out(f"{APP_NAME} {__version__} self-test")
    check("music file bundled", bool(find_music(opts.music)))
    try:
        from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput, QMediaDevices   # noqa: F401
        check("QtMultimedia loads", True)
        check("audio output device present", bool(QMediaDevices.audioOutputs()), warn=True)
    except Exception as ex:
        out(f"       {ex}")
        check("QtMultimedia loads", False)
    check("icon bundled", bool(resource_path("Assets", "Icons", "icon.png")), warn=True)
    try:
        app = QApplication([sys.argv[0]])
        w = StageWidget(app.primaryScreen(), Headless(), size=(1920, 1080))
        w.build_all_sync()
        check("30 phrases laid out", len(w.entries) == 30)
        check("no overlapping phrases", StageWidget.rects_ok([e["rect"] for e in w.entries], 2, 1920, 1080, 0))
        img = render_frame(w, 26.0)
        lit = sum(1 for y in range(0, img.height(), 9) for x in range(0, img.width(), 9)
                  if img.pixelColor(x, y).red() > 60)
        check("heart frame renders", lit > 400)
        check("intro frame renders", render_frame(w, 3.2).pixelColor(img.width() // 2, img.height() // 2).alpha() > 0)
    except Exception as ex:
        out(f"       {type(ex).__name__}: {ex}")
        check("rendering engine (offscreen)", False, warn=True)
    out("RESULT: " + ("PASS" if fails[0] == 0 else f"{fails[0]} FAILED"))
    if opts.log:
        try:
            with open(opts.log, "w", encoding="utf-8") as fh:
                fh.write("\n".join(lines) + "\n")
        except Exception:
            pass
    return 1 if fails[0] else 0


# ----------------------------------------------------------------------------
def main():
    opts = parse_args(sys.argv[1:])
    if opts.version:
        print(APP_NAME, __version__)
        print(COPYRIGHT)
        return 0
    if opts.selftest:
        return run_selftest(opts)
    if opts.screenshot:
        return run_screenshots(opts)
    # Wayland cannot place windows on specific monitors -> prefer X11/XWayland when available
    if sys.platform.startswith("linux") and os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland":
        os.environ.setdefault("QT_QPA_PLATFORM", "xcb;wayland")
    app = QApplication([sys.argv[0]])
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(__version__)
    app.setOrganizationName("4R022")
    icon = resource_path("Assets", "Icons", "icon.png")
    if icon:
        app.setWindowIcon(QIcon(icon))
    if not opts.windowed:
        app.setOverrideCursor(QCursor(Qt.CursorShape.BlankCursor))
        keep_awake(True)
    ctl = Controller(app, opts)          # noqa: F841  (reference must be kept)
    code = app.exec()
    keep_awake(False)
    return code


if __name__ == "__main__":
    sys.exit(main())
