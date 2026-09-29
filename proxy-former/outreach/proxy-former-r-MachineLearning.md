TITLE:
[R] ProxyFormer: compress chunks into proxy tokens, attend only among proxies, inject back into a persistent local stream. Trains ~717K-token sequences on one 16 GB GPU

BODY:
I'm an independent researcher, and I'd like critical feedback on an architecture for ultra-long context.

**Idea**

In each layer, fine-grained local chunks are compressed bottom-up into a small set of **proxy states**. Global attention runs *only* among the proxies. The globally contextualized proxies are then decompressed and injected top-down back into the local stream.

The local stream persists across layers. Detail that one compression step misses is still there for later layers to recover, which avoids the irreversible loss of one-shot compression (the paper calls this dual-stream design "micro guides macro / macro guides micro").

With compression ratio r, global attention cost goes to (1/r)² and length-linear memory to 1/r. Decoding only needs a **proxy KV cache** of length L/P. Other pieces:

* factorized multi-level compression (e.g. 64 = 4·4·4), with a symmetric cascade on the way back up
* layer-wise and distance-dependent compression ratios
* asymmetric embeddings: history in a narrow width (e.g. 64), current tokens in the full width (e.g. 512)
* a "space-to-channel" budget argument: raise the ratio by α and widen proxies by β, and the attention cost scales as β/α², so the budget holds as long as β ≤ α²

It's built only from reshape / Linear / Conv, standard SDPA (or an SSM) and ConvTranspose. There are no sparse indexers and no custom CUDA kernels.

**Results** (small models, d_model 512; the goal is feasibility, not SOTA)

*Memory and speed, one 16 GB GPU, batch size 1:*

| Model | History | VRAM | Train speed |
|:--|--:|--:|--:|
| Full-attention baseline | 20,992 | 15.6 GB | 1.3 it/s |
| ProxyFormer (r = 64) | 20,992 | 2.9 GB | 16.1 it/s |
| ProxyFormer (r = 64) | 716,800 | 15.1 GB | 2.7 it/s |

A standard decoder-only model tops out around 20K training tokens on this card, so that's roughly a 35× longer trainable sequence.

*Multi-needle retrieval.* 50 distinct passkeys are inserted per document at 0–90% depth, every needle is queried, and each length is repeated for 100 rounds, giving 5,000 lookups per length.

* Trained on a **64K** window: 128K → **100%** at every depth; 256K → **99–100%**; 512K → 98–100%; **1M (16× extrapolation) → 92–95%**
* Trained on an **8K** window: 256K (32×) → >94%. It degrades beyond that: about 0.7 at 512K and about 0.33 at 1M.
* Accuracy is flat across depth, with no lost-in-the-middle dip.

*Language modeling* (WikiText-103, no positional encoding), perplexity:

* decoder-only baseline (no history): 21.36
* ProxyFormer (no history): 22.10
* ProxyFormer with compressed history: 21.01

*Images (preliminary):* pixel-space flow matching reaches FID 16.21 on CIFAR-10 and 2.06 on MNIST. Latent-space flow matching also works (MNIST FID 4.36).

**Limitations and what I'd like feedback on**

1. **Scale.** Everything here is small. I don't know how this behaves at 1B+ parameters, and I don't have the compute to find out.
2. **Related work.** How do you see this relative to hierarchical designs (Funnel / Hourglass Transformers), inducing-point or latent approaches (Perceiver, Set Transformer), and memory or recurrence methods (RMT, AutoCompressors, Landmark Attention)? My view is that the per-layer compress → interact → inject loop over a persistent local stream is the key difference, but I'd like to hear where you think the overlap is.
3. **Benchmarks.** NIAH is a retrieval stress test, not a reasoning test. Which long-context benchmark (RULER, LongBench, BABILong...) would you want to see first?

Paper: https://arxiv.org/abs/2608.23463
Code: https://github.com/simonFelix-Ai/proxy-former
6-minute animated explainer: [VIDEO_LINK]

Disclosure: the Proxy Token method is patent pending. Code and weights are free for academic and non-commercial research.

---- POSTING NOTES (do not copy below this line) ----
- Text post, "Research" flair, weekday 8–10 am US Eastern. Stay 2–3 hours and answer every comment.
- Expect pushback on the patent and the non-commercial license. Stay calm: "It lets me keep doing this as an
  independent researcher; academic use is fully free." Don't argue further.
- Expect "compare against X". Thank them and say what's feasible with your compute. Don't claim results
  you haven't run.
- The PPL rows are not a perfect apples-to-apples comparison (the baseline has no history). If someone
  points that out, agree and explain the table.
