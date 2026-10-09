# Leyang Xia 的个人网站

正式地址：[leyang-xia.github.io](https://leyang-xia.github.io/)。GitHub Pages 从 `main` 分支的仓库根目录发布。

## 编辑文章

文章源文件位于 [`personal-site/content/posts/`](personal-site/content/posts/)，每篇文章一个 `.md` 文件。生成的 HTML 和搜索索引无需手工编辑。

复制现有文章作为起点，使用以下 front matter：

```markdown
---
slug: my-first-post
title: 我的第一篇文章
category: 技术 / 学习记录
summary: 用一句话说明这篇文章讨论的问题。
number: "04"
status: published
published_at: 2026-10-09
tags:
  - 学习记录
cover:
---

## 从问题开始

这里写正文。支持 **加粗**、*斜体*、`行内代码` 和 [链接](https://example.com/)。
```

- 上述字段均需保留。`published_at`、`cover` 不填时留空；`tags` 使用缩进两个空格的列表。字符串可直接写，或用双引号（JSON 转义）/单引号（两个单引号表示一个单引号）包围。此格式是本站的严格子集，**不是完整 YAML**：不支持内联列表、多行值、锚点、内联注释等；未知或重复字段会报错。
- 示例稿使用 `status: sample`，`published_at:` 留空；正式发布使用 `status: published` 和有效的 `YYYY-MM-DD` 日期。正式文章按日期倒序、年份分组，示例稿继续在“版式预览”区展示。
- `number` 为数字字符串，决定示例稿的顺序；相同时按 slug 排序。新增文章使用下一个编号即可。
- 标签必须非空、无重复且不能包含 `|`。封面路径相对 `personal-site/dist/`，例如 `assets/cover.png`；图片须先放在 `personal-site/dist/assets/`，不能越出该资源目录。
- 不要随意改动已发布文章的 `slug`，它决定文章 URL 和评论线程；改文件名不改变 URL。

正文使用 CommonMark 解析器，启用表格、删除线、任务列表和脚注扩展。支持嵌套/多段列表、图片、引用式链接、分隔线、嵌套加粗/斜体、反引号或波浪线代码块、缩进代码和自动链接 `<https://example.com>`。标题由 front matter 提供，正文从 `##` 开始；顶层 `#` 会报错。顶层 `##` 继续使用原站点章节容器，引用、列表和脚注中的标题不改变文章结构。

详细语法和图片路径见 [Markdown 写作指南](docs/markdown-writing.md)，可复制 [综合示例](personal-site/tests/fixtures/markdown/showcase.md)。图片自适应宽度并延迟加载，宽表格和代码块可横向滚动，任务列表为只读勾选状态；这些内容均支持明暗主题。搜索包括表格、列表、代码、脚注正文及图片替代文字。

原始 HTML 继续转义为文字，不执行脚本。链接只允许 HTTP(S)、mailto、相对路径和页内锚点；图片只允许 HTTP(S) 和相对路径。禁止脚本协议、data URI、协议相对地址及含账户信息的 URL。不安全或未定义的链接保留为文字。含括号的 URL 可直接使用；含空格的地址用 `<...>` 包围，或将空格写成 `%20`。未闭合代码块等不完整语法按 CommonMark 的规则处理，而不是一律报错。当前不包含公式渲染、Mermaid 或代码语法高亮，代码的语言类名保留，便于后续扩展。

固定版本的解析器已随仓库保存到 `personal-site/vendor/`，构建无需 pip 安装，也不会访问网络；第三方来源、版本和许可证见 [依赖记录](personal-site/vendor/README.md)。Python 需要 3.10 或以上，CI 使用 3.12。front matter 仍使用上文的严格格式。

## 构建与发布

在仓库根目录运行：

```sh
PYTHONPATH=personal-site python3 -S -m unittest discover -s personal-site/tests -v
node personal-site/tests/test_archive_client.js
node personal-site/tests/test_comments_client.js
node personal-site/tests/test_search_client.js
python3 -S personal-site/build.py
```

生成器把页面写入 `personal-site/dist/`，再同步到仓库根目录。样式和脚本源文件位于 `personal-site/dist/assets/`。搜索索引生成到 `personal-site/dist/assets/search-index.json` 并同步到 `assets/search-index.json`。搜索框首次打开或输入时加载一次，后续复用；失败时显示提示，重新打开或输入可重试。无 JavaScript 时仍可阅读页面、文章和文库，搜索按钮隐藏。请通过 HTTP 预览（例如 `python3 -m http.server 8000`），浏览器直接打开 `file://` 文件可能阻止搜索请求。

GitHub Actions 在 push、PR 和手动触发时运行上述测试、重新构建，再用 Git diff 和未跟踪文件检查阻止生成结果漂移。新增文章时同时提交 Markdown、两份文章 HTML、相关页面和两份索引；删除文章后构建会清理旧文章页面。构建校验通过不代表线上部署或 Sites 预览已完成。

评论后端的部署与审核检查见 [`docs/comment-operations.md`](docs/comment-operations.md)。

## 发布顺序

1. 本地编辑并运行上述测试与构建命令。
2. **先同步到 [Sites 预览站](https://leyang-xia-notes.spicycurrykk.chatgpt.site/)**。Sites 使用独立源码仓库；同步 `personal-site/` 的源码与 `dist/`，部署新版本。
3. 在 Sites 检查首页、文库和标签、文章、留言板、关于、404、搜索、明暗主题与手机布局；确认预览站不连接正式评论后端。发现问题先修改并重新预览。
4. 预览通过后，才提交并推送 GitHub 仓库的 `main`。GitHub Pages 从仓库根目录发布[公开网站](https://leyang-xia.github.io/)。

Sites 与 GitHub Pages 独立。以后修改网站时保持这个“Sites 验证 → 公开网站”顺序。
