"""
「压缩即路由」—— 3Blue1Brown 风格科普讲解视频（Manim Community 版）

论文：Compression is Routing: Reconstruction Error as an Intrinsic Signal
      for Modular Language Models (Zhongpan Tang, 2025)

每个场景的旁白以内嵌字幕形式呈现，同时会导出时间轴 JSON，
由 build.sh 合并为完整视频和 SRT 字幕文件（可用于后期配音）。
"""

import json
import os

import numpy as np
from manim import *

CJK = "Noto Sans CJK SC"
MONO = "DejaVu Sans Mono"

CODE_C = BLUE_C
WIKI_C = YELLOW_C
RAND_C = RED_C
NOVEL_C = PURPLE_B
MED_C = GREEN_C

CUE_DIR = os.environ.get("CUE_DIR", os.path.join(os.path.dirname(__file__), "build", "cues"))


def T(s, size=36, color=WHITE, **kw):
    return Text(s, font=CJK, font_size=size, color=color, **kw)


def wrap(text, width=26):
    """把较长的字幕按标点折成两行。"""
    if len(text) <= width:
        return text
    mid = len(text) // 2
    best = None
    for i, ch in enumerate(text):
        if ch in "，。；：、？！" and 0 < i < len(text) - 1:
            if best is None or abs(i - mid) < abs(best - mid):
                best = i
    if best is None:
        best = mid - 1
    return text[: best + 1] + "\n" + text[best + 1 :]


def make_sub(text):
    t = Text(wrap(text), font=CJK, font_size=26, color=GREY_A, line_spacing=0.8)
    if t.width > 12.5:
        t.scale_to_fit_width(12.5)
    t.to_edge(DOWN, buff=0.3)
    bg = BackgroundRectangle(t, color=BLACK, fill_opacity=0.75, buff=0.12)
    return VGroup(bg, t)


class Base(Scene):
    """带字幕旁白的基础场景：self.say(文本, *动画)。"""

    def setup(self):
        self.sub = None
        self.cues = []

    def read_time(self, text):
        return max(1.8, 0.2 * len(text) + 0.6)

    def make_sub(self, text):
        return make_sub(text)

    def say(self, text, *anims, run_time=None, dur=None, show=True):
        dur = dur if dur is not None else self.read_time(text)
        t0 = self.renderer.time
        self.hide_sub()
        if show:
            self.sub = self.make_sub(text)
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


# ---------------------------------------------------------------- 小部件

def token_boxes(values, color=BLUE, size=0.75, font_size=30):
    g = VGroup()
    for v in values:
        sq = RoundedRectangle(corner_radius=0.08, width=size, height=size,
                              stroke_color=color, fill_color=color, fill_opacity=0.15)
        g.add(VGroup(sq, Text(str(v), font=MONO, font_size=font_size).move_to(sq)))
    return g.arrange(RIGHT, buff=0.15)


def trapezoid(left_h, right_h, width, color):
    w, a, b = width / 2, left_h / 2, right_h / 2
    return Polygon([-w, a, 0], [w, b, 0], [w, -b, 0], [-w, -a, 0],
                   stroke_color=color, fill_color=color, fill_opacity=0.25)


def lock_icon(color=GREY_B, s=0.35):
    body = RoundedRectangle(corner_radius=0.04, width=s, height=s * 0.8,
                            fill_color=color, fill_opacity=1, stroke_width=0)
    shackle = Arc(radius=s * 0.3, start_angle=0, angle=PI, stroke_color=color, stroke_width=4)
    shackle.next_to(body, UP, buff=-0.02)
    return VGroup(shackle, body)


def expert_box(name, color, width=3.4):
    box = RoundedRectangle(corner_radius=0.15, width=width, height=0.85,
                           stroke_color=color, fill_color=color, fill_opacity=0.12)
    icon = trapezoid(0.55, 0.22, 0.45, color).move_to(box.get_left() + RIGHT * 0.5)
    label = T(name, 26, color).next_to(icon, RIGHT, buff=0.25)
    return VGroup(box, icon, label)


# ================================================================ 场景

class S01_Title(Base):
    def construct(self):
        q1 = T("一个模型「压缩得好不好」", 44)
        q2 = T("能不能直接告诉我们：", 44)
        q3 = T("这段数据，该交给谁处理？", 44, YELLOW)
        qs = VGroup(q1, q2, q3).arrange(DOWN, buff=0.4)
        self.say("如果我告诉你，一个模型压缩数据的好坏，", Write(q1), run_time=1.8)
        self.say("本身就能回答一个问题：", FadeIn(q2, shift=UP * 0.2))
        self.say("这段数据，应该交给哪个专家来处理？", Write(q3), run_time=1.6)
        self.play(FadeOut(qs, shift=UP * 0.5))

        title = T("压缩即路由", 88)
        en = Text("Compression is Routing", font_size=40, color=BLUE_B, slant=ITALIC)
        sub = T("重建误差：模块化语言模型的内在路由信号", 28, GREY_B)
        g = VGroup(title, en, sub).arrange(DOWN, buff=0.35).shift(UP * 0.4)
        line = Line(LEFT * 4, RIGHT * 4, color=BLUE_D).next_to(en, DOWN, buff=0.2)
        sub.next_to(line, DOWN, buff=0.3)
        self.say("今天，我们来聊一篇有意思的技术报告——",
                 Write(title), run_time=2)
        self.say("《压缩即路由》。",
                 FadeIn(en, shift=UP * 0.2), Create(line), FadeIn(sub), run_time=1.5)
        self.wait(0.5)
        self.clear_all()


