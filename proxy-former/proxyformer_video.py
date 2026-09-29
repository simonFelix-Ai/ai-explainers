"""
ProxyFormer -- a 3Blue1Brown-style explainer (Manim Community), bilingual.

Paper: ProxyFormer: A Dual-Stream Proxy Architecture for Ultra-Long Context and
       High-Resolution Generation (Zhongpan Tang, arXiv:2608.23463)

Every on-screen string and narration line is written as tr(chinese, english);
PF_LANG=zh|en selects the language. Narration is burned in as subtitles and
exported per scene as JSON cues, merged into an SRT by build.sh.
"""

import json
import os
import textwrap

import numpy as np
from manim import *

LANG = os.environ.get("PF_LANG", "zh")
CUE_DIR = os.path.join(os.environ.get("CUE_DIR", os.path.join(os.path.dirname(__file__), "build", "cues")), LANG)

CJK = "Noto Sans CJK SC"
SERIF = "Latin Modern Roman"
MONO = "DejaVu Sans Mono"

LOCAL_C = BLUE_C
PROXY_C = YELLOW
BASE_C = GREY_B
BAD_C = RED_C
GOOD_C = GREEN_C


def tr(zh, en):
    return zh if LANG == "zh" else en


def T(s, size=36, color=WHITE, **kw):
    return Text(s, font=CJK if LANG == "zh" else SERIF, font_size=size, color=color, **kw)


def fit(mob, width):
    if mob.width > width:
        mob.scale_to_fit_width(width)
    return mob


def wrap(text):
    if LANG == "en":
        return textwrap.fill(text, 64)
    if len(text) <= 26:
        return text
    mid, best = len(text) // 2, None
    for i, ch in enumerate(text):
        if ch in "，。；：、？！" and 0 < i < len(text) - 1:
            if best is None or abs(i - mid) < abs(best - mid):
                best = i
    best = mid - 1 if best is None else best
    return text[: best + 1] + "\n" + text[best + 1:]


def make_sub(text):
    t = Text(wrap(text), font=CJK, font_size=26, color=GREY_A, line_spacing=0.8)
    fit(t, 12.5).to_edge(DOWN, buff=0.3)
    return VGroup(BackgroundRectangle(t, color=BLACK, fill_opacity=0.75, buff=0.12), t)


class Base(Scene):
    """Scene with narrated subtitles: self.say(text, *animations)."""

    def setup(self):
        self.sub = None
        self.cues = []

    def read_time(self, text):
        per_char = 0.2 if LANG == "zh" else 0.066
        return max(1.8, per_char * len(text) + 0.6)

    def say(self, text, *anims, run_time=None, dur=None, show=True):
        dur = dur if dur is not None else self.read_time(text)
        t0 = self.renderer.time
        self.hide_sub()
        if show:
            self.sub = make_sub(text)
            self.add_foreground_mobject(self.sub)
        if anims:
            self.play(*anims, run_time=run_time or 1.5)
        rest = dur - (self.renderer.time - t0)
        if rest > 0.05:
            self.wait(rest)
        self.cues.append([t0, self.renderer.time, text])

    def hide_sub(self):
        if self.sub is not None:
            self.remove_foreground_mobject(self.sub)
            self.remove(self.sub)
            self.sub = None

    def clear_all(self, run_time=0.8):
        self.hide_sub()
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=run_time)

    def tear_down(self):
        os.makedirs(CUE_DIR, exist_ok=True)
        with open(os.path.join(CUE_DIR, f"{type(self).__name__}.json"), "w", encoding="utf-8") as f:
            json.dump({"duration": self.renderer.time, "cues": self.cues}, f, ensure_ascii=False, indent=1)


def heat_color(v):
    """Approximation of matplotlib's RdYlGn used in the paper's NIAH heatmaps."""
    stops = [(0.0, "#a50026"), (0.25, "#f46d43"), (0.5, "#ffffbf"), (0.75, "#a6d96a"),
             (0.9, "#1a9850"), (1.0, "#006837")]
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        if v <= b:
            return interpolate_color(ManimColor(ca), ManimColor(cb), (v - a) / (b - a))
    return ManimColor(stops[-1][1])


def token_row(n, color=LOCAL_C, size=0.22, buff=0.06):
    return VGroup(*[Square(size, stroke_width=1, stroke_color=color, fill_color=color, fill_opacity=0.6)
                    for _ in range(n)]).arrange(RIGHT, buff=buff)


# NIAH accuracy from the paper (trained on a 64K window); rows = needle depth 0..90%,
# columns = haystack length 4K..1M.
NIAH_64K = [
    [.93, .98, .99, .99, 1.00, 1.00, 1.00, .99, .94],
    [.94, .98, .99, 1.00, 1.00, 1.00, 1.00, .99, .95],
    [.93, .98, .99, 1.00, 1.00, 1.00, 1.00, .98, .94],
    [.95, .98, .99, .99, 1.00, 1.00, 1.00, .99, .92],
    [.89, .98, .99, .99, 1.00, 1.00, 1.00, 1.00, .95],
    [.89, .98, 1.00, 1.00, .99, 1.00, 1.00, .98, .94],
    [.92, .97, .99, 1.00, 1.00, 1.00, 1.00, .99, .92],
    [.93, .98, 1.00, 1.00, 1.00, 1.00, .99, .98, .93],
    [.93, .98, 1.00, 1.00, 1.00, 1.00, 1.00, .99, .93],
    [.94, .99, 1.00, 1.00, 1.00, 1.00, 1.00, .99, .93],
]
LENGTHS = ["4K", "8K", "16K", "32K", "64K", "128K", "256K", "512K", "1M"]


# ================================================================ scenes

