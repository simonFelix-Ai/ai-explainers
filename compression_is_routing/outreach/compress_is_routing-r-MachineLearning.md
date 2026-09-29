TITLE:
[R] Compression is Routing: a 64× Transformer autoencoder trained only on code reconstructs held-out code at 99.47%, Wikipedia at 47.76%, random tokens at 0.57%

BODY:
I'm an independent researcher and I'd like critical feedback on a small result that I think points to a cheap routing signal for modular LMs.

**Setup**

* 87M-parameter Transformer autoencoder, trained end-to-end (encoder and decoder jointly, nothing frozen).
* Encoder: 512 tokens (d_model = 512) → **8 latent vectors**, i.e. 64:1 compression along the sequence axis.
* Strict isolation: the decoder never sees the input x. It gets z plus an auxiliary signal m of the same length as x that carries no content, so z is the only information path.
* Trained on code only (codeparrot/codeparrot-clean), GPT-2 tokenizer. Loss is plain cross-entropy on reconstructed tokens.

**Metric:** token-level reconstruction accuracy (TRA), the fraction of positions where the reconstructed token exactly equals the input token. No semantic similarity or partial credit.

**Results**

| Eval set | Eval tokens | TRA |
|:--|--:|--:|
| Code, held-out split (in-domain) | 3,170,816 | **99.47%** |
| WikiText-103 validation (semi-OOD) | 320,512 | **47.76%** |
| Random token sequences (fully OOD) | 3,170,816 | **0.57%** |

Chance is about 1/|V| ≈ 0.002%, so the 47.76% isn't noise. It reflects the vocabulary and low-level statistics that code and English share. The 0.57% shows the model didn't degenerate into an identity channel.

**Latent geometry**

* In UMAP, code and Wikipedia latents form two dense, disconnected islands. t-SNE shows the same split.
* The two classes are linearly separable in z.
* PCA on code latents: about 200 of 512 components explain 95% of the variance.

**The claim**

If each expert module has its own domain compressor, reconstruction error works directly as the routing signal: send the input to whichever compressor rebuilds it best. That needs no separately trained gating network, and the decision is interpretable (you can read the error). A new domain gets a new compressor while existing ones stay frozen, so old experts are untouched by construction. That's the argument for why this could help with catastrophic forgetting.

**What this does NOT show yet (please push on these)**

* No continual-learning benchmark. The forgetting argument is architectural, not measured.
* Fixed 512-token windows lag when the distribution switches mid-window, and the error spikes at the boundary.
* Interleaved data (for example a blog post with code snippets) lands in a gray zone that's hard to classify.
* Limited ablations because of compute. For L = 512, M = 8 was the smallest latent length that reconstructed near-losslessly; M = 2 and M = 4 lost a lot of information. Early runs hint at 128× or more, but I haven't verified that properly.
* I saw the same three-tier pattern earlier with a custom tokenizer on Chinese novels. The report focuses on the HF-standard setup for reproducibility.

**Questions for you**

1. How does this compare to using a single LM's perplexity as an OOD or routing score? My intuition is that the 64× bottleneck sharpens the separation, but I'd like to hear counterarguments.
2. Which continual-learning benchmark would be the fairest first test of the "add a compressor, freeze the rest" setup?
3. Any prior work I should cite on reconstruction-error-based routing for language?

Paper: [PAPER_LINK]
Repo: https://github.com/simonFelix-Ai/compression_is_routing
I also made an 8-minute animated explainer for anyone who prefers visuals: [VIDEO_LINK]

---- POSTING NOTES (do not copy below this line) ----
- Post as a text post. Put the [R] tag at the start of the title and pick the "Research" flair if the sub asks for one.
- Best time: Tue–Thu, 8–10 am US Eastern.
- Stay online for the first 2–3 hours and reply to every comment, especially the critical ones.
  Thank critics and concede valid points. On r/ML that builds more credibility than defending.
- Don't edit the title after posting (you can't anyway). Edits to the body are fine; mark them "EDIT:".