class S02_Problem(Base):
    def construct(self):
        header = T("大语言模型的三大难题", 40).to_edge(UP, buff=0.5)
        self.say("当今的大语言模型，面临三个老大难问题。", FadeIn(header, shift=DOWN * 0.2))

        cards = VGroup()
        specs = [("上下文长度受限", BLUE_C), ("推理成本高昂", YELLOW_C), ("灾难性遗忘", RED_C)]
        for name, c in specs:
            r = RoundedRectangle(corner_radius=0.2, width=3.8, height=3.0,
                                 stroke_color=c, fill_color=c, fill_opacity=0.08)
            r_label = T(name, 30, c).move_to(r.get_top() + DOWN * 0.45)
            cards.add(VGroup(r, r_label))
        cards.arrange(RIGHT, buff=0.4).shift(DOWN * 0.1)

        # 图标 1：被截断的长条
        bar = VGroup(*[Square(0.18, stroke_width=1, stroke_color=BLUE_B, fill_color=BLUE,
                              fill_opacity=0.6) for _ in range(14)]).arrange(RIGHT, buff=0.04)
        bar.move_to(cards[0][0]).shift(DOWN * 0.3)
        cut = DashedLine(UP * 0.5, DOWN * 0.5, color=RED).move_to(bar[9].get_right() + RIGHT * 0.02)
        for sq in bar[10:]:
            sq.set_fill(opacity=0.1).set_stroke(opacity=0.3)
        icon1 = VGroup(bar, cut)
        # 图标 2：一叠 GPU
        gpus = VGroup(*[RoundedRectangle(corner_radius=0.05, width=1.6, height=0.28,
                                         stroke_color=YELLOW_B, fill_color=YELLOW_E,
                                         fill_opacity=0.5) for _ in range(5)]).arrange(UP, buff=0.07)
        icon2 = gpus.move_to(cards[1][0]).shift(DOWN * 0.3)
        # 图标 3：旧知识被新知识覆盖
        old = VGroup(*[Dot(radius=0.07, color=BLUE_B) for _ in range(12)]).arrange_in_grid(3, 4, buff=0.15)
        old.move_to(cards[2][0]).shift(DOWN * 0.3)
        icon3 = old

        self.say("第一，上下文长度有限：太长的文本塞不进去。",
                 FadeIn(cards[0], shift=UP * 0.2), FadeIn(icon1))
        self.say("第二，推理成本高：动辄需要一整排显卡。",
                 FadeIn(cards[1], shift=UP * 0.2), LaggedStartMap(FadeIn, gpus, shift=DOWN * 0.2))
        self.say("第三，灾难性遗忘：学了新知识，就忘了旧知识。",
                 FadeIn(cards[2], shift=UP * 0.2), FadeIn(icon3))
        self.play(LaggedStart(*[d.animate.set_color(RED_C).scale(0.5).set_opacity(0.3)
                                for d in old[::2]], lag_ratio=0.1), run_time=1.2)
        self.wait(0.5)
        self.clear_all()

        # MoE 与门控网络
        header = T("混合专家模型（MoE）", 40).to_edge(UP, buff=0.5)
        inp = RoundedRectangle(corner_radius=0.1, width=1.6, height=0.8, color=WHITE)
        inp_t = T("输入", 28).move_to(inp)
        inp_g = VGroup(inp, inp_t).move_to(LEFT * 5.2)
        router = RoundedRectangle(corner_radius=0.15, width=2.2, height=1.6,
                                  stroke_color=ORANGE, fill_color=ORANGE, fill_opacity=0.15)
        router_t = T("门控网络", 26, ORANGE).move_to(router.get_top() + DOWN * 0.35)
        qmark = Text("?", font_size=64, color=ORANGE).move_to(router).shift(DOWN * 0.2)
        router_g = VGroup(router, router_t, qmark).move_to(LEFT * 1.8)
        experts = VGroup(*[
            VGroup(RoundedRectangle(corner_radius=0.1, width=2.0, height=0.7,
                                    stroke_color=c, fill_color=c, fill_opacity=0.15),
                   T(f"专家 {i + 1}", 24, c))
            for i, c in enumerate([BLUE_C, GREEN_C, PURPLE_B, TEAL_C])
        ])
        for e in experts:
            e[1].move_to(e[0])
        experts.arrange(DOWN, buff=0.25).move_to(RIGHT * 3.2 + DOWN * 0.2)
        a0 = Arrow(inp_g.get_right(), router_g.get_left(), buff=0.1)
        arrows = VGroup(*[Arrow(router_g.get_right(), e.get_left(), buff=0.1, stroke_width=3,
                                max_tip_length_to_length_ratio=0.1) for e in experts])

        self.say("混合专家模型——MoE——缓解了其中一部分矛盾。",
                 FadeIn(header), FadeIn(inp_g), FadeIn(experts, lag_ratio=0.2))
        self.say("但它的路由，依赖一个额外训练的门控网络。",
                 GrowArrow(a0), FadeIn(router_g), LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.2))
        self.say("这个网络增加了系统复杂度，而且它为什么这样分配，往往说不清楚。",
                 Wiggle(qmark, scale_value=1.4), run_time=1.5)
        self.play(Wiggle(router_g, scale_value=1.05, rotation_angle=0.03 * TAU))
        self.clear_all()

        q = T("路由，真的需要「额外学习」吗？", 48, YELLOW)
        self.say("那么问题来了：路由这件事，真的需要额外学习吗？", Write(q), run_time=2)
        self.wait(0.8)
        self.clear_all()


