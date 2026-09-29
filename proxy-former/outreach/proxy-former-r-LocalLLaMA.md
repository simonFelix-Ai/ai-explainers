TITLE:
Same 16 GB card: full attention OOMs around 20K tokens, ProxyFormer trains on 716,800. Proxy KV cache is 1/64 the length

BODY:
Independent project, sharing because this sub cares about memory more than anyone.

**The trick:** chop the sequence into chunks and compress each chunk into a "proxy" token. Only the proxies attend to each other; the result is then pushed back into the full-resolution tokens. At compression ratio 64, the global attention work drops to 1/4096, and at inference you only keep a **proxy KV cache**, 64× shorter than the normal one.

**Measured on one 16 GB GPU, batch size 1:**

* ~21K tokens of history: **15.6 GB → 2.9 GB**, **1.3 → 16.1 it/s** (full-attention baseline vs ProxyFormer)
* Fill the card: **716,800 tokens** of trainable history (15.1 GB), about 35× what a standard decoder fits

**Does it still remember things?** In a 50-needle passkey test (every needle queried), a model trained on 64K windows finds 99–100% at 128K–256K, and still 92–95% at 1M tokens.

It's built from plain PyTorch ops (reshape, Linear, Conv, standard SDPA), with no custom CUDA kernels.

**Caveats:** these are small research models (d_model 512), not something you can chat with yet. There are no pretrained chat weights. The results show the architecture is feasible, not that it's SOTA.

Paper: https://arxiv.org/abs/2608.23463
Code: https://github.com/simonFelix-Ai/proxy-former
Animated explainer (6 min): [VIDEO_LINK]

If anyone has spare GPUs and wants to try scaling it, I'd love to hear from you.
(The Proxy Token method is patent pending; academic and non-commercial use is free.)

---- POSTING NOTES (do not copy below this line) ----
- Post 1–2 days after r/MachineLearning. Posting the same links in several subs within hours trips
  Reddit's spam filter.
- The first question will be "GGUF / can I run it?". Answer honestly: research code, no chat weights yet.
