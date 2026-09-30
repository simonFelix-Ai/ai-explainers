"""
ProxyFormer -- asymmetric embeddings: why the history can be 8x narrower than the present.
3Blue1Brown-style explainer (Manim Community), bilingual via PF_LANG=zh|en.

Facts shown are taken from the repository (src/models/architectures/llm/proxy_former_llm.py and configs):
  h_embedding = nn.Embedding(vocab, d_history)   # d_history = 64
  x_embedding = nn.Embedding(vocab, d_model)     # d_model  = 512
  the history's fine (local) stream stays d_history wide in every layer; proxies are d_model wide;
  every published result uses d_model=512, d_history=64, 10 layers, compression ratio 64.

Memory accounting (one 16-bit hidden-state tensor per layer, 716,800-token history):
  full width   716,800 x 512 x 2 B = 734.0 MB
  fine stream  716,800 x  64 x 2 B =  91.8 MB
  proxies       11,200 x 512 x 2 B =  11.5 MB   -> 103.2 MB, 7.1x smaller
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from manim import *  # noqa: E402

from proxyformer_video import (BAD_C, BASE_C, GOOD_C, LOCAL_C, MONO, PROXY_C, SERIF, Base, T, fit,  # noqa: E402
                               tr)

GEN_C = GREEN_C


def column(height, color, width=0.16, opacity=0.75):
    return Rectangle(width=width, height=height, stroke_width=0.6, stroke_color=color, fill_color=color,
                     fill_opacity=opacity)


def ribbon(n, height, color, width=0.16, buff=0.03):
    return VGroup(*[column(height, color, width) for _ in range(n)]).arrange(RIGHT, buff=buff)


# ================================================================ scenes

class A00_Hook(Base):
    """Cold open: a wide history ribbon collapses to 1/8 height while the memory number drops."""

    def construct(self):
        top = T(tr("同一段历史 · 716,800 个 token", "Same history · 716,800 tokens"), 44).to_edge(UP, buff=0.6)
        hist = ribbon(48, 3.6, BLUE_D).move_to(UP * 0.4)
        lab_d = MathTex(r"d = 512", font_size=52, color=BLUE_B).next_to(hist, LEFT, buff=0.3)
        mem = VGroup(T(tr("每层显存", "memory per layer"), 30, GREY_B),
                     T("734 MB", 60, BAD_C)).arrange(DOWN, buff=0.15).to_edge(DOWN, buff=1.2)
        # Frame one already shows the full-width history.
        self.add(top, hist, lab_d, mem)
        thin = ribbon(48, 3.6 / 8, LOCAL_C).move_to(hist.get_center())
        lab_64 = MathTex(r"d = 64", font_size=52, color=LOCAL_C).next_to(thin, LEFT, buff=0.3)
        mem2 = VGroup(T(tr("每层显存", "memory per layer"), 30, GREY_B),
                      T("103 MB", 60, GOOD_C)).arrange(DOWN, buff=0.15).move_to(mem)
        self.say(tr("同一段历史，宽度只要八分之一。", "Same history. One-eighth the width."),
                 Transform(hist, thin), Transform(lab_d, lab_64), Transform(mem, mem2),
                 run_time=1.4, dur=2.2, show=False)
        x7 = T("7.1×", 90, GOOD_C).next_to(mem2, RIGHT, buff=0.8)
        self.say(tr("显存直接省下 7 倍。", "Seven times less memory."), FadeIn(x7, scale=1.5),
                 run_time=0.4, dur=1.6, show=False)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.3)
        q = T(tr("历史，为什么不需要和「当下」一样宽？", "Why doesn't the past need to be as wide as the present?"),
              44, YELLOW)
        fit(q, 12.5)
        self.say(tr("为什么历史不需要和当下一样宽？", "Why doesn't the past need to be as wide as the present?"),
                 Write(q), run_time=1.0, dur=2.4, show=False)
        self.play(FadeOut(q), run_time=0.4)


class A01_Title(Base):
    def construct(self):
        title = Text("ProxyFormer", font=SERIF, font_size=80)
        sub = T(tr("非对称嵌入：从源头节省显存", "Asymmetric embeddings: saving memory at the source"), 36, BLUE_B)
        fit(sub, 12)
        paper = Text("arXiv:2608.23463 · Zhongpan Tang", font=SERIF, font_size=26, color=GREY_B)
        line = Line(LEFT * 4, RIGHT * 4, color=BLUE_D)
        VGroup(title, line, sub, paper).arrange(DOWN, buff=0.35)
        self.say(tr("这一期，我们只讲 ProxyFormer 的一个细节：非对称嵌入。",
                    "This time we zoom into one detail of ProxyFormer: asymmetric embeddings."),
                 Write(title), Create(line), run_time=1.6)
        self.say(tr("它让显存从模型的第一层之前，就开始节省。",
                    "It starts saving memory before the first layer even runs."), FadeIn(sub, shift=UP * 0.2),
                 FadeIn(paper))
        self.clear_all()


class A02_WhereMemoryGoes(Base):
    def construct(self):
        header = T(tr("显存花在哪里？", "Where does the memory go?"), 44).to_edge(UP, buff=0.5)
        self.say(tr("先看显存到底花在哪里。", "First: where does the memory actually go?"), FadeIn(header))

        tok = RoundedRectangle(corner_radius=0.1, width=1.3, height=0.7, color=WHITE)
        tok_t = Text("token 1532", font=MONO, font_size=20).move_to(tok)
        tok_g = VGroup(tok, tok_t).move_to(LEFT * 5 + UP * 0.8)
        arr = Arrow(tok_g.get_right(), tok_g.get_right() + RIGHT * 1.6, buff=0.1)
        vec = VGroup(*[Square(0.22, stroke_width=0.8, stroke_color=BLUE_B, fill_color=BLUE_D,
                              fill_opacity=0.25 + 0.6 * abs(np.sin(i * 1.7))) for i in range(16)]
                     ).arrange(DOWN, buff=0.02).next_to(arr, RIGHT, buff=0.2)
        brace = Brace(vec, RIGHT)
        dl = MathTex(r"d \text{ numbers}", font_size=34).next_to(brace, RIGHT)
        self.say(tr("嵌入层把每个 token 变成一个 d 维向量。",
                    "The embedding layer turns each token into a vector of d numbers."),
                 FadeIn(tok_g), GrowArrow(arr), LaggedStartMap(FadeIn, vec, lag_ratio=0.05), GrowFromCenter(brace),
                 Write(dl))
        self.play(FadeOut(VGroup(tok_g, arr, vec, brace, dl)))

        mat = Rectangle(width=9.0, height=2.2, stroke_color=BLUE_B, fill_color=BLUE_D, fill_opacity=0.45)
        mat.move_to(UP * 0.5)
        bL = Brace(mat, DOWN)
        lL = MathTex(r"L \text{ tokens}", font_size=36).next_to(bL, DOWN, buff=0.1)
        bd = Brace(mat, LEFT)
        ld = MathTex(r"d", font_size=40).next_to(bd, LEFT)
        self.say(tr("一段长度为 L 的序列，就是一个 L 乘 d 的矩阵。",
                    "A sequence of L tokens becomes an L-by-d matrix."),
                 DrawBorderThenFill(mat), GrowFromCenter(bL), Write(lL), GrowFromCenter(bd), Write(ld))
        stack = VGroup(*[mat.copy().set_fill(opacity=0.18).set_stroke(opacity=0.4).shift(UP * 0.18 * k + RIGHT * 0.18 * k)
                         for k in range(1, 6)])
        self.say(tr("每一层都要保存这样的中间结果，训练时还要留着做反向传播。",
                    "Every layer keeps activations like this, and training holds on to them for backprop."),
                 LaggedStartMap(FadeIn, stack, lag_ratio=0.15), run_time=1.6)
        f = MathTex(r"\text{memory} \;\propto\; L \times d \times \text{layers}", font_size=50).to_edge(DOWN, buff=1.4)
        self.say(tr("所以显存大致正比于：长度乘以宽度乘以层数。",
                    "So memory scales roughly with length times width times depth."), Write(f))
        self.play(FadeOut(VGroup(mat, bL, lL, bd, ld, stack)), f.animate.move_to(UP * 1.2))
        opts = VGroup(
            VGroup(T(tr("缩短 L", "shrink L"), 34, PROXY_C), T(tr("→ 代理 Token 压缩（上一期）", "→ proxy-token compression"), 26, GREY_B)),
            VGroup(T(tr("收窄 d", "shrink d"), 34, LOCAL_C), T(tr("→ 非对称嵌入（本期）", "→ asymmetric embeddings (this video)"), 26, GREY_B)),
        )
        for o in opts:
            o.arrange(RIGHT, buff=0.4)
        opts.arrange(DOWN, buff=0.5, aligned_edge=LEFT).next_to(f, DOWN, buff=0.8)
        self.say(tr("长上下文里 L 巨大。要省显存，要么缩短 L，要么收窄 d。",
                    "With long context, L is huge. You can shrink L, or you can shrink d."),
                 FadeIn(opts[0], shift=RIGHT * 0.2))
        self.say(tr("缩短 L 是代理 Token 的工作；这一期讲的是收窄 d。",
                    "Proxy tokens shrink L. This video is about shrinking d."), FadeIn(opts[1], shift=RIGHT * 0.2))
        self.clear_all()


class A03_TwoRoles(Base):
    def construct(self):
        header = T(tr("历史和当下，分工不同", "The past and the present do different jobs"), 42).to_edge(UP, buff=0.5)
        self.say(tr("关键观察是：历史 token 和当前 token 的分工完全不同。",
                    "The key observation: history tokens and current tokens have completely different jobs."),
                 FadeIn(header))
        hist = ribbon(30, 0.45, LOCAL_C, 0.16).move_to(LEFT * 2.3 + DOWN * 0.6)
        cur = ribbon(6, 3.6, GEN_C, 0.3, 0.05).move_to(RIGHT * 4.5 + DOWN * 0.6)
        hl = VGroup(T(tr("历史", "history"), 32, LOCAL_C), T(tr("超长 · 只需被记住", "very long · only needs to be remembered"), 24, GREY_B)
                    ).arrange(DOWN, buff=0.12).next_to(hist, UP, buff=1.9)
        cl = VGroup(T(tr("当下", "present"), 32, GEN_C), T(tr("很短 · 要预测下一个 token", "short · must predict the next token"), 24, GREY_B)
                    ).arrange(DOWN, buff=0.12).next_to(cur, UP, buff=0.3)
        fit(hl, 6.2)
        fit(cl, 4.6)
        self.say(tr("当下的 token 很少，却要直接预测下一个词，需要完整的宽度。",
                    "Current tokens are few, but they predict the next word directly, so they need full width."),
                 FadeIn(cur, shift=UP * 0.2), FadeIn(cl))
        self.say(tr("历史 token 极多，但它们的任务只是被记住、被压缩进代理里。",
                    "History tokens are countless, but their only job is to be remembered and condensed into proxies."),
                 LaggedStartMap(FadeIn, hist, lag_ratio=0.03), FadeIn(hl))
        d1 = MathTex(r"d_{\text{history}} = 64", font_size=40, color=LOCAL_C).next_to(hist, DOWN, buff=0.4)
        d2 = MathTex(r"d_{\text{model}} = 512", font_size=40, color=GEN_C).next_to(cur, DOWN, buff=0.4)
        self.say(tr("所以给它们不同的宽度：历史 64 维，当下 512 维。",
                    "So give them different widths: 64 for the history, 512 for the present."), Write(d1), Write(d2))
        self.play(FadeOut(VGroup(hist, cur, hl, cl, d1, d2)))

        code = VGroup(
            Text("self.h_embedding = nn.Embedding(vocab, d_history)", font=MONO, font_size=24, color=LOCAL_C,
                 t2c={"# 64": GREY_B}),
            Text("self.x_embedding = nn.Embedding(vocab, d_model)", font=MONO, font_size=24, color=GEN_C),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        notes = VGroup(Text("# 64", font=MONO, font_size=24, color=GREY_B),
                       Text("# 512", font=MONO, font_size=24, color=GREY_B))
        for n, c in zip(notes, code):
            n.next_to(c, RIGHT, buff=0.4)
        box = SurroundingRectangle(VGroup(code, notes), color=GREY_D, buff=0.35, corner_radius=0.1)
        src = Text("src/models/architectures/llm/proxy_former_llm.py", font=MONO, font_size=18, color=GREY_B)
        src.next_to(box, DOWN, buff=0.25)
        self.say(tr("当前实现用的是两张嵌入表：历史用 d_history，当下用 d_model。",
                    "The current implementation uses two embedding tables: d_history for the past, d_model for the present."),
                 Create(box), LaggedStartMap(FadeIn, code, lag_ratio=0.4), FadeIn(notes), FadeIn(src), run_time=2)
        self.clear_all()


class A03b_Sources(Base):
    """The 64-dim local stream can come from different sources; the memory math is the same."""

    def construct(self):
        header = T(tr("局部流从哪里来？", "Where does the local stream come from?"), 42).to_edge(UP, buff=0.4)
        self.say(tr("不过，64 维的局部流不一定非要来自一张独立的表。",
                    "But the 64-dim local stream doesn't have to come from a separate table."), FadeIn(header))

        def tok():
            b = RoundedRectangle(corner_radius=0.08, width=1.05, height=0.55, color=WHITE)
            return VGroup(b, Text("token", font=MONO, font_size=20).move_to(b))

        def table(label, w, h, color):
            r = Rectangle(width=w, height=h, stroke_color=color, fill_color=color, fill_opacity=0.25)
            grid = VGroup(*[Line(r.get_left() + RIGHT * w * k / 6, r.get_left() + RIGHT * w * k / 6 + UP * 0,
                                 stroke_width=0) for k in range(1)])
            return VGroup(r, grid, MathTex(label, font_size=26, color=color).move_to(r))

        def vec(n, color, cell=0.1):
            return VGroup(*[Square(cell, stroke_width=0.6, stroke_color=color, fill_color=color, fill_opacity=0.7)
                            for _ in range(n)]).arrange(DOWN, buff=0.01)

        rows = VGroup()
        # 1) separate history table (current implementation)
        r1 = VGroup(tok(), table(r"h\_embedding\;\; 50{,}257 \times 64", 3.6, 0.7, LOCAL_C), vec(8, LOCAL_C))
        # 2) shared x_embedding + projection
        r2 = VGroup(tok(), table(r"x\_embedding\;\; 50{,}257 \times 512", 3.6, 0.7, GEN_C), vec(16, GEN_C, 0.07),
                    table(r"W:\ 512 \to 64", 1.9, 0.7, PROXY_C), vec(8, LOCAL_C))
        # 3) other mappings
        r3 = VGroup(tok(), table(r"\text{other mapping}", 3.6, 0.7, GREY_B), vec(8, LOCAL_C))
        for r in (r1, r2, r3):
            r.arrange(RIGHT, buff=0.55)
        rows.add(r1, r2, r3)
        rows.arrange(DOWN, buff=0.75, aligned_edge=LEFT).shift(LEFT * 1.3 + DOWN * 0.15)
        for r in rows:
            arrows = VGroup(*[Arrow(r[k].get_right(), r[k + 1].get_left(), buff=0.08, stroke_width=3,
                                    max_tip_length_to_length_ratio=0.25) for k in range(len(r) - 1)])
            r.add(arrows)
        labels = VGroup(
            T(tr("① 独立历史嵌入表（当前实现）", "① separate history table (current code)"), 22, LOCAL_C),
            T(tr("② 共享生成嵌入 + 投影", "② shared generation table + projection"), 22, PROXY_C),
            T(tr("③ 其他映射方式", "③ other mappings"), 22, GREY_B),
        )
        for lab, r in zip(labels, rows):
            lab.next_to(r[0], UP, buff=0.12, aligned_edge=LEFT)
        out_l = MathTex(r"d_{\text{history}} = 64", font_size=30, color=LOCAL_C).next_to(rows, RIGHT, buff=0.35)

        self.say(tr("第一种，就是当前代码的做法：一张独立的 64 维历史嵌入表。",
                    "Option one is what the current code does: a separate 64-dim history table."),
                 FadeIn(labels[0]), FadeIn(rows[0], lag_ratio=0.1), run_time=1.5)
        self.say(tr("第二种：直接复用生成侧的 512 维嵌入，再用一个线性层投影到 64 维。",
                    "Option two: reuse the 512-dim generation embedding and project it down to 64 with a linear layer."),
                 FadeIn(labels[1]), FadeIn(rows[1], lag_ratio=0.1), run_time=1.5)
        self.say(tr("第三种：论文中也说明，局部流还可以通过其他方式得到。",
                    "Option three: as the paper notes, the local stream can also come from other mappings."),
                 FadeIn(labels[2]), FadeIn(rows[2], lag_ratio=0.1), run_time=1.2)
        self.play(Write(out_l))
        self.play(FadeOut(VGroup(rows, labels, out_l)))

        cmp = VGroup(
            VGroup(T(tr("① 独立表", "① separate table"), 28, LOCAL_C),
                   MathTex(r"50{,}257 \times 64 \approx 3.2\text{M params}", font_size=36, color=LOCAL_C)),
            VGroup(T(tr("② 投影矩阵", "② projection"), 28, PROXY_C),
                   MathTex(r"512 \times 64 = 32{,}768 \text{ params}", font_size=36, color=PROXY_C)),
        )
        for c in cmp:
            c.arrange(RIGHT, buff=0.6)
        cmp.arrange(DOWN, buff=0.5, aligned_edge=LEFT).shift(UP * 0.7)
        pros = T(tr("② 的好处：同一个 token 在历史与当下共享语义，参数少约 98 倍",
                    "Option ②: one token, one shared meaning in past and present, ~98x fewer parameters"), 26, GREY_A)
        fit(pros, 12.5).next_to(cmp, DOWN, buff=0.5)
        self.say(tr("第二种的好处：历史和当下共享同一套词表语义，而且投影只有 3.3 万个参数。",
                    "Option two keeps one shared vocabulary meaning for past and present, with only 33 thousand parameters."),
                 LaggedStartMap(FadeIn, cmp, shift=RIGHT * 0.2, lag_ratio=0.3), FadeIn(pros))
        same = T(tr("无论来源如何：进入网络后都是 64 维，显存账完全一样",
                    "Whatever the source: 64 dims once inside the network, the same memory math"), 30, YELLOW)
        fit(same, 12.5).next_to(pros, DOWN, buff=0.6)
        self.say(tr("关键是：无论从哪里来，局部流进入网络后都是 64 维，后面的显存账完全一样。",
                    "The key point: whatever the source, the local stream is 64-wide inside the network, "
                    "so the memory math is identical."), FadeIn(same, shift=UP * 0.2))
        self.clear_all()


class A04_DualStream(Base):
    def construct(self):
        header = T(tr("窄的历史流，宽的代理", "A narrow history stream, wide proxies"), 42).to_edge(UP, buff=0.4)
        self.say(tr("关键在于：历史的局部流，在每一层都保持 64 维。",
                    "The key: the history's local stream stays 64-wide in every layer."), FadeIn(header))
        layers = VGroup()
        for k in range(3):
            row = ribbon(32, 0.4, LOCAL_C, 0.16, 0.02)
            layers.add(row)
        layers.arrange(UP, buff=1.25).shift(LEFT * 1.3 + DOWN * 0.35)
        self.play(LaggedStartMap(FadeIn, layers, lag_ratio=0.3), run_time=1.2)
        prox = VGroup()
        for k in range(3):
            row = layers[k]
            ps = VGroup(*[column(1.0, PROXY_C, 0.3, 0.8) for _ in range(4)])
            for j, p in enumerate(ps):
                grp = VGroup(*row[j * 8:(j + 1) * 8])
                p.move_to([grp.get_center()[0], row.get_top()[1] + 0.62, 0])
            prox.add(ps)
        lp = MathTex(r"d_{\text{proxy}} = 512", font_size=32, color=PROXY_C).next_to(prox[2], RIGHT, buff=0.3)
        lf = MathTex(r"d_{\text{history}} = 64", font_size=32, color=LOCAL_C).next_to(layers[0], RIGHT, buff=0.3)
        self.say(tr("每一段历史先压缩成一个代理，而代理是 512 维的宽向量。",
                    "Each chunk of history is compressed into a proxy, and proxies are 512 wide."),
                 LaggedStart(*[FadeIn(p, shift=UP * 0.2) for p in prox], lag_ratio=0.25), Write(lp), Write(lf))
        gen = column(3.4, GEN_C, 0.6, 0.6).move_to(RIGHT * 5.3 + DOWN * 0.1)
        gl = MathTex(r"d_{\text{model}} = 512", font_size=32, color=GEN_C).next_to(gen, UP, buff=0.2)
        arcs = VGroup(*[CurvedArrow(gen.get_left() + UP * (0.8 - 0.8 * k), prox[k][-1].get_right(), angle=0.3,
                                    color=GEN_C, stroke_width=2) for k in range(3)])
        self.say(tr("生成侧是 512 维，它只和代理交互，不直接读 64 维的历史流。",
                    "The generation side is 512 wide and attends only to the proxies, never to the narrow stream directly."),
                 FadeIn(gen), Write(gl), LaggedStart(*[Create(a) for a in arcs], lag_ratio=0.2))
        self.play(FadeOut(VGroup(layers, prox, lp, lf, gen, gl, arcs)))

        eq = MathTex(r"64 \text{ tokens} \times 64 \text{ dims} = 4096", r"\;\longrightarrow\;",
                     r"1 \text{ proxy} \times 512 \text{ dims}", font_size=44)
        eq[0].set_color(LOCAL_C)
        eq[2].set_color(PROXY_C)
        note = T(tr("窄进，宽出：空间换通道", "narrow in, wide out: space traded for channels"), 30, GREY_B)
        VGroup(eq, note).arrange(DOWN, buff=0.6)
        self.say(tr("压缩比 64 时，一个代理汇总 64 个 token 乘 64 维，共 4096 个数，输出 512 维。",
                    "At ratio 64, one proxy summarizes 64 tokens times 64 dims, 4,096 numbers, into 512."),
                 Write(eq), run_time=2)
        self.say(tr("历史流窄，代理宽：信息在进入代理时被重新组织到更宽的通道里。",
                    "The stream is narrow, the proxy is wide: information is regrouped into wider channels."),
                 FadeIn(note, shift=UP * 0.2))
        self.say(tr("而且窄的历史流一直保留，某一层没压进代理的细节，下一层还能取到。",
                    "And the narrow stream persists, so detail one layer missed is still there for the next."))
        self.clear_all()


class A05_Accounting(Base):
    def construct(self):
        header = T(tr("算一笔账", "Let's do the math"), 44).to_edge(UP, buff=0.4)
        cond = T(tr("716,800 个 token 的历史 · 16 位精度 · 每层一个隐状态张量",
                    "716,800-token history · 16-bit · one hidden-state tensor per layer"), 24, GREY_B)
        fit(cond, 12).next_to(header, DOWN, buff=0.2)
        self.say(tr("来算一笔账：716,800 个 token 的历史，16 位精度，每层一个隐状态张量。",
                    "Let's do the math: a 716,800-token history, 16-bit, one hidden-state tensor per layer."),
                 FadeIn(header), FadeIn(cond))
        W = 6.8
        rows = [
            (tr("全宽历史", "full-width history"), r"716{,}800 \times 512 \times 2\,\text{B}", 734.0, BAD_C),
            (tr("64 维历史流", "64-dim history stream"), r"716{,}800 \times 64 \times 2\,\text{B}", 91.8, LOCAL_C),
            (tr("512 维代理", "512-dim proxies"), r"11{,}200 \times 512 \times 2\,\text{B}", 11.5, PROXY_C),
        ]
        grp = VGroup()
        for i, (name, formula, mb, c) in enumerate(rows):
            lab = VGroup(T(name, 26, c), MathTex(formula, font_size=24, color=GREY_B)).arrange(DOWN, aligned_edge=RIGHT,
                                                                                             buff=0.08)
            bar = Rectangle(width=max(W * mb / 734.0, 0.05), height=0.45, fill_color=c, fill_opacity=0.85,
                            stroke_width=0)
            val = T(f"{mb:.1f} MB", 26, c)
            y = 1.4 - i * 1.05
            lab.move_to([-2.9, y, 0], aligned_edge=RIGHT)
            bar.move_to([-2.6, y, 0], aligned_edge=LEFT)
            val.next_to(bar, RIGHT, buff=0.2)
            grp.add(VGroup(lab, bar, val))
        lines = [
            tr("全宽的话：716,800 乘 512 乘 2 字节，每层 734 MB。",
               "At full width: 716,800 times 512 times 2 bytes, 734 MB per layer."),
            tr("64 维的历史流只要 91.8 MB。", "The 64-dim history stream needs just 91.8 MB."),
            tr("代理只有 11,200 个，512 维也只占 11.5 MB。", "There are only 11,200 proxies; even at 512 wide they take 11.5 MB."),
        ]
        for g, line in zip(grp, lines):
            self.say(line, FadeIn(g[0]), GrowFromEdge(g[1], LEFT), FadeIn(g[2]), run_time=1.3)
        tot = VGroup(T(tr("合计", "total"), 30, WHITE), T("103.2 MB", 40, GOOD_C), T(tr("约为 1/7.1", "≈ 7.1× smaller"), 30, GOOD_C)
                     ).arrange(RIGHT, buff=0.5).to_edge(DOWN, buff=1.5)
        self.say(tr("合计 103 MB，比全宽小 7.1 倍。", "Together: 103 MB, 7.1 times smaller than full width."),
                 FadeIn(tot, shift=UP * 0.2))
        ten = T(tr("10 层：7.3 GB → 1.0 GB", "10 layers: 7.3 GB → 1.0 GB"), 30, YELLOW).next_to(tot, UP, buff=0.3)
        self.say(tr("10 层就是 7.3 GB 对 1.0 GB。真实训练每层会保存好几个这样的张量，省下的也按同样比例叠加。",
                    "Over 10 layers, 7.3 GB versus 1.0 GB. Training keeps several such tensors per layer, "
                    "so the savings stack the same way."), FadeIn(ten))
        self.clear_all()

        header = T(tr("代价：多一张小嵌入表", "The cost: one small extra table"), 40).to_edge(UP, buff=0.5)
        t1 = VGroup(T(tr("历史嵌入表", "history table"), 28, LOCAL_C),
                    MathTex(r"50{,}257 \times 64 \approx 3.2\text{M params}", font_size=36, color=LOCAL_C)
                    ).arrange(DOWN, buff=0.15)
        t2 = VGroup(T(tr("生成嵌入表（与输出层共享）", "generation table (tied to the output head)"), 28, GEN_C),
                    MathTex(r"50{,}257 \times 512 \approx 25.7\text{M params}", font_size=36, color=GEN_C)
                    ).arrange(DOWN, buff=0.15)
        VGroup(t1, t2).arrange(DOWN, buff=0.6).shift(UP * 0.2)
        note = T(tr("固定成本，不随历史长度增长", "a fixed cost that does not grow with history length"), 28, YELLOW)
        note.next_to(VGroup(t1, t2), DOWN, buff=0.6)
        self.say(tr("代价是多了一张历史嵌入表：五万词表乘 64，约 320 万参数。",
                    "The cost is one extra history table: 50K vocabulary times 64, about 3.2 million parameters."),
                 FadeIn(header), FadeIn(t1, shift=UP * 0.2))
        self.say(tr("它是固定成本，不随历史变长而增长；而省下的激活显存随长度线性增长。",
                    "It's a fixed cost that never grows with the history, while the activation savings grow with length."),
                 FadeIn(t2, shift=UP * 0.2), FadeIn(note))
        self.clear_all()


class A06_Results(Base):
    def construct(self):
        header = T(tr("实测结果（完整设计）", "Measured results (full design)"), 42).to_edge(UP, buff=0.4)
        cfg = T(tr("d_model = 512 · d_history = 64 · 10 层 · 压缩比 64", "d_model = 512 · d_history = 64 · 10 layers · ratio 64"),
                26, GREY_B).next_to(header, DOWN, buff=0.2)
        self.say(tr("论文里所有的实测结果，用的都是这组配置：生成侧 512 维，历史 64 维。",
                    "Every measured result in the paper uses this setup: 512 on the generation side, 64 for the history."),
                 FadeIn(header), FadeIn(cfg))
        items = VGroup(
            T(tr("单卡 16 GB：约 2.1 万 token 历史，15.6 GB → 2.9 GB，速度 1.3 → 16.1 it/s",
                 "One 16 GB GPU, ~21K-token history: 15.6 GB → 2.9 GB, 1.3 → 16.1 it/s"), 26),
            T(tr("可训练历史长度：716,800 token，约为全注意力的 35 倍",
                 "Trainable history: 716,800 tokens, ~35× a full-attention model"), 26),
            T(tr("多针检索（64K 训练）：256K 为 99%–100%，100 万 token 为 92%–95%",
                 "Multi-needle retrieval (trained on 64K): 99–100% at 256K, 92–95% at 1M tokens"), 26),
            T(tr("WikiText-103 困惑度：压缩历史 21.01，全注意力基线 21.36",
                 "WikiText-103 perplexity: 21.01 with compressed history vs 21.36 baseline"), 26),
        ).arrange(DOWN, buff=0.4, aligned_edge=LEFT)
        fit(items, 12.5).shift(DOWN * 0.1)
        lines = [
            tr("同样两万多 token 的历史，显存从 15.6 GB 降到 2.9 GB。", "With ~21K tokens of history, memory falls from 15.6 GB to 2.9 GB."),
            tr("一块 16 GB 的卡，可以训练 71.7 万 token 的历史。", "One 16 GB card trains on 716,800 tokens of history."),
            tr("64 维的历史并没有丢掉记忆：一百万 token 的多针检索仍有九成以上。",
               "A 64-dim history doesn't forget: multi-needle retrieval stays above 90% at a million tokens."),
            tr("语言建模质量也保持住了。", "And language-modeling quality holds."),
        ]
        for it, line in zip(items, lines):
            self.say(line, FadeIn(it, shift=RIGHT * 0.2))
        caveat = T(tr("注：以上是压缩 + 非对称嵌入的整体效果，不是单独消融",
                      "Note: these reflect compression + asymmetric embeddings together, not an isolated ablation"), 22, YELLOW)
        fit(caveat, 12.5).to_edge(DOWN, buff=1.3)
        self.say(tr("需要说明：这些是完整设计的整体结果，并不是只拆出非对称嵌入的单独消融。",
                    "To be precise: these are results of the full design, not an ablation of the embedding alone."),
                 FadeIn(caveat))
        self.clear_all()


class A07_Outro(Base):
    def construct(self):
        header = T(tr("一个可以调的旋钮", "A knob you can turn"), 42).to_edge(UP, buff=0.5)
        self.say(tr("d_history 其实是一个可以调的旋钮。", "d_history is really a knob you can turn."), FadeIn(header))
        dials = VGroup()
        for d, c in ((32, LOCAL_C), (64, GOOD_C), (128, PROXY_C)):
            dials.add(VGroup(column(0.25 * d / 32, c, 1.2, 0.7), MathTex(rf"d_{{\text{{history}}}} = {d}", font_size=32, color=c)
                             ).arrange(DOWN, buff=0.25))
        dials.arrange(RIGHT, buff=1.4, aligned_edge=DOWN).shift(UP * 0.3)
        tradeoff = T(tr("更窄 → 更省显存；更宽 → 每个 token 保留更多细节",
                        "narrower → less memory; wider → more detail per token"), 28, GREY_B).next_to(dials, DOWN, buff=0.6)
        fit(tradeoff, 12.5)
        self.say(tr("更窄更省，更宽保留更多细节；论文实验用的是 64。",
                    "Narrower saves more, wider keeps more detail; the paper's experiments use 64."),
                 LaggedStartMap(FadeIn, dials, shift=UP * 0.2, lag_ratio=0.3), FadeIn(tradeoff))
        idea = T(tr("设想：越久远的历史，越窄", "an idea: the older the history, the narrower"), 28, YELLOW)
        idea.next_to(tradeoff, DOWN, buff=0.4)
        self.say(tr("一个自然的延伸：越久远的历史用越窄的宽度，这仍有待实验验证。",
                    "A natural extension: make older history narrower still. That remains to be tested."),
                 FadeIn(idea))
        self.clear_all()

        title = Text("ProxyFormer", font=SERIF, font_size=72)
        tag = T(tr("历史要长，不必要宽", "Long history. Narrow history."), 36, BLUE_B)
        badge = Text("PATENT PENDING", font=SERIF, font_size=34, color=YELLOW)
        info = VGroup(Text("arXiv:2608.23463", font=MONO, font_size=24, color=GREY_A),
                      Text("github.com/simonFelix-Ai/proxy-former", font=MONO, font_size=24, color=GREY_A),
                      Text("tangzhongp@qq.com", font=MONO, font_size=24, color=GREY_A)).arrange(DOWN, buff=0.2)
        lic = T(tr("学术与非商业研究免费 · 欢迎商业授权与合作", "Free for academic research · open to licensing & collaboration"),
                24, GREY_B)
        fit(lic, 12)
        VGroup(title, tag, badge, lic, info).arrange(DOWN, buff=0.35)
        self.say(tr("历史要长，不必要宽。这就是非对称嵌入。", "Long history, narrow history. That's asymmetric embedding."),
                 Write(title), FadeIn(tag, shift=UP * 0.2), run_time=1.6)
        self.say(tr("代理 Token 方法已申请专利，欢迎合作。论文和代码都在这里，感谢观看。",
                    "The Proxy Token method is patent pending, and collaborations are welcome. Paper and code are here. "
                    "Thanks for watching."), FadeIn(badge), FadeIn(lic), FadeIn(info, shift=UP * 0.2))
        self.wait(1.2)
        self.clear_all(run_time=1.0)


SCENES = [A00_Hook, A01_Title, A02_WhereMemoryGoes, A03_TwoRoles, A03b_Sources, A04_DualStream, A05_Accounting, A06_Results,
          A07_Outro]

CHAPTERS = {
    "A00_Hook": tr("开场", "Intro"),
    "A02_WhereMemoryGoes": tr("显存花在哪里", "Where the memory goes"),
    "A03_TwoRoles": tr("历史与当下的分工", "Two jobs, two widths"),
    "A03b_Sources": tr("局部流的来源", "Sources of the local stream"),
    "A04_DualStream": tr("窄历史流与宽代理", "Narrow stream, wide proxies"),
    "A05_Accounting": tr("算一笔账", "The math"),
    "A06_Results": tr("实测结果", "Measured results"),
    "A07_Outro": tr("旋钮与总结", "The knob, and wrap-up"),
}