class S03_Compression(Base):
    def construct(self):
        header = T("压缩即智能", 44).to_edge(UP, buff=0.5)
        self.say("先回到一个流传很广的观点：压缩即智能。", Write(header))

        s1 = Text("for i in range(10):", font=MONO, font_size=34, color=CODE_C)
        s2 = Text("q#7z !pW~ k&Lx0 :", font=MONO, font_size=34, color=RAND_C)
        rows = VGroup(s1, s2).arrange(DOWN, buff=1.4, aligned_edge=LEFT).shift(LEFT * 3.2 + UP * 0.3)

        def bits(n, color):
            return VGroup(*[Text(str(np.random.randint(2)), font=MONO, font_size=22, color=color)
                            for _ in range(n)]).arrange(RIGHT, buff=0.06)

        np.random.seed(3)
        b1 = bits(8, CODE_C).next_to(s1, DOWN, buff=0.3, aligned_edge=LEFT)
        b2 = bits(34, RAND_C).next_to(s2, DOWN, buff=0.3, aligned_edge=LEFT)
        l1 = T("可预测 → 编码短", 26, CODE_C).next_to(b1, RIGHT, buff=0.5)
        l2 = T("不可预测 → 编码长", 26, RAND_C).next_to(s2, RIGHT, buff=0.6)

        self.say("一个好的语言模型，能准确预测下一个词。", FadeIn(s1, shift=RIGHT * 0.2))
        self.say("而能预测，就能压缩：越可预测的内容，需要的比特越少。",
                 LaggedStartMap(FadeIn, b1, lag_ratio=0.1), FadeIn(l1))
        self.say("越陌生、越混乱的内容，编码就越长。",
                 FadeIn(s2, shift=RIGHT * 0.2), LaggedStartMap(FadeIn, b2, lag_ratio=0.03), FadeIn(l2))

        eq = MathTex(r"\text{Prediction}", r"\;\Longleftrightarrow\;", r"\text{Compression}",
                     font_size=52).shift(DOWN * 2.0)
        cite = Text("Delétang et al., 2024 · Language Modeling Is Compression",
                    font_size=20, color=GREY_B).next_to(eq, DOWN, buff=0.2)
        self.say("预测与压缩，是同一枚硬币的两面。", Write(eq), FadeIn(cite))
        self.wait(0.5)
        self.play(FadeOut(VGroup(s1, s2, b1, b2, l1, l2, eq, cite)))

        insight1 = T("推论：压缩器只擅长压缩它「熟悉」的数据", 36)
        insight2 = T("⇒ 压缩的好坏，本身就是一枚「指纹」", 40, YELLOW)
        VGroup(insight1, insight2).arrange(DOWN, buff=0.7)
        self.say("但这里藏着一个常被忽略的推论：", FadeIn(insight1, shift=UP * 0.2))
        self.say("压缩器，只擅长压缩它熟悉的那一类数据。", Indicate(insight1, color=BLUE_B))
        self.say("换句话说，压缩得好不好，本身就在告诉你：这段数据是不是「自己人」。",
                 Write(insight2), run_time=2)
        self.say("这篇报告，把这个直觉推向了一个新的架构理念：压缩即路由。",
                 Transform(header, T("压缩即智能  →  压缩即路由", 44).to_edge(UP, buff=0.5)))
        self.wait(0.5)
        self.clear_all()


