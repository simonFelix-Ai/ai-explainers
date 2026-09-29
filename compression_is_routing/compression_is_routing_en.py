"""
"Compression Is Routing" -- English explainer in the style of 3Blue1Brown (Manim Community).

Paper: Compression is Routing: Reconstruction Error as an Intrinsic Signal
       for Modular Language Models (Zhongpan Tang, 2025)

Shares the subtitle/cue machinery and small widgets with the Chinese version
(compression_is_routing.py). E00_Hook is a cold open built for the first
five seconds on YouTube: the first frame already has content on screen.
"""

import textwrap

import numpy as np
from manim import *

from compression_is_routing import (CODE_C, MED_C, MONO, NOVEL_C, RAND_C, WIKI_C, Base,
                                    lock_icon, token_boxes, trapezoid)

SERIF = "Latin Modern Roman"
SANS = "Noto Sans CJK SC"


def T(s, size=36, color=WHITE, **kw):
    return Text(s, font=SERIF, font_size=size, color=color, **kw)


def fit(mob, width):
    """Shrink a mobject so it is at most `width` wide."""
    if mob.width > width:
        mob.scale_to_fit_width(width)
    return mob


def make_sub_en(text):
    t = Text(textwrap.fill(text, 64), font=SANS, font_size=26, color=GREY_A, line_spacing=0.8)
    if t.width > 12.5:
        t.scale_to_fit_width(12.5)
    t.to_edge(DOWN, buff=0.3)
    return VGroup(BackgroundRectangle(t, color=BLACK, fill_opacity=0.75, buff=0.12), t)


class BaseEN(Base):
    def read_time(self, text):
        # ~150 words per minute of narration
        return max(1.8, 0.066 * len(text) + 0.6)

    def make_sub(self, text):
        return make_sub_en(text)


def expert_box(name, color, width=4.2):
    box = RoundedRectangle(corner_radius=0.15, width=width, height=0.85,
                           stroke_color=color, fill_color=color, fill_opacity=0.12)
    icon = trapezoid(0.55, 0.22, 0.45, color).move_to(box.get_left() + RIGHT * 0.5)
    label = fit(T(name, 28, color), width - 1.1).next_to(icon, RIGHT, buff=0.25)
    return VGroup(box, icon, label)


def result_bars(base_y, H, xs, width=1.6, font_size=40):
    """Three bar trackers + labels for the 99.47 / 47.76 / 0.57 result."""
    names = [("Code", "in-domain", CODE_C), ("Wikipedia", "semi-OOD", WIKI_C),
             ("Random tokens", "fully OOD", RAND_C)]
    out = []
    for (n, tag, c), xpos in zip(names, xs):
        tr = ValueTracker(0.0)
        bar = always_redraw(lambda tr=tr, c=c, xpos=xpos: Rectangle(
            width=width, height=max(tr.get_value() / 100 * H, 0.001),
            fill_color=c, fill_opacity=0.85, stroke_width=0).move_to(
            [xpos, base_y + max(tr.get_value() / 100 * H, 0.001) / 2, 0]))
        num = always_redraw(lambda tr=tr, c=c, xpos=xpos: VGroup(
            DecimalNumber(tr.get_value(), num_decimal_places=2, font_size=font_size, color=c),
            MathTex(r"\%", font_size=font_size, color=c)).arrange(RIGHT, buff=0.05).move_to(
            [xpos, base_y + tr.get_value() / 100 * H + 0.35, 0]))
        lab = VGroup(T(n, 30, c), T(tag, 22, GREY_B)).arrange(DOWN, buff=0.08)
        lab.next_to([xpos, base_y, 0], DOWN, buff=0.15)
        out.append((tr, bar, num, lab))
    return out


# ================================================================ scenes

class E00_Hook(BaseEN):
    """Cold open: pain point -> striking result -> open question, in ~6 seconds."""

    def construct(self):
        line1 = T("Teach an AI something new...", 54).to_edge(UP, buff=0.8)
        rng = np.random.default_rng(1)
        old = VGroup(*[Dot(radius=0.11, color=BLUE_C) for _ in range(40)])
        old.arrange_in_grid(4, 10, buff=0.38).shift(DOWN * 0.4)
        # Frame one already shows content: no fade-in from black.
        self.add(line1, old)
        new = VGroup(*[Dot(radius=0.11, color=YELLOW) for _ in range(40)])
        for d, o in zip(new, old):
            d.move_to(o.get_center() + RIGHT * 9)
        line2 = T("...and it forgets something old.", 54, RED_C).next_to(line1, DOWN, buff=0.3)
        order = rng.permutation(40)
        # Motion starts on the very first frame: new knowledge flies in, old knowledge dies.
        self.say("Teach an AI something new... and it forgets something old.",
                 LaggedStart(*[AnimationGroup(new[i].animate.move_to(old[i].get_center()),
                                              old[i].animate.set_color(RED_C).scale(0.3).set_opacity(0))
                               for i in order], lag_ratio=0.04),
                 Succession(Wait(0.6), FadeIn(line2, shift=UP * 0.2, run_time=0.6)),
                 run_time=1.8, dur=2.6, show=False)
        self.play(FadeOut(VGroup(line1, line2, old, new)), run_time=0.25)

        head = T("One tiny model. No router. It knows what's its own.", 40).to_edge(UP, buff=0.5)
        bars = result_bars(base_y=-2.2, H=4.4, xs=[-4.0, 0, 4.0], width=2.0, font_size=48)
        for tr, bar, num, lab in bars:
            self.add(bar, num, lab)
        self.say("But this tiny model knows what's its own. No router.",
                 FadeIn(head),
                 LaggedStart(*[tr.animate.set_value(v) for (tr, *_), v in zip(bars, [99.47, 47.76, 0.57])],
                             lag_ratio=0.25),
                 run_time=1.3, dur=2.4, show=False)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.25)

        title = T("Compression Is Routing", 84)
        q = T("What if forgetting is just a routing problem?", 38, YELLOW).next_to(title, DOWN, buff=0.5)
        self.say("The secret? Compression.", FadeIn(title, scale=1.1), run_time=0.4, dur=1.1, show=False)
        self.say("What if forgetting is just a routing problem?", Write(q), run_time=0.8, dur=2.2,
                 show=False)
        self.play(FadeOut(VGroup(title, q)), run_time=0.4)


