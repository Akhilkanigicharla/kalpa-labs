"""A201 · Exam Kits explainer clips (Manim CE, MIT). 9:16, Kalpa light palette, EN + TE captions.

Render: bash 03-kits/explainers/render.sh   (CI: .github/workflows/manim-clips.yml)
Data:   clips.json (one entry per clip; Text only, no LaTeX needed).
"""
import json
import tempfile
from pathlib import Path

from manim import (DOWN, LEFT, UP, Create, FadeIn, FadeOut, Line, Rectangle,
                   RoundedRectangle, Scene, Text, Transform, VGroup, Write, config)
from manimpango import register_font

HERE = Path(__file__).resolve().parent
FONTS = HERE.parents[1] / "00-hq" / "design" / "fonts"
DATA = json.loads((HERE / "clips.json").read_text(encoding="utf-8"))

config.pixel_width, config.pixel_height = 1080, 1920
config.frame_width, config.frame_height = 9, 16
config.frame_rate = 30

# Kalpa tokens (00-hq/design/tokens.css, light). b3 = --l3.
BG, PANEL, FG, MUTED, RULE = "#F2EEE3", "#FCFAF4", "#1E2A1F", "#5A6152", "#DCD5C3"
L3, GOLD, MADDER = "#3B7A3A", "#C38E12", "#8A4A28"  # gold = lines only (low text contrast)
LATIN, TELUGU = "Anek Latin", "Anek Telugu"
HOLD = 3.2  # seconds each step stays on screen (reading time for two captions)


def _register_fonts():
    """woff -> ttf in a temp dir (Pango cannot read woff), then register with Pango."""
    from fontTools.ttLib import TTFont
    out = Path(tempfile.mkdtemp(prefix="kalpa-fonts-"))
    for name in ("anek-latin-latin-600-normal", "anek-latin-latin-700-normal",
                 "anek-telugu-telugu-400-normal", "anek-telugu-telugu-700-normal"):
        src = FONTS / f"{name}.woff"
        if src.exists():
            f = TTFont(src)
            f.flavor = None
            dst = out / f"{name}.ttf"
            f.save(dst)
            register_font(str(dst))


_register_fonts()


def txt(s, size, color=FG, font=LATIN, weight="NORMAL", max_w=8.2):
    m = Text(s, font=font, font_size=size, color=color, weight=weight)
    if m.width > max_w:
        m.scale_to_fit_width(max_w)
    return m


def clip(cid):
    return next(c for c in DATA["clips"] if c["id"] == cid)


class Explainer(Scene):
    clip_id = ""

    def header(self, c):
        kicker = txt("KALPA EXAM KITS", 22, MUTED, weight="BOLD")
        t_en = txt(c["title_en"], 52, L3, weight="BOLD")
        t_te = txt(c["title_te"], 40, FG, TELUGU)
        g = VGroup(kicker, t_en, t_te).arrange(DOWN, buff=0.25).to_edge(UP, buff=0.9)
        rule = Line(LEFT * 4, -LEFT * 4, color=GOLD, stroke_width=4).next_to(g, DOWN, buff=0.35)
        self.play(FadeIn(g, shift=DOWN * 0.3), Create(rule), run_time=1)
        return VGroup(g, rule)

    def caption_box(self):
        box = RoundedRectangle(corner_radius=0.3, width=8.6, height=3.0, fill_color=PANEL,
                               fill_opacity=1, stroke_color=RULE, stroke_width=2).to_edge(DOWN, buff=0.8)
        self.play(FadeIn(box), run_time=0.3)
        return box

    def caption(self, box, step):
        en = txt(step["en"], 42, FG, weight="BOLD", max_w=8)
        te = txt(step["te"], 40, FG, TELUGU, max_w=8)
        return VGroup(en, te).arrange(DOWN, buff=0.3).move_to(box)

    def show_caption(self, box, old, step):
        new = self.caption(box, step)
        if old is None:
            self.play(FadeIn(new), run_time=0.5)
        else:
            self.play(FadeOut(old), FadeIn(new), run_time=0.5)
        return new

    def outro(self):
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        end = VGroup(txt("Practise more with", 40, MUTED),
                     txt("Kalpa Exam Kits", 60, L3, weight="BOLD"),
                     txt("మరిన్ని సాధన ప్రశ్నలు", 40, FG, TELUGU)).arrange(DOWN, buff=0.35)
        self.play(FadeIn(end), run_time=0.6)
        self.wait(1.4)


