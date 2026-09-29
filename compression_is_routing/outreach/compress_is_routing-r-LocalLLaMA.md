TITLE:
512 tokens → 8 vectors: my 87M autoencoder rebuilds unseen code at 99.47%, and its reconstruction error tells you when text isn't "its own"

BODY:
Independent side project that I think this sub will find interesting from a memory and modularity angle.

**What it is:** a small Transformer autoencoder (87M params) that compresses a 512-token block into 8 latent vectors, which is 64× shorter along the sequence. The decoder never sees the original tokens; everything has to pass through those 8 vectors. I trained it on code only.

**What happens on different data** (exact token match after reconstruction):

* held-out code: **99.47%**
* Wikipedia: **47.76%**
* random tokens: **0.57%**

**Why I care:**

1. **Routing for free.** Give every expert its own small compressor and send each input to the one that reconstructs it best. There's no gating network to train, and you can see exactly why a decision was made.
2. **Add knowledge without breaking old knowledge.** A new domain gets a new compressor, and old ones stay frozen, so nothing old gets overwritten.
3. **Memory.** 512 positions become 8 vectors, so long contexts could in principle be held in a fraction of the KV-cache memory. The paper frames this as "contexts that needed several A100s might fit on one consumer card". That's a direction, not a benchmark yet.

**Honest caveats:** no continual-learning benchmark yet; fixed windows react slowly when a document switches domain mid-block; mixed text (prose with code snippets) is a gray zone; ablations are limited by my compute.

Paper: [PAPER_LINK]
Repo: https://github.com/simonFelix-Ai/compression_is_routing
8-min animated explainer: [VIDEO_LINK]

Happy to answer questions, and if anyone has spare GPU time and wants to push the compression ratio (early runs hinted at 128×), I'd love to collaborate.

---- POSTING NOTES (do not copy below this line) ----
- Flair: "Discussion" or "Resources".
- Post 1–2 days after the r/MachineLearning post. Reddit's spam filter flags the same links posted
  across several subs in a short window, especially from newer accounts.
- Expect questions like "can I run it?" and "where are the weights?". If you can release weights or
  code, say so; if not, say when.