class P00_Hook(Base):
    """Cold open: same GPU, 20K tokens vs 700K tokens, then a million-token haystack."""

    def construct(self):
        W = 11.0
        top = T(tr("同一块显卡 · 同样 16 GB 显存", "Same GPU. Same 16 GB."), 48).to_edge(UP, buff=0.6)
        gpu = RoundedRectangle(corner_radius=0.12, width=W + 0.2, height=1.3, stroke_color=GREY_B)
        gpu.shift(UP * 0.6)
        cap = T("16 GB", 26, GREY_B).next_to(gpu, UR, buff=0.1).shift(LEFT * 1.0 + DOWN * 0.05)
        left = gpu.get_left() + RIGHT * 0.1
        # Start mid-fill so the very first frame already shows a loaded GPU.
        gb = ValueTracker(5.0)
        tok = ValueTracker(6700.0)
        color = [LOCAL_C]

        bar = always_redraw(lambda: Rectangle(
            width=max(gb.get_value() / 16 * W, 0.001), height=1.1, stroke_width=0,
            fill_color=color[0], fill_opacity=0.85).move_to(left, aligned_edge=LEFT))
        counter = always_redraw(lambda: VGroup(
            Integer(int(tok.get_value()), font_size=56, color=color[0]),
            T(tr(" 个 token", " tokens"), 40, color[0])).arrange(RIGHT, buff=0.15).next_to(gpu, DOWN, buff=0.5))
        name = T(tr("普通 Transformer", "Standard Transformer"), 34, LOCAL_C).next_to(gpu, DOWN, buff=1.4)
        # Frame one already has content, and motion starts immediately.
        self.add(top, gpu, cap, bar, counter, name)
        self.say(tr("同一块 16G 显卡，普通 Transformer：两万 token，显存就满了。",
                    "Same 16-gig GPU. A standard Transformer: about 20K tokens, and it's full."),
                 gb.animate.set_value(15.6), tok.animate.set_value(20992), run_time=1.4, dur=1.5, show=False)
        color[0] = BAD_C
        oom = Text("OUT OF MEMORY", font=CJK, weight=BOLD, font_size=60, color=WHITE).move_to(gpu)
        self.play(FadeIn(oom, scale=1.4), Flash(gpu.get_right(), color=BAD_C, flash_radius=0.6), run_time=0.4)
        self.wait(0.3)

        color[0] = PROXY_C
        name2 = T("ProxyFormer", 38, PROXY_C).move_to(name)
        self.play(FadeOut(oom), FadeTransform(name, name2), gb.animate.set_value(2.9), run_time=0.4)
        self.say(tr("ProxyFormer：七十万。", "ProxyFormer: seven hundred thousand."),
                 gb.animate.set_value(15.1), tok.animate.set_value(716800),
                 run_time=1.3, dur=1.7, show=False)
        x35 = T("35×", 72, PROXY_C).next_to(counter, RIGHT, buff=0.5)
        self.play(FadeIn(x35, scale=1.6), run_time=0.3)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.25)

        same = T(tr("同样 2.1 万 token 的历史", "Same 21K-token history"), 44, GREY_A).to_edge(UP, buff=1.0)
        mem_l = T(tr("显存", "Memory"), 48)
        spd_l = T(tr("速度", "Speed"), 48)
        mem_a = T("15.6 GB", 72, BASE_C)
        spd_a = T("1.3 it/s", 72, BASE_C)
        mem_b = T("2.9 GB", 72, PROXY_C)
        spd_b = T("16.1 it/s", 72, PROXY_C)
        mem_x = T("1/5", 64, GOOD_C)
        spd_x = T("12×", 64, GOOD_C)
        for lab, val, y in ((mem_l, mem_a, 0.5), (spd_l, spd_a, -1.0)):
            lab.move_to([-3.6, y, 0])
            val.move_to([0.4, y, 0])
        mem_b.move_to(mem_a)
        spd_b.move_to(spd_a)
        mem_x.move_to([3.9, 0.5, 0])
        spd_x.move_to([3.9, -1.0, 0])
        self.add(same, mem_l, spd_l, mem_a, spd_a)
        self.say(tr("同样的长度：显存只要五分之一，速度快 12 倍。",
                    "Same length: one-fifth the memory, twelve times the speed."),
                 Transform(mem_a, mem_b), Transform(spd_a, spd_b), FadeIn(mem_x, scale=1.6), FadeIn(spd_x, scale=1.6),
                 run_time=0.9, dur=2.1, show=False)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.25)

        title = Text("ProxyFormer", font=SERIF, font_size=100)
        how = T(tr("它是怎么做到的？", "How?"), 48, YELLOW).next_to(title, DOWN, buff=0.5)
        self.say(tr("它是怎么做到的？", "How?"), FadeIn(title, scale=1.1), Write(how),
                 run_time=0.7, dur=1.8, show=False)
        self.play(FadeOut(VGroup(title, how)), run_time=0.4)


class P01_Title(Base):
    def construct(self):
        title = Text("ProxyFormer", font=SERIF, font_size=84)
        sub = fit(T(tr("用极短的「代理 Token」承载全局交互", "Carry global interaction with a handful of proxy tokens"),
                    34, BLUE_B), 12)
        paper = Text("arXiv:2608.23463 · Zhongpan Tang", font=SERIF, font_size=26, color=GREY_B)
        line = Line(LEFT * 4, RIGHT * 4, color=BLUE_D)
        VGroup(title, line, sub, paper).arrange(DOWN, buff=0.35)
        self.say(tr("这是 ProxyFormer，一个面向超长上下文和高分辨率生成的新架构。",
                    "This is ProxyFormer, a new architecture for ultra-long context and high-resolution generation."),
                 Write(title), Create(line), run_time=1.6)
        self.say(tr("它的核心，是用极少的「代理 Token」，来承载全局的信息交互。",
                    "Its core idea: let a tiny set of 'proxy tokens' carry all the global interaction."),
                 FadeIn(sub, shift=UP * 0.2), FadeIn(paper))
        self.clear_all()

        prev = T(tr("前作：压缩即路由", "Previous work: Compression Is Routing"), 36, GREY_A).to_edge(UP, buff=0.8)
        grid = VGroup(*[Square(0.1, stroke_width=0.4, stroke_color=BLUE_A, fill_color=BLUE, fill_opacity=0.65)
                        for _ in range(512)]).arrange_in_grid(rows=16, cols=32, buff=0.02)
        z = VGroup(*[Rectangle(width=0.16, height=1.0, stroke_width=1, stroke_color=YELLOW_A,
                               fill_color=interpolate_color(YELLOW_D, ORANGE, i / 7), fill_opacity=0.9)
                     for i in range(8)]).arrange(RIGHT, buff=0.07)
        VGroup(grid, z).arrange(RIGHT, buff=2.0).shift(UP * 1.0)
        arr = Arrow(grid.get_right(), z.get_left(), buff=0.2)
        l1 = T(tr("512 个 token", "512 tokens"), 26, BLUE_B).next_to(grid, DOWN)
        l2 = T(tr("8 个向量", "8 vectors"), 26, YELLOW).next_to(z, DOWN)
        acc = T(tr("还原准确率 99.47%", "99.47% reconstructed"), 30, GOOD_C).next_to(VGroup(l1, l2), DOWN, buff=0.35)
        self.say(tr("在上一个工作里，我们发现：512 个 token 可以被压成 8 个向量，几乎无损地还原。",
                    "In earlier work, 512 tokens were squeezed into 8 vectors and rebuilt almost losslessly."),
                 FadeIn(prev), FadeIn(grid), GrowArrow(arr), FadeIn(z), FadeIn(l1), FadeIn(l2), FadeIn(acc))
        q = fit(T(tr("既然序列能被几乎无损地压缩，为什么还要让注意力在原始长序列上计算？",
                     "If a sequence compresses almost losslessly, why run attention on the uncompressed one?"),
                  32, YELLOW), 12.5).to_edge(DOWN, buff=1.5)
        self.say(tr("那一个自然的问题就是：为什么还要让昂贵的注意力，在原始长序列上计算？",
                    "So the natural question: why let expensive attention run on the raw, uncompressed sequence?"),
                 Write(q), run_time=1.8)
        self.clear_all()


