from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import build
from site_fixtures import FIXTURES, SiteTestCase


class MarkdownContentTests(SiteTestCase):
    def test_markdown_loader_preserves_sections_and_thread_path(self):
        post = build.load_posts(FIXTURES, build.OUT)[0]
        self.assertEqual('<section><h2>从问题开始</h2><p>固定输入与接收缓冲。</p><p>另一段文字。</p></section>'
                         '<section><h2>固定可变的东西</h2><p>保留运行命令。</p></section>', post['body_html'])
        self.assertIn('data-thread-path="/writing/example/"', build.article(post))

    def test_invalid_metadata(self):
        for field, value in [('tags', ['']), ('tags', ['a|b']), ('tags', ['a', 'a']),
                             ('title', ' '), ('number', 'x'), ('category', ''),
                             ('published_at', '2026-02-30'), ('published_at', '20261009')]:
            with self.subTest(field=field, value=value):
                post = deepcopy(build.POSTS[0])
                post[field] = value
                if field == 'published_at':
                    post['status'] = 'published'
                with self.assertRaises(ValueError):
                    build.validate_posts([post])

    def test_published_requires_date_and_sample_forbids_date(self):
        for state, day in [('published', None), ('sample', '2026-10-09')]:
            post = deepcopy(build.POSTS[0])
            post.update(status=state, published_at=day)
            with self.assertRaises(ValueError):
                build.validate_posts([post])

    def test_front_matter_errors_include_source_filename(self):
        source = (FIXTURES / 'example.md').read_text()
        for invalid in [source.replace('status: sample', 'status: draft'),
                        source.replace('slug:', 'unknown:', 1),
                        source.replace('title:', 'slug: repeated\ntitle:', 1),
                        source.replace('tags:\n  - 实验方法', 'tags: [实验方法]'),
                        source.replace('## 从问题开始', '# 重复文章标题')]:
            with TemporaryDirectory() as directory:
                path = Path(directory) / 'bad.md'
                path.write_text(invalid)
                with self.assertRaisesRegex(ValueError, 'bad.md'):
                    build.load_posts(Path(directory), build.OUT)

    def test_search_contains_plain_body_tags_and_stable_routes(self):
        index = build.search_index()
        self.assertEqual(5, len(index))
        self.assertEqual('writing/example/', index[0]['path'])
        self.assertIn('实验方法', index[0]['text'])
        self.assertIn('固定可变的东西', index[0]['text'])
        self.assertIn('接收缓冲', index[0]['text'])
        self.assertNotIn('<section>', index[0]['text'])

    def test_markdown_renders_structure_and_safe_inline_content(self):
        from content import render_markdown
        html, text = render_markdown('## 标题\n\n**重点**与 *斜体*、`a < b`、[站点](https://example.com/)\n\n- 一\n- 二\n\n1. 三\n2. 四\n\n> 引用\n\n```python\nprint("<script>")\n```\n\n<script>alert(1)</script>')
        for fragment in ['<section><h2>标题</h2>', '<strong>重点</strong>', '<em>斜体</em>',
                         '<code>a &lt; b</code>', 'href="https://example.com/"',
                         '<ul><li>一</li><li>二</li></ul>', '<ol><li>三</li><li>四</li></ol>',
                         '<blockquote>', '<pre><code class="language-python">', '&lt;script&gt;']:
            self.assertIn(fragment, html)
        self.assertNotIn('<script>', html)
        self.assertIn('重点', text)
        self.assertNotIn('<strong>', text)

    def test_build_reloads_sources_syncs_assets_and_removes_deleted_routes(self):
        from contextlib import redirect_stdout
        from io import StringIO
        import json
        import shutil
        from unittest.mock import patch
        with TemporaryDirectory() as directory:
            root = Path(directory) / 'personal-site'
            shutil.copytree(FIXTURES, root / 'content/posts')
            shutil.copytree(build.OUT / 'assets', root / 'dist/assets')
            with patch.object(build, 'ROOT', root), patch.object(build, 'OUT', root / 'dist'), patch.object(build, 'POSTS', []), redirect_stdout(StringIO()):
                build.build_site()
                before = (root / 'dist/index.html').read_bytes()
                for path in (root / 'dist').rglob('*'):
                    if path.is_file() and path.name != '.generated-pages.json':
                        self.assertEqual(path.read_bytes(), (root.parent / path.relative_to(root / 'dist')).read_bytes())
                post = root / 'content/posts/example.md'
                post.write_text(post.read_text().replace('测试文章', '修改后的标题'))
                build.build_site()
                self.assertNotEqual(before, (root / 'dist/index.html').read_bytes())
                index = json.loads((root / 'dist/assets/search-index.json').read_text())
                self.assertEqual('修改后的标题', index[0]['title'])
                post.unlink()
                build.build_site()
                for base in (root / 'dist', root.parent):
                    self.assertFalse((base / 'writing/example/index.html').exists())
                self.assertNotIn('writing/example/', (root / 'dist/assets/search-index.json').read_text())

    def test_missing_content_directory_is_not_silently_empty(self):
        with TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, 'directory'):
                build.load_posts(Path(directory) / 'missing', build.OUT)

    def test_search_text_keeps_words_across_inline_formatting(self):
        from content import render_markdown
        _, text = render_markdown('## 标题\n\n接收**缓冲**与`代码`。\n\n第二段。')
        self.assertEqual('标题 接收缓冲与代码。 第二段。', text)
