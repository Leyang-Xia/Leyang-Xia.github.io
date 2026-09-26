# 博客留言系统 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 GitHub Pages 主站的留言板和每篇文章启用免登录、先审核的公开评论与回复。

**Architecture:** 静态页面只输出评论容器、固定线程路径和公开后端地址。客户端仅在正式域名加载固定版本 Twikoo；Netlify Functions 运行评论后端，MongoDB Atlas 保存数据。Sites 预览和后端故障时展示明确状态，不伪装成可提交的表单。

**Tech Stack:** Python 3 标准库、原生 JavaScript、Twikoo 2.0.9、Netlify Functions、MongoDB Atlas、GitHub Pages。

**Spec:** `docs/superpowers/specs/2026-09-26-personal-blog-redesign-design.md`

## Global Constraints

- 先完成 `2026-09-26-blog-pages.md`；它提供 `/guestbook/` 与文章页的 `id="comments"` 容器。
- 主站仅为 `https://leyang-xia.github.io/`；Sites 只预览，不写入正式评论。
- 留言板和每篇文章都有独立线程；访客免登录，昵称与内容必填，邮箱选填。
- 所有留言和回复先审核，批准后才公开。
- 评论不可用时，正文与导航继续可用；数据库密钥不得进入仓库或生成站点。

## Review Focus

1. Sites 预览域名或 `file://` 打开页面，不会请求生产评论后端（任务 1 测试）。
2. 相同文章在不同域名预览时不会产生不同的正式线程标识（任务 1 测试）。
3. 未配置后端地址时不会显示可提交表单（任务 1 测试）。
4. CDN 或后端加载失败时，页面显示错误状态且文章正文可读（任务 2 测试）。
5. 提交回复也要经过审核，不能因为是回复而立即公开（任务 3 线上验收）。

---

### Task 1: 评论配置和域名边界

**Files:**
- Modify: `personal-site/build.py`
- Create: `personal-site/dist/assets/comments.js`
- Create: `personal-site/tests/test_comments_config.py`

**Interfaces:**
- Consumes: 页面中的 `id="comments"`，留言板路径 `/guestbook/`，文章路径 `/writing/{slug}/`。
- Produces: `comment_shell(path: str, env_id: str | None) -> str`，输出 `data-thread-path` 与 `data-env-id`；`comments.js` 仅在 `location.hostname === 'leyang-xia.github.io'` 且 `data-env-id` 非空时加载服务。

- [ ] **Step 1: 写失败测试。**

```python
from unittest import TestCase
from build import comment_shell

class CommentConfigTests(TestCase):
    def test_article_thread_is_site_path(self):
        html = comment_shell('/writing/example/', 'https://comments.example.net')
        self.assertIn('data-thread-path="/writing/example/"', html)
        self.assertIn('data-env-id="https://comments.example.net"', html)

    def test_missing_backend_is_not_a_form(self):
        html = comment_shell('/guestbook/', None)
        self.assertIn('评论暂不可用', html)
        self.assertNotIn('<form', html)
```

- [ ] **Step 2: 运行 `PYTHONPATH=personal-site python3 -m unittest discover -s personal-site/tests -p 'test_comments_config.py' -v`，预期 `comment_shell` 未定义。**
- [ ] **Step 3: 实现 `comment_shell`，用 `html.escape(..., quote=True)` 转义路径和地址；从构建环境读取 `TWIKOO_ENV_ID`。** 生成器在文章与留言板注入此壳，不写入任何 MongoDB 密钥。客户端的最小域名门禁：

```javascript
const shell = document.getElementById('comments');
if (shell) {
  if (location.hostname !== 'leyang-xia.github.io') {
    shell.textContent = '预览站不开放留言；请前往正式站点。';
  } else if (!shell.dataset.envId) {
    shell.textContent = '评论暂不可用';
  } else {
    shell.textContent = '评论功能正在准备';
  }
}
```

- [ ] **Step 4: 运行同一测试，预期通过；以 `file://` 和 Sites 预览网址打开页面，确认不发送评论网络请求。**
- [ ] **Step 5: 提交。** `git add personal-site/build.py personal-site/dist/assets/comments.js personal-site/tests/test_comments_config.py && git commit -m 'Add production-only comment configuration'`。

### Task 2: Twikoo 客户端与降级状态