class S04_Architecture(Base):
    def construct(self):
        title = T("端到端 Transformer 自编码器 · 87M 参数", 32).to_edge(UP, buff=0.35)
        self.say("为了验证这个想法，作者训练了一个 8700 万参数的端到端 Transformer 自编码器。",
                 FadeIn(title, shift=DOWN * 0.2))

        y0 = 0.3
        grid = VGroup(*[Square(0.09, stroke_width=0.4, stroke_color=BLUE_A, fill_color=BLUE,
                               fill_opacity=0.65) for _ in range(512)])
        grid.arrange_in_grid(rows=32, cols=16, buff=0.022).move_to([-5.4, y0, 0])
        gl = T("x：512 个 token", 24, BLUE_B).next_to(grid, UP, buff=0.15)

        enc = trapezoid(3.2, 1.1, 1.9, BLUE_D).move_to([-2.9, y0, 0])
        enc_t = T("编码器", 26).move_to(enc)
        z = VGroup(*[Rectangle(width=0.16, height=1.1, stroke_width=1, stroke_color=YELLOW_A,
                               fill_color=interpolate_color(YELLOW_D, ORANGE, i / 7), fill_opacity=0.9)
                     for i in range(8)]).arrange(RIGHT, buff=0.07).move_to([0, y0, 0])
        zl = T("z：8 个潜向量", 24, YELLOW).next_to(z, UP, buff=0.35)
        dec = trapezoid(1.1, 3.2, 1.9, TEAL_D).move_to([2.9, y0, 0])
        dec_t = T("解码器", 26).move_to(dec)
        out = grid.copy().move_to([5.4, y0, 0]).set_fill(TEAL, 0.65).set_stroke(TEAL_A)
        ol = T("x̂：重建结果", 24, TEAL_B).next_to(out, UP, buff=0.15)

        self.say("输入是一段 512 个 token 的序列。",
                 LaggedStartMap(FadeIn, grid, lag_ratio=0.002), FadeIn(gl), run_time=1.8)
        self.say("编码器通过注意力机制，把它压缩成仅仅 8 个潜向量。",
                 FadeIn(enc), Write(enc_t))
        flow = grid.copy()
        self.play(flow.animate.scale(0.15).move_to(enc.get_right()).set_opacity(0), run_time=1.3)
        self.remove(flow)
        self.play(LaggedStartMap(GrowFromEdge, z, edge=DOWN, lag_ratio=0.12), FadeIn(zl), run_time=1.2)

        brace = Brace(z, DOWN, color=YELLOW)
        ratio = MathTex(r"512 \to 8 \;=\; 64{:}1", color=YELLOW, font_size=40).next_to(brace, DOWN)
        self.say("512 比 8——序列长度压缩了整整 64 倍。", GrowFromCenter(brace), Write(ratio))

        self.say("解码器则只凭这 8 个向量，把原始序列逐个 token 地还原回来。",
                 FadeIn(dec), Write(dec_t))
        flow2 = z.copy()
        self.play(flow2.animate.move_to(dec.get_left()).set_opacity(0), run_time=0.8)
        self.remove(flow2)
        self.play(LaggedStartMap(FadeIn, out, lag_ratio=0.002), FadeIn(ol), run_time=1.5)

        # 物理隔离
        m = VGroup(*[Square(0.09, stroke_width=0.4, stroke_color=GREY_B, fill_color=GREY_D,
                            fill_opacity=0.8) for _ in range(32)]).arrange_in_grid(2, 16, buff=0.022)
        m.move_to([2.9, -2.2, 0])
        m_arrow = Arrow(m.get_top(), dec.get_bottom() + UP * 0.35, buff=0.05, color=GREY_B)
        m_l = T("m：辅助信号（与 x 等长，不含任何内容）", 20, GREY_B).next_to(m, LEFT, buff=0.3)
        self.say("关键在于「物理隔离」：解码器另外只收到一个辅助信号 m，它不含任何与原文相关的内容。",
                 FadeIn(m), GrowArrow(m_arrow), FadeIn(m_l), run_time=1.5)

        self.play(FadeOut(title))
        skip = CurvedArrow(gl.get_top() + UP * 0.1, ol.get_top() + UP * 0.1, angle=-TAU / 10,
                           color=RED_C)
        mid = skip.point_from_proportion(0.5)
        skip = DashedVMobject(skip, num_dashes=40)
        cross = Cross(scale_factor=0.35, stroke_color=RED).move_to(mid)
        no = T("解码器看不到原文 x", 24, RED_C).next_to(cross, DOWN, buff=0.12)
        self.say("解码器无法偷看原文，所有信息，都必须挤过这 8 个向量的瓶颈。",
                 Create(skip), run_time=1.2)
        self.play(Create(cross), FadeIn(no))
        self.say("这逼着编码器去学习数据分布本身的结构，而不是简单地搬运信号。",
                 Indicate(z, color=WHITE, scale_factor=1.15))

        formula = MathTex(r"x \;\to\; \text{Encoder} \;\to\; z \;\to\; [z,\,m] \;\to\; "
                          r"\text{Decoder} \;\to\; \hat{x}", font_size=40)
        formula.to_edge(UP, buff=0.35)
        self.play(FadeOut(VGroup(skip, cross, no)))
        self.say("训练数据是代码：用 GPT-2 分词器，在 codeparrot 代码数据集上训练。",
                 Write(formula), run_time=1.5)
        self.wait(0.5)
        self.clear_all()


class S05_Metric(Base):
    def construct(self):
        header = T("如何衡量「还原得好不好」？", 40).to_edge(UP, buff=0.5)
        self.say("怎么衡量还原得好不好？作者用了一个非常严格的指标。", FadeIn(header))

        x = token_boxes([1, 2, 3, 4, 5], BLUE)
        xh = token_boxes([1, 2, 6, 7, 5], TEAL)
        xl = MathTex("x", font_size=48).next_to(x, LEFT, buff=0.5)
        xhl = MathTex(r"\hat{x}", font_size=48).next_to(xh, LEFT, buff=0.5)
        rows = VGroup(VGroup(xl, x), VGroup(xhl, xh)).arrange(DOWN, buff=0.9).shift(UP * 0.6)
        self.say("比如原始序列是 1、2、3、4、5，", FadeIn(rows[0], shift=RIGHT * 0.2))
        self.say("重建结果是 1、2、6、7、5。", FadeIn(rows[1], shift=RIGHT * 0.2))

        marks = VGroup()
        for a, b in zip([1, 2, 3, 4, 5], [1, 2, 6, 7, 5]):
            marks.add(MathTex(r"\checkmark" if a == b else r"\times",
                              color=GREEN if a == b else RED, font_size=48))
        for mk, box in zip(marks, xh):
            mk.next_to(box, DOWN, buff=0.3)
        self.say("逐个位置比对：第 1、2、5 个对上了，第 3、4 个错了。",
                 LaggedStartMap(FadeIn, marks, shift=UP * 0.2, lag_ratio=0.25), run_time=2)
        res = MathTex(r"\text{TRA} = \frac{3}{5} = 60\%", font_size=48, color=YELLOW)
        res.next_to(marks, DOWN, buff=0.4)
        self.say("准确率就是 5 个里对了 3 个——60%。", Write(res))

        self.play(FadeOut(VGroup(rows, marks, res)))
        formula = MathTex(r"\text{TRA}(x,\hat{x}) = \frac{1}{L}\sum_{t=1}^{L}\mathbb{I}(x_t = \hat{x}_t)",
                          font_size=56)
        self.say("这就是 token 级重建准确率，TRA。", Write(formula), run_time=2)
        note = T("严格逐位比对，而非模糊的「语义相似」", 28, GREY_B).next_to(formula, DOWN, buff=0.6)
        self.say("它只认逐位精确匹配，不接受「意思差不多」。", FadeIn(note))
        self.wait(0.5)
        self.clear_all()


