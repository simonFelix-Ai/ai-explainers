TITLE:
Why is long context so expensive, and how "proxy tokens" fix it: a 3Blue1Brown-style explainer (6 min)

BODY:
I made an animated explainer of my own architecture, ProxyFormer, aimed at anyone who knows the basics of attention.

**The intuition, as a conference analogy:**

* 10,000 people can't all talk to each other. 24 people already means 276 conversations. That's attention's quadratic cost.
* So each table elects a **representative** (compression).
* Only the representatives talk to each other: 4 reps, 6 conversations (global attention among proxies).
* Then each rep goes back and briefs their table (decompression and injection).

The twist is that the tables never disband. The full-resolution tokens persist through every layer, so nothing a rep missed is lost for good.

The video also covers why compressing by r cuts attention to (1/r)², the "space-to-channel" budget trick (β ≤ α²), and results:
* one 16 GB GPU trains on 716,800 tokens
* 99–100% needle retrieval at 4× the training length
* 92–95% at 1M tokens

Video: [VIDEO_LINK]
Paper: https://arxiv.org/abs/2608.23463
Code: https://github.com/simonFelix-Ai/proxy-former

Tell me which part lost you. I'm trying to get better at explaining this.

---- POSTING NOTES (do not copy below this line) ----
- Video posts are fine here. Friendly audience, good for "what was confusing" feedback.
