# Let the Representatives Talk: How Proxy Tokens Stretch One GPU to 700K Tokens

## ProxyFormer compresses local chunks into proxies, runs attention only among them, and never throws the original tokens away

*[Image: proxy-former-hook.gif]*

Put a standard Transformer on a single 16 GB GPU and try to train it on long sequences. Around 20,000 tokens, it runs out of memory.

Put **ProxyFormer** on the same card and it trains on **716,800** tokens.

This post explains how, and it's simpler than you might expect.

---

## Why long context is expensive

Attention asks every token to look at every other token. Eight tokens means 64 pairs. Double the length and the work quadruples. At a million tokens, you're at a trillion pairs.

Inference has its own bill. The KV cache, which stores keys and values for everything the model has seen, grows linearly with context and eats GPU memory fast.

---

## The core idea: elect representatives

*[Image: fig-proxy-idea.png]*

Picture a ten-thousand-person conference. Everyone can't talk to everyone; even 24 people make 276 separate conversations.

A better protocol:

1. **Each table elects a representative**, who listens to everyone at the table. That's *compression*: a chunk of tokens becomes one **proxy token**.
2. **Only the representatives meet.** Four reps need just 6 conversations. That's *global attention*, run only in the tiny proxy space.
3. **Each rep goes back and briefs their table.** That's *decompression and injection*: the global picture flows back into every token.

*[Image: fig-proxy-cost.png]*

If every r tokens become one proxy, global attention cost drops to **(1/r)²** and length-dependent memory to **1/r**. At r = 64, attention costs one four-thousandth of the original.

---

## The key: two streams, not one-shot compression

*[Image: fig-dual-stream.png]*

The obvious objection is that compression loses information. If you compress once and throw the original away, whatever got dropped is gone for good.

ProxyFormer doesn't throw it away. It keeps **two parallel streams**:

- a **fine-grained local stream** (the full-resolution tokens), and
- a **coarse proxy stream**.

In *every* layer, local features condense into proxies ("micro guides macro"), the proxies interact globally, and the result is decompressed and injected back into the local stream ("macro guides micro"). The local stream then carries on to the next layer.

So detail that one compression step misses is still there for the next layer to extract. This is what separates the design from architectures that compress once and move on.

---

## What makes it practical

- **Cascaded compression.** Instead of one 64× jump, compress 4× three times (64 = 4·4·4), and decompress through a symmetric cascade.
- **Dynamic ratios.** Different layers, or more distant history, can use different compression ratios.
- **Proxy KV cache.** At generation time a new token attends only to the proxies, a cache of length L/P, not to the full history.
- **Asymmetric embeddings.** History is embedded in a narrow width (e.g. 64) while the current input uses the full width (e.g. 512), so memory savings start at the very first layer.
- **Space-to-channel.** Raise the compression ratio by α and proxies get α× shorter, so attention drops by α². Reinvest that into channels by making each proxy β× wider, and the cost becomes β/α². As long as β ≤ α², the budget doesn't grow, while each proxy carries more. The harder you compress, the more room you have to make proxies stronger, which in turn supports higher ratios.
- **Plain operators.** Chunking and compression use reshape, Linear and Conv. Interaction is standard SDPA (or an SSM). Injection uses Linear or ConvTranspose. There are no sparse indexers and no custom CUDA kernels.

---

## Results

These are small research models (d_model 512). The goal is to show the architecture works, not to top a leaderboard.

### Memory and speed

*[Image: fig-memory.png]*

One 16 GB GPU, batch size 1:

| Model | History (tokens) | VRAM | Training speed |
|---|---:|---:|---:|
| Full-attention baseline | 20,992 | 15.6 GB | 1.3 it/s |
| ProxyFormer (r = 64) | 20,992 | 2.9 GB | 16.1 it/s |
| ProxyFormer (r = 64) | 716,800 | 15.1 GB | 2.7 it/s |

At the same length, it uses about one-fifth of the memory and trains about 12× faster. Filling the card gives roughly **35×** the trainable sequence length of a standard decoder.

### Needles in a million-token haystack

This test is much harder than the usual single-needle one. **50 different passkeys** are hidden in every document at depths from 0% to 90%. **Every one** is queried, over 100 rounds per length, which comes to 5,000 lookups per length.

*[Image: fig-niah-256k.png]*

A model trained on a **64K** window:
- **128K** (2× beyond training): 100% at every depth
- **256K** (4×): 99–100%
- **512K** (8×): 98–100%

*[Image: fig-niah-1m.png]*

- **1,048,576 tokens** (16×): still **92–95%** at every depth, with no lost-in-the-middle dip.

A model trained on only an **8K** window still exceeds 94% at 256K (32× extrapolation) before degrading at 512K and beyond.

### Quality

On WikiText-103 (no positional encoding), perplexity is 21.36 for a decoder-only baseline without history, 22.10 for ProxyFormer without history, and **21.01 for ProxyFormer with compressed history**.

Preliminary image generation works in both pixel space (CIFAR-10 FID 16.21, MNIST FID 2.06) and latent space (MNIST FID 4.36).

---

## Beyond text

The same chunk → compress → interact → decompress recipe applies to 2D image patches, 3D video, point clouds and voxels, and higher-dimensional tensors. In text-to-image generation, the text condition only needs to interact with the compressed image proxies, not every pixel, which makes cross-modal fusion cheap.

---

## Where it came from

ProxyFormer builds on three observations from my earlier work:

1. **Shortening the sequence is feasible**: TLinformer (arXiv:2508.20407) and TConstFormer (arXiv:2509.00202).
2. **Sequences compress almost losslessly**: *Compression Is Routing* (arXiv:2512.16963) squeezed 512 tokens into 8 vectors and rebuilt them with 99.47% accuracy.
3. **Space can be traded for channels**, as image VAEs have shown for years.

If a sequence can be compressed almost losslessly, there's little reason to run expensive attention on the uncompressed version.

---

## Open questions and an invitation

The big open question is scale: how this behaves at billions of parameters, and on reasoning-heavy long-context benchmarks rather than retrieval alone. As an independent researcher, I don't have the compute to answer that.

**The Proxy Token method is patent pending.** Code and weights are free for academic and non-commercial research. For commercial licensing, or if you can contribute compute, research funding or a real long-context use case, please get in touch.

🎬 **Watch the 6-minute animated explainer:** [VIDEO_LINK]
📄 **Paper:** https://arxiv.org/abs/2608.23463
💻 **Code:** https://github.com/simonFelix-Ai/proxy-former
📧 **Contact:** tangzhongp@qq.com

---- POSTING NOTES (do not copy below this line) ----
- Replace each "[Image: ...]" line by uploading that file from this folder at that spot.
- Paste the YouTube URL on its own line so Medium embeds the player.
- Tags: Machine Learning, Artificial Intelligence, LLM, Deep Learning, Transformers.
- Submit to Towards Data Science or Towards AI for reach. If cross-posting to Substack or dev.to,
  set the canonical URL to the first version.