class S06_Results(Base):
    def construct(self):
        header = T("核心发现：三级台阶式衰减", 40).to_edge(UP, buff=0.4)
        self.say("现在，是见证结果的时候了。", FadeIn(header))

        base_y = -1.8
        H = 3.3
        axis = Line([-5.5, base_y, 0], [5.5, base_y, 0], color=GREY_B)
        names = [("代码", "域内", CODE_C), ("维基百科", "半域外", WIKI_C), ("随机序列", "完全域外", RAND_C)]
        vals = [99.47, 47.76, 0.57]
        xs = [-3.6, 0, 3.6]
        self.play(Create(axis))

        bars, nums, labels = [], [], []
        for (n, tag, c), v, xpos in zip(names, vals, xs):
            tr = ValueTracker(0.0)
            bar = always_redraw(lambda tr=tr, c=c, xpos=xpos: Rectangle(
                width=1.6, height=max(tr.get_value() / 100 * H, 0.001),
                fill_color=c, fill_opacity=0.85, stroke_width=0).move_to(
                [xpos, base_y + max(tr.get_value() / 100 * H, 0.001) / 2, 0]))
            num = always_redraw(lambda tr=tr, c=c, xpos=xpos: VGroup(
                DecimalNumber(tr.get_value(), num_decimal_places=2, font_size=40, color=c),
                MathTex(r"\%", font_size=40, color=c)).arrange(RIGHT, buff=0.05).move_to(
                [xpos, base_y + tr.get_value() / 100 * H + 0.35, 0]))
            lab = VGroup(T(n, 28, c), T(tag, 22, GREY_B)).arrange(DOWN, buff=0.08)
            lab.next_to([xpos, base_y, 0], DOWN, buff=0.15)
            bars.append((tr, bar, v))
            nums.append(num)
            labels.append(lab)

        lines = [
            "在从未见过的代码验证集上：重建准确率 99.47%。",
            "换成自然语言的维基百科：骤降到 47.76%。",
            "而对完全随机的 token 序列：只剩 0.57%。",
        ]
        for (tr, bar, v), num, lab, line in zip(bars, nums, labels, lines):
            self.add(bar, num)
            self.say(line, FadeIn(lab), tr.animate.set_value(v), run_time=2)

        guess = DashedLine([-5.5, base_y + 0.02, 0], [5.5, base_y + 0.02, 0], color=GREY_A)
        g_t = T("随机猜测 ≈ 1/|V| ≈ 0.002%", 20, GREY_A).move_to([2.5, base_y + 1.4, 0])
        g_l = VGroup(g_t, Arrow(g_t.get_bottom(), [2.0, base_y + 0.05, 0], buff=0.08,
                                color=GREY_A, stroke_width=3))
        self.say("注意，47.76% 绝不是瞎猜——瞎猜的准确率只有约十万分之二。",
                 Create(guess), FadeIn(g_l))
        self.say("它说明模型利用了代码与自然语言共享的词汇和统计规律：两个分布有一部分重叠。")

        tags = VGroup(T("完美拟合", 26, CODE_C), T("结构偏差", 26, WIKI_C), T("完全拒绝", 26, RAND_C))
        for tg, xpos, v in zip(tags, xs, vals):
            tg.move_to([xpos, base_y + v / 100 * H + 0.9, 0])
        tags[2].shift(UP * 0.3)
        self.play(FadeOut(VGroup(guess, g_l)))
        self.say("而随机序列几乎完全被拒绝，证明模型没有退化成一根「信号传输线」。",
                 LaggedStartMap(FadeIn, tags, shift=DOWN * 0.2, lag_ratio=0.3))
        self.say("一个压缩器，三个分布，三级台阶——差距是系统性的、巨大的。")
        self.wait(0.3)
        self.clear_all()

        big = T("重建误差 = 内在的分布指纹", 50, YELLOW)
        self.say("于是，重建误差，就成了一枚天然的「分布指纹」。", Write(big), run_time=2)
        self.wait(0.8)
        self.clear_all()


