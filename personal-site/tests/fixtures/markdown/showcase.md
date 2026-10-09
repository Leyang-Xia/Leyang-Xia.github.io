---
slug: markdown-showcase
title: Markdown 排版示例
category: 技术 / 写作
summary: 表格、列表、图片、脚注和代码的组合示例。
number: "04"
status: sample
published_at:
tags:
  - 写作
cover:
---

## 对照结果

**可复现的结果需要 *完整记录* 和 [参考资料][reference]**，~~只留下平均值~~并不足够。[^method]

| 方法 | 输入采样率 | 网络轨迹 | 缓冲策略 | 观察结果 |
| :--- | ---: | :--- | :--- | :--- |
| 固定输入 | 48000 Hz | 固定种子 | 自适应缓冲 | 便于复听对照 |
| 对照实验 | 48000 Hz | 相同轨迹 | 相同配置 | 记录实际丢包 |

- 记录输入
  - 文件与采样率
  - 运行命令

  这是同一条外层列表项的第二段：保留环境与软件版本。

- 保存可播放的音频

### 验收清单

- [x] 固定输入与网络条件
- [ ] 复听异常片段

> 多段引用也可以嵌套。
>
> - 指标说明整体变化。
> - 听感帮助定位短时异常。

---

## 波形与代码

![对照实验波形](/assets/markdown-waveform.svg "原始输入和接收输出")

图片使用站点根目录的 `/assets/` 路径；文件名有空格时用尖括号，例如 `[资料](<https://example.com/audio notes(1)> "实验记录")`。

```python
# 代码中的换行、缩进及尖括号都保留。
def compare(original, received):
    return {"original": original, "received": received, "marker": "<audio>"}
```

[带括号的链接](https://example.com/audio_(experiment))，<https://example.com/docs>，以及 `inline_code`。

[reference]: https://example.com/docs "参考资料"

[^method]: 固定输入、轨迹和版本，结果才便于比较。

    脚注也支持第二段，以及 **加粗** 和 [补充资料](https://example.com/details)。
