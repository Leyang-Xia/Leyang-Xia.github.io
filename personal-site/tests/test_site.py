from copy import deepcopy
from html.parser import HTMLParser
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

import build


class ContentTests(TestCase):
    def test_samples_have_no_date(self):
        build.validate_posts(build.POSTS)
        published, samples = build.split_posts(build.POSTS)
        self.assertEqual([], published)
        self.assertEqual(3, len(samples))
        self.assertTrue(all(post['status'] == 'sample' and not post['published_at'] for post in samples))

    def test_duplicate_slug_is_rejected(self):
        posts = deepcopy(build.POSTS)
        posts.append(deepcopy(posts[0]))
        with self.assertRaisesRegex(ValueError, 'slug'):
            build.validate_posts(posts)

    def test_published_posts_sort_by_date(self):
        posts = deepcopy(build.POSTS[:2])
        for post, day in zip(posts, ('2025-12-01', '2026-01-02')):
            post['status'] = 'published'
            post['published_at'] = day
        published, samples = build.split_posts(posts)
        self.assertEqual([], samples)
        self.assertEqual(posts[1]['slug'], published[0]['slug'])

    def test_title_is_escaped(self):
        post = deepcopy(build.POSTS[0])
        post['title'] = '<script>&'
        row = build.post_row(post, './')
        self.assertIn('&lt;script&gt;&amp;', row)
        self.assertNotIn('<script>', row)

    def test_optional_cover_uses_publishable_assets(self):
        with TemporaryDirectory() as directory:
            asset = Path(directory) / 'assets' / 'cover.png'
            asset.parent.mkdir()
            asset.write_bytes(b'png')
            post = deepcopy(build.POSTS[0])
            post['cover'] = 'assets/cover.png'
            with patch.object(build, 'OUT', Path(directory)):
                build.validate_posts([post])

    def test_slug_cannot_escape_article_directory(self):
        post = deepcopy(build.POSTS[0])
        post['slug'] = '../about'
        with self.assertRaisesRegex(ValueError, 'slug'):
            build.validate_posts([post])

    def test_cover_cannot_escape_publishable_assets(self):
        post = deepcopy(build.POSTS[0])
        post['cover'] = '../build.py'
        with self.assertRaisesRegex(ValueError, 'cover'):
            build.validate_posts([post])


class PageTests(TestCase):
    def test_archive_keeps_samples_out_of_year_groups(self):
        page = build.writing()
        self.assertIn('版式预览', page)
        self.assertNotIn('class="archive-year"', page)
        self.assertIn('示例稿', page)

    def test_published_archive_is_newest_first(self):
        posts = deepcopy(build.POSTS[:2])
        for post, day in zip(posts, ('2025-12-01', '2026-01-02')):
            post['status'] = 'published'
            post['published_at'] = day
        with patch.object(build, 'POSTS', posts):
            page = build.writing()
        self.assertLess(page.index('2026'), page.index('2025'))

    def test_navigation_and_sidebar(self):
        page = build.home()
        self.assertIn('>文库</a>', page)
        self.assertIn('>留言板</a>', page)
        self.assertIn('class="profile-card"', page)
        self.assertNotIn('>研究</a>', page)

    def test_empty_article_collection_still_builds_home(self):
        with patch.object(build, 'POSTS', []):
            page = build.home()
        self.assertIn('文库', page)
        self.assertIn('暂无文章', page)

    def test_guestbook_and_articles_have_comments(self):
        self.assertIn('id="comments"', build.guestbook())
        self.assertIn('id="comments"', build.article(build.POSTS[0]))
        self.assertIn('示例稿', build.article(build.POSTS[0]))

    def test_search_has_no_research_page(self):
        page = build.search_dialog('../')
        self.assertNotIn('研究方向', page)
        self.assertIn('示例稿', page)

    def test_search_indexes_article_tags(self):
        class SearchItems(HTMLParser):
            def __init__(self):
                super().__init__()
                self.index = []
            def handle_starttag(self, tag, attrs):
                values = dict(attrs)
                if tag == 'li' and values.get('class') == 'search-item':
                    self.index.append(values['data-search'])
        parser = SearchItems()
        parser.feed(build.search_dialog('../'))
        self.assertIn('实验方法', parser.index[0])
        self.assertIn('实时音频', parser.index[1])

    def test_cleanup_only_removes_old_generated_files(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            out = root / 'dist'
            for base in (root, out):
                (base / 'writing').mkdir(parents=True, exist_ok=True)
                (base / 'writing' / 'keep.png').write_bytes(b'keep')
                (base / 'writing' / 'old.html').write_text('old')
            build.remove_stale_generated_files(out, root, {'writing/old.html'}, set())
            for base in (root, out):
                self.assertTrue((base / 'writing' / 'keep.png').exists())
                self.assertFalse((base / 'writing' / 'old.html').exists())


class CommentTests(TestCase):
    def test_thread_uses_site_path(self):
        shell = build.comment_shell('/writing/example/', 'https://comments.example.net')
        self.assertIn('data-thread-path="/writing/example/"', shell)
        self.assertIn('data-env-id="https://comments.example.net"', shell)

    def test_missing_backend_does_not_show_form(self):
        shell = build.comment_shell('/guestbook/', None)
        self.assertIn('评论暂不可用', shell)
        self.assertNotIn('<form', shell)
