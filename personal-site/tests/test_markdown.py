from html.parser import HTMLParser
from unittest import TestCase

from content import render_markdown


class Document(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.elements = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))

    def attrs(self, tag):
        return [attrs for name, attrs in self.elements if name == tag]


class MarkdownTests(TestCase):
    def test_tables_nested_lists_and_multi_paragraph_items(self):
        html, text = render_markdown('''## 数据

| 方法 | 结果 |
| :--- | ---: |
| **原始** | 12 |

- 外层
  - 内层

  同一个列表项的第二段。

---
''')
        doc = Document(html)
        self.assertEqual(1, len(doc.attrs('table')))
        self.assertEqual(2, len(doc.attrs('ul')))
        self.assertIn('<p>同一个列表项的第二段。</p>', html)
        self.assertEqual(1, len(doc.attrs('hr')))
        for word in ('方法', '结果', '原始', '12', '内层', '第二段'):
            self.assertIn(word, text)
        self.assertIn('方法 结果', text)

    def test_reference_links_images_titles_and_parenthesized_urls(self):
        html, text = render_markdown('''[参考][source] 与 [括号](https://example.com/a_(b))。

![实验 **波形**](</assets/audio plot(1).svg> "对照图")

[source]: https://example.com/docs "资料"
''')
        doc = Document(html)
        self.assertEqual(['https://example.com/docs', 'https://example.com/a_(b)'], [a['href'] for a in doc.attrs('a')])
        image = doc.attrs('img')[0]
        self.assertEqual('/assets/audio%20plot(1).svg', image['src'])
        self.assertEqual('实验 波形', image['alt'])
        self.assertEqual('lazy', image['loading'])
        self.assertEqual('资料', doc.attrs('a')[0]['title'])
        self.assertIn('实验 波形', text)
        self.assertNotIn('**', text)

    def test_footnotes_link_both_ways_and_are_in_search(self):
        html, text = render_markdown('''正文[^note]，再次引用[^note]。

[^note]: 脚注 **解释**。

    第二段补充。
''')
        doc = Document(html)
        ids = {attrs['id'] for _, attrs in doc.elements if 'id' in attrs}
        anchors = [attrs['href'][1:] for attrs in doc.attrs('a') if attrs.get('href', '').startswith('#')]
        self.assertTrue(anchors)
        self.assertTrue(set(anchors).issubset(ids))
        self.assertIn('脚注 解释', text)
        self.assertIn('第二段补充', text)
        self.assertNotIn('↩', text)

    def test_nested_inline_format_task_lists_and_indented_code(self):
        html, text = render_markdown('''**粗体里有 *强调* 和 [链接](https://example.com)**，~~删除~~，<https://example.com>。

- [x] 已完成
- [ ] 待完成

    # nested heading in code

~~~python
print("<tag>")
~~~
''')
        doc = Document(html)
        self.assertIn('<strong>粗体里有 <em>强调</em>', html)
        self.assertIn('<s>删除</s>', html)
        checks = doc.attrs('input')
        self.assertEqual(2, len(checks))
        self.assertTrue(all('disabled' in item for item in checks))
        self.assertIn('checked', checks[0])
        self.assertNotIn('checked', checks[1])
        self.assertIn('print(&quot;&lt;tag&gt;&quot;)', html)
        self.assertIn('已完成', text)

    def test_raw_html_is_text_and_dangerous_urls_never_render(self):
        for body in ['[x](javascript:alert(1))', '[x](vbscript:msgbox)',
                     '[x](data:text/html;base64,AAAA)', '[x](file:///etc/passwd)',
                     '![x](data:image/svg+xml;base64,AAAA)', '![x](mailto:a@example.com)',
                     '[x](//evil.example)', '[x](https://good.example\\@evil.example)']:
            with self.subTest(body=body):
                html, _ = render_markdown(body)
                doc = Document(html)
                self.assertEqual([], doc.attrs('a'))
                self.assertEqual([], doc.attrs('img'))
        html, _ = render_markdown('<script>alert(1)</script>\n\n<img src=x onerror=alert(1)>')
        self.assertIn('&lt;script&gt;', html)
        self.assertNotIn('<script', html)
        self.assertNotIn('<img', html)

    def test_top_level_h1_fails_but_nested_h2_does_not_open_article_sections(self):
        with self.assertRaisesRegex(ValueError, 'h1'):
            render_markdown('# 第二个文章标题')
        html, _ = render_markdown('## 章节\n\n> ## 引用里的标题\n\n正文\n\n## 下一章\n\n结束')
        self.assertEqual(2, len(Document(html).attrs('section')))
        self.assertIn('<blockquote>', html)
        self.assertIn('引用里的标题', html)

    def test_commonmark_fallback_for_unclosed_fence_and_undefined_reference(self):
        html, text = render_markdown('```\n未闭合代码')
        self.assertIn('<pre><code>未闭合代码', html)
        self.assertIn('未闭合代码', text)
        html, _ = render_markdown('[未知][missing]')
        self.assertEqual([], Document(html).attrs('a'))
        self.assertIn('[未知][missing]', html)

    def test_four_space_indented_code_preserves_whitespace(self):
        html, text = render_markdown('    x = 1\n    y = 2\n')
        self.assertIn('<pre><code>x = 1\ny = 2\n</code></pre>', html)
        self.assertIn('x = 1 y = 2', text)

    def test_subheadings_inside_footnotes_do_not_create_article_sections(self):
        html, _ = render_markdown('## 正文\n\n内容[^n]\n\n[^n]: 注释\n\n    ## 注释的小标题\n\n    补充')
        sections = Document(html).attrs('section')
        self.assertEqual([{}, {'class': 'footnotes'}], sections)

    def test_link_destinations_with_space_entities_and_image_reference(self):
        html, text = render_markdown('[空格](<https://example.com/a b(c)> "说明") 与 [邮件](mailto:a@example.com)\n\n![波形][fig]\n\n[fig]: /assets/wave.svg')
        doc = Document(html)
        self.assertEqual('https://example.com/a%20b(c)', doc.attrs('a')[0]['href'])
        self.assertEqual('mailto:a@example.com', doc.attrs('a')[1]['href'])
        self.assertEqual('/assets/wave.svg', doc.attrs('img')[0]['src'])
        self.assertIn('波形', text)
        for source in ('[x](javascript&#58;alert)', '[x](JAVASCRIPT:alert)', '[x](https://example.com/%0afoo)'):
            html, _ = render_markdown(source)
            self.assertEqual([], Document(html).attrs('a'))

    def test_code_in_image_alt_is_readable_and_searchable(self):
        html, text = render_markdown('![使用 `Opus` 的波形](/assets/wave.svg)')
        self.assertEqual('使用 Opus 的波形', Document(html).attrs('img')[0]['alt'])
        self.assertIn('使用 Opus 的波形', text)

    def test_rich_article_is_built_and_searchable_with_stable_comment_route(self):
        from contextlib import redirect_stdout
        from io import StringIO
        import json
        from pathlib import Path
        import shutil
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        import build
        fixture = Path(__file__).parent / 'fixtures/markdown'
        with TemporaryDirectory() as directory:
            root = Path(directory) / 'personal-site'
            (root / 'content/posts').mkdir(parents=True)
            shutil.copy2(fixture / 'showcase.md', root / 'content/posts/showcase.md')
            shutil.copytree(build.OUT / 'assets', root / 'dist/assets')
            shutil.copy2(fixture / 'waveform.svg', root / 'dist/assets/markdown-waveform.svg')
            with patch.object(build, 'ROOT', root), patch.object(build, 'OUT', root / 'dist'), patch.object(build, 'POSTS', []), redirect_stdout(StringIO()):
                build.build_site()
            page = (root / 'dist/writing/markdown-showcase/index.html').read_text()
            doc = Document(page)
            self.assertEqual(1, len(doc.attrs('table')))
            self.assertEqual('/assets/markdown-waveform.svg', doc.attrs('img')[0]['src'])
            self.assertIn('data-thread-path="/writing/markdown-showcase/"', page)
            index = json.loads((root / 'dist/assets/search-index.json').read_text())[0]
            for term in ('48000 Hz', '软件版本', '对照实验波形', '固定输入、轨迹和版本', 'marker'):
                self.assertIn(term, index['text'])
            self.assertNotIn('<img', index['text'])
            self.assertEqual('writing/markdown-showcase/', index['path'])
            self.assertEqual((root / 'dist/assets/search-index.json').read_bytes(), (root.parent / 'assets/search-index.json').read_bytes())