class E01_Title(BaseEN):
    def construct(self):
        title = T("Compression Is Routing", 76)
        sub = T("Reconstruction error as an intrinsic signal for modular language models", 28, GREY_B)
        line = Line(LEFT * 4.5, RIGHT * 4.5, color=BLUE_D)
        by = T("Based on the technical report by Zhongpan Tang (2025)", 24, GREY_B)
        g = VGroup(title, line, sub, by).arrange(DOWN, buff=0.35)
        self.say("Today's idea comes from a short technical report by an independent researcher.",
                 Write(title), Create(line), run_time=1.8)
        self.say("Its claim: how well a model compresses your data already tells you who should handle it.",
                 FadeIn(sub, shift=UP * 0.2), FadeIn(by))
        self.wait(0.3)
        self.clear_all()


class E02_Problem(BaseEN):
    def construct(self):
        header = T("Three headaches of large language models", 44).to_edge(UP, buff=0.5)
        self.say("Large language models run into three stubborn problems.", FadeIn(header, shift=DOWN * 0.2))

        cards = VGroup()
        for name, c in [("Limited context", BLUE_C), ("Costly inference", YELLOW_C),
                        ("Catastrophic forgetting", RED_C)]:
            r = RoundedRectangle(corner_radius=0.2, width=3.9, height=3.0,
                                 stroke_color=c, fill_color=c, fill_opacity=0.08)
            cards.add(VGroup(r, fit(T(name, 30, c), 3.6).move_to(r.get_top() + DOWN * 0.45)))
        cards.arrange(RIGHT, buff=0.35).shift(DOWN * 0.1)

        bar = VGroup(*[Square(0.18, stroke_width=1, stroke_color=BLUE_B, fill_color=BLUE,
                              fill_opacity=0.6) for _ in range(14)]).arrange(RIGHT, buff=0.04)
        bar.move_to(cards[0][0]).shift(DOWN * 0.3)
        cut = DashedLine(UP * 0.5, DOWN * 0.5, color=RED).move_to(bar[9].get_right() + RIGHT * 0.02)
        for sq in bar[10:]:
            sq.set_fill(opacity=0.1).set_stroke(opacity=0.3)
        gpus = VGroup(*[RoundedRectangle(corner_radius=0.05, width=1.6, height=0.28,
                                         stroke_color=YELLOW_B, fill_color=YELLOW_E,
                                         fill_opacity=0.5) for _ in range(5)]).arrange(UP, buff=0.07)
        gpus.move_to(cards[1][0]).shift(DOWN * 0.3)
        old = VGroup(*[Dot(radius=0.07, color=BLUE_B) for _ in range(12)]).arrange_in_grid(3, 4, buff=0.15)
        old.move_to(cards[2][0]).shift(DOWN * 0.3)

        self.say("One: the context window is finite, so long documents simply don't fit.",
                 FadeIn(cards[0], shift=UP * 0.2), FadeIn(VGroup(bar, cut)))
        self.say("Two: inference is expensive, often a whole rack of GPUs.",
                 FadeIn(cards[1], shift=UP * 0.2), LaggedStartMap(FadeIn, gpus, shift=DOWN * 0.2))
        self.say("Three: catastrophic forgetting. Fine-tune on something new, and old skills quietly erode.",
                 FadeIn(cards[2], shift=UP * 0.2), FadeIn(old))
        self.play(LaggedStart(*[d.animate.set_color(RED_C).scale(0.5).set_opacity(0.3)
                                for d in old[::2]], lag_ratio=0.1), run_time=1.2)
        self.say("That third one is why updating a giant model means re-training on mountains of old data.")
        self.clear_all()

        header = T("Mixture of Experts (MoE)", 44).to_edge(UP, buff=0.5)
        inp = RoundedRectangle(corner_radius=0.1, width=1.6, height=0.8, color=WHITE)
        inp_g = VGroup(inp, T("input", 28).move_to(inp)).move_to(LEFT * 5.2)
        router = RoundedRectangle(corner_radius=0.15, width=2.4, height=1.6,
                                  stroke_color=ORANGE, fill_color=ORANGE, fill_opacity=0.15)
        router_t = T("gating network", 24, ORANGE).move_to(router.get_top() + DOWN * 0.35)
        qmark = Text("?", font_size=64, color=ORANGE).move_to(router).shift(DOWN * 0.2)
        router_g = VGroup(router, router_t, qmark).move_to(LEFT * 1.8)
        experts = VGroup()
        for i, c in enumerate([BLUE_C, GREEN_C, PURPLE_B, TEAL_C]):
            r = RoundedRectangle(corner_radius=0.1, width=2.0, height=0.7,
                                 stroke_color=c, fill_color=c, fill_opacity=0.15)
            experts.add(VGroup(r, T(f"expert {i + 1}", 24, c).move_to(r)))
        experts.arrange(DOWN, buff=0.25).move_to(RIGHT * 3.2 + DOWN * 0.2)
        a0 = Arrow(inp_g.get_right(), router_g.get_left(), buff=0.1)
        arrows = VGroup(*[Arrow(router_g.get_right(), e.get_left(), buff=0.1, stroke_width=3,
                                max_tip_length_to_length_ratio=0.1) for e in experts])

        self.say("Mixture-of-Experts models help: split the work across specialists.",
                 FadeIn(header), FadeIn(inp_g), FadeIn(experts, lag_ratio=0.2))
        self.say("But who decides which expert gets which input? A separately trained gating network.",
                 GrowArrow(a0), FadeIn(router_g),
                 LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.2))
        self.say("It's one more thing to train, and its decisions are hard to interpret.",
                 Wiggle(qmark, scale_value=1.4), run_time=1.5)
        self.clear_all()

        q = T("Does routing really need to be learned?", 50, YELLOW)
        self.say("So here's the question: does routing really need to be learned at all?", Write(q), run_time=2)
        self.wait(0.6)
        self.clear_all()


