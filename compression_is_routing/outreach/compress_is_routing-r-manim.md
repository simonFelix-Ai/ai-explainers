TITLE:
Explaining my own ML paper with Manim: "Compression Is Routing" (source included)

BODY:
After finishing a technical report, I animated the whole thing in Manim CE in the 3b1b style: dark background, LaTeX formulas, everything built up step by step.

Some scenes you might find reusable:

* **Autoencoder funnel:** a 512-cell token grid flowing through an encoder trapezoid into 8 latent bars, with a brace showing the 64:1 ratio.
* **Animated bar chart:** bars grow to 99.47% / 47.76% / 0.57%, driven by ValueTrackers and always_redraw with live DecimalNumber labels.
* **Latent-space scatter** with a linear separator, plus a PCA cumulative-variance curve.
* **Expert routing diagram:** frozen experts get lock icons and a new expert slides in.
* **Burned-in subtitles** from a small `say()` helper that also exports an SRT timeline, so the video can be dubbed later.

The first ~5 seconds are a cold open designed for YouTube retention: motion starts on frame one, the key result lands by about 3.5 s, and the title arrives at 5 s.

Video: [VIDEO_LINK]
Source: https://github.com/simonFelix-Ai/compression_is_routing/tree/main/video

Feedback on pacing, color choices, or animation technique is very welcome.

---- POSTING NOTES (do not copy below this line) ----
- Also consider r/3Blue1Brown with the same text.
- If the video/ folder is not on main yet, merge the branch first or link the branch path instead.
- If 3Blue1Brown's Summer of Math Exposition (SoME) is open, submit there too.
