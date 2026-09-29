# ProxyFormer: cinematic music video

A 72-second music video for ProxyFormer ([arXiv:2608.23463](https://arxiv.org/abs/2608.23463)).
Everything is procedural: the visuals come from a small particle renderer (numpy + OpenCV), and the
soundtrack is synthesized in numpy. There are no stock footage, samples or third-party music, so there
are no licensing issues.

| File | |
| --- | --- |
| `proxyformer_mv.mp4` | Final video, 1920×1080, 60 fps, H.264 + AAC |
| `proxyformer_mv.py` | Renderer and all eight scenes |
| `music.py` | Soundtrack synthesizer (D minor, 100 BPM, 30 bars) |
| `fonts/` | Source Sans Pro (SIL OFL 1.1) and Roboto (Apache 2.0), with licenses |

## Timeline

Locked to the beat: 100 BPM, one bar is 2.4 s.

| Time | Scene | Music |
| --- | --- | --- |
| 0:00 | **River of light**: the camera flies through a stream of tokens | pad, heartbeat |
| 0:09.6 | **O(N²)**: all-to-all connections weave into an overheating web; counters reach 1,048,576 tokens and 1.1 trillion pairs; glitch, **OUT OF MEMORY** | hats accelerate, riser, hard stop |
| 0:19.2 | *What if only the representatives spoke?* | silence, plucks, swell |
| 0:21.6 | **Drop**: tokens burst into 16 chunks, stream up into golden proxy stars, proxies arc together, and the global view is injected back | impact, four-on-the-floor |
| 0:31.2 | **Dual stream**: flythrough of stacked layers; light packets travel up (compress) and down (inject) on every beat | + arpeggio, claps |
| 0:40.8 | **Numbers**: 16 GB GPU runs out of memory at 20,992 tokens, ProxyFormer reaches 716,800 (35×); 1/5 memory, 12× faster; 50-needle heatmap: 99–100% at 4× beyond training, 92–95% at 1M | a boom on every bar |
| 0:52.8 | **Galaxy**: a million-token galaxy; trained on 64K, still finding needles at one million | breakdown, riser |
| 1:00 | **Title**: particles converge into PROXYFORMER, then a light sweep; **PATENT PENDING**, open to licensing, compute and research collaboration; links | final impact, long tail |

All numbers come from the paper and the repository README.

## Rebuild

```bash
sudo apt-get install ffmpeg fonts-noto-cjk
pip install numpy scipy opencv-python-headless pillow

python proxyformer_mv.py --out proxyformer_mv.mp4 --fps 60      # full video (~10 min on 4 cores)
python proxyformer_mv.py --still 26.5 --png frame.png            # a single frame for tuning
python proxyformer_mv.py --out preview.mp4 --fps 30 --start 40 --end 53   # a section
```