class E03_Compression(BaseEN):
    def construct(self):
        header = T("Compression is intelligence", 46).to_edge(UP, buff=0.5)
        self.say("Start with a popular slogan: compression is intelligence.", Write(header))

        s1 = Text("for i in range(10):", font=MONO, font_size=34, color=CODE_C)
        s2 = Text("q#7z !pW~ k&Lx0 :", font=MONO, font_size=34, color=RAND_C)
        VGroup(s1, s2).arrange(DOWN, buff=1.4, aligned_edge=LEFT).shift(LEFT * 3.2 + UP * 0.3)

        def bits(n, color):
            return VGroup(*[Text(str(np.random.randint(2)), font=MONO, font_size=22, color=color)
                            for _ in range(n)]).arrange(RIGHT, buff=0.06)

        np.random.seed(3)
        b1 = bits(8, CODE_C).next_to(s1, DOWN, buff=0.3, aligned_edge=LEFT)
        b2 = bits(34, RAND_C).next_to(s2, DOWN, buff=0.3, aligned_edge=LEFT)
        l1 = T("predictable → short code", 28, CODE_C).next_to(b1, RIGHT, buff=0.5)
        l2 = T("unpredictable → long code", 28, RAND_C).next_to(s2, RIGHT, buff=0.6)

        self.say("A good language model predicts the next token well.", FadeIn(s1, shift=RIGHT * 0.2))
        self.say("And if you can predict, you can compress: predictable text needs very few bits.",
                 LaggedStartMap(FadeIn, b1, lag_ratio=0.1), FadeIn(l1))
        self.say("Unfamiliar, chaotic text needs many more.",
                 FadeIn(s2, shift=RIGHT * 0.2), LaggedStartMap(FadeIn, b2, lag_ratio=0.03), FadeIn(l2))

        eq = MathTex(r"\text{Prediction}", r"\;\Longleftrightarrow\;", r"\text{Compression}",
                     font_size=52).shift(DOWN * 2.0)
        cite = Text("Delétang et al., 2024 · Language Modeling Is Compression",
                    font_size=20, color=GREY_B).next_to(eq, DOWN, buff=0.2)
        self.say("Prediction and compression are two sides of the same coin.", Write(eq), FadeIn(cite))
        self.play(FadeOut(VGroup(s1, s2, b1, b2, l1, l2, eq, cite)))

        i1 = T("Corollary: a compressor is only good at data it knows.", 38)
        i2 = T("⇒  Compression quality is a fingerprint.", 44, YELLOW)
        VGroup(i1, i2).arrange(DOWN, buff=0.7)
        self.say("But there's a quieter corollary hiding here.", FadeIn(i1, shift=UP * 0.2))
        self.say("A compressor is only good at compressing the kind of data it was trained on.",
                 Indicate(i1, color=BLUE_B))
        self.say("So how well it compresses something tells you whether that something is 'one of its own'.",
                 Write(i2), run_time=2)
        self.say("This report turns that intuition into an architecture: compression is routing.",
                 Transform(header, T("Compression is intelligence  →  Compression is routing", 42)
                           .to_edge(UP, buff=0.5)))
        self.clear_all()