class S07_Geometry(Base):
    def construct(self):
        header = T("潜空间里发生了什么？", 40).to_edge(UP, buff=0.4)
        self.say("为什么差距会这么大？我们看看潜向量 z 的几何形状。", FadeIn(header))

        rng = np.random.default_rng(7)
        frame = RoundedRectangle(corner_radius=0.15, width=6.0, height=4.6, color=GREY_D)
        frame.move_to([-3.4, -0.1, 0])
        c_center = frame.get_center() + np.array([-1.3, 0.8, 0])
        w_center = frame.get_center() + np.array([1.3, -0.8, 0])
        code_pts = VGroup(*[Dot(c_center + np.array([*rng.normal(0, 0.42, 2), 0]), radius=0.035,
                                color=CODE_C) for _ in range(160)])
        wiki_pts = VGroup(*[Dot(w_center + np.array([*rng.normal(0, 0.42, 2), 0]), radius=0.035,
                                color=WIKI_C) for _ in range(160)])
        leg = VGroup(
            VGroup(Dot(color=CODE_C), T("代码（域内）", 20, CODE_C)).arrange(RIGHT, buff=0.1),
            VGroup(Dot(color=WIKI_C), T("维基（域外）", 20, WIKI_C)).arrange(RIGHT, buff=0.1),
        ).arrange(RIGHT, buff=0.4).next_to(frame, UP, buff=0.12)
        note = T("示意图 · 论文中为 t-SNE / UMAP 可视化", 18, GREY_B).next_to(frame, DOWN, buff=0.1)

        self.say("把代码和维基文本的潜向量投影到二维平面：",
                 Create(frame), FadeIn(leg), FadeIn(note))
        self.play(LaggedStartMap(FadeIn, code_pts, lag_ratio=0.005),
                  LaggedStartMap(FadeIn, wiki_pts, lag_ratio=0.005), run_time=1.5)
        self.say("它们是两座致密的、彼此断开的孤岛，中间隔着一大片真空。")
        sep = DashedLine(frame.get_center() + np.array([-2.2, -1.9, 0]),
                         frame.get_center() + np.array([2.2, 1.9, 0]), color=WHITE)
        self.say("一条直线就能把它们分开——线性可分。", Create(sep))
        self.say("这意味着路由决策的计算代价几乎为零，无需训练复杂的门控网络。")
        self.say("同时，不同分布占据互不重叠的区域，训练一个专家，几乎不会干扰另一个。")

        ax = Axes(x_range=[0, 512, 128], y_range=[0.2, 1.0, 0.2], x_length=5.2, y_length=3.6,
                  axis_config={"color": GREY_B, "include_numbers": True, "font_size": 18},
                  tips=False).move_to([3.5, -0.2, 0])
        tau = 200 / np.log(16)
        curve = ax.plot(lambda k: 1 - 0.8 * np.exp(-k / tau), x_range=[0, 512], color=CODE_C)
        h95 = DashedLine(ax.c2p(0, 0.95), ax.c2p(512, 0.95), color=RED_C)
        v200 = DashedLine(ax.c2p(200, 0.2), ax.c2p(200, 0.95), color=RED_C)
        xl = T("主成分个数", 18, GREY_B).next_to(ax, DOWN, buff=0.1)
        yl = T("累计解释方差", 18, GREY_B).rotate(PI / 2).next_to(ax, LEFT, buff=0.1)
        lab = T("≈200 维即解释 95% 方差", 22, YELLOW).next_to(ax.c2p(200, 0.95), DR, buff=0.15)
        self.say("再看代码潜向量的主成分分析：虽然 z 的物理维度是 512，",
                 Create(ax), FadeIn(xl), FadeIn(yl))
        self.play(Create(curve), run_time=1.5)
        self.say("但前约 200 个主成分，就解释了 95% 的方差。",
                 Create(h95), Create(v200), FadeIn(lab))
        self.say("编码器学会了丢掉噪声与冗余，只保留数据最核心的「骨架」。")
        self.wait(0.3)
        self.clear_all()


