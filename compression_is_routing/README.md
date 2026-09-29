# 「压缩即路由」科普讲解视频

3Blue1Brown 风格的中文讲解动画，用 [Manim Community](https://www.manim.community/) 制作，
介绍论文 *Compression is Routing: Reconstruction Error as an Intrinsic Signal for Modular Language Models*。

| 文件 | 说明 |
| --- | --- |
| `compression_is_routing.zh.mp4` | 成片（1080p60，中文字幕内嵌，无配音） |
| `compression_is_routing.zh.srt` | 旁白字幕时间轴，可直接作为配音稿或外挂字幕 |
| `compression_is_routing.en.mp4` / `.en.srt` | 英文版（约 8 分钟，含 5 秒开场钩子），面向 YouTube |
| `thumbnail.en.png` / `youtube.en.md` | 英文版缩略图、标题、简介、章节、标签 |
| `compression_is_routing.py` | 中文版动画源码（11 个场景） |
| `compression_is_routing_en.py` | 英文版动画源码（开场钩子 + 11 个场景，缩略图场景 `Thumbnail`） |
| `build.sh` / `make_srt.py` | 一键渲染、拼接与导出字幕 |

## 内容结构（约 9 分钟）

1. **开场**：压缩得好不好，能不能决定数据该交给谁？
2. **问题**：上下文长度、推理成本、灾难性遗忘；MoE 门控网络的复杂与不可解释
3. **压缩即智能**：预测 ⇔ 压缩；压缩器只擅长压缩「熟悉」的数据
4. **架构**：512 token → 8 个潜向量（64×），解码器与原文物理隔离
5. **指标**：token 级重建准确率 TRA
6. **核心结果**：99.47% → 47.76% → 0.57% 三级台阶
7. **潜空间几何**：流形分离、线性可分、内在维度 ≈ 200
8. **压缩即路由**：按重建误差选专家；新领域挂载新专家、冻结旧专家
9. **显存**：KV Cache 序列长度压缩 64×
10. **局限与未来**：滞后效应、交错分布、M 与 L 的缩放定律猜想
11. **结尾**

> 潜空间散点图、PCA 曲线和路由场景中的数值为示意，真实数据请参考论文。

## 重新渲染

```bash
sudo apt-get install ffmpeg libcairo2-dev libpango1.0-dev fonts-noto-cjk \
     texlive-latex-base texlive-latex-extra texlive-fonts-recommended dvisvgm cm-super
python -m venv venv && . venv/bin/activate && pip install manim

./build.sh h      # 中文版；l=480p15（预览）  m=720p30  h=1080p60  k=2160p60
./build.sh h en   # 英文版（另外输出 YouTube 章节 compression_is_routing.en.chapters.txt）
manim render -s -qh compression_is_routing_en.py Thumbnail   # 缩略图
```

## 添加配音

成片没有配音。可以按 `compression_is_routing.zh.srt` 的时间轴录制旁白，
或用任意 TTS 逐条合成后与视频合并，例如：

```bash
ffmpeg -i compression_is_routing.zh.mp4 -i narration.wav -c:v copy -c:a aac -shortest out.mp4
```