class P02_Problem(Base):
    def construct(self):
        header = T(tr("长上下文，贵在哪里？", "Why is long context so expensive?"), 44).to_edge(UP, buff=0.5)
        self.say(tr("先看问题：长上下文到底贵在哪？", "First, the problem. What makes long context expensive?"),
                 FadeIn(header))

        def grid(n, side=3.2):
            s = side / n
            return VGroup(*[Square(s, stroke_width=0.6, stroke_color=BLUE_E, fill_color=BLUE_D, fill_opacity=0.55)
                            for _ in range(n * n)]).arrange_in_grid(n, n, buff=0)

        g8 = grid(8).shift(LEFT * 3 + DOWN * 0.3)
        l8 = MathTex(r"N = 8 \;\Rightarrow\; 64", font_size=40).next_to(g8, DOWN)
        self.say(tr("注意力机制里，每个 token 都要和其他所有 token 打交道。8 个 token，就是 64 对。",
                    "In attention, every token talks to every other token. Eight tokens means 64 pairs."),
                 LaggedStartMap(FadeIn, g8, lag_ratio=0.01), Write(l8))
        g16 = grid(16).shift(RIGHT * 3 + DOWN * 0.3)
        l16 = MathTex(r"N = 16 \;\Rightarrow\; 256", font_size=40).next_to(g16, DOWN)
        self.say(tr("长度翻一倍，计算量翻四倍。这就是平方增长。",
                    "Double the length and the work quadruples. That's quadratic growth."),
                 LaggedStartMap(FadeIn, g16, lag_ratio=0.003), Write(l16))
        big = MathTex(r"N = 10^6 \;\Rightarrow\; 10^{12}\ \text{pairs}", font_size=56, color=BAD_C)
        self.play(FadeOut(VGroup(g8, l8, g16, l16)))
        self.say(tr("到一百万 token，就是一万亿对。", "At a million tokens, that's a trillion pairs."), Write(big))
        self.play(big.animate.scale(0.7).shift(UP * 1.4))

        kv = Rectangle(width=0.4, height=0.5, fill_color=BAD_C, fill_opacity=0.8, stroke_width=0)
        kv.move_to(LEFT * 5.5 + DOWN * 1.0, aligned_edge=LEFT)
        kv_l = T(tr("KV Cache：随长度线性增长", "KV cache: grows linearly with length"), 28, BAD_C).next_to(kv, UP,
                                                                                                    aligned_edge=LEFT)
        self.say(tr("推理时的 KV Cache 也随长度线性膨胀，显存很快就被吃光。",
                    "And at inference the KV cache grows linearly, eating GPU memory fast."),
                 FadeIn(kv_l), kv.animate.stretch_to_fit_width(11).align_to(kv, LEFT), run_time=2)
        self.clear_all()


