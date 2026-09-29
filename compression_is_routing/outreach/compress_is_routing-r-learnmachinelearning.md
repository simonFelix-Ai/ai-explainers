TITLE:
I made a 3Blue1Brown-style explainer of my paper: why a compressor's error can tell you where data came from (8 min)

BODY:
I wrote a short technical report and then animated it, hoping it's useful to people learning about autoencoders, OOD detection, or mixture-of-experts.

**The idea in three steps:**

1. **Prediction ⇔ compression.** A model that predicts text well can compress it well (Delétang et al., 2024).
2. **Corollary:** a compressor is only good at the kind of data it was trained on.
3. **So its reconstruction error is a fingerprint.** I trained an autoencoder on code that squeezes 512 tokens into 8 vectors. It rebuilds unseen code at 99.47% exact-token accuracy, Wikipedia at 47.76%, and random tokens at 0.57%.

That fingerprint can act as a router between expert models, with no extra gating network to train.

The video covers the architecture (and why the decoder must never see the input), the metric, the latent-space geometry (two linearly separable clusters, about 200 effective dimensions out of 512), and the limitations.

Video: [VIDEO_LINK]
Paper: [PAPER_LINK]
The Manim source is in the repo if you want to reuse the animations: https://github.com/simonFelix-Ai/compression_is_routing

Feedback on clarity is very welcome. Tell me which part lost you.

---- POSTING NOTES (do not copy below this line) ----
- This sub is fine with video posts, so you can post the YouTube link directly with this text in the body.
- Low-stakes, friendly audience. Good for collecting "what was confusing" feedback before bigger posts.
