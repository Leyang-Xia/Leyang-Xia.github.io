"""Build the dependency-free static personal site into dist/."""

from html import escape
from pathlib import Path


ROOT = Path(__file__).parent
OUT = ROOT / "dist"

POSTS = [
    {
        "slug": "reproducible-audio-experiments",
        "title": "如何让一次音频实验可以重来",
        "category": "技术 / 实验方法",
        "summary": "从固定输入、网络条件到听感样本：一份结果真正值得信任，需要留下哪些线索？",
        "number": "01",
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


def search_dialog(root: str) -> str:
    items = []
    for post in POSTS:
        body = " ".join(
            heading + " " + " ".join(paragraphs)
            for heading, paragraphs in post["sections"]
        )
        items.append((
            f'writing/{post["slug"]}/', post["category"],
            post["title"], post["summary"], body,
        ))
    items.extend([
        ("work/", "页面", "研究方向", "实时语音、网络条件与压缩系统。", "音频 编解码 丢包 抖动 体验评估 信息压缩 表示 系统设计"),
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


def layout(title: str, description: str, root: str, current: str, content: str) -> str:
    nav = [
        ("首页", "", "home"),
        ("文章", "writing/", "writing"),
        ("研究", "work/", "work"),
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
    return f'''<a class="post-row" href="{href}">
      <span class="post-index">{post['number']}</span>
      <span class="post-main"><span class="post-category">{post['category']}</span><strong>{post['title']}</strong><span class="post-summary">{post['summary']}</span></span>
      <span class="post-arrow" aria-hidden="true">↗</span>
    </a>'''


def home() -> str:
    rows = "".join(post_row(p, "./") for p in POSTS)
    content = f'''<section class="home-hero container">
      <div class="hero-main"><p class="eyebrow">LEYANG XIA / 个人网站</p><h1>把复杂的事，<br><span>慢慢讲清楚。</span></h1><p class="hero-description">这里记录我对实时音频、网络传输和信息压缩的探索，也写工作之外那些值得停下来想一想的事。</p><a class="inline-link" href="./writing/">浏览文章 <span aria-hidden="true">↗</span></a></div>
      <div class="hero-side"><span class="side-line"></span><p>技术是理解世界的一种方式。写作让理解变得更清晰。</p><span class="side-mark">NOTES ON MAKING &amp; LIVING</span></div>
    </section>
    <section class="container content-section" aria-labelledby="featured-title"><div class="section-top"><div><p class="eyebrow">SELECTED WRITING</p><h2 id="featured-title">文章与随笔</h2></div><a class="quiet-link" href="./writing/">全部文章 ↗</a></div><div class="post-list">{rows}</div><p class="draft-note">当前文章为展示版式的示例稿，正式发布前可替换为你的原文。</p></section>
    <section class="container focus-section" aria-labelledby="focus-title"><div><p class="eyebrow">FOCUS</p><h2 id="focus-title">长期关注的问题</h2></div><div class="focus-copy"><p>语音穿过不稳定网络之后，怎样依然清晰、自然？一个实验的结果，怎样经得起重复与比较？这些问题把系统、算法和人的感受连在一起。</p><a class="inline-link" href="./work/">了解我的研究方向 <span aria-hidden="true">↗</span></a></div></section>'''
    return layout("首页", "Leyang Xia 的个人网站，记录技术探索、研究方向与日常随笔。", "./", "home", content)


def writing() -> str:
    rows = "".join(post_row(p, "../") for p in POSTS)
    content = f'''<section class="page-intro container"><p class="eyebrow">WRITING / 文章</p><h1>写下来，<br><span>才能想得更清楚。</span></h1><p>技术笔记、研究方法，以及工作之外的观察。每一篇都从一个具体的问题开始。</p></section>
    <section class="container listing-section" aria-label="文章列表"><div class="listing-head"><span>全部文章</span><span>共 {len(POSTS)} 篇</span></div><div class="post-list">{rows}</div><p class="draft-note">这些文章是用于展示网站结构的示例稿，等待替换为你的正式内容。</p></section>'''
    return layout("文章", "技术笔记与日常随笔。", "../", "writing", content)


def work() -> str:
    content = '''<section class="page-intro container"><p class="eyebrow">FOCUS / 研究方向</p><h1>从真实问题，<br><span>走向可验证的答案。</span></h1><p>我关心音频与网络交汇处的工程问题，也在意结论能否被复现、被解释、被真正用起来。</p></section>
    <section class="container work-list" aria-label="关注的方向">
      <article class="work-item"><span class="work-num">01 / AUDIO</span><div><h2>实时语音与编解码</h2><p>低延迟通信里，音质、带宽和计算成本总在互相拉扯。我关注编码、冗余与恢复策略如何影响最终的通话体验。</p></div></article>
      <article class="work-item"><span class="work-num">02 / NETWORK</span><div><h2>网络条件与体验评估</h2><p>丢包和抖动不只是一组百分比。把网络轨迹、接收行为和可播放结果放在一起，才能看清一次改进究竟带来了什么。</p></div></article>
      <article class="work-item"><span class="work-num">03 / SYSTEMS</span><div><h2>压缩、表示与系统设计</h2><p>从紧凑的数据表示到完整链路的实现，好的设计需要清楚的边界、可解释的取舍和经得起验证的结果。</p></div></article>
    </section>
    <section class="container end-cta"><p>这些方向还在不断变化，文章里会记录具体问题与思考过程。</p><a class="inline-link" href="../writing/">读一些文章 <span aria-hidden="true">↗</span></a></section>'''
    return layout("研究方向", "Leyang Xia 关注实时音频、网络评估与信息压缩。", "../", "work", content)


def about() -> str:
    content = '''<section class="page-intro container"><p class="eyebrow">ABOUT / 关于</p><h1>你好，<br><span>我是 Leyang。</span></h1><p>喜欢追问一个系统为什么这样工作，也喜欢把复杂问题拆开，再用清楚的语言重新讲出来。</p></section>
    <section class="container about-layout"><div class="about-label">A LITTLE MORE</div><div class="prose"><p>我的兴趣常常落在实时音频、网络传输和信息压缩的交叉处：从一个具体的现象出发，沿着数据与代码追下去，再回到人实际听见、感受到的结果。</p><p>这个网站是一个开放的笔记本。技术文章会尽量交代问题、方法与边界；日常随笔则留给那些暂时不需要结论的观察。</p><p>如果你对相似的问题感兴趣，可以从文章开始，也可以看看我的公开代码。</p><p><a class="inline-link" href="../writing/">阅读文章 <span aria-hidden="true">↗</span></a><br><a class="inline-link" href="https://github.com/Leyang-Xia" target="_blank" rel="noopener noreferrer">访问 GitHub <span aria-hidden="true">↗</span></a></p></div></section>'''
    return layout("关于", "关于 Leyang Xia：技术探索与日常记录。", "../", "about", content)


def article(post: dict) -> str:
    paragraphs = "".join(
        f'<section><h2>{heading}</h2>' + "".join(f'<p>{paragraph}</p>' for paragraph in items) + '</section>'
        for heading, items in post["sections"]
    )
    other = [p for p in POSTS if p is not post]
    next_post = other[0]
    content = f'''<article class="article-page container"><div class="article-narrow"><a class="back-link" href="../../writing/">← 返回文章列表</a><p class="eyebrow">{post['category']}</p><h1>{post['title']}</h1><p class="article-deck">{post['summary']}</p><div class="article-meta"><span>示例稿</span><span>LEYANG XIA</span></div><div class="article-body">{paragraphs}</div><div class="article-end"><p>写作是持续修正理解的过程。</p><a class="inline-link" href="../../writing/">返回全部文章 <span aria-hidden="true">↗</span></a></div></div><div class="read-next"><span class="eyebrow">NEXT READ</span><a href="../{next_post['slug']}/">{next_post['title']} <span aria-hidden="true">↗</span></a></div></article>'''
    return layout(post["title"], post["summary"], "../../", "writing", content)


def write(path: str, content: str) -> None:
    target = OUT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content + "\n", encoding="utf-8")


if __name__ == "__main__":
    write("index.html", home())
    write("writing/index.html", writing())
    write("work/index.html", work())
    write("about/index.html", about())
    for item in POSTS:
        write(f"writing/{item['slug']}/index.html", article(item))
    print(f"Built {4 + len(POSTS)} pages in {OUT}")
