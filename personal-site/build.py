"""Build the dependency-free static personal site into dist/."""

from datetime import date
from html import escape
import os
from pathlib import Path
import re
import shutil
import json


ROOT = Path(__file__).parent
OUT = ROOT / "dist"

POSTS = [
    {
        "slug": "reproducible-audio-experiments",
        "title": "如何让一次音频实验可以重来",
        "category": "技术 / 实验方法",
        "summary": "从固定输入、网络条件到听感样本：一份结果真正值得信任，需要留下哪些线索？",
        "number": "01",
        "status": "sample", "published_at": None, "tags": ["实验方法"], "cover": None,
        "sections": [
            ("从问题开始", [
                "做音频实验时，很容易先得到一张漂亮的图，再回头想它说明什么。更可靠的顺序是先写下问题：我们想比较的是编解码器、丢包恢复策略，还是整条实时链路的体验？问题不同，实验边界也不同。",
                "如果关注真实通话，编码、发包、网络、接收缓冲和解码就都在结果里。只测试某个离线解码器可以回答更窄的问题，但不应把结论扩展到完整通话。",
            ]),
            ("固定可变的东西", [
                "同一段输入音频、相同的采样率、相同的网络轨迹和随机种子，是比较两种方案的起点。网络损失还要记录实际发生的丢包率与连续丢包长度；配置中的目标值未必等于运行时的结果。",
                "除了参数，也要保留软件版本和运行命令。这样一段时间后回看时，才知道曲线改变来自方案本身，还是来自输入、依赖或环境。",
            ]),
            ("让数字可以被听见", [
                "平均延迟、字错误率或客观音质分数都很有用，却无法独自解释一次短暂的断音。最好同时保存处理前后的可播放音频，并挑选有代表性的片段复听。",
                "一份好的实验记录不只是结论，也包括失败的样本、适用范围和仍然不确定的地方。可复现的意义，是让下一次判断建立在同一块地面上。",
            ]),
        ],
    },
    {
        "slug": "packet-loss-listening",
        "title": "丢包率之外，语音体验还取决于什么",
        "category": "技术 / 实时音频",
        "summary": "相同的平均丢包率，可能听起来完全不同。理解连续丢包、恢复策略与缓冲延迟之间的取舍。",
        "number": "02",
        "status": "sample", "published_at": None, "tags": ["实时音频"], "cover": None,
        "sections": [
            ("平均值会藏起形状", [
                "一次通话丢掉百分之五的数据包，听感并不由“百分之五”单独决定。零散的单包丢失，和集中发生的一串丢失，会给接收端留下完全不同的恢复任务。",
                "因此，描述网络条件时，除了平均丢包率，还需要看丢失的时间分布、连续长度、抖动和延迟。仅凭一个百分比比较算法，常常会漏掉最令人难受的片段。",
            ]),
            ("恢复总有代价", [
                "接收端可以通过冗余信息、预测或缓冲等待来减轻丢包影响。但冗余占带宽，等待会增加延迟，预测也可能在长时间缺失时失真。没有一种策略能在所有网络条件下同时最优。",
                "评价恢复效果时，要把它放回实时链路：发送端实际带来的开销是多少？接收端增加了多少等待？语音是否仍然容易理解？这些问题比单个音质分数更接近用户体验。",
            ]),
            ("把边界写清楚", [
                "可比较的测试需要固定语料和网络轨迹，并报告每次运行实际观察到的损失情况。保留原音与接收后的音频，能让统计指标和人的听觉互相校验。",
                "当某个方案在一类突发丢包下表现更好，结论应写成这个具体条件下的改善。边界清楚，结果才容易被别人在自己的场景中使用。",
            ]),
        ],
    },
    {
        "slug": "room-for-observation",
        "title": "给观察留一点时间",
        "category": "日常 / 随笔",
        "summary": "做事之外，也需要一些不急着产出结果的时刻。关于节奏、注意力和日常的小小记录。",
        "number": "03",
        "status": "sample", "published_at": None, "tags": ["随笔"], "cover": None,
        "sections": [
            ("不急着命名", [
                "很多时候，我们习惯迅速给一件事归类：有用或无用，进步或停滞，值得或不值得。判断带来效率，也会让一些细节在被看清之前就消失。",
                "偶尔放慢一点，不急着把想法写成结论，反而能看到它原来的样子。一次谈话里没有说完的话，一段路上光线的变化，或一个问题反复出现的原因，都是这样的细节。",
            ]),
            ("留白也是一种安排", [
                "日程排满时，新的念头通常只能从旧任务之间的缝隙里挤出来。留白不一定意味着什么都不做；它也可以是读几页书、走一段路，或把一个问题放在心里多待一会儿。",
                "我想在这里保留这样一个角落：记录尚未成熟的想法，也记录那些不需要被证明有用的瞬间。",
            ]),
        ],
    },
]


