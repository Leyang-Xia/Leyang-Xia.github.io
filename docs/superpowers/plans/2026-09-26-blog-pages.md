# 博客页面改版 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将现有静态博客改成经确认的双栏首页、按年份整理的文库和精简文章页，并保留三篇示例稿。

**Architecture:** 继续用 `personal-site/build.py` 生成 HTML。文章元数据决定首页、文库、标签、搜索和文章页；现有 CSS/JS 随构建结果发布到仓库根目录。此计划生成留言板的静态页面与评论容器；真实评论由独立计划接入。

**Tech Stack:** Python 3 标准库、静态 HTML/CSS/JavaScript、GitHub Pages。

**Spec:** `docs/superpowers/specs/2026-09-26-personal-blog-redesign-design.md`

## Global Constraints

- 主站是 `https://leyang-xia.github.io/`；Sites 仅作预览。
- 主导航为“首页、文库、留言板、关于”，搜索和明暗切换保留。
- `/writing/` 和现有三篇文章的 URL 不变；`/work/` 移除；留言板为 `/guestbook/`。
- 三篇示例稿留在“版式预览”区，没有虚构发布日期。
- 文章封面可选；没有封面时仍显示完整文字卡片。
- 继续支持键盘焦点、减少动态效果、浅色和深色主题。

## Review Focus

1. 只有示例稿、没有正式文章时，文库仍展示“版式预览”且不出现空年份标题（任务 2 测试）。
2. 中文标签出现在查询参数中时，筛选正确且 URL 可分享（任务 2 浏览器检查）。
3. 没有封面的重点文章仍有可读标题和入口（任务 3 测试）。
4. 标题或摘要含 `<`、`&` 时，不会作为 HTML 执行（任务 1 测试）。
5. JavaScript 关闭时，文库仍列出全部文章（任务 2 浏览器检查）。

---

### Task 1: 文章元数据与校验

**Files:**
- Modify: `personal-site/build.py:10-70`
- Create: `personal-site/tests/test_content.py`

**Interfaces:**
- Produces: `validate_posts(posts: list[dict]) -> None`；`split_posts(posts: list[dict]) -> tuple[list[dict], list[dict]]`，前者为按日期倒序的正式文章，后者为原顺序的示例稿。
- Consumes: 现有 `POSTS` 的 `slug`、`title`、`summary` 和 `sections`。

- [ ] **Step 1: 写失败测试。** `test_content.py` 至少覆盖重复 slug、正式文章缺日期、示例稿带日期、缺失封面、HTML 特殊字符与日期倒序：

```python
from copy import deepcopy
from unittest import TestCase
from build import POSTS, split_posts, validate_posts

class ContentTests(TestCase):
    def test_sample_posts_have_no_publication_date(self):
        validate_posts(POSTS)
        published, samples = split_posts(POSTS)
        self.assertEqual([], published)
        self.assertEqual(3, len(samples))
        self.assertTrue(all(p['status'] == 'sample' for p in samples))

    def test_duplicate_slug_is_rejected(self):
        posts = deepcopy(POSTS)
        posts.append(deepcopy(posts[0]))
        with self.assertRaisesRegex(ValueError, 'slug'):
            validate_posts(posts)

    def test_published_post_requires_date(self):
        posts = deepcopy(POSTS)
        posts[0]['status'] = 'published'
        with self.assertRaisesRegex(ValueError, 'published_at'):
            validate_posts(posts)

    def test_title_is_escaped_in_article_link(self):
        from build import post_row
        post = deepcopy(POSTS[0])
        post['title'] = '<script>&'
        html = post_row(post, './')
        self.assertIn('&lt;script&gt;&amp;', html)
        self.assertNotIn('<script>', html)
```

- [ ] **Step 2: 运行失败测试。** `PYTHONPATH=personal-site python3 -m unittest discover -s personal-site/tests -p 'test_content.py' -v`；预期因 `split_posts` 或 `validate_posts` 未定义失败。
- [ ] **Step 3: 给三篇现有文章加入 `status='sample'`、`tags`、`published_at=None`、`cover=None`，并实现校验和拆分。** 标签按现有内容暂用“实验方法”“实时音频”“随笔”；不要改文章原文。核心逻辑：