class S08_Routing(Base):
    def construct(self):
        header = T("压缩即路由", 44).to_edge(UP, buff=0.3)
        self.say("现在，把这些拼在一起，就得到了「压缩即路由」。", FadeIn(header))

        experts = VGroup(expert_box("代码压缩器", CODE_C),
                         expert_box("百科压缩器", WIKI_C),
                         expert_box("小说压缩器", NOVEL_C))
        experts.arrange(DOWN, buff=0.35).move_to([0.3, 0.9, 0])
        inp = VGroup(RoundedRectangle(corner_radius=0.12, width=3.2, height=1.1, color=WHITE),
                     Text("def area(r):\n    return 3.14*r*r", font=MONO, font_size=18, color=CODE_C))
        inp[1].move_to(inp[0])
        inp.move_to([-5.0, 0.9, 0])
        in_l = T("新的输入片段", 22, GREY_B).next_to(inp, UP, buff=0.15)
        arrows = VGroup(*[Arrow(inp.get_right(), e.get_left(), buff=0.15, stroke_width=3,
                                max_tip_length_to_length_ratio=0.08) for e in experts])

        self.say("假设我们有好几个专家，每个专家都配有一个只在自己领域训练的压缩器。",
                 LaggedStartMap(FadeIn, experts, shift=LEFT * 0.2, lag_ratio=0.2))
        self.say("来了一段新输入，比如一段代码。", FadeIn(inp, shift=RIGHT * 0.2), FadeIn(in_l))
        self.say("让每个压缩器都试着压缩、再重建它一次。", LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.2))

        def readouts(vals):
            g = VGroup()
            for v, e in zip(vals, experts):
                c = GREEN if v >= 90 else (YELLOW if v >= 50 else RED_C)
                g.add(T(f"{v}%", 30, c).next_to(e, RIGHT, buff=0.5))
            return g

        r1 = readouts([99, 44, 41])
        self.say("然后看各自的重建准确率。", LaggedStartMap(FadeIn, r1, shift=LEFT * 0.2, lag_ratio=0.3))
        win = SurroundingRectangle(VGroup(experts[0], r1[0]), color=YELLOW, buff=0.12)
        route = T("→ 路由给代码专家", 26, YELLOW).next_to(win, RIGHT, buff=0.3)
        self.say("谁重建得最好，就交给谁。就这么简单。", Create(win), FadeIn(route))
        self.say("没有门控网络，没有额外参数；重建误差本身就是路由信号，而且一目了然、完全可解释。")
        demo = T("示意数值", 18, GREY_B).to_corner(UR, buff=0.4)
        self.add(demo)

        # 新领域到来
        self.play(FadeOut(VGroup(win, route, r1)))
        inp2 = VGroup(RoundedRectangle(corner_radius=0.12, width=3.2, height=1.1, color=WHITE),
                      T("患者主诉：反复\n咳嗽三周，伴低热", 18, MED_C))
        inp2[1].move_to(inp2[0])
        inp2.move_to(inp)
        self.say("如果来的是一个全新领域，比如医学文本呢？", ReplacementTransform(inp, inp2))
        r2 = readouts([31, 46, 38])
        self.say("所有压缩器都「看不懂」，重建准确率普遍偏低。",
                 LaggedStartMap(FadeIn, r2, shift=LEFT * 0.2, lag_ratio=0.3))
        self.say("这本身就是一个信号：该添加一个新专家了。")

        new_e = expert_box("医学压缩器", MED_C).next_to(experts, DOWN, buff=0.35)
        locks = VGroup(*[lock_icon().next_to(e, LEFT, buff=0.12).shift(RIGHT * 0.0) for e in experts])
        for lk, e in zip(locks, experts):
            lk.move_to(e.get_corner(UL) + RIGHT * 0.05 + DOWN * 0.05)
        self.play(FadeOut(r2))
        self.say("挂载一个新的医学压缩器，只训练它；旧专家的参数全部冻结。",
                 FadeIn(new_e, shift=UP * 0.3), experts.animate.set_opacity(0.45),
                 LaggedStartMap(FadeIn, locks, scale=0.5))
        a_new = Arrow(inp2.get_right(), new_e.get_left(), buff=0.15, stroke_width=3, color=MED_C,
                      max_tip_length_to_length_ratio=0.08)
        r3 = T("98%", 30, GREEN).next_to(new_e, RIGHT, buff=0.5)
        self.say("旧知识在物理上不受干扰，从架构层面避开了灾难性遗忘。", GrowArrow(a_new), FadeIn(r3))
        self.say("系统不再是一个需要反复重铸的巨石，而是可以持续挂载新模块、不断演化的生态。")
        self.wait(0.3)
        self.clear_all()


class S09_Memory(Base):
    def construct(self):
        header = T("意外收获：显存", 40).to_edge(UP, buff=0.5)
        self.say("这个架构还有一个意外的好处：显存。", FadeIn(header))

        full = Rectangle(width=11.5, height=0.6, fill_color=BLUE, fill_opacity=0.7, stroke_width=0)
        full.move_to(UP * 1.0)
        fl = T("传统 KV Cache：随序列长度线性增长（512 个位置）", 24, BLUE_B).next_to(full, UP, buff=0.15)
        comp = Rectangle(width=11.5 / 64, height=0.6, fill_color=YELLOW, fill_opacity=0.9,
                         stroke_width=0).align_to(full, LEFT).shift(DOWN * 1.6 + UP * 1.0)
        cl = T("压缩后：8 个潜向量", 24, YELLOW).next_to(comp, RIGHT, buff=0.3)
        self.say("传统 Transformer 的 KV Cache，随上下文长度线性增长。",
                 GrowFromEdge(full, LEFT), FadeIn(fl), run_time=1.8)
        ghost = full.copy().set_fill(opacity=0.25)
        self.add(ghost)
        self.say("而在潜空间里，512 个位置只需 8 个向量表示——序列长度压缩 64 倍。",
                 ReplacementTransform(full.copy(), comp), FadeIn(cl), run_time=1.8)
        big = MathTex(r"\frac{1}{64}", font_size=90, color=YELLOW).shift(DOWN * 1.9 + RIGHT * 3)
        self.say("论文设想：原本需要多张 A100 才能处理的超长上下文，", Write(big))
        self.say("有望在一张消费级显卡上完成。")
        self.wait(0.3)
        self.clear_all()