def link(root: str, path: str = "") -> str:
    return root + path


def validate_posts(posts: list[dict]) -> None:
    slugs = [post['slug'] for post in posts]
    if len(slugs) != len(set(slugs)):
        raise ValueError('duplicate slug')
    for post in posts:
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', post['slug']):
            raise ValueError('invalid slug')
        if post['status'] not in {'sample', 'published'}:
            raise ValueError('invalid status')
        if not post.get('title') or not post.get('summary') or not isinstance(post.get('tags'), list):
            raise ValueError('missing article metadata')
        if post['status'] == 'published':
            if not post.get('published_at'):
                raise ValueError('published_at is required')
            date.fromisoformat(post['published_at'])
        elif post.get('published_at'):
            raise ValueError('sample must not set published_at')
        if post.get('cover'):
            cover = Path(post['cover'])
            if cover.is_absolute() or '..' in cover.parts or not cover.parts or cover.parts[0] != 'assets' or not (OUT / cover).is_file():
                raise ValueError('cover must be an existing file in assets')


def split_posts(posts: list[dict]) -> tuple[list[dict], list[dict]]:
    published = sorted((post for post in posts if post['status'] == 'published'),
                       key=lambda post: post['published_at'], reverse=True)
    samples = [post for post in posts if post['status'] == 'sample']
    return published, samples


def search_dialog(root: str) -> str:
    items = []
    for post in POSTS:
        body = " ".join(
            heading + " " + " ".join(paragraphs)
            for heading, paragraphs in post["sections"]
        )
        items.append((
            f'writing/{post["slug"]}/', '示例稿' if post['status'] == 'sample' else '文章',
            post["title"], post["summary"], ' '.join(post['tags']) + ' ' + body,
        ))
    items.extend([
        ("guestbook/", "页面", "留言板", "欢迎留下你的想法。", "留言 评论 讨论"),
        ("about/", "页面", "关于 Leyang", "关于我和这个网站。", "个人介绍 技术探索 日常记录 GitHub"),
    ])
    results = "".join(
        f'<li class="search-item" data-search="{escape(" ".join((category, title, summary, body)).lower(), quote=True)}">'
        f'<a href="{link(root, path)}"><span>{escape(category)}</span>'
        f'<strong>{escape(title)}</strong><small>{escape(summary)}</small></a></li>'
        for path, category, title, summary, body in items
    )
    return f'''<dialog class="search-dialog" id="site-search" aria-labelledby="search-title">
    <div class="search-head"><div><p class="eyebrow">SEARCH / 站内搜索</p><h2 id="search-title">寻找一篇文章</h2></div><button class="icon-button search-close" type="button" aria-label="关闭搜索" title="关闭搜索">×</button></div>
    <label class="search-field"><svg aria-hidden="true" viewBox="0 0 24 24" fill="none"><circle cx="10.8" cy="10.8" r="6.8" stroke="currentColor" stroke-width="1.8"/><path d="m16 16 5 5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg><input id="search-query" type="search" placeholder="搜索文章、主题…" autocomplete="off" aria-label="搜索文章和页面"></label>
    <p class="search-status" id="search-status" aria-live="polite">全部内容</p><ul class="search-results" id="search-results">{results}</ul><p class="search-empty" id="search-empty" hidden>没有找到相关内容，试试其他关键词。</p>
  </dialog>'''


