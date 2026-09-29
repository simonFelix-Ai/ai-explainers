# Upload kit

## English (YouTube)

**Title (recommended)**

> Same GPU, 35× Longer Context: How ProxyFormer Handles 1M Tokens

Alternatives:
- 20K → 700K Tokens on One 16 GB GPU: ProxyFormer Explained
- Let the Representatives Talk: The Proxy Token Trick for Million-Token Context

**Thumbnail:** `thumbnail.en.png`

**Description**

```
On the same 16 GB GPU, a standard Transformer runs out of memory at about 20K tokens. ProxyFormer trains on 716,800.

ProxyFormer compresses local chunks into a handful of "proxy tokens", runs global attention only among them, and injects the global view back into a fine-grained local stream that persists through every layer. Attention cost drops to (1/r)², memory to 1/r, and decoding only needs a tiny proxy KV cache.

Results (from the paper):
• 16 GB GPU, batch size 1: 15.6 GB → 2.9 GB at 21K tokens of history, 1.3 → 16.1 it/s; trainable length ~35× longer (716,800 tokens)
• Multi-needle retrieval (all 50 needles per document, 5,000 lookups per length): a 64K-trained model finds 99–100% at 128K–256K (4× beyond training) and still 92–95% at 1,048,576 tokens (16×)
• WikiText-103 perplexity 21.01 with compressed history vs 21.36 full-attention baseline

📄 Paper: https://arxiv.org/abs/2608.23463
💻 Code: https://github.com/simonFelix-Ai/proxy-former

The Proxy Token method is patent pending. Free for academic and non-commercial research; for commercial licensing, compute, funding or research collaboration, contact tangzhongp@qq.com

Chapters
0:00 Intro
0:36 Why long context is expensive
1:03 The core idea: proxy tokens
1:53 Dual-stream architecture
2:36 Cascades and the proxy KV cache
3:24 Space-to-channel
3:58 Memory: 20K → 700K tokens
4:22 Million-token needle-in-a-haystack
5:10 Quality: perplexity and images
5:29 Any dimension
5:53 Patent & collaboration

#MachineLearning #LLM #LongContext #Transformer
```

**Tags:** long context, transformer architecture, efficient attention, KV cache, million token context,
needle in a haystack, proxy tokens, ProxyFormer, LLM memory, sequence compression, machine learning explained

## 中文（B站 / YouTube 中文）

**标题（推荐）**

> 同一块显卡，训练长度提升 35 倍：ProxyFormer 如何用「代理 Token」撑起百万上下文

备选：
- 【硬核科普】让「代表」开会：ProxyFormer 百万 token 大海捞针 92%+
- 20K → 700K：一个独立研究者的超长上下文新架构

**封面：** `thumbnail.zh.png`

**简介**

```
同一块 16GB 显卡：普通 Transformer 训练到约 2 万 token 就爆显存，ProxyFormer 可以直接训练 71.7 万 token。

ProxyFormer 把局部片段压缩成极少的「代理 Token」，只在代理之间做全局注意力，再把全局信息注入回在每一层都保留的局部流。注意力开销降到 (1/r)²，显存降到 1/r，推理只需维护极短的代理 KV Cache。

论文结果：
• 16GB 显卡、batch size 1：约 2.1 万 token 历史下显存 15.6GB → 2.9GB，速度 1.3 → 16.1 it/s；可训练长度提升约 35 倍
• 多针大海捞针（每篇 50 根针全部要找，每个长度 5000 次检索）：64K 训练的模型在 128K–256K（4 倍外推）找回 99%–100%，推到 1,048,576 token（16 倍外推）仍有 92%–95%
• WikiText-103 困惑度：压缩历史 21.01，全注意力基线 21.36

📄 论文：https://arxiv.org/abs/2608.23463
💻 代码：https://github.com/simonFelix-Ai/proxy-former

代理 Token 方法已提交专利申请。学术与非商业研究可免费使用；商业授权、算力、资金或研究合作，请联系 tangzhongp@qq.com

章节
0:00 开场
0:42 长上下文为什么贵
1:16 核心想法：代理 Token
2:13 双流架构
2:57 级联压缩与代理 KV Cache
3:52 空间换通道
4:30 显存：20K → 700K
5:06 百万 token 大海捞针
6:08 质量：困惑度与图像生成
6:34 任意维度通用
7:00 专利与合作
```