class E04_Architecture(BaseEN):
    def construct(self):
        title = T("An end-to-end Transformer autoencoder · 87M parameters", 34).to_edge(UP, buff=0.35)
        self.say("To test it, the author trained an 87-million-parameter Transformer autoencoder, end to end.",
                 FadeIn(title, shift=DOWN * 0.2))

        y0 = 0.3
        grid = VGroup(*[Square(0.09, stroke_width=0.4, stroke_color=BLUE_A, fill_color=BLUE,
                               fill_opacity=0.65) for _ in range(512)])
        grid.arrange_in_grid(rows=32, cols=16, buff=0.022).move_to([-5.4, y0, 0])
        gl = T("x: 512 tokens", 26, BLUE_B).next_to(grid, UP, buff=0.15)
        enc = trapezoid(3.2, 1.1, 1.9, BLUE_D).move_to([-2.9, y0, 0])
        enc_t = T("Encoder", 28).move_to(enc)
        z = VGroup(*[Rectangle(width=0.16, height=1.1, stroke_width=1, stroke_color=YELLOW_A,
                               fill_color=interpolate_color(YELLOW_D, ORANGE, i / 7), fill_opacity=0.9)
                     for i in range(8)]).arrange(RIGHT, buff=0.07).move_to([0, y0, 0])
        zl = T("z: 8 latent vectors", 26, YELLOW).next_to(z, UP, buff=0.35)
        dec = trapezoid(1.1, 3.2, 1.9, TEAL_D).move_to([2.9, y0, 0])
        dec_t = T("Decoder", 28).move_to(dec)
        out = grid.copy().move_to([5.4, y0, 0]).set_fill(TEAL, 0.65).set_stroke(TEAL_A)
        ol = T("x̂: reconstruction", 26, TEAL_B).next_to(out, UP, buff=0.15)

        self.say("The input is a block of 512 tokens.",
                 LaggedStartMap(FadeIn, grid, lag_ratio=0.002), FadeIn(gl), run_time=1.8)
        self.say("The encoder squeezes it, through attention, into just 8 latent vectors.",
                 FadeIn(enc), Write(enc_t))
        flow = grid.copy()
        self.play(flow.animate.scale(0.15).move_to(enc.get_right()).set_opacity(0), run_time=1.3)
        self.remove(flow)
        self.play(LaggedStartMap(GrowFromEdge, z, edge=DOWN, lag_ratio=0.12), FadeIn(zl), run_time=1.2)
        brace = Brace(z, DOWN, color=YELLOW)
        ratio = MathTex(r"512 \to 8 \;=\; 64{:}1", color=YELLOW, font_size=40).next_to(brace, DOWN)
        self.say("512 down to 8: a 64-fold compression of sequence length.", GrowFromCenter(brace), Write(ratio))
        self.say("The decoder then rebuilds the original sequence, token by token, from those 8 vectors alone.",
                 FadeIn(dec), Write(dec_t))
        flow2 = z.copy()
        self.play(flow2.animate.move_to(dec.get_left()).set_opacity(0), run_time=0.8)
        self.remove(flow2)
        self.play(LaggedStartMap(FadeIn, out, lag_ratio=0.002), FadeIn(ol), run_time=1.5)

        m = VGroup(*[Square(0.09, stroke_width=0.4, stroke_color=GREY_B, fill_color=GREY_D,
                            fill_opacity=0.8) for _ in range(32)]).arrange_in_grid(2, 16, buff=0.022)
        m.move_to([2.9, -2.2, 0])
        m_arrow = Arrow(m.get_top(), dec.get_bottom() + UP * 0.35, buff=0.05, color=GREY_B)
        m_l = T("m: auxiliary signal, same length as x, zero content", 22, GREY_B).next_to(m, LEFT, buff=0.3)
        self.say("The key is strict isolation. Besides z, the decoder only gets a signal m that carries no content.",
                 FadeIn(m), GrowArrow(m_arrow), FadeIn(m_l), run_time=1.5)

        self.play(FadeOut(title))
        skip = CurvedArrow(gl.get_top() + UP * 0.1, ol.get_top() + UP * 0.1, angle=-TAU / 10, color=RED_C)
        mid = skip.point_from_proportion(0.5)
        skip = DashedVMobject(skip, num_dashes=40)
        cross = Cross(scale_factor=0.35, stroke_color=RED).move_to(mid)
        no = T("no peeking at x", 26, RED_C).next_to(cross, DOWN, buff=0.12)
        self.say("No shortcut to the original: every bit of information must squeeze through that 8-vector bottleneck.",
                 Create(skip), run_time=1.2)
        self.play(Create(cross), FadeIn(no))
        self.say("That forces the encoder to learn the structure of the data itself, not just pass a signal along.",
                 Indicate(z, color=WHITE, scale_factor=1.15))

        formula = MathTex(r"x \;\to\; \text{Encoder} \;\to\; z \;\to\; [z,\,m] \;\to\; "
                          r"\text{Decoder} \;\to\; \hat{x}", font_size=40).to_edge(UP, buff=0.35)
        self.play(FadeOut(VGroup(skip, cross, no)))
        self.say("Training data: source code only, from codeparrot, with the GPT-2 tokenizer.",
                 Write(formula), run_time=1.5)
        self.clear_all()