def layout(title: str, description: str, root: str, current: str, content: str, comments: bool = False) -> str:
    comments_script = f'<script src="{link(root, "assets/comments.js")}" defer></script>' if comments else ''
    nav = [
        ("首页", "", "home"),
        ("文库", "writing/", "writing"),
        ("留言板", "guestbook/", "guestbook"),
        ("关于", "about/", "about"),
    ]
    nav_html = "".join(
        f'<a href="{link(root, path)}"{(" aria-current=\"page\"" if key == current else "")}>{label}</a>'
        for label, path, key in nav
    )
    return f'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#f8f9fa">
  <meta name="description" content="{escape(description, quote=True)}">
  <title>{escape(title)} · Leyang Xia</title>
  <script>(function(){{var t;try{{t=localStorage.getItem('lx-theme')}}catch(e){{}}if(t!=='light'&&t!=='dark'){{var m=String(document.cookie||'').match(/(?:^|; )lx-theme=(dark|light)(?:;|$)/);t=m&&m[1]}}if(t!=='light'&&t!=='dark')t=window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';document.documentElement.dataset.theme=t}})();</script>
  <link rel="stylesheet" href="{link(root, 'assets/site.css')}">
  <script src="{link(root, 'assets/site.js')}" defer></script>
{comments_script}
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%231b1d21'/%3E%3Cpath d='M17 17v30h17M46 17 28 47' fill='none' stroke='white' stroke-width='5' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E">
</head>
<body>
  <a class="skip-link" href="#content">跳转到正文</a>
  <header class="site-header"><div class="container header-inner">
    <a class="wordmark" href="{root}" aria-label="Leyang Xia，返回首页">Leyang Xia<span class="wordmark-dot">.</span></a>
    <nav class="nav-links" aria-label="主导航">{nav_html}</nav>
    <div class="header-actions"><button class="icon-button" id="search-toggle" type="button" aria-label="打开搜索" title="搜索" aria-haspopup="dialog" aria-controls="site-search" hidden><svg aria-hidden="true" viewBox="0 0 24 24" fill="none"><circle cx="10.8" cy="10.8" r="6.8" stroke="currentColor" stroke-width="1.8"/><path d="m16 16 5 5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg></button><button class="icon-button" id="theme-toggle" type="button" aria-label="切换颜色模式" title="切换颜色模式" hidden><svg class="moon-icon" aria-hidden="true" viewBox="0 0 24 24" fill="none"><path d="M20.1 15.5A8.4 8.4 0 0 1 8.5 3.9 8.6 8.6 0 1 0 20.1 15.5Z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></svg><svg class="sun-icon" aria-hidden="true" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="3.8" stroke="currentColor" stroke-width="1.8"/><path d="M12 2v2m0 16v2M4.9 4.9l1.4 1.4m11.4 11.4 1.4 1.4M2 12h2m16 0h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg></button></div>
  </div></header>
  <main id="content">{content}</main>
  {search_dialog(root)}
  <footer class="site-footer"><div class="container footer-inner"><span>© 2026 Leyang Xia</span><span>Built with curiosity.</span><a href="https://github.com/Leyang-Xia" target="_blank" rel="noopener noreferrer">GitHub ↗</a></div></footer>
</body>
</html>'''


def post_row(post: dict, root: str) -> str:
    href = link(root, f'writing/{post["slug"]}/')
    when = post['published_at'] if post['status'] == 'published' else '示例稿'
    tags = '|'.join(post['tags'])
    return f'''<a class="post-row" href="{escape(href, quote=True)}" data-tags="{escape(tags, quote=True)}">
      <span class="post-index">{escape(when)}</span>
      <span class="post-main"><span class="post-category">{escape(' · '.join(post['tags']))}</span><strong>{escape(post['title'])}</strong><span class="post-summary">{escape(post['summary'])}</span></span>
      <span class="post-arrow" aria-hidden="true">↗</span>
    </a>'''


def tag_links(posts: list[dict], root: str) -> str:
    from urllib.parse import quote
    tags = list(dict.fromkeys(tag for post in posts for tag in post['tags']))
    return ''.join(f'<a class="tag-link" href="{root}writing/?tag={quote(tag)}">{escape(tag)}</a>' for tag in tags)


def home() -> str:
    published, samples = split_posts(POSTS)
    available = published or samples
    feature = available[0] if available else None
    if feature:
        feature_href = f'./writing/{feature["slug"]}/'
        cover = (f'<img src="./{escape(feature["cover"], quote=True)}" alt="" loading="lazy">'
                 if feature.get('cover') else '<span class="feature-art" aria-hidden="true">LX / NOTES</span>')
        feature_card = f'<a class="feature-card" href="{feature_href}">{cover}<span class="feature-copy"><small>{"示例稿" if feature["status"] == "sample" else escape(feature["published_at"])}</small><strong>{escape(feature["title"])}</strong><span>{escape(feature["summary"])}</span><b>阅读文章 ↗</b></span></a>'
    else:
        feature_card = '<p class="sample-explainer">暂无文章，欢迎稍后再来。</p>'
    rows = ''.join(post_row(post, './') for post in available[1:4])
    recent = ''.join(f'<a href="./writing/{escape(post["slug"], quote=True)}/">{escape(post["title"])}</a>'
                     for post in available[:3])
    content = f'''<div class="home-grid container">
      <div class="home-main"><section class="home-intro"><p class="eyebrow">LEYANG XIA / NOTES</p>
      <h1>记录值得分享的发现。</h1><p>这里写有意思的技术、学习路上的问题，也留下一些日常里的想法。</p></section>
      <section class="home-feature" aria-labelledby="feature-heading"><div class="section-top"><div><p class="eyebrow">START HERE</p><h2 id="feature-heading">从这里读起</h2></div><a class="quiet-link" href="./writing/">进入文库 ↗</a></div>
      {feature_card}</section>
      <section class="latest-writing"><div class="section-top"><div><p class="eyebrow">MORE TO READ</p><h2>继续阅读</h2></div></div><div class="post-list">{rows}</div></section>
      <section class="home-tags"><h2>按标签探索</h2><div class="tag-list">{tag_links(available, './')}</div></section>
      </div><aside class="profile-card" aria-label="关于作者"><div class="profile-monogram" aria-hidden="true">LX</div><p class="eyebrow">ABOUT ME</p><h2>Leyang Xia</h2><p>喜欢把学到的东西写清楚，也记录工作和生活中的小发现。</p><div class="profile-links"><a href="./about/">关于我 ↗</a><a href="https://github.com/Leyang-Xia" target="_blank" rel="noopener noreferrer">GitHub ↗</a></div><div class="profile-recent"><strong>最近文章</strong>{recent}</div></aside>
    </div>'''
    return layout('首页', '技术分享、学习记录和生活随笔。', './', 'home', content)


def writing() -> str:
    from itertools import groupby
    published, samples = split_posts(POSTS)
    years = []
    for year, group in groupby(published, key=lambda post: post['published_at'][:4]):
        rows = ''.join(post_row(post, '../') for post in group)
        years.append(f'<section class="archive-year"><h2>{year}</h2><div class="post-list">{rows}</div></section>')
    sample_rows = ''.join(post_row(post, '../') for post in samples)
    sample_section = (f'<section class="sample-section"><div class="section-top"><div><p class="eyebrow">LAYOUT PREVIEW</p><h2>版式预览</h2></div></div><p class="sample-explainer">以下内容是示例稿，用来展示阅读版式，尚未作为正式文章发布。</p><div class="post-list">{sample_rows}</div></section>' if samples else '')
    all_posts = published + samples
    content = f'''<section class="page-intro container"><p class="eyebrow">WRITING / 文库</p><h1>文库。</h1><p>技术、学习与日常。循着问题写，也允许想法慢慢生长。</p></section>
    <section class="container listing-section"><div class="listing-head"><span>所有内容</span><span>共 {len(all_posts)} 篇</span></div>
    <div class="tag-list archive-tags"><a class="tag-link" href="../writing/">全部</a>{tag_links(all_posts, '../')}</div>
    {''.join(years)}{sample_section}</section>'''
    return layout('文库', '技术分享、学习记录与生活随笔。', '../', 'writing', content)


def about() -> str:
    content = '''<section class="page-intro container"><p class="eyebrow">ABOUT / 关于</p><h1>你好，<br><span>我是 Leyang。</span></h1><p>这里是我分享发现、整理学习过程和记录生活的地方。</p></section>
    <section class="container about-layout"><div class="about-label">A LITTLE MORE</div><div class="prose"><p>我喜欢从一个具体问题出发，沿着代码和现象追下去，再试着用清楚的话讲出来。</p><p>有些文章分享有意思的技术，有些记录尚在学习的过程；生活中的观察也会出现在这里。</p><p>如果你读到感兴趣的内容，欢迎去文库继续探索，或在留言板打个招呼。</p><p><a class="inline-link" href="../writing/">进入文库 ↗</a><br><a class="inline-link" href="../guestbook/">前往留言板 ↗</a></p></div></section>'''
    return layout("关于", "关于 Leyang Xia 和这个网站。", "../", "about", content)


def comment_shell(path: str, env_id: str | None) -> str:
    address = escape(env_id or '', quote=True)
    initial = '加载留言中…' if env_id else '评论暂不可用'
    return (f'<section class="comment-section" aria-labelledby="comment-heading"><h2 id="comment-heading">讨论</h2>'
            '<p class="comment-explainer">无需登录。昵称和内容必填，邮箱选填且不会公开；提交后会显示“等待审核”，留言与回复经审核后公开。</p>'
            f'<div id="comments" data-thread-path="{escape(path, quote=True)}" data-env-id="{address}" role="status">{initial}</div></section>')


def article(post: dict) -> str:
    paragraphs = ''.join(
        f'<section><h2>{escape(heading)}</h2>' + ''.join(f'<p>{escape(paragraph)}</p>' for paragraph in items) + '</section>'
        for heading, items in post['sections']
    )
    other = [p for p in POSTS if p['slug'] != post['slug']]
    next_link = (f'<div class="read-next"><span class="eyebrow">NEXT READ</span><a href="../{escape(other[0]["slug"], quote=True)}/">{escape(other[0]["title"])} ↗</a></div>' if other else '')
    published = post['status'] == 'published'
    when = post['published_at'] if published else '示例稿'
    cover = (f'<figure class="article-cover"><img src="../../{escape(post["cover"], quote=True)}" alt="" loading="lazy"></figure>' if post.get('cover') else '')
    from urllib.parse import quote
    tags = ''.join(f'<a class="tag-link" href="../../writing/?tag={quote(tag)}">{escape(tag)}</a>' for tag in post['tags'])
    content = f'''<article class="article-page container"><div class="article-narrow"><a class="back-link" href="../../writing/">← 返回文库</a>
      <p class="eyebrow">{'ARTICLE' if published else 'PREVIEW / 示例稿'}</p><h1>{escape(post['title'])}</h1><p class="article-deck">{escape(post['summary'])}</p>
      <div class="article-meta"><span>{escape(when)}</span><span>LEYANG XIA</span></div>{cover}<div class="tag-list article-tags">{tags}</div>
      <div class="article-body">{paragraphs}</div><div class="article-end"><a class="inline-link" href="../../writing/">返回文库 ↗</a></div>
      {comment_shell('/writing/' + post['slug'] + '/', os.getenv('TWIKOO_ENV_ID'))}</div>{next_link}</article>'''
    return layout(post['title'], post['summary'], '../../', 'writing', content, comments=True)


def guestbook() -> str:
    content = ('<section class="page-intro container"><p class="eyebrow">GUESTBOOK / 留言板</p><h1>留下几句话。</h1>'
               '<p>关于一篇文章、一个问题，或最近的生活，都欢迎在这里聊聊。</p></section>'
               '<section class="container guestbook-content">' + comment_shell('/guestbook/', os.getenv('TWIKOO_ENV_ID')) + '</section>')
    return layout('留言板', '欢迎留下你的想法。', '../', 'guestbook', content, comments=True)


def not_found() -> str:
    content = '''<section class="page-intro container"><p class="eyebrow">404 / PAGE NOT FOUND</p><h1>这里没有页面。<br><span>换个地方看看。</span></h1><p>你访问的地址可能已经变更。可以回到首页，或从文章列表继续浏览。</p></section>
    <section class="container end-cta"><p>继续探索</p><div><a class="inline-link" href="/">返回首页 ↗</a>　<a class="inline-link" href="/writing/">浏览文章 ↗</a></div></section>'''
    return layout("页面未找到", "你访问的页面不存在。", "/", "", content)


def write(path: str, content: str) -> None:
    target = OUT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content + "\n", encoding="utf-8")


def remove_stale_generated_files(out: Path, publish_root: Path, old_paths: set[str], new_paths: set[str]) -> None:
    for relative in old_paths - new_paths:
        route = Path(relative)
        if route.is_absolute() or '..' in route.parts or route.suffix != '.html':
            raise ValueError(f'invalid generated route: {relative}')
        for base in (out, publish_root):
            target = base / route
            target.unlink(missing_ok=True)
            parent = target.parent
            while parent != base:
                try:
                    parent.rmdir()
                except OSError:
                    break
                parent = parent.parent


def build_site() -> None:
    validate_posts(POSTS)
    pages = {
        'index.html': home(),
        '404.html': not_found(),
        'writing/index.html': writing(),
        'guestbook/index.html': guestbook(),
        'about/index.html': about(),
    }
    for item in POSTS:
        pages[f"writing/{item['slug']}/index.html"] = article(item)
    manifest = OUT / '.generated-pages.json'
    old_paths = set(json.loads(manifest.read_text(encoding='utf-8'))) if manifest.exists() else {'work/index.html'}
    remove_stale_generated_files(OUT, ROOT.parent, old_paths, set(pages))
    for path, content in pages.items():
        write(path, content)
    manifest.write_text(json.dumps(sorted(pages), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for source in [*(OUT / path for path in pages), *(OUT / 'assets').rglob('*')]:
        if source.is_file():
            target = ROOT.parent / source.relative_to(OUT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    print(f"Built {len(pages)} pages in {OUT} and copied to repository root")


if __name__ == '__main__':
    build_site()
