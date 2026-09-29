# Your Compressor Already Knows Where Your Data Came From

## A tiny autoencoder, a three-step cliff, and a new way to think about routing in modular language models

*[Image: compress_is_routing-hook.gif]*

Every time you fine-tune a large language model on something new, it quietly loses something old. This is **catastrophic forgetting**, and it's a big part of why updating a frontier model is so expensive: to keep the old skills alive, you mix mountains of old data back into every new training run.

Mixture-of-Experts (MoE) models offer one way out: split the model into specialists. But that raises a new question: *who decides which specialist gets which input?* Usually the answer is a separately trained **gating network**. That's one more component to train, and its decisions are notoriously hard to interpret.

This post is about a different answer, from my technical report *Compression is Routing*: **you may not need to learn the router at all. The compressor already knows.**

---

## Compression is intelligence, and its overlooked corollary

There's a well-known idea in machine learning that **prediction and compression are two sides of the same coin**. Delétang et al. (2024) made this rigorous in *Language Modeling Is Compression*: a model that predicts the next token well can compress text well, and vice versa.

Predictable text compresses to very few bits, and chaotic or unfamiliar text needs many more.

That leads to a corollary that gets less attention:

> **A compressor is only good at compressing the kind of data it was trained on.**

Flip that around and you get something useful. *How well* a compressor handles an input tells you whether that input is "one of its own." Compression quality becomes a **fingerprint** of the data's origin.

The rest of this post tests that intuition.

---

## The experiment: 512 tokens through an 8-vector keyhole

*[Image: fig-architecture.png]*

I trained an **87M-parameter Transformer autoencoder**, end to end:

- The **encoder** takes a block of **512 tokens** and compresses it, through attention, into **8 latent vectors**. That's a **64:1** compression along the sequence axis.
- The **decoder** rebuilds the original 512 tokens from those 8 vectors.

The key design choice is **strict isolation**. The decoder never sees the original tokens. Besides the latents z, it receives only an auxiliary signal m that has the same length as the input but carries no content. Every bit of information has to squeeze through those 8 vectors. That rules out shortcuts and forces the encoder to learn the structure of the data rather than just pass a signal along.

The model was trained on **source code only** (codeparrot-clean, GPT-2 tokenizer).

To score reconstructions, I used a deliberately strict metric: **token-level reconstruction accuracy (TRA)**, the fraction of positions where the rebuilt token *exactly* matches the original. If the input is `[1, 2, 3, 4, 5]` and the output is `[1, 2, 6, 7, 5]`, TRA is 3/5 = 60%. "Roughly the same meaning" earns nothing.

---

## The result: a three-step cliff

*[Image: fig-results.png]*

| Evaluation data | Tokens | Reconstruction accuracy |
|---|---:|---:|
| Code, held-out (in-domain) | 3,170,816 | **99.47%** |
| Wikipedia (semi-out-of-domain) | 320,512 | **47.76%** |
| Random tokens (fully out-of-domain) | 3,170,816 | **0.57%** |

Each number says something different:

- **99.47%** on code the model has never seen shows that 8 vectors carry enough capacity to encode 512 tokens of code almost perfectly.
- **47.76%** on Wikipedia is *not* noise: random guessing would score about 1/|V| ≈ 0.002%. The model is using what code and English share, such as vocabulary and low-level statistics. The two distributions partly overlap.
- **0.57%** on random tokens shows the model didn't degenerate into a copy machine. It rejects inputs that don't match what it learned.

One compressor, three distributions, three clearly separated levels.

---

## What the latent space looks like

*[Image: fig-latent.png]*

Visualizing the latent vectors (t-SNE and UMAP in the paper) shows the geometry behind those numbers:

- **Two islands.** Code and Wikipedia latents form two dense clusters with empty space between them.
- **Linear separability.** A single straight line separates them, so a routing decision is nearly free.
- **Low intrinsic dimension.** z has 512 dimensions, but about **200 principal components explain 95%** of the variance on code. The encoder keeps the skeleton of the data and drops redundancy.