class E05_Metric(BaseEN):
    def construct(self):
        header = T("How good is a reconstruction?", 44).to_edge(UP, buff=0.5)
        self.say("How do we score a reconstruction? With a deliberately strict metric.", FadeIn(header))

        x = token_boxes([1, 2, 3, 4, 5], BLUE)
        xh = token_boxes([1, 2, 6, 7, 5], TEAL)
        xl = MathTex("x", font_size=48).next_to(x, LEFT, buff=0.5)
        xhl = MathTex(r"\hat{x}", font_size=48).next_to(xh, LEFT, buff=0.5)
        rows = VGroup(VGroup(xl, x), VGroup(xhl, xh)).arrange(DOWN, buff=0.9).shift(UP * 0.6)
        self.say("Say the original is 1, 2, 3, 4, 5...", FadeIn(rows[0], shift=RIGHT * 0.2))
        self.say("...and the reconstruction is 1, 2, 6, 7, 5.", FadeIn(rows[1], shift=RIGHT * 0.2))
        marks = VGroup()
        for a, b, box in zip([1, 2, 3, 4, 5], [1, 2, 6, 7, 5], xh):
            marks.add(MathTex(r"\checkmark" if a == b else r"\times", color=GREEN if a == b else RED,
                              font_size=48).next_to(box, DOWN, buff=0.3))
        self.say("Compare position by position: 1, 2 and 5 match; 3 and 4 don't.",
                 LaggedStartMap(FadeIn, marks, shift=UP * 0.2, lag_ratio=0.25), run_time=2)
        res = MathTex(r"\text{TRA} = \frac{3}{5} = 60\%", font_size=48, color=YELLOW).next_to(marks, DOWN, buff=0.4)
        self.say("Three out of five: 60 percent.", Write(res))
        self.play(FadeOut(VGroup(rows, marks, res)))
        formula = MathTex(r"\text{TRA}(x,\hat{x}) = \frac{1}{L}\sum_{t=1}^{L}\mathbb{I}(x_t = \hat{x}_t)",
                          font_size=56)
        self.say("That's token-level reconstruction accuracy, or TRA.", Write(formula), run_time=2)
        note = T("exact token matches, not 'roughly the same meaning'", 30, GREY_B).next_to(formula, DOWN, buff=0.6)
        self.say("It only counts exact matches. 'Close enough' earns nothing.", FadeIn(note))
        self.clear_all()


class E06_Results(BaseEN):
    def construct(self):
        header = T("The result: a three-step cliff", 44).to_edge(UP, buff=0.4)
        self.say("Now, the moment of truth.", FadeIn(header))
        base_y, H, xs = -1.8, 3.3, [-3.6, 0, 3.6]
        axis = Line([-5.5, base_y, 0], [5.5, base_y, 0], color=GREY_B)
        self.play(Create(axis))
        bars = result_bars(base_y, H, xs)
        vals = [99.47, 47.76, 0.57]
        lines = ["On held-out code it has never seen: 99.47 percent of tokens rebuilt exactly.",
                 "Switch to English Wikipedia: accuracy collapses to 47.76 percent.",
                 "And on random token sequences: 0.57 percent."]
        for (tr, bar, num, lab), v, line in zip(bars, vals, lines):
            self.add(bar, num)
            self.say(line, FadeIn(lab), tr.animate.set_value(v), run_time=2)

        guess = DashedLine([-5.5, base_y + 0.02, 0], [5.5, base_y + 0.02, 0], color=GREY_A)
        g_t = T("random guessing ≈ 1/|V| ≈ 0.002%", 22, GREY_A).move_to([4.2, base_y + 1.5, 0])
        g_l = VGroup(g_t, Arrow(g_t.get_bottom(), [5.0, base_y + 0.05, 0], buff=0.08, color=GREY_A,
                                stroke_width=3))
        self.say("Note that 47.76 is not a guess. Guessing would score about two thousandths of a percent.",
                 Create(guess), FadeIn(g_l))
        self.say("The model is exploiting what code and English share: vocabulary and basic statistics. "
                 "The two distributions partly overlap.")
        tags = VGroup(T("perfect fit", 28, CODE_C), T("structural bias", 28, WIKI_C),
                      T("total rejection", 28, RAND_C))
        for tg, xpos, v in zip(tags, xs, vals):
            tg.move_to([xpos, base_y + v / 100 * H + 0.9, 0])
        tags[2].shift(UP * 0.3)
        self.play(FadeOut(VGroup(guess, g_l)))
        self.say("And random noise is flatly rejected. The model did not degenerate into a copy machine.",
                 LaggedStartMap(FadeIn, tags, shift=DOWN * 0.2, lag_ratio=0.3))
        self.say("One compressor, three distributions, three steps. The gap is huge and systematic.")
        self.clear_all()

        big = fit(T("Reconstruction error = a distribution fingerprint", 50, YELLOW), 12.5)
        self.say("So reconstruction error works as a built-in fingerprint of where data comes from.",
                 Write(big), run_time=2)
        self.wait(0.6)
        self.clear_all()