```python
def split_posts(posts):
    published = sorted((p for p in posts if p['status'] == 'published'),
                       key=lambda p: p['published_at'], reverse=True)
    samples = [p for p in posts if p['status'] == 'sample']
    return published, samples

def validate_posts(posts):
    from datetime import date
    slugs = [p['slug'] for p in posts]
    if len(slugs) != len(set(slugs)):
        raise ValueError('duplicate slug')
    for post in posts:
        if post['status'] not in {'sample', 'published'}:
            raise ValueError('invalid status')
        if post['status'] == 'published' and not post.get('published_at'):
            raise ValueError('published_at is required')
        if post['status'] == 'published':
            date.fromisoformat(post['published_at'])
        if post['status'] == 'sample' and post.get('published_at'):
            raise ValueError('sample must not set published_at')
        if post.get('cover') and not (ROOT / post['cover']).is_file():
            raise ValueError('cover does not exist')
```

  测试再覆盖两个日期不同的正式文章按日期倒序、不存在的封面报错、无效 `status` 与日期格式报错。`post_row()` 使用 `html.escape` 转义文章内容和属性。
- [ ] **Step 4: 运行同一测试，预期全部通过。**
- [ ] **Step 5: 提交。** `git add personal-site/build.py personal-site/tests/test_content.py && git commit -m 'Model published and sample posts'`。

### Task 2: 文库、标签与搜索

**Files:**
- Modify: `personal-site/build.py:77-102,143-167`
- Modify: `personal-site/dist/assets/site.js`
- Modify: `personal-site/dist/assets/site.css`
- Create: `personal-site/tests/test_archive.py`

**Interfaces:**
- Consumes: `split_posts(POSTS)` 与文章 `tags`、`status`、`published_at`。
- Produces: `writing() -> str`；页面上每个正式文章行有 `data-tags`，筛选器读取 `URLSearchParams(location.search).get('tag')`。

- [ ] **Step 1: 写失败测试。** 用两个有日期的测试文章和一篇示例稿检查年份、顺序、示例区；只使用示例稿时检查没有空年份标题。检查搜索结果带“示例稿”，不再包含“研究方向”：

```python
from unittest import TestCase
import build

class ArchiveTests(TestCase):
    def test_samples_are_separate_without_empty_year(self):
        html = build.writing()
        self.assertIn('版式预览', html)
        self.assertNotIn('class="archive-year"', html)
        self.assertIn('示例稿', html)

    def test_search_has_no_research_page(self):
        html = build.search_dialog('../')
        self.assertNotIn('研究方向', html)
        self.assertIn('示例稿', html)

    def test_formal_posts_are_grouped_by_year(self):
        from copy import deepcopy
        from unittest.mock import patch
        posts = deepcopy(build.POSTS[:2])
        for post, day in zip(posts, ('2025-12-01', '2026-01-02')):
            post['status'] = 'published'
            post['published_at'] = day
        with patch.object(build, 'POSTS', posts):
            html = build.writing()
        self.assertLess(html.index('2026'), html.index('2025'))
        self.assertNotIn('版式预览', html)
```

- [ ] **Step 2: 运行 `PYTHONPATH=personal-site python3 -m unittest discover -s personal-site/tests -p 'test_archive.py' -v`，预期失败。**
- [ ] **Step 3: 改写 `writing()` 为按年份分组的正式文章列表加单独的示例区；生成标签链接。** 每个文章行使用转义后的 `data-tags`；JS 中按查询参数匹配标签，缺少或未知标签时显示全部并保持页面可读：

```javascript
const selectedTag = new URLSearchParams(location.search).get('tag');
const rows = [...document.querySelectorAll('[data-tags]')];
const knownTag = rows.some(row => row.dataset.tags.split('|').includes(selectedTag));
for (const row of rows) {
  row.hidden = Boolean(selectedTag && knownTag) && !row.dataset.tags.split('|').includes(selectedTag);
}
```

  更新 `search_dialog()`，索引文章和留言板/关于页，示例文章的结果显示“示例稿”。
- [ ] **Step 4: 运行测试，预期通过；在真实浏览器打开 `/writing/?tag=%E9%9A%8F%E7%AC%94` 验证中文标签筛选，禁用 JS 后验证所有文章仍可读。**
- [ ] **Step 5: 提交。** `git add personal-site/build.py personal-site/dist/assets/site.js personal-site/dist/assets/site.css personal-site/tests/test_archive.py && git commit -m 'Build tagged archive and searchable samples'`。

### Task 3: 双栏首页与导航

**Files:**
- Modify: `personal-site/build.py:105-160,181-184`
- Modify: `personal-site/dist/assets/site.css`
- Create: `personal-site/tests/test_home.py`

**Interfaces:**
- Consumes: `POSTS`、`split_posts()` 和 `post_row()`。
- Produces: `home() -> str`；`layout(title: str, description: str, root: str, current: str, content: str) -> str` 的导航只有首页/文库/留言板/关于。

- [ ] **Step 1: 写失败测试。**