class S10_Limits(Base):
    def construct(self):
        header = T("局限与未来", 40).to_edge(UP, buff=0.4)
        self.say("当然，作为一项基础验证，这项工作也有它的局限。", FadeIn(header))

        n = 48
        cells = VGroup(*[Square(0.22, stroke_width=0.5, stroke_color=GREY_B,
                                fill_color=NOVEL_C if i < 28 else CODE_C, fill_opacity=0.7)
                         for i in range(n)]).arrange(RIGHT, buff=0.02).move_to(UP * 1.6)
        nl = T("小说", 22, NOVEL_C).next_to(cells[10], UP, buff=0.15)
        cl = T("代码", 22, CODE_C).next_to(cells[38], UP, buff=0.15)
        self.say("第一，滞后效应：窗口固定为 512 个 token。",
                 LaggedStartMap(FadeIn, cells, lag_ratio=0.02), FadeIn(nl), FadeIn(cl))

        win = SurroundingRectangle(cells[16:32], color=YELLOW, buff=0.06)
        self.say("当数据分布在窗口内部突然切换，比如小说里突然插入一段代码，", Create(win))

        ax = Axes(x_range=[0, n, 8], y_range=[0, 1, 0.5], x_length=cells.width, y_length=2.0,
                  tips=False, axis_config={"color": GREY_C}).next_to(cells, DOWN, buff=0.35)
        ax.align_to(cells, LEFT)

        def err(t):
            b = 28
            if t < b:
                return 0.1
            return 0.1 + 0.8 * np.exp(-(t - b) / 5.0) * min(1, (t - b + 0.5) / 1.5)

        g = ax.plot(err, x_range=[0, n - 0.01, 0.05], color=RED_C)
        gl = T("重建误差", 20, RED_C).next_to(ax, LEFT, buff=0.1)
        self.say("z 仍被前面的分布「主导」，反应迟钝，切换处的重建误差会异常升高。",
                 Create(ax), Create(g), FadeIn(gl), win.animate.move_to(
                     VGroup(*cells[22:38]).get_center()), run_time=2)
        self.play(FadeOut(VGroup(cells, nl, cl, win, ax, g, gl)))

        items = VGroup(
            T("• 交错分布：技术博客夹着代码片段，易落入难以判别的「灰色地带」", 26),
            T("• 压缩极限：64× 下 M=8 是最小可行长度；M=2、4 时明显失真", 26),
            T("• 早期探索显示 128× 甚至更高亦有可能", 26),
            T("• 猜想：M 与 L 之间存在基于信息熵的 Scaling Law", 26, YELLOW),
        ).arrange(DOWN, buff=0.45, aligned_edge=LEFT).shift(UP * 0.2)
        self.say("第二，现实数据常常是交错混合的，单一窗口里同时存在两种分布。", FadeIn(items[0], shift=RIGHT * 0.2))
        self.say("第三，受限于算力，消融实验有限：M 等于 8 是这个设置下的最小可行长度。",
                 FadeIn(items[1], shift=RIGHT * 0.2))
        self.say("早期实验还提示，压缩比有可能推到 128 倍甚至更高。", FadeIn(items[2], shift=RIGHT * 0.2))
        self.say("作者猜想，潜向量长度与序列长度之间，或许存在一条基于信息熵的缩放定律。",
                 FadeIn(items[3], shift=RIGHT * 0.2))
        self.say("此外，作者在中文小说语料和自定义分词器上，也复现了同样的三级台阶现象。")
        self.wait(0.3)
        self.clear_all()


class S11_Outro(Base):
    def construct(self):
        nums = VGroup(T("99.47%", 60, CODE_C), MathTex(r"\to", font_size=60),
                      T("47.76%", 60, WIKI_C), MathTex(r"\to", font_size=60),
                      T("0.57%", 60, RAND_C)).arrange(RIGHT, buff=0.4).shift(UP * 1.2)
        self.say("99.47、47.76、0.57——", LaggedStartMap(FadeIn, nums, shift=UP * 0.2, lag_ratio=0.3),
                 run_time=2)
        line = T("压缩得好不好，就是「这是谁的数据」的答案。", 36).next_to(nums, DOWN, buff=0.7)
        self.say("这三个数字说明：压缩得好不好，本身就回答了「这是谁的数据」。", Write(line), run_time=2)
        self.play(FadeOut(VGroup(nums, line), shift=UP * 0.3))

        title = T("压缩即路由", 80)
        en = Text("Compression is Routing", font_size=36, color=BLUE_B, slant=ITALIC)
        g = VGroup(title, en).arrange(DOWN, buff=0.3).shift(UP * 1.2)
        repo = Text("github.com/simonFelix-Ai/compression_is_routing", font=MONO, font_size=26,
                    color=GREY_A)
        paper = T("论文：doc/paper/pdf/Compression_is_routing.pdf · Zhongpan Tang", 22, GREY_B)
        chain = T("论文 SHA256 已上链存证（BscScan）", 22, GREY_B)
        info = VGroup(repo, paper, chain).arrange(DOWN, buff=0.25).next_to(g, DOWN, buff=0.8)
        self.say("从「压缩即预测」，到「压缩即路由」。", Write(title), FadeIn(en), run_time=2)
        self.say("作者希望这份报告能成为一个起点，邀请更多社区和实验室一起探索编码器作为知识容器的极限。",
                 FadeIn(info, shift=UP * 0.2))
        self.say("论文与更多信息，都在这个 GitHub 仓库里。感谢观看！",
                 Circumscribe(repo, color=YELLOW))
        self.wait(1.0)
        self.clear_all(run_time=1.2)


SCENES = [S01_Title, S02_Problem, S03_Compression, S04_Architecture, S05_Metric,
          S06_Results, S07_Geometry, S08_Routing, S09_Memory, S10_Limits, S11_Outro]