class E07_Geometry(BaseEN):
    def construct(self):
        header = T("What happens in latent space?", 44).to_edge(UP, buff=0.4)
        self.say("Why is the gap so large? Look at the shape of the latent vectors z.", FadeIn(header))
        rng = np.random.default_rng(7)
        frame = RoundedRectangle(corner_radius=0.15, width=6.0, height=4.6, color=GREY_D).move_to([-3.4, -0.1, 0])
        cc = frame.get_center() + np.array([-1.3, 0.8, 0])
        wc = frame.get_center() + np.array([1.3, -0.8, 0])
        code_pts = VGroup(*[Dot(cc + np.array([*rng.normal(0, 0.42, 2), 0]), radius=0.035, color=CODE_C)
                            for _ in range(160)])
        wiki_pts = VGroup(*[Dot(wc + np.array([*rng.normal(0, 0.42, 2), 0]), radius=0.035, color=WIKI_C)
                            for _ in range(160)])
        leg = VGroup(VGroup(Dot(color=CODE_C), T("code (in-domain)", 22, CODE_C)).arrange(RIGHT, buff=0.1),
                     VGroup(Dot(color=WIKI_C), T("wiki (out-of-domain)", 22, WIKI_C)).arrange(RIGHT, buff=0.1)
                     ).arrange(RIGHT, buff=0.4).next_to(frame, UP, buff=0.12)
        note = T("illustration · the paper shows t-SNE / UMAP plots", 20, GREY_B).next_to(frame, DOWN, buff=0.1)
        self.say("Project code and Wikipedia latents down to two dimensions:",
                 Create(frame), FadeIn(leg), FadeIn(note))
        self.play(LaggedStartMap(FadeIn, code_pts, lag_ratio=0.005),
                  LaggedStartMap(FadeIn, wiki_pts, lag_ratio=0.005), run_time=1.5)
        self.say("Two dense, disconnected islands, with empty space between them.")
        sep = DashedLine(frame.get_center() + np.array([-2.2, -1.9, 0]),
                         frame.get_center() + np.array([2.2, 1.9, 0]), color=WHITE)
        self.say("A single straight line separates them. They are linearly separable.", Create(sep))
        self.say("So the routing decision is nearly free. No elaborate gating network required.")
        self.say("And since each distribution lives in its own region, training one expert barely disturbs another.")

        ax = Axes(x_range=[0, 512, 128], y_range=[0.2, 1.0, 0.2], x_length=5.2, y_length=3.6,
                  axis_config={"color": GREY_B, "include_numbers": True, "font_size": 18},
                  tips=False).move_to([3.5, -0.2, 0])
        tau = 200 / np.log(16)
        curve = ax.plot(lambda k: 1 - 0.8 * np.exp(-k / tau), x_range=[0, 512], color=CODE_C)
        h95 = DashedLine(ax.c2p(0, 0.95), ax.c2p(512, 0.95), color=RED_C)
        v200 = DashedLine(ax.c2p(200, 0.2), ax.c2p(200, 0.95), color=RED_C)
        xl = T("principal components", 20, GREY_B).next_to(ax, DOWN, buff=0.1)
        yl = T("explained variance", 20, GREY_B).rotate(PI / 2).next_to(ax, LEFT, buff=0.1)
        lab = T("~200 dims → 95%", 24, YELLOW).next_to(ax.c2p(200, 0.95), DR, buff=0.15)
        self.say("PCA on the code latents: z has 512 dimensions on paper...", Create(ax), FadeIn(xl), FadeIn(yl))
        self.play(Create(curve), run_time=1.5)
        self.say("...but about 200 principal components already explain 95 percent of the variance.",
                 Create(h95), Create(v200), FadeIn(lab))
        self.say("The encoder has learned to drop noise and keep only the skeleton of the data.")
        self.clear_all()


class E08_Routing(BaseEN):
    def construct(self):
        header = T("Compression is routing", 46).to_edge(UP, buff=0.3)
        self.say("Put it all together and you get compression as routing.", FadeIn(header))
        experts = VGroup(expert_box("Code compressor", CODE_C), expert_box("Wiki compressor", WIKI_C),
                         expert_box("Novel compressor", NOVEL_C)).arrange(DOWN, buff=0.35).move_to([0.3, 0.9, 0])
        inp = VGroup(RoundedRectangle(corner_radius=0.12, width=3.2, height=1.1, color=WHITE),
                     Text("def area(r):\n    return 3.14*r*r", font=MONO, font_size=18, color=CODE_C))
        inp[1].move_to(inp[0])
        inp.move_to([-5.0, 0.9, 0])
        in_l = T("new input", 24, GREY_B).next_to(inp, UP, buff=0.15)
        arrows = VGroup(*[Arrow(inp.get_right(), e.get_left(), buff=0.15, stroke_width=3,
                                max_tip_length_to_length_ratio=0.08) for e in experts])
        self.say("Give each expert its own compressor, trained only on its own domain.",
                 LaggedStartMap(FadeIn, experts, shift=LEFT * 0.2, lag_ratio=0.2))
        self.say("A new input arrives. Say, a bit of code.", FadeIn(inp, shift=RIGHT * 0.2), FadeIn(in_l))
        self.say("Every compressor tries to compress and rebuild it.",
                 LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.2))

        def readouts(vals):
            g = VGroup()
            for v, e in zip(vals, experts):
                c = GREEN if v >= 90 else (YELLOW if v >= 50 else RED_C)
                g.add(T(f"{v}%", 32, c).next_to(e, RIGHT, buff=0.5))
            return g

        r1 = readouts([99, 44, 41])
        self.add(T("illustrative numbers", 20, GREY_B).to_corner(UR, buff=0.4))
        self.say("Then compare their reconstruction accuracy.", LaggedStartMap(FadeIn, r1, shift=LEFT * 0.2, lag_ratio=0.3))
        win = SurroundingRectangle(VGroup(experts[0], r1[0]), color=YELLOW, buff=0.12)
        route = T("→ route to code", 28, YELLOW).next_to(win, RIGHT, buff=0.3)
        self.say("Whoever rebuilds it best gets the job. That's the whole rule.", Create(win), FadeIn(route))
        self.say("No gating network, no extra parameters. The error itself is the routing signal, and you can read it.")

        self.play(FadeOut(VGroup(win, route, r1)))
        inp2 = VGroup(RoundedRectangle(corner_radius=0.12, width=3.2, height=1.1, color=WHITE),
                      T("Patient reports a dry\ncough for three weeks...", 20, MED_C))
        inp2[1].move_to(inp2[0])
        inp2.move_to(inp)
        self.say("Now the part that matters for forgetting. What if a whole new domain shows up, like medical notes?",
                 ReplacementTransform(inp, inp2))
        r2 = readouts([31, 46, 38])
        self.say("Nobody recognizes it. Every compressor reconstructs it poorly.",
                 LaggedStartMap(FadeIn, r2, shift=LEFT * 0.2, lag_ratio=0.3))
        self.say("That is itself a signal: time to add a new expert.")
        new_e = expert_box("Medical compressor", MED_C).next_to(experts, DOWN, buff=0.35)
        locks = VGroup(*[lock_icon().move_to(e.get_corner(UL) + RIGHT * 0.05 + DOWN * 0.05) for e in experts])
        self.play(FadeOut(r2))
        self.say("Mount a medical compressor and train only that. Every old expert stays frozen.",
                 FadeIn(new_e, shift=UP * 0.3), experts.animate.set_opacity(0.45),
                 LaggedStartMap(FadeIn, locks, scale=0.5))
        a_new = Arrow(inp2.get_right(), new_e.get_left(), buff=0.15, stroke_width=3, color=MED_C,
                      max_tip_length_to_length_ratio=0.08)
        r3 = T("98%", 32, GREEN).next_to(new_e, RIGHT, buff=0.5)
        self.say("Old knowledge is physically untouched, so it can't be overwritten. "
                 "Forgetting is sidestepped by design.", GrowArrow(a_new), FadeIn(r3))
        self.say("Instead of a monolith you re-forge every time, you get an ecosystem that grows by adding modules.")
        self.clear_all()


