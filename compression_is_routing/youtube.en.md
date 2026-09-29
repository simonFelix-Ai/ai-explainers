# YouTube upload kit (English)

## Title

Recommended:

> **Compression Is Routing: The Trick That Could End Catastrophic Forgetting**

Alternatives:

- No Router, No Forgetting? How Compression Tells an AI What It Knows
- This 87M Model Knows What It Doesn't Know (Compression Is Routing)
- Why Your LLM Forgets, and a Radical Fix: Compression Is Routing

> Avoid "completely solves catastrophic forgetting": the paper argues it architecturally
> but does not yet run a continual-learning benchmark. ML viewers will call it out in the
> comments. "Could end" / "?" keeps the hook and stays defensible.

## Thumbnail

`thumbnail.en.png` (1280×720)

## Description

```
Every time you fine-tune a language model on something new, it quietly forgets something old.
What if the fix was hiding in compression?

An 87M-parameter Transformer autoencoder squeezes 512 tokens into just 8 vectors (64× compression).
On code it has never seen, it rebuilds 99.47% of tokens exactly. On Wikipedia: 47.76%. On random
tokens: 0.57%. That gap turns reconstruction error into a built-in fingerprint of where data comes
from, so it can route inputs to experts with no gating network, and lets you add new experts
without touching (or forgetting) the old ones.

📄 Paper: Compression is Routing: Reconstruction Error as an Intrinsic Signal for Modular Language Models, Zhongpan Tang (2025)
💻 Repo: https://github.com/simonFelix-Ai/compression_is_routing

Chapters
0:00 Intro
0:22 Why LLMs forget (and why MoE routing is hard)
1:14 Compression is intelligence
1:59 A 64× Transformer autoencoder
3:00 Measuring reconstruction
3:29 The three-step cliff: 99.47% / 47.76% / 0.57%
4:23 Inside the latent space
5:14 Compression is routing (and forgetting)
6:25 Bonus: 64× less memory
6:47 Limitations and open questions
7:49 Wrap-up

Note: latent-space scatter, PCA curve and the routing percentages are illustrations;
the 99.47 / 47.76 / 0.57 results are from the paper.

References
- Delétang et al. (2024) Language Modeling Is Compression, arXiv:2309.10668
- Ge et al. (2024) In-context Autoencoder (ICAE), arXiv:2307.06945
- Mu et al. (2024) Gist Tokens, arXiv:2304.08467
- Kuratov et al. (2025) Cramming 1568 Tokens into a Single Vector, arXiv:2502.13063

#MachineLearning #LLM #MixtureOfExperts
```

## Tags

catastrophic forgetting, continual learning, mixture of experts, MoE routing, LLM, transformer
autoencoder, context compression, compression is intelligence, modular neural networks,
reconstruction error, out-of-distribution detection, KV cache, machine learning explained

## Subtitles

Upload `compression_is_routing.en.srt` as English captions. Captions are also burned into the
video. For a voiceover, the SRT doubles as a timed narration script.