**Files:**
- Modify: `personal-site/dist/assets/comments.js`
- Modify: `personal-site/build.py`
- Modify: `personal-site/dist/assets/site.css`
- Create: `personal-site/tests/test_comments_client.js`

**Interfaces:**
- Consumes: `data-thread-path`、`data-env-id`、`id="comments"`。
- Produces: 仅主站加载固定版本 `https://cdn.jsdelivr.net/npm/twikoo@2.0.9/dist/twikoo.min.js`，调用 `twikoo.init({envId, el:'#tcomment', path, lang:'zh-CN'})`。

- [ ] **Step 1: 写失败测试。** 用 Node 的模拟 `document`、`location`、`twikoo` 检查预览域名不加载脚本、生产域名传入稳定 `path`、加载失败显示“评论暂不可用”；示例断言：

```javascript
const assert = require('node:assert/strict');
const { canLoadComments } = require('../dist/assets/comments.js');
assert.equal(canLoadComments('leyang-xia.github.io', 'https://comments.example.net'), true);
assert.equal(canLoadComments('leyang-xia-notes.spicycurrykk.chatgpt.site', 'https://comments.example.net'), false);
assert.equal(canLoadComments('leyang-xia.github.io', ''), false);
```

- [ ] **Step 2: 运行 `node personal-site/tests/test_comments_client.js`，预期因 `canLoadComments` 未导出失败。**
- [ ] **Step 3: 实现纯函数 `canLoadComments(hostname, envId)` 并给 Node 导出；浏览器加载固定版本脚本，`onload` 后初始化，`onerror` 和初始化异常都替换为不可用提示。** 评论容器内独立的 `#tcomment` 供 Twikoo 渲染；加载中显示状态文字。样式遵守现有明暗变量，并保持正文与评论区分离。脚本只在含评论区的页面输出。
- [ ] **Step 4: 运行 Node 测试与完整 Python 单元测试，预期通过；浏览器分别检查生产/预览/断网状态。**
- [ ] **Step 5: 提交。** `git add personal-site/build.py personal-site/dist/assets/comments.js personal-site/dist/assets/site.css personal-site/tests/test_comments_client.js && git commit -m 'Load moderated comments on canonical host'`。

### Task 3: 后端、审核与发布验收

**Files:**
- Create: `docs/comment-operations.md`
- Generate: `personal-site/dist/**` and root site files from the source generator.

**Interfaces:**
- Consumes: Netlify Twikoo 环境地址 `TWIKOO_ENV_ID`；MongoDB Atlas `MONGODB_URI` 仅在 Netlify 环境变量设置。
- Produces: 可访问的评论端点、站长管理账号，以及 GitHub Pages 上通过验收的留言板与文章评论。

- [ ] **Step 1: 写验收记录模板到 `docs/comment-operations.md`。** 固定检查项：Netlify 健康地址、管理后台登录、审核开关、留言提交前后可见性、文章回复前后可见性、数据导出/备份、Sites 预览不可写。记录每项真实时间与结果，不写密码或连接字符串。
- [ ] **Step 2: 依 [Twikoo 官方 Netlify 部署步骤](https://twikoo.js.org/backend.html)建立 MongoDB Atlas 数据库和 Netlify Functions，Netlify 环境变量设置 `MONGODB_URI`，配置站长管理密码与人工审核。** 用 Netlify 提供的 `/.netlify/functions/twikoo` 地址作为 `TWIKOO_ENV_ID`；密钥只保存在服务端设置。
- [ ] **Step 3: 将 Netlify 公开端点设为本机环境变量 `TWIKOO_ENV_ID`，运行 `test -n "$TWIKOO_ENV_ID" && python3 personal-site/build.py`，同步输出到根目录；运行全套单元测试和站内链接检查。** 提交生成页面与资源，推送 `main` 后等 GitHub Pages 构建成功。公开端点可进入构建输出；`MONGODB_URI` 不可进入本机站点构建环境。
- [ ] **Step 4: 线上验收。** 在 `/guestbook/` 提交注明为测试的留言、在任意文章提交测试回复：两者审核前均不可见，后台批准后可见；Sites 预览不可提交，断开后端时正文仍可读。记录结果后从后台移除测试留言及回复。
- [ ] **Step 5: 提交运维文档与必要的修正，并推送 `main`。** `git add docs/comment-operations.md personal-site index.html about assets writing guestbook 404.html && git commit -m 'Document and verify moderated comments' && git push origin main`。