class E09_Memory(BaseEN):
    def construct(self):
        header = T("A bonus: memory", 44).to_edge(UP, buff=0.5)
        self.say("There's also an unexpected bonus: memory.", FadeIn(header))
        full = Rectangle(width=11.5, height=0.6, fill_color=BLUE, fill_opacity=0.7, stroke_width=0).move_to(UP * 1.0)
        fl = T("standard KV cache: grows linearly with length (512 positions)", 26, BLUE_B).next_to(full, UP, buff=0.15)
        comp = Rectangle(width=11.5 / 64, height=0.6, fill_color=YELLOW, fill_opacity=0.9,
                         stroke_width=0).align_to(full, LEFT).shift(DOWN * 0.6)
        cl = T("compressed: 8 latent vectors", 26, YELLOW).next_to(comp, RIGHT, buff=0.3)
        self.say("A standard Transformer's KV cache grows linearly with context length.",
                 GrowFromEdge(full, LEFT), FadeIn(fl), run_time=1.8)
        self.add(full.copy().set_fill(opacity=0.25))
        self.say("In latent space, 512 positions become 8 vectors: 64 times shorter.",
                 ReplacementTransform(full.copy(), comp), FadeIn(cl), run_time=1.8)
        big = MathTex(r"\frac{1}{64}", font_size=90, color=YELLOW).shift(DOWN * 1.9 + RIGHT * 3)
        self.say("The paper's vision: contexts that once needed several A100s", Write(big))
        self.say("might fit on a single consumer graphics card.")
        self.clear_all()


class E10_Limits(BaseEN):
    def construct(self):
        header = T("Limitations and open questions", 44).to_edge(UP, buff=0.4)
        self.say("To be clear, this is a foundational proof of concept, and it has real limits.", FadeIn(header))
        n = 48
        cells = VGroup(*[Square(0.22, stroke_width=0.5, stroke_color=GREY_B,
                                fill_color=NOVEL_C if i < 28 else CODE_C, fill_opacity=0.7)
                         for i in range(n)]).arrange(RIGHT, buff=0.02).move_to(UP * 1.6)
        nl = T("novel", 24, NOVEL_C).next_to(cells[10], UP, buff=0.15)
        cl = T("code", 24, CODE_C).next_to(cells[38], UP, buff=0.15)
        self.say("First, hysteresis. The compression window is a fixed 512 tokens.",
                 LaggedStartMap(FadeIn, cells, lag_ratio=0.02), FadeIn(nl), FadeIn(cl))
        win = SurroundingRectangle(cells[16:32], color=YELLOW, buff=0.06)
        self.say("When the content switches mid-window, say from a novel into a code block,", Create(win))
        ax = Axes(x_range=[0, n, 8], y_range=[0, 1, 0.5], x_length=cells.width, y_length=2.0,
                  tips=False, axis_config={"color": GREY_C}).next_to(cells, DOWN, buff=0.35)
        ax.align_to(cells, LEFT)

        def err(t):
            b = 28
            if t < b:
                return 0.1
            return 0.1 + 0.8 * np.exp(-(t - b) / 5.0) * min(1, (t - b + 0.5) / 1.5)

        g = ax.plot(err, x_range=[0, n - 0.01, 0.05], color=RED_C)
        gl = T("error", 22, RED_C).next_to(ax, LEFT, buff=0.1)
        self.say("z is still dominated by what came before, so the error spikes at the switch.",
                 Create(ax), Create(g), FadeIn(gl),
                 win.animate.move_to(VGroup(*cells[22:38]).get_center()), run_time=2)
        self.play(FadeOut(VGroup(cells, nl, cl, win, ax, g, gl)))
        items = VGroup(
            T("• Interleaved data (blogs with code snippets) lands in a gray zone", 28),
            T("• At 64×, M = 8 vectors is the minimum; M = 2 or 4 loses information", 28),
            T("• Early runs hint at 128× or more", 28),
            T("• No full continual-learning benchmark yet", 28),
            T("• Conjecture: an entropy-based scaling law between M and L", 28, YELLOW),
        ).arrange(DOWN, buff=0.4, aligned_edge=LEFT).shift(UP * 0.3)
        self.say("Second, real text is often interleaved, so one window can straddle two distributions.",
                 FadeIn(items[0], shift=RIGHT * 0.2))
        self.say("Third, compute was limited. At this setting, 8 vectors is the smallest length that works.",
                 FadeIn(items[1], shift=RIGHT * 0.2))
        self.say("Early experiments suggest even 128-fold compression may be possible.", FadeIn(items[2], shift=RIGHT * 0.2))
        self.say("And the forgetting story is an architectural argument; "
                 "a full continual-learning benchmark is still open work.", FadeIn(items[3], shift=RIGHT * 0.2))
        self.say("The author conjectures a scaling law, rooted in entropy, linking latent length to sequence length.",
                 FadeIn(items[4], shift=RIGHT * 0.2))
        self.say("The same three-step pattern also showed up on Chinese novels with a custom tokenizer.")
        self.clear_all()


