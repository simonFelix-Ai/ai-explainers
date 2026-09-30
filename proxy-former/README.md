# ProxyFormer explainer video

A 3Blue1Brown-style explainer of **ProxyFormer** ([arXiv:2608.23463](https://arxiv.org/abs/2608.23463)),
made with [Manim Community](https://www.manim.community/). One script renders both languages.

| File | |
| --- | --- |
| `proxyformer.zh.mp4` / `.srt` | Chinese version (1080p60, burned-in subtitles, no voiceover) |
| `proxyformer.en.mp4` / `.srt` | English version |
| `proxyformer.{zh,en}.chapters.txt` | YouTube / Bilibili chapter timestamps |
| `thumbnail.{zh,en}.png` | 1280×720 thumbnails |
| `youtube.md` | Titles, descriptions and tags for upload |
| `proxyformer_video.py` | All scenes; every string is `tr(chinese, english)` |
| `build.sh` / `make_srt.py` | Render, concatenate, export SRT + chapters + thumbnail |
| `asymmetric-embedding/` | Follow-up explainer: why the history embedding can be 64-dim while generation uses 512 (zh / en) |
| `mv/` | 72-second cinematic music video (procedural particles + synthesized soundtrack, 1080p60) |
| `outreach/` | Ready-to-post articles (Reddit, X, Hacker News, Medium, LinkedIn, Chinese platforms) with a hook GIF and figures |

## Structure

0. **Cold open (~8 s)**: same 16 GB GPU. Standard Transformer runs out of memory at about 20K tokens, ProxyFormer trains on 716,800 (35×), then a 1M-token haystack with 92–95% retrieval.
1. Title and lineage from *Compression Is Routing* (512 → 8, 99.47%).
2. Why long context is expensive: quadratic attention, linear KV cache.
3. Core idea: proxy tokens, explained with a conference analogy. Cost goes to (N/r)² and memory to N/r.
4. Dual stream: why the persistent local stream avoids irreversible one-shot loss.
5. Engineering: cascaded compression, per-layer ratios, proxy KV cache, asymmetric embeddings, simple operators.
6. Space-to-channel: β/α² ≤ 1 and the compress → save → widen cycle.
7. Memory and speed: 15.6 GB vs 2.9 GB, 1.3 vs 16.1 it/s, 716,800 tokens.
8. Multi-needle NIAH heatmap (real values, 64K-trained model, 4K → 1M) plus the 8K-trained extrapolation limit.
9. Quality: WikiText-103 perplexity 21.01 vs 21.36; preliminary FID.
10. Any dimension: 1D / 2D / 3D, and text-to-image in proxy space.
11. Honest scope, **Patent Pending**, license terms, call for collaboration and contact details.

All numbers come from the paper and the README. The heatmap uses the values from
`doc/img/niah/niah_heatmap_train_seq_64k.png`.

## Rebuild

```bash
sudo apt-get install ffmpeg libcairo2-dev libpango1.0-dev fonts-noto-cjk \
     texlive-latex-base texlive-latex-extra texlive-fonts-recommended dvisvgm cm-super
python -m venv venv && . venv/bin/activate && pip install manim

./build.sh h zh    # Chinese, 1080p60   (l = 480p preview, k = 4K)
./build.sh h en    # English
```

## Voiceover

The videos have no voiceover. Use the SRT as a timed narration script, record or synthesize the audio, then:

```bash
ffmpeg -i proxyformer.en.mp4 -i narration.wav -c:v copy -c:a aac -shortest out.mp4
```
