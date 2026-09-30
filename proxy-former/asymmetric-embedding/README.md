# ProxyFormer: asymmetric embeddings

A 3Blue1Brown-style explainer (Manim) of one ProxyFormer design detail: **the history is embedded
at d_history = 64 while the generation side uses d_model = 512**, and the history's local stream
stays 64-wide in every layer. Chinese and English versions come from one script.

| File | |
| --- | --- |
| `asym_embedding.zh.mp4` / `asym_embedding.en.mp4` | 1080p60, burned-in subtitles, no voiceover |
| `asym_embedding.{zh,en}.srt` / `.chapters.txt` | Subtitles (usable as a voiceover script) and chapter timestamps |
| `asym_embedding.py` | All scenes, `tr(chinese, english)` strings; reuses helpers from `../proxyformer_video.py` |
| `build.sh` / `make_srt.py` | `./build.sh h zh` or `./build.sh h en` |

## What the video says, and where it comes from

| Claim | Source |
| --- | --- |
| `h_embedding = nn.Embedding(vocab, d_history)`, `x_embedding = nn.Embedding(vocab, d_model)` | `src/models/architectures/llm/proxy_former_llm.py` |
| The history fine stream is `d_history` wide in every layer; proxies are `d_model` wide; the generation side attends to proxies | same file (`d_fine = d_history`, `d_proxy = d_model`) |
| All published results use d_model=512, d_history=64, 10 layers, ratio 64 | `configs/niah/...`, `configs/vram_usage/...`, `configs/llm/...` |
| Per-layer hidden state at 716,800 tokens, 16-bit: 734.0 MB full width vs 91.8 + 11.5 = 103.2 MB (7.1×); 10 layers 7.3 GB vs 1.0 GB | arithmetic, one tensor per layer |
| Extra history table: 50,257 × 64 ≈ 3.2M parameters (fixed cost) | GPT-2 vocabulary in the configs |
| 15.6 → 2.9 GB, 716,800 trainable tokens, NIAH 99–100% at 256K and 92–95% at 1M, PPL 21.01 vs 21.36 | paper / repository README |

The measured results reflect the **full design** (compression + asymmetric embeddings). The video
says so explicitly; there is no isolated ablation of the embedding width.

## Structure

0. Cold open: a 512-wide history ribbon collapses to 64; per-layer memory 734 MB → 103 MB (7.1×)
1. Title
2. Where memory goes: tokens → d-dim vectors, L×d activations per layer; shrink L (proxies) or shrink d (this video)
3. Two jobs, two widths: the present predicts (512), the past is remembered (64); the two embedding tables in code
4. Narrow stream, wide proxies: 64 tokens × 64 dims = 4,096 numbers → one 512-dim proxy
5. The math: 734.0 vs 103.2 MB per layer; the fixed cost of the extra table
6. Measured results with d_history = 64, with a caveat
7. d_history as a tunable knob (32 / 64 / 128), "older history, narrower" as an untested idea, patent and contact