class E11_Outro(BaseEN):
    def construct(self):
        nums = VGroup(T("99.47%", 64, CODE_C), MathTex(r"\to", font_size=60), T("47.76%", 64, WIKI_C),
                      MathTex(r"\to", font_size=60), T("0.57%", 64, RAND_C)).arrange(RIGHT, buff=0.4).shift(UP * 1.2)
        self.say("99.47. 47.76. 0.57.", LaggedStartMap(FadeIn, nums, shift=UP * 0.2, lag_ratio=0.3), run_time=2)
        line = T("How well you compress it tells you whose data it is.", 40).next_to(nums, DOWN, buff=0.7)
        self.say("Three numbers that say: how well you compress something tells you whose data it is.",
                 Write(line), run_time=2)
        self.play(FadeOut(VGroup(nums, line), shift=UP * 0.3))
        title = T("Compression Is Routing", 80)
        g = VGroup(title).shift(UP * 1.2)
        repo = Text("github.com/simonFelix-Ai/compression_is_routing", font=MONO, font_size=26, color=GREY_A)
        paper = T("Paper: Zhongpan Tang, 2025 · link in the description", 24, GREY_B)
        chain = T("Paper SHA-256 timestamped on-chain (BscScan)", 24, GREY_B)
        info = VGroup(repo, paper, chain).arrange(DOWN, buff=0.25).next_to(g, DOWN, buff=0.8)
        self.say("From 'compression is prediction' to 'compression is routing'.", Write(title), run_time=2)
        self.say("The author frames this as a starting point, and invites labs with more compute to push it further.",
                 FadeIn(info, shift=UP * 0.2))
        self.say("The paper and everything else are in the repo linked below. Thanks for watching.",
                 Circumscribe(repo, color=YELLOW))
        self.wait(1.0)
        self.clear_all(run_time=1.2)


SCENES = [E00_Hook, E01_Title, E02_Problem, E03_Compression, E04_Architecture, E05_Metric,
          E06_Results, E07_Geometry, E08_Routing, E09_Memory, E10_Limits, E11_Outro]

CHAPTERS = {
    "E00_Hook": "Intro",
    "E02_Problem": "Why LLMs forget (and why MoE routing is hard)",
    "E03_Compression": "Compression is intelligence",
    "E04_Architecture": "A 64× Transformer autoencoder",
    "E05_Metric": "Measuring reconstruction",
    "E06_Results": "The three-step cliff: 99.47% / 47.76% / 0.57%",
    "E07_Geometry": "Inside the latent space",
    "E08_Routing": "Compression is routing (and forgetting)",
    "E09_Memory": "Bonus: 64× less memory",
    "E10_Limits": "Limitations and open questions",
    "E11_Outro": "Wrap-up",
}


class Thumbnail(Scene):
    """YouTube thumbnail (render with -s). Not part of SCENES."""

    def construct(self):
        a = Text("NO ROUTER.", font=SANS, weight=BOLD, font_size=96)
        b = Text("NO FORGETTING?", font=SANS, weight=BOLD, font_size=96, color=YELLOW)
        c = Text("Compression Is Routing", font=SERIF, font_size=44, color=GREY_B)
        left = VGroup(a, b, c).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        fit(left, 7.0).to_edge(LEFT, buff=0.6).shift(UP * 0.4)
        base_y, H = -2.6, 5.4
        bars = VGroup()
        for i, (v, col, name) in enumerate([(99.47, CODE_C, "code"), (47.76, WIKI_C, "wiki"),
                                            (0.57, RAND_C, "noise")]):
            x = 2.4 + i * 1.75
            h = max(v / 100 * H, 0.06)
            r = Rectangle(width=1.35, height=h, fill_color=col, fill_opacity=0.95, stroke_width=0)
            r.move_to([x, base_y + h / 2, 0])
            num = Text(f"{v}%", font=SANS, weight=BOLD, font_size=34, color=col).next_to(r, UP, buff=0.12)
            lab = Text(name, font=SANS, font_size=30, color=GREY_A).next_to([x, base_y, 0], DOWN, buff=0.15)
            bars.add(VGroup(r, num, lab))
        axis = Line([1.4, base_y, 0], [6.9, base_y, 0], color=GREY_B)
        self.add(left, axis, bars)