class StepsClip(Explainer):
    def construct(self):
        self.camera.background_color = BG
        c = clip(self.clip_id)
        self.header(c)
        box = self.caption_box()
        cap, lines = None, VGroup()
        for i, step in enumerate(c["steps"]):
            cap = self.show_caption(box, cap, step)
            line = txt(step["math"], 58, L3, weight="BOLD")
            line.move_to(UP * (2.8 - i * 1.5))
            if lines:
                self.play(*[m.animate.set_color(MUTED) for m in lines], run_time=0.2)
            self.play(Write(line), run_time=0.9)
            lines.add(line)
            self.wait(HOLD)
        self.play(lines[-1].animate.set_color(MADDER).scale(1.08), run_time=0.5)
        self.wait(0.6)
        self.outro()


class GraphClip(Explainer):
    def construct(self):
        self.camera.background_color = BG
        c = clip(self.clip_id)
        g = c["graph"]
        self.header(c)
        box = self.caption_box()
        # plot area: origin at (-3.2, -2.4), 6.6 wide, 5.4 tall
        ox, oy, W, H = -3.2, -2.4, 6.6, 5.4
        sx, sy = W / g["x_max"], H / g["y_max"]
        pt = lambda x, y: [ox + x * sx, oy + y * sy, 0]  # noqa: E731
        x_ax = Line(pt(0, 0), pt(g["x_max"], 0), color=FG, stroke_width=4)
        y_ax = Line(pt(0, 0), pt(0, g["y_max"]), color=FG, stroke_width=4)
        x_lab = txt("time (h)", 28, MUTED).next_to(x_ax, DOWN, buff=0.75).align_to(x_ax, -LEFT)
        y_lab = txt("speed (km/h)", 28, MUTED).next_to(y_ax, UP, buff=0.2).align_to(y_ax, LEFT)
        ticks = VGroup(*[txt(str(h), 26, MUTED).next_to(pt(h, 0), DOWN, buff=0.15) for h in range(g["x_max"] + 1)])
        steps = c["steps"]
        cap = self.show_caption(box, None, steps[0])
        self.play(Create(x_ax), Create(y_ax), FadeIn(x_lab, y_lab, ticks), run_time=1)
        self.wait(HOLD)

        cap = self.show_caption(box, cap, steps[1])
        flat = Line(pt(0, g["speed"]), pt(g["hours"], g["speed"]), color=L3, stroke_width=8)
        v_lab = txt(str(g["speed"]), 28, L3, weight="BOLD").next_to(pt(0, g["speed"]), LEFT, buff=0.15)
        self.play(Create(flat), FadeIn(v_lab), run_time=1)
        self.wait(HOLD)

        cap = self.show_caption(box, cap, steps[2])
        drop = Line(pt(g["hours"], g["speed"]), pt(g["hours"], 0), color=GOLD, stroke_width=5)
        self.play(Create(drop), ticks[g["hours"]].animate.set_color(MADDER), run_time=0.8)
        self.wait(HOLD)

        cap = self.show_caption(box, cap, steps[3])
        area = Rectangle(width=g["hours"] * sx, height=g["speed"] * sy, fill_color=L3, fill_opacity=0.25,
                         stroke_width=0).move_to(pt(g["hours"] / 2, g["speed"] / 2))
        self.play(FadeIn(area), run_time=0.8)
        self.wait(HOLD)

        cap = self.show_caption(box, cap, steps[4])
        ans = txt(steps[4]["math"], 48, MADDER, weight="BOLD", max_w=area.width * 0.9).move_to(area)
        self.play(Write(ans), run_time=0.9)
        self.wait(HOLD)
        self.outro()


class SimpleInterest(StepsClip):
    clip_id = "simple-interest"


class SpeedTimeGraph(GraphClip):
    clip_id = "speed-time-graph"


class ProfitPercent(StepsClip):
    clip_id = "profit-percent"


SCENES = {"simple-interest": "SimpleInterest", "speed-time-graph": "SpeedTimeGraph", "profit-percent": "ProfitPercent"}