```python
from unittest import TestCase
import build

class HomeTests(TestCase):
    def test_navigation_and_sidebar(self):
        html = build.home()
        self.assertIn('>文库</a>', html)
        self.assertIn('>留言板</a>', html)
        self.assertIn('class="profile-card"', html)
        self.assertNotIn('>研究</a>', html)

    def test_feature_without_cover_has_link_and_title(self):
        html = build.home()
        self.assertIn(build.POSTS[0]['title'], html)
        self.assertIn('writing/' + build.POSTS[0]['slug'] + '/', html)
```

- [ ] **Step 2: 运行 `PYTHONPATH=personal-site python3 -m unittest discover -s personal-site/tests -p 'test_home.py' -v`，预期失败。**
- [ ] **Step 3: 更新首页、关于页和导航文案。** 首页主栏为短介绍、重点文章、其余文章、标签入口；右栏为姓名标识/一句话/关于与 GitHub/最近文章。CSS 以现有变量实现桌面双栏、手机单栏；保留焦点与减少动态效果。示意结构：

```html
<div class="home-grid container">
  <div class="home-main"><section class="home-intro"><h1>记录值得分享的发现</h1></section><article class="feature-card"><a href="./writing/reproducible-audio-experiments/">如何让一次音频实验可以重来</a></article><section class="latest-writing"><h2>最近文章</h2></section></div>
  <aside class="profile-card" aria-label="关于作者"><strong>Leyang Xia</strong><a href="./about/">关于我</a></aside>
</div>
```

  更新 About 文字为技术分享、学习记录与生活随笔；移除与研究方向绑定的引导。
- [ ] **Step 4: 运行测试，预期通过；在真实浏览器检查 1280px、768px、390px，浅色/深色、键盘 Tab 焦点和减少动态效果。**
- [ ] **Step 5: 提交。** `git add personal-site/build.py personal-site/dist/assets/site.css personal-site/tests/test_home.py && git commit -m 'Redesign home and profile sidebar'`。

### Task 4: 文章、留言板外壳与发布副本

**Files:**
- Modify: `personal-site/build.py:187-218`
- Modify: `personal-site/dist/assets/site.css`
- Create: `personal-site/tests/test_routes.py`
- Delete: `personal-site/dist/work/index.html`, `work/index.html`
- Generate: `personal-site/dist/guestbook/index.html`, `guestbook/index.html` and updated root HTML/assets.

**Interfaces:**
- Consumes: `layout()`、`POSTS`、`split_posts()`。
- Produces: `guestbook() -> str`、`article(post: dict) -> str`；两页预留 `id="comments"`，由评论计划接入。

- [ ] **Step 1: 写失败测试。** 构建后检查留言板及文章评论容器、原有文章路径、导航链接、没有旧研究页；用 HTMLParser 遍历本地 `href`/`src`，忽略 `http`、`mailto`、`data`、`#`：

```python
from pathlib import Path
from unittest import TestCase
import build

class RouteTests(TestCase):
    def test_guestbook_and_article_shell(self):
        self.assertIn('id="comments"', build.guestbook())
        self.assertIn('id="comments"', build.article(build.POSTS[0]))
        self.assertIn('示例稿', build.article(build.POSTS[0]))

    def test_old_article_paths_stay_stable(self):
        for post in build.POSTS:
            self.assertIn('writing/' + post['slug'] + '/', build.writing())
```

- [ ] **Step 2: 运行 `PYTHONPATH=personal-site python3 -m unittest discover -s personal-site/tests -p 'test_routes.py' -v`，预期 `guestbook` 未定义或缺评论容器。**
- [ ] **Step 3: 实现 `guestbook()` 与文章底部评论外壳，生成 `/guestbook/`。** 文章页同时从元数据展示标签、正式发布日期和可选封面；示例稿仅展示其标识。`build.py` 在构建前清理自己管理的 `dist`，以免旧 `/work/` 残留；不要删除仓库中不属于生成器的文件。将新版 HTML 和资源同步到仓库根目录，并移除根目录旧 `/work/`。评论外壳初始显示“留言功能正在准备”；真实表单由评论计划替换。具体输出：

```python
def guestbook():
    content = '<section class="page-intro container"><h1>留言板</h1><p>欢迎留下你的想法。</p></section><section class="container"><h2>留言</h2><div id="comments">留言功能正在准备</div></section>'
    return layout('留言板', '聊聊技术、学习和日常。', '../', 'guestbook', content)
```
- [ ] **Step 4: 运行完整单元测试 `PYTHONPATH=personal-site python3 -m unittest discover -s personal-site/tests -v`，预期通过；运行构建，核对 `dist` 与根目录副本、站内链接，确认 `/work/` 不存在。**
- [ ] **Step 5: 提交。** `git add -A personal-site index.html 404.html about assets writing guestbook work && git commit -m 'Publish redesigned static blog pages'`。