The 64× bottleneck seems to *force* different distributions onto different sub-manifolds, and that separation is exactly what a router needs.

---

## From fingerprint to router

*[Image: fig-routing.png]*

Now put the pieces together:

1. Give every expert in a modular system its **own compressor**, trained only on its domain.
2. When an input arrives, **let every compressor try to reconstruct it**.
3. **Route to whichever reconstructs it best.**

That's the whole rule. There's no gating network and no extra routing parameters, and every decision comes with a readable explanation: *this expert reconstructed the input at 99%, the others at around 40%.*

It also changes how a system learns something new. Suppose medical notes arrive and **every** compressor reconstructs them poorly. That low score is itself a signal: *nobody here knows this.* So you **mount a new compressor** for the new domain and train only it, while every existing expert stays frozen. Old knowledge isn't overwritten, because nothing touches its parameters.

Instead of a monolith that has to be re-trained every time the world changes, you get an ecosystem that **grows by adding modules**.

There's a bonus as well: because 512 positions become 8 vectors, the same idea points toward much cheaper long contexts. That's a 64× shorter sequence than a standard KV cache for the same span.

---

## What this does *not* show yet

I think this section matters as much as the results.

- **No continual-learning benchmark yet.** The argument that frozen experts avoid forgetting holds by construction, but I haven't measured the whole system on a standard continual-learning suite.
- **Hysteresis.** Compression uses fixed 512-token windows. When a document switches domain mid-window (a novel that suddenly contains code), the latent is still dominated by what came before, and the error spikes at the boundary.
- **Interleaved data.** Real text mixes distributions, like blog posts with code snippets. A window that contains both lands in a gray zone.
- **Limited ablations.** At this setting, 8 latent vectors was the smallest length that reconstructed near-losslessly; 2 or 4 lost a lot of information. Early runs suggest 128× or more might be reachable, and I suspect there's an entropy-based scaling law linking latent length to sequence length. Testing that needs more compute than I have.

In early exploration, the same three-tier pattern also appeared with a custom tokenizer on Chinese novels, which suggests the effect isn't tied to one language or tokenizer.

---

## Why this matters

"Compression is prediction" has been a powerful lens on language models. This work suggests extending it: **compression is routing.** A compressor's reconstruction error is an intrinsic, interpretable signal of where data belongs, and it could replace learned gating while making modular systems easier to extend without forgetting.

This is a starting point, not a finished system. If you work on continual learning, MoE, or context compression and have ideas, criticism, or compute, I'd like to hear from you.

**Watch the 8-minute animated explainer:** [VIDEO_LINK]
**Read the paper:** [PAPER_LINK]
**Code and materials:** https://github.com/simonFelix-Ai/compression_is_routing

---

### References

- Delétang et al. (2024). *Language Modeling Is Compression.* arXiv:2309.10668
- Ge et al. (2024). *In-context Autoencoder for Context Compression in a Large Language Model.* arXiv:2307.06945
- Mu, Li & Goodman (2024). *Learning to Compress Prompts with Gist Tokens.* arXiv:2304.08467
- Kuratov et al. (2025). *Cramming 1568 Tokens into a Single Vector and Back Again.* arXiv:2502.13063
- Berton et al. (2025). *CompLLM: Compression for Long Context Q&A.* arXiv:2509.19228
- Wei, Sun & Li (2025). *DeepSeek-OCR: Contexts Optical Compression.* arXiv:2510.18234

---- POSTING NOTES (do not copy below this line) ----
- Replace each "[Image: ...]" line by uploading that file at that spot in the Medium editor.
  Medium can't take a GIF by URL; upload the .gif file itself.
- Paste the YouTube URL alone on its own line. Medium turns it into an embedded player.
- Tags (max 5): Machine Learning, Artificial Intelligence, LLM, Deep Learning, Research.
- For more reach, submit to the "Towards Data Science" or "Towards AI" publications instead of posting on
  your own profile. They review submissions, usually within a few days.
- The same article works on Substack, dev.to or Hashnode. If you cross-post, set the canonical URL to the
  first version so search engines don't treat the copies as duplicates.
