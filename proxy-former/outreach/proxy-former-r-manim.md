TITLE:
Manim explainer of my ML architecture, rendered in Chinese and English from one script (tr() strings)

BODY:
This is my second paper explainer in Manim CE. This time one script renders both a Chinese and an English version: every string is written as `tr(chinese, english)` and an env var picks the language.

Scenes you might find reusable:

* **Cold open built for retention:** frame 0 already shows a GPU memory bar filling. It goes red with OUT OF MEMORY at ~1.8 s, then a ValueTracker-driven counter races to 716,800 tokens.
* **Conference analogy:** 24 dots with all 276 pairwise arcs (ArcBetweenPoints), collapsing into 4 "representative" dots with 6 arcs.
* **Dual-stream layer stack:** compress lines up, proxy link, dashed inject lines down, and the local stream flowing through.
* **Heatmap reveal:** a real 10×9 accuracy grid with an RdYlGn-style color ramp, revealed column by column as the haystack length grows, with SurroundingRectangle callouts.
* **Space-to-channel:** a rectangle trading length for width while the cost formula morphs to β/α² ≤ 1.
* **Subtitles as data:** a `say()` helper burns captions in and exports per-scene cue JSON, merged into an SRT and YouTube chapters.

Video: [VIDEO_LINK]
Source: [SOURCE_LINK]

Feedback on pacing and visual clarity is very welcome.

---- POSTING NOTES (do not copy below this line) ----
- [SOURCE_LINK]: the Manim source lives in the private ai-explainers repo (proxy-former/). Make that
  repo (or a copy of the proxy-former/ folder) public first, or drop the Source line.
- Also fits r/3Blue1Brown, and 3b1b's Summer of Math Exposition (SoME) if it's open.