class P03_Proxy(Base):
    def construct(self):
        header = T(tr("核心想法：代理 Token", "The core idea: proxy tokens"), 44).to_edge(UP, buff=0.4)
        self.say(tr("ProxyFormer 的想法，用一个比喻就能说清楚。", "ProxyFormer's idea fits one analogy."),
                 FadeIn(header))
        meet = fit(T(tr("一万人的大会：不可能人人互相交谈", "A 10,000-person conference: not everyone can talk to everyone"),
                     30, GREY_A), 12.5).next_to(header, DOWN, buff=0.3)
        self.say(tr("想象一个一万人的大会，不可能每个人都和每个人交谈。",
                    "Picture a ten-thousand-person conference. Everyone can't talk to everyone."), FadeIn(meet))

        n, k = 24, 6
        toks = VGroup(*[Dot(radius=0.09, color=LOCAL_C) for _ in range(n)]).arrange(RIGHT, buff=0.36)
        toks.move_to(DOWN * 1.9)
        arcs = VGroup(*[ArcBetweenPoints(toks[i].get_center(), toks[j].get_center(), angle=-PI / 2,
                                         stroke_width=0.6, stroke_opacity=0.35, color=BLUE_B)
                        for i in range(n) for j in range(i + 1, n)])
        pairs = MathTex(r"\binom{24}{2} = 276", font_size=40, color=BLUE_B).to_corner(UR, buff=0.5).shift(DOWN * 1.2)
        self.play(LaggedStartMap(FadeIn, toks, lag_ratio=0.03), run_time=0.8)
        self.say(tr("全员互相交谈：24 个人就有 276 条连线。", "All-to-all: 24 people already means 276 conversations."),
                 Create(arcs, lag_ratio=0.002), Write(pairs), run_time=2)
        self.play(FadeOut(arcs), run_time=0.6)

        groups = [VGroup(*toks[i * k:(i + 1) * k]) for i in range(n // k)]
        braces = VGroup(*[Brace(g, DOWN, buff=0.1, color=GREY_B) for g in groups])
        proxies = VGroup(*[Dot(radius=0.2, color=PROXY_C).move_to(g.get_center() + UP * 2.1) for g in groups])
        up = VGroup(*[Line(t.get_center(), p.get_center(), stroke_width=1.5, color=PROXY_C, stroke_opacity=0.6)
                      for g, p in zip(groups, proxies) for t in g])
        self.say(tr("更好的办法：每桌选一个代表。", "Better: each table sends one representative."),
                 GrowFromCenter(braces), run_time=1.0)
        self.say(tr("代表先听取本桌所有人的意见——这就是压缩。",
                    "The rep first listens to everyone at the table. That's compression."),
                 Create(up, lag_ratio=0.02), LaggedStartMap(GrowFromCenter, proxies, lag_ratio=0.2), run_time=1.8)
        links = VGroup(*[ArcBetweenPoints(proxies[i].get_center(), proxies[j].get_center(), angle=-PI / 3,
                                          color=PROXY_C, stroke_width=3)
                         for i in range(4) for j in range(i + 1, 4)])
        pairs2 = MathTex(r"\binom{4}{2} = 6", font_size=40, color=PROXY_C).move_to(pairs)
        self.say(tr("然后只有代表之间开会交流——只需要 6 条连线。",
                    "Then only the reps meet with each other. Just six conversations."),
                 Create(links), Transform(pairs, pairs2), run_time=1.5)
        down = VGroup(*[DashedLine(p.get_center(), t.get_center(), stroke_width=1.5, color=PROXY_C, dash_length=0.08)
                        for g, p in zip(groups, proxies) for t in g])
        self.say(tr("最后，代表回到本桌，把全局的消息带回来——这就是解压与注入。",
                    "Finally each rep goes back and shares the global picture. That's decompression and injection."),
                 FadeOut(up), Create(down, lag_ratio=0.02),
                 toks.animate.set_color(interpolate_color(LOCAL_C, PROXY_C, 0.45)), run_time=1.8)
        self.clear_all()

        f1 = MathTex(r"\text{compute} \;\propto\; \left(\tfrac{N}{r}\right)^2", font_size=54)
        f2 = MathTex(r"\text{memory} \;\propto\; \tfrac{N}{r}", font_size=54)
        f3 = MathTex(r"r = 64:\quad \tfrac{1}{4096}\ \text{attention},\quad \tfrac{1}{64}\ \text{memory}",
                     font_size=44, color=YELLOW)
        VGroup(f1, f2, f3).arrange(DOWN, buff=0.6)
        self.say(tr("每 r 个 token 压成一个代理，全局注意力的计算就降到 r 平方分之一，",
                    "Compress every r tokens into one proxy, and global attention drops to one over r squared,"),
                 Write(f1))
        self.say(tr("和长度相关的显存降到 r 分之一。", "and length-dependent memory drops to one over r."), Write(f2))
        self.say(tr("压缩比 64 时，注意力只剩四千分之一。", "At a ratio of 64, attention costs one four-thousandth."),
                 Write(f3))
        self.clear_all()


class P04_DualStream(Base):
    def construct(self):
        header = T(tr("关键：双流，而不是一次性压缩", "The key: two streams, not one-shot compression"), 40).to_edge(UP,
                                                                                                        buff=0.4)
        self.say(tr("但压缩总会丢信息，不是吗？", "But compression always loses something, right?"), FadeIn(header))

        # One-shot compression: what is lost stays lost.
        row = token_row(12, size=0.2, buff=0.05).move_to([-4.6, -1.2, 0])
        p = Dot(radius=0.18, color=PROXY_C).move_to(row.get_center() + UP * 1.4)
        out = token_row(12, size=0.2, buff=0.05).move_to([-4.6, 1.6, 0])
        for i in [2, 5, 6, 10]:
            out[i].set_fill(GREY_D, 0.6).set_stroke(GREY_C)
        a1 = Arrow(row.get_top(), p.get_bottom(), buff=0.1)
        a2 = Arrow(p.get_top(), out.get_bottom(), buff=0.1)
        lab = fit(T(tr("一次性压缩：丢了就找不回", "One-shot: what's lost is gone"), 26, BAD_C), 3.8).next_to(out, UP)
        self.say(tr("如果只压缩一次，丢掉的细节就永远丢了。", "Compress once, and whatever got dropped is gone for good."),
                 FadeIn(row), GrowArrow(a1), FadeIn(p), GrowArrow(a2), FadeIn(out), FadeIn(lab))

        # Dual stream: local stream persists through every layer.
        xs = 0.4
        rows = [token_row(12, size=0.2, buff=0.05).move_to([xs, y, 0]) for y in (-2.0, -0.7, 0.6, 1.9)]
        self.say(tr("ProxyFormer 的做法不同：原始的局部流，在每一层都保留着。",
                    "ProxyFormer does it differently: the fine-grained local stream is kept at every layer."),
                 FadeIn(rows[0]))
        notes = VGroup(T(tr("① 局部 → 代理（自下而上）", "① local → proxy (bottom-up)"), 22, PROXY_C),
                       T(tr("② 代理之间全局交互", "② proxies interact globally"), 22, PROXY_C),
                       T(tr("③ 代理 → 局部（自上而下注入）", "③ proxy → local (top-down)"), 22, PROXY_C),
                       T(tr("④ 局部流直通下一层", "④ local stream carries on"), 22, LOCAL_C)
                       ).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
        fit(notes, 4.4).move_to([4.75, 0.0, 0])
        for li in range(3):
            lo, hi = rows[li], rows[li + 1]
            mid_y = (lo.get_center()[1] + hi.get_center()[1]) / 2
            prox = VGroup(*[Dot(radius=0.12, color=PROXY_C).move_to([VGroup(*lo[i * 6:(i + 1) * 6]).get_center()[0],
                                                                      mid_y, 0]) for i in range(2)])
            ups = VGroup(*[Line(lo[i].get_top(), prox[i // 6].get_center(), stroke_width=1, color=PROXY_C)
                           for i in range(12)])
            link = Line(prox[0].get_center(), prox[1].get_center(), color=PROXY_C, stroke_width=4)
            downs = VGroup(*[DashedLine(prox[i // 6].get_center(), hi[i].get_bottom(), stroke_width=1, color=PROXY_C,
                                        dash_length=0.05) for i in range(12)])
            skip = VGroup(*[Line(lo[i].get_top(), hi[i].get_bottom(), stroke_width=1.2, color=LOCAL_C,
                                 stroke_opacity=0.5) for i in range(12)])
            hi.set_color(interpolate_color(LOCAL_C, PROXY_C, 0.15 * (li + 1)))
            if li == 0:
                self.say(tr("每一层：局部特征先汇聚成代理——「微观指导宏观」；",
                            "Each layer: local features condense into proxies, micro guiding macro;"),
                         Create(ups), FadeIn(prox), FadeIn(notes[0]))
                self.say(tr("代理之间做全局交互；", "the proxies interact globally;"), Create(link), FadeIn(notes[1]))
                self.say(tr("再把全局视野解压、注入回局部——「宏观指导微观」。",
                            "then the global view is decompressed back into the local stream, macro guiding micro."),
                         Create(downs), FadeIn(notes[2]))
                self.say(tr("同时，局部流本身直通下一层。", "Meanwhile the local stream itself flows on to the next layer."),
                         Create(skip), FadeIn(hi), FadeIn(notes[3]))
            else:
                self.play(Create(ups), FadeIn(prox), run_time=0.5)
                self.play(Create(link), run_time=0.3)
                self.play(Create(downs), Create(skip), FadeIn(hi), run_time=0.6)
        self.say(tr("所以某一层没抓住的细节，下一层还能继续提取——避免了一次性压缩不可逆的信息损失。",
                    "So detail missed by one compression step is still there for the next layer to pick up."),
                 Indicate(rows[3], color=WHITE))
        self.clear_all()


class P05_Engineering(Base):
    def construct(self):
        header = T(tr("让它真正可用的几个设计", "Design details that make it practical"), 40).to_edge(UP, buff=0.4)
        self.say(tr("为了把压缩比推得更高，还有几个关键设计。",
                    "A few more design choices push the compression ratio further."), FadeIn(header))

        # Multi-level cascade: 64 -> 16 -> 4 -> 1
        levels = VGroup()
        for n, c in [(64, LOCAL_C), (16, TEAL_C), (4, GREEN_C), (1, PROXY_C)]:
            s = 0.075 if n == 64 else (0.3 if n == 16 else (0.6 if n == 4 else 0.9))
            levels.add(VGroup(*[Square(s, stroke_width=0.5, fill_color=c, fill_opacity=0.8, stroke_color=c)
                                for _ in range(n)]).arrange(RIGHT, buff=0.02))
        levels.arrange(UP, buff=0.45).move_to([-3.3, -0.2, 0])
        eq = MathTex(r"P = k_1 k_2 k_3 = 4 \cdot 4 \cdot 4 = 64", font_size=40)
        lab = T(tr("多级级联压缩", "Multi-level cascaded compression"), 28, GREY_A)
        dyn = T(tr("每一层、每段历史\n都可以用不同压缩比", "Each layer, and each stretch of\nhistory, can use its own ratio"),
                26, GREY_B)
        side = VGroup(lab, eq, dyn).arrange(DOWN, buff=0.45)
        fit(side, 5.8).move_to([3.6, -0.1, 0])
        self.say(tr("一是多级级联：不是一步压 64 倍，而是 4 乘 4 乘 4，逐级压缩，再对称地逐级解压。",
                    "First, cascades: instead of 64x in one jump, compress 4x three times, then decompress symmetrically."),
                 LaggedStart(*[FadeIn(l, shift=UP * 0.2) for l in levels], lag_ratio=0.35), Write(eq), FadeIn(lab),
                 run_time=2)
        self.say(tr("而且不同层、不同远近的历史，可以用不同的压缩比。",
                    "And different layers, or older history, can use different ratios."), FadeIn(dyn))
        self.clear_all()

        header = T(tr("代理 KV Cache", "Proxy KV cache"), 40).to_edge(UP, buff=0.4)
        hist = Rectangle(width=10, height=0.5, fill_color=BASE_C, fill_opacity=0.3, stroke_color=BASE_C)
        hist.move_to(UP * 1.6 + LEFT * 1)
        hl = T(tr("完整历史：L 个 token", "Full history: L tokens"), 26, BASE_C).next_to(hist, UP)
        pc = Rectangle(width=10 / 64, height=0.5, fill_color=PROXY_C, fill_opacity=0.95, stroke_width=0)
        pc.align_to(hist, LEFT).set_y(0.0)
        pl = T(tr("代理 KV Cache：L / P", "Proxy KV cache: L / P"), 26, PROXY_C).next_to(pc, UP, buff=0.15,
                                                                                     aligned_edge=LEFT)
        new = RoundedRectangle(corner_radius=0.1, width=1.6, height=0.8, color=WHITE).move_to(RIGHT * 5.3)
        nl = T(tr("新 token", "new token"), 24).move_to(new)
        att = Arrow(new.get_left(), pc.get_right(), buff=0.1, color=PROXY_C)
        self.say(tr("二是代理 KV Cache。生成新 token 时，不再回看全部历史，",
                    "Second, the proxy KV cache. When generating, a new token doesn't look back at the whole history;"),
                 FadeIn(header), FadeIn(hist), FadeIn(hl))
        self.say(tr("只需要和极短的代理缓存交互，显存和延迟都大幅下降。",
                    "it only attends to a tiny cache of proxies, cutting memory and latency."),
                 FadeIn(pc), FadeIn(pl), FadeIn(new), FadeIn(nl), Create(att))
        emb = fit(T(tr("三：非对称嵌入——历史用小维度（如 64），当前输入用大维度（如 512）",
                       "Third: asymmetric embeddings. History uses a small width (e.g. 64), the current input a large one (512)"),
                    26, GREY_A), 12.5).move_to(DOWN * 1.5)
        self.say(tr("三是非对称嵌入：历史部分从第一层起就用更小的维度，显存从源头就开始省。",
                    "Third, asymmetric embeddings: history starts in a narrower space, so savings begin at layer one."),
                 FadeIn(emb))
        self.clear_all()

        header = T(tr("实现极其简单", "Remarkably simple to implement"), 40).to_edge(UP, buff=0.5)
        ops = VGroup(*[T(s, 30) for s in [
            tr("• 切块与压缩：reshape / Linear / Conv", "• Chunk & compress: reshape / Linear / Conv"),
            tr("• 代理交互：标准注意力（SDPA），也可换成 SSM", "• Proxy interaction: standard attention (SDPA), or an SSM"),
            tr("• 解压与注入：Linear / ConvTranspose", "• Decompress & inject: Linear / ConvTranspose"),
            tr("• 不需要稀疏索引，不需要自定义 CUDA 核", "• No sparse indexers, no custom CUDA kernels"),
        ]]).arrange(DOWN, aligned_edge=LEFT, buff=0.4)
        ops[3].set_color(GOOD_C)
        self.say(tr("而这一切，只用最常见的深度学习算子就能实现，", "And all of it uses the most common deep-learning operators,"),
                 FadeIn(header), LaggedStartMap(FadeIn, ops[:3], shift=RIGHT * 0.2, lag_ratio=0.3), run_time=2)
        self.say(tr("不需要稀疏索引，也不需要手写 CUDA 算子，容易复现，也容易部署。",
                    "with no sparse indexers or hand-written CUDA kernels. Easy to reproduce and deploy."),
                 FadeIn(ops[3], shift=RIGHT * 0.2))
        self.clear_all()


class P06_SpaceToChannel(Base):
    def construct(self):
        header = T(tr("空间换通道：越压越强", "Space-to-channel: compress harder, get stronger"), 40).to_edge(UP, buff=0.4)
        self.say(tr("还有一个很漂亮的性质，借鉴自图像 VAE 的经验。",
                    "There's also an elegant property, borrowed from image VAEs."), FadeIn(header))
        base = Rectangle(width=6, height=0.8, fill_color=PROXY_C, fill_opacity=0.5, stroke_color=PROXY_C)
        base.shift(UP * 0.4)
        wl = T(tr("序列长度", "sequence length"), 24, GREY_A).next_to(base, DOWN)
        hl = T(tr("通道宽度", "channel width"), 24, GREY_A).rotate(PI / 2).next_to(base, LEFT)
        wl.add_updater(lambda m: m.next_to(base, DOWN))
        hl.add_updater(lambda m: m.next_to(base, LEFT))
        self.play(FadeIn(base), FadeIn(wl), FadeIn(hl))
        f = MathTex(r"\text{cost} \propto (\text{length})^2 \times \text{width}", font_size=40).to_edge(DOWN, buff=1.6)
        self.say(tr("把压缩比再提高 α 倍，代理序列就缩短 α 倍，注意力开销降到 α 平方分之一。",
                    "Raise the compression ratio by alpha: proxies get alpha times shorter, attention drops by alpha squared."),
                 base.animate.stretch_to_fit_width(1.5), Write(f), run_time=1.8)
        self.say(tr("省下的算力，可以投到通道上：把每个代理加宽 β 倍。",
                    "Reinvest the savings into channels: make each proxy beta times wider."),
                 base.animate.stretch_to_fit_height(3.0).shift(UP * 0.8), run_time=1.8)
        f2 = MathTex(r"\text{cost} \propto \frac{\beta}{\alpha^2} \;\le\; 1 \quad\text{when}\quad \beta \le \alpha^2",
                     font_size=48, color=YELLOW).move_to(f)
        self.say(tr("只要 β 不超过 α 的平方，总开销不增加，但每个代理能装下更多信息。",
                    "As long as beta stays under alpha squared, the budget doesn't grow, yet each proxy holds more."),
                 Transform(f, f2))
        wl.clear_updaters()
        hl.clear_updaters()
        self.play(FadeOut(VGroup(base, wl, hl, f)))

        nodes = VGroup(T(tr("序列压得更狠", "compress sequence harder"), 28, PROXY_C),
                       T(tr("省下算力", "free up compute"), 28, GOOD_C),
                       T(tr("通道更宽更强", "wider, stronger channels"), 28, LOCAL_C))
        for nd, ang in zip(nodes, [PI / 2, PI / 2 + 2 * PI / 3, PI / 2 + 4 * PI / 3]):
            nd.move_to(2.0 * np.array([np.cos(ang), np.sin(ang), 0]) + DOWN * 0.2)
        arrows = VGroup(*[CurvedArrow(nodes[i].get_center(), nodes[(i + 1) % 3].get_center(), angle=-TAU / 6,
                                      color=GREY_B) for i in range(3)])
        for a in arrows:
            a.scale(0.6)
        self.say(tr("这就形成了一个正循环：压得越狠，省得越多；通道越强，又能支撑更高的压缩比。",
                    "A virtuous cycle: compress harder, save more; stronger channels then support even higher ratios."),
                 LaggedStartMap(FadeIn, nodes, lag_ratio=0.3), LaggedStart(*[Create(a) for a in arrows], lag_ratio=0.3), run_time=2.5)
        self.clear_all()


class P07_Memory(Base):
    def construct(self):
        header = T(tr("实验一：显存与速度", "Result 1: memory and speed"), 40).to_edge(UP, buff=0.4)
        cond = T(tr("单卡 16 GB · batch size 1", "one 16 GB GPU · batch size 1"), 24, GREY_B).next_to(header, DOWN)
        self.say(tr("来看实验。第一组：一块 16G 显卡，batch size 为 1。",
                    "Now the experiments. First: a single 16 GB GPU, batch size one."), FadeIn(header), FadeIn(cond))
        W = 7.0
        rows_spec = [
            (tr("全注意力基线", "Full-attention baseline"), "20,992", 15.6, "1.3 it/s", BASE_C),
            ("ProxyFormer (r=64)", "20,992", 2.9, "16.1 it/s", PROXY_C),
            ("ProxyFormer (r=64)", "716,800", 15.1, "2.7 it/s", PROXY_C),
        ]
        rows = VGroup()
        for name, toks, gb, speed, c in rows_spec:
            lab = VGroup(T(name, 26, c), T(tr(f"历史 {toks} token", f"{toks} tokens of history"), 20, GREY_B)
                         ).arrange(DOWN, aligned_edge=RIGHT, buff=0.05)
            bar = Rectangle(width=gb / 16 * W, height=0.55, fill_color=c, fill_opacity=0.85, stroke_width=0)
            val = T(f"{gb} GB · {speed}", 24, c)
            rows.add(VGroup(lab, bar, val))
        for i, r in enumerate(rows):
            r[0].move_to([-3.6, 1.2 - i * 1.3, 0], aligned_edge=RIGHT)
            r[1].move_to([-3.3, 1.2 - i * 1.3, 0], aligned_edge=LEFT)
            r[2].next_to(r[1], RIGHT, buff=0.2)
        cap = DashedLine([-3.3 + W, 1.8, 0], [-3.3 + W, -1.6, 0], color=BAD_C)
        capl = T("16 GB", 22, BAD_C).next_to(cap, UP, buff=0.05)
        self.play(Create(cap), FadeIn(capl))
        lines = [
            tr("同样两万多 token 的历史：全注意力基线吃掉 15.6G 显存，每秒 1.3 步。",
               "With ~21K tokens of history, full attention uses 15.6 GB at 1.3 steps per second."),
            tr("ProxyFormer 只用 2.9G，速度快了十几倍。", "ProxyFormer uses 2.9 GB, and runs over ten times faster."),
            tr("把显存用满，ProxyFormer 能直接训练 71.7 万 token——可训练长度提升约 35 倍。",
               "Fill the card, and ProxyFormer trains on 716,800 tokens: about 35 times the trainable length."),
        ]
        for r, line in zip(rows, lines):
            self.say(line, FadeIn(r[0]), GrowFromEdge(r[1], LEFT), FadeIn(r[2]), run_time=1.3)
        self.clear_all()


class P08_NIAH(Base):
    def construct(self):
        header = T(tr("实验二：百万 token 大海捞针", "Result 2: needles in a million-token haystack"), 40).to_edge(UP,
                                                                                                            buff=0.3)
        proto = fit(T(tr("每篇随机插入 50 根针 · 逐一提问 · 每个长度 100 轮 = 5000 次检索",
                         "50 needles per document · each queried · 100 rounds per length = 5,000 lookups"),
                      24, GREY_B), 12.5).next_to(header, DOWN, buff=0.15)
        self.say(tr("第二组：多针大海捞针。每篇文档随机藏 50 个密码，逐一提问，每个长度测 5000 次。",
                    "Second: multi-needle retrieval. Fifty passkeys hidden per document, each one queried, 5,000 lookups per length."),
                 FadeIn(header), FadeIn(proto))

        cw, ch = 1.05, 0.4
        cells = VGroup()
        grid = [[None] * 9 for _ in range(10)]
        for r in range(10):
            for c in range(9):
                v = NIAH_64K[r][c]
                sq = Rectangle(width=cw, height=ch, stroke_width=0.8, stroke_color=BLACK,
                               fill_color=heat_color(v), fill_opacity=1)
                txt = Text(f"{v:.2f}", font=MONO, font_size=14, color=WHITE if v > 0.85 else BLACK)
                cell = VGroup(sq, txt)
                cell.move_to([(c - 4) * cw + 0.3, (4.5 - r) * ch - 0.05, 0])
                txt.move_to(sq)
                grid[r][c] = cell
                cells.add(cell)
        xl = VGroup(*[Text(s, font=MONO, font_size=18, color=GREY_A).next_to(grid[9][i], DOWN, buff=0.1)
                      for i, s in enumerate(LENGTHS)])
        yl = VGroup(*[Text(f"{d}%", font=MONO, font_size=16, color=GREY_B).next_to(grid[d // 10][0], LEFT, buff=0.1)
                      for d in range(0, 100, 10)])
        ylab = T(tr("针的深度", "needle depth"), 20, GREY_B).rotate(PI / 2).next_to(yl, LEFT, buff=0.1)
        train = T(tr("训练窗口：64K", "trained on a 64K window"), 22, YELLOW).next_to(cells, UP, buff=0.1).align_to(cells,
                                                                                                          RIGHT)
        self.add(yl, ylab, train)
        cols = [VGroup(*[grid[r][c] for r in range(10)]) for c in range(9)]
        self.say(tr("这比常见的单针测试难得多：每篇 50 根针全部要找，而且测试长度远超训练长度。",
                    "This is much harder than a single-needle test: all 50 needles must be found, "
                    "at lengths far beyond training."), Indicate(proto, color=WHITE))
        self.say(tr("这个模型只用 64K 的窗口训练。",
                    "This model was trained on a 64K window."),
                 LaggedStart(*[AnimationGroup(FadeIn(cols[c], shift=DOWN * 0.1), FadeIn(xl[c])) for c in range(5)],
                             lag_ratio=0.3), run_time=2)
        box1 = SurroundingRectangle(VGroup(cols[5], cols[6]), color=GOOD_C, buff=0.03)
        self.say(tr("推到 128K、256K，也就是训练长度的 4 倍：50 根针几乎全部找回，99% 到 100%。",
                    "Push to 128K and 256K, four times the training length: 99 to 100 percent of the needles found."),
                 LaggedStart(*[AnimationGroup(FadeIn(cols[c], shift=DOWN * 0.1), FadeIn(xl[c])) for c in range(5, 7)],
                             lag_ratio=0.4), Create(box1), run_time=1.6)
        self.say(tr("再往极限推：512K，然后一百万 token，整整 16 倍外推。",
                    "Now push to the limit: 512K, then a million tokens, sixteen times beyond training."),
                 FadeOut(box1),
                 LaggedStart(*[AnimationGroup(FadeIn(cols[c], shift=DOWN * 0.1), FadeIn(xl[c])) for c in range(7, 9)],
                             lag_ratio=0.5), run_time=1.4)
        box = SurroundingRectangle(cols[8], color=YELLOW, buff=0.03)
        self.say(tr("即便如此，每个深度仍保持 92% 到 95%。", "Even there, every depth still holds 92 to 95 percent."),
                 Create(box))
        self.say(tr("而且没有「中间迷失」：开头、中间、结尾，表现一样稳定。",
                    "And no 'lost in the middle': beginning, middle, end, all equally stable."),
                 Indicate(VGroup(*[grid[r][c] for r in (4, 5) for c in range(9)]), color=WHITE, scale_factor=1.03))
        note = fit(T(tr("另一个只用 8K 窗口训练的模型：外推到 256K（32 倍）仍 > 94%；再往上会明显下降",
                        "An 8K-trained model: still >94% at 256K (32×), then it degrades beyond that"),
                     22, YELLOW), 12.5).move_to(proto)
        self.say(tr("另一个只用 8K 训练的模型，外推 32 倍到 256K 依然超过 94%；再往上才会明显下降。",
                    "A model trained on just 8K still tops 94% at 256K, 32 times out; beyond that it degrades."),
                 FadeOut(proto), FadeIn(note))
        self.clear_all()


class P09_Quality(Base):
    def construct(self):
        header = T(tr("实验三：压缩之后，质量掉了吗？", "Result 3: does quality survive compression?"), 40).to_edge(UP, buff=0.5)
        self.say(tr("压缩这么狠，语言建模的质量会不会掉？", "With compression this aggressive, does language modeling suffer?"),
                 FadeIn(header))
        rows = VGroup(
            VGroup(T(tr("全注意力基线（无历史）", "Full-attention baseline (no history)"), 28, BASE_C), T("21.36", 34, BASE_C)),
            VGroup(T(tr("ProxyFormer（无历史）", "ProxyFormer (no history)"), 28, PROXY_C), T("22.10", 34, PROXY_C)),
            VGroup(T(tr("ProxyFormer（压缩历史）", "ProxyFormer (compressed history)"), 28, PROXY_C), T("21.01", 34, GOOD_C)),
        )
        for r in rows:
            r.arrange(RIGHT, buff=0.8)
        rows.arrange(DOWN, buff=0.45, aligned_edge=RIGHT).shift(UP * 0.4)
        ppl = T(tr("WikiText-103 困惑度（越低越好）", "WikiText-103 perplexity (lower is better)"), 24, GREY_B).next_to(rows, UP,
                                                                                                          buff=0.4)
        self.say(tr("在 WikiText-103 上，带压缩历史的 ProxyFormer，困惑度 21.01，与全注意力基线的 21.36 相当甚至略好。",
                    "On WikiText-103, ProxyFormer with compressed history scores 21.01 perplexity, on par with the 21.36 baseline."),
                 FadeIn(ppl), LaggedStartMap(FadeIn, rows, shift=RIGHT * 0.2, lag_ratio=0.3), run_time=2)
        img = fit(T(tr("图像生成（初步）：CIFAR-10 FID 16.21 · MNIST FID 2.06",
                       "Image generation (preliminary): CIFAR-10 FID 16.21 · MNIST FID 2.06"), 26, GREY_A), 12.5)
        img.next_to(rows, DOWN, buff=0.8)
        self.say(tr("图像生成上，像素空间和潜空间的流匹配也都能跑通，验证了可行性。",
                    "Early image-generation runs, in both pixel and latent space, also confirm it works."), FadeIn(img))
        self.clear_all()


class P10_General(Base):
    def construct(self):
        header = T(tr("不只是文本：任意维度通用", "Not just text: any dimension"), 40).to_edge(UP, buff=0.5)
        self.say(tr("同样的「切块、压缩、代理交互、解压」机制，不只适用于文本。",
                    "The same chunk, compress, interact, decompress recipe isn't limited to text."), FadeIn(header))
        # 1D
        r1 = token_row(12, size=0.25, buff=0.04)
        p1 = VGroup(*[Dot(radius=0.12, color=PROXY_C).next_to(VGroup(*r1[i * 4:(i + 1) * 4]), UP, buff=0.35)
                      for i in range(3)])
        g1 = VGroup(r1, p1, T(tr("1D 文本", "1D text"), 26, GREY_A).next_to(r1, DOWN, buff=0.3))
        # 2D
        r2 = VGroup(*[Square(0.3, stroke_width=0.6, fill_color=TEAL_C, fill_opacity=0.6, stroke_color=TEAL_A)
                      for _ in range(36)]).arrange_in_grid(6, 6, buff=0.03)
        p2 = VGroup(*[Dot(radius=0.12, color=PROXY_C).move_to(VGroup(*[r2[(rr + a) * 6 + cc + b] for a in range(3)
                                                                         for b in range(3)]).get_center())
                      for rr in (0, 3) for cc in (0, 3)])
        g2 = VGroup(r2, p2, T(tr("2D 图像", "2D images"), 26, GREY_A).next_to(r2, DOWN, buff=0.3))
        # 3D
        cube = VGroup(*[Cube(side_length=0.5, fill_color=PURPLE_B, fill_opacity=0.35, stroke_width=0.8,
                             stroke_color=PURPLE_A).shift(np.array([i, j, k]) * 0.55)
                        for i in range(3) for j in range(3) for k in range(3)])
        cube.rotate(-PI / 6, axis=UP).rotate(PI / 8, axis=RIGHT)
        p3 = Dot(radius=0.14, color=PROXY_C).move_to(cube.get_center())
        g3 = VGroup(cube, p3, T(tr("3D 视频 / 点云 / 体素", "3D video / point clouds / voxels"), 26, GREY_A).next_to(cube, DOWN,
                                                                                                         buff=0.3))
        VGroup(g1, g2, g3).arrange(RIGHT, buff=1.0).shift(DOWN * 0.2)
        fit(VGroup(g1, g2, g3), 12.5)
        self.say(tr("一维的文本，二维的图像块，三维的视频、点云、体素，乃至更高维的张量——",
                    "1D text, 2D image patches, 3D video, point clouds and voxels, even higher-dimensional tensors:"),
                 LaggedStart(FadeIn(g1), FadeIn(g2), FadeIn(g3), lag_ratio=0.4), run_time=2.2)
        self.say(tr("都可以用同一套代理机制处理。", "all handled by the same proxy mechanism."),
                 Indicate(VGroup(p1, p2, p3), color=WHITE))
        t2i = fit(T(tr("文生图：文本条件只和图像的代理状态交互，而不是全部像素",
                       "Text-to-image: conditions attend only to image proxies, not every pixel"), 26, YELLOW), 12.5)
        t2i.next_to(VGroup(g1, g2, g3), DOWN, buff=0.6)
        self.say(tr("比如文生图里，文本条件只需要和压缩后的图像代理交互，跨模态融合的成本极低。",
                    "In text-to-image, the text condition talks only to compressed image proxies, so fusion is cheap."),
                 FadeIn(t2i))
        self.clear_all()


class P11_Outro(Base):
    def construct(self):
        honest = VGroup(
            T(tr("目标：验证架构的可行性，而非刷榜", "Goal: prove feasibility, not chase leaderboards"), 32),
            T(tr("大规模算力下的上限，仍待探索", "Its ceiling at large scale is still unexplored"), 32, YELLOW),
        ).arrange(DOWN, buff=0.4)
        self.say(tr("需要说明：这些实验的目标是验证架构可行，并不是去刷排行榜。",
                    "To be clear: these experiments prove the architecture works. They're not chasing leaderboards."),
                 FadeIn(honest[0]))
        self.say(tr("在大规模算力下，它的上限还是一个开放问题。", "How far it goes with serious compute is still an open question."),
                 FadeIn(honest[1]))
        self.play(FadeOut(honest))

        badge_t = Text("PATENT PENDING", font=SERIF, font_size=60, color=YELLOW)
        badge = VGroup(RoundedRectangle(corner_radius=0.3, width=badge_t.width + 1.0, height=1.4, stroke_color=YELLOW,
                                        stroke_width=4, fill_color=YELLOW, fill_opacity=0.08), badge_t)
        badge_t.move_to(badge[0])
        badge.shift(UP * 2.2)
        pat = T(tr("代理 Token（Proxy Token）方法已正式提交专利申请", "The Proxy Token method has been filed for a patent"), 30)
        fit(pat, 12).next_to(badge, DOWN, buff=0.35)
        self.say(tr("ProxyFormer 的核心方法——代理 Token，已经正式提交专利申请。",
                    "ProxyFormer's core method, the Proxy Token, has been formally filed for a patent."),
                 DrawBorderThenFill(badge), FadeIn(pat), run_time=1.5)
        lic = VGroup(
            T(tr("✓ 学术与非商业研究：免费使用", "✓ Academic & non-commercial research: free to use"), 28, GOOD_C),
            T(tr("✓ 商业使用：欢迎洽谈授权与合作", "✓ Commercial use: licensing & partnerships welcome"), 28, YELLOW),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.25).next_to(pat, DOWN, buff=0.45)
        self.say(tr("学术研究和非商业用途可以免费使用；商业部署与产品集成，欢迎联系洽谈授权。",
                    "Academic and non-commercial use is free. For commercial deployment, let's talk licensing."),
                 LaggedStartMap(FadeIn, lic, shift=RIGHT * 0.2, lag_ratio=0.4))
        self.play(FadeOut(VGroup(badge, pat, lic)))

        want = T(tr("寻求合作", "Looking for partners"), 48, YELLOW).to_edge(UP, buff=0.7)
        items = VGroup(*[T(s, 36) for s in [tr("算力资源", "Compute"), tr("研究资金", "Research funding"),
                                             tr("深度研究合作", "Research collaboration"),
                                             tr("商业授权", "Commercial licensing")]]).arrange(RIGHT, buff=0.7)
        fit(items, 12.5).shift(UP * 0.9)
        contact = VGroup(
            Text("tangzhongp@qq.com", font=MONO, font_size=32, color=WHITE),
            Text("arXiv:2608.23463", font=MONO, font_size=26, color=GREY_A),
            Text("github.com/simonFelix-Ai/proxy-former", font=MONO, font_size=26, color=GREY_A),
        ).arrange(DOWN, buff=0.25).shift(DOWN * 1.0)
        self.say(tr("作为独立研究者，作者希望与有算力、有资金、有场景的机构合作，一起把这个架构推向极限。",
                    "As an independent researcher, the author welcomes partners with compute, funding, or real use cases "
                    "to push this architecture to its limits."),
                 FadeIn(want), LaggedStartMap(FadeIn, items, shift=UP * 0.2, lag_ratio=0.2), run_time=2)
        self.say(tr("论文、代码和联系方式都在这里。感谢观看！", "Paper, code and contact are right here. Thanks for watching."),
                 FadeIn(contact, shift=UP * 0.2), Circumscribe(contact[0], color=YELLOW))
        self.wait(1.5)
        self.clear_all(run_time=1.2)


class Thumbnail(Scene):
    """YouTube thumbnail (render with -s); not part of SCENES."""

    def construct(self):
        a = Text("20K → 700K", font=CJK, weight=BOLD, font_size=110, color=PROXY_C)
        b = Text(tr("同一块 16GB 显卡", "tokens on one 16 GB GPU"), font=CJK, weight=BOLD, font_size=52)
        c = Text(tr("同样长度：显存 1/5 · 速度 12×", "Same length: 1/5 the memory · 12× faster"), font=CJK,
                 font_size=44, color=GOOD_C)
        d = Text("ProxyFormer", font=SERIF, font_size=56, color=GREY_A)
        g = VGroup(a, b, c, d).arrange(DOWN, buff=0.35)
        fit(g, 12.5)
        self.add(g)


SCENES = [P00_Hook, P01_Title, P02_Problem, P03_Proxy, P04_DualStream, P05_Engineering,
          P06_SpaceToChannel, P07_Memory, P08_NIAH, P09_Quality, P10_General, P11_Outro]

CHAPTERS = {
    "P00_Hook": tr("开场", "Intro"),
    "P02_Problem": tr("长上下文为什么贵", "Why long context is expensive"),
    "P03_Proxy": tr("核心想法：代理 Token", "The core idea: proxy tokens"),
    "P04_DualStream": tr("双流架构", "Dual-stream architecture"),
    "P05_Engineering": tr("级联压缩与代理 KV Cache", "Cascades and the proxy KV cache"),
    "P06_SpaceToChannel": tr("空间换通道", "Space-to-channel"),
    "P07_Memory": tr("显存：20K → 700K", "Memory: 20K → 700K tokens"),
    "P08_NIAH": tr("百万 token 大海捞针", "Million-token needle-in-a-haystack"),
    "P09_Quality": tr("质量：困惑度与图像生成", "Quality: perplexity and images"),
    "P10_General": tr("任意维度通用", "Any dimension"),
    "P11_Outro": tr("专利与合作", "Patent & collaboration"),
}
