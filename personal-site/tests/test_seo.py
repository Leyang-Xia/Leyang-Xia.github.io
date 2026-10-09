from copy import deepcopy
from html.parser import HTMLParser
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
import xml.etree.ElementTree as ET
import build
from site_fixtures import SiteTestCase

class Head(HTMLParser):
    def __init__(self, html):
        super().__init__(); self.meta={}; self.links={}; self.feed(html)
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=='meta': self.meta[a.get('property') or a.get('name')]=a.get('content')
        if tag=='link': self.links[a.get('rel')]=a.get('href')

class SeoTests(SiteTestCase):
    def test_page_canonical_and_sample_noindex(self):
        home=Head(build.home()); archive=Head(build.writing()); sample=Head(build.article(build.POSTS[0]))
        self.assertEqual('https://leyang-xia.github.io/', home.links.get('canonical'))
        self.assertEqual('https://leyang-xia.github.io/writing/', archive.links.get('canonical'))
        self.assertEqual('noindex, follow', sample.meta.get('robots'))
        self.assertEqual('noindex, follow', Head(build.not_found()).meta.get('robots'))
        self.assertEqual('summary_large_image', home.meta.get('twitter:card'))
        self.assertEqual('https://leyang-xia.github.io/assets/share-default.png', home.meta.get('og:image'))
        self.assertEqual('https://leyang-xia.github.io/feed.xml', home.links.get('alternate'))

    def test_published_metadata_and_navigation_are_date_ordered(self):
        posts=deepcopy(build.POSTS)
        for p,d in zip(posts,['2025-01-01','2026-02-01','2026-01-01']):p.update(status='published',published_at=d)
        with patch.object(build,'POSTS',posts):
            page=build.article(posts[2]); head=Head(page)
            self.assertEqual('article',head.meta.get('og:type'))
            self.assertNotEqual('noindex, follow',head.meta.get('robots'))
            self.assertIn('rel="prev" href="../second/"',page)
            self.assertIn('rel="next" href="../example/"',page)
            self.assertIn('<time datetime="2026-01-01">',page)
            self.assertNotIn('rel="prev"',build.article(posts[1]))
            self.assertNotIn('rel="next"',build.article(posts[0]))
        mixed=deepcopy(build.POSTS)
        mixed[1].update(status='published',published_at='2026-01-01')
        with patch.object(build,'POSTS',mixed):
            navigation=build.article_navigation(mixed[0])
            self.assertNotIn('second/',navigation)
            self.assertIn('third/',navigation)


    def test_feed_sitemap_only_published_and_xml_escaping(self):
        from seo import discovery_files
        posts=deepcopy(build.POSTS)
        posts[0].update(status='published',published_at='2026-10-09',title='A & <B>')
        files=discovery_files(posts)
        urls=[node.text for node in ET.fromstring(files['sitemap.xml']).iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
        self.assertIn('https://leyang-xia.github.io/writing/example/',urls)
        self.assertNotIn('https://leyang-xia.github.io/writing/second/',urls)
        rss=ET.fromstring(files['feed.xml']); items=rss.findall('./channel/item')
        self.assertEqual(1,len(items));self.assertEqual('A & <B>',items[0].findtext('title'))
        self.assertIn('sitemap.xml',files['robots.txt'])
        self.assertEqual([],ET.fromstring(discovery_files([])['feed.xml']).findall('./channel/item'))

class LinkTests(TestCase):
    def test_local_routes_images_fragments_and_queries(self):
        from check_links import check_site
        with TemporaryDirectory() as directory:
            root=Path(directory);(root/'writing/example').mkdir(parents=True);(root/'assets').mkdir()
            (root/'assets/a b.png').write_bytes(b'png')
            (root/'index.html').write_text('<a href="writing/example/?tag=x#note">ok</a><img src="assets/a%20b.png"><a href="https://other.example">external</a>')
            post=root/'writing/example/index.html';post.write_text('<p id="note">ok</p><a href="../../">home</a>')
            check_site(root)
            post.write_text('<a href="/missing/">broken</a><a href="/#missing">fragment</a><img src="/assets/gone.png">')
            with self.assertRaisesRegex(ValueError,'missing'):
                check_site(root)

class MetadataSafetyTests(SiteTestCase):
    def test_custom_share_image_and_script_safe_json(self):
        import json,re
        post=deepcopy(build.POSTS[0]);post.update(status='published',published_at='2026-10-09',
            title='</script><script>alert(1)</script>',share_image='assets/share-default.png',share_image_alt='分享图 <说明>')
        page=build.article(post);head=Head(page)
        self.assertEqual('分享图 <说明>',head.meta['og:image:alt'])
        data=re.search(r'<script type="application/ld\+json">(.*?)</script>',page,re.S)[1]
        self.assertNotIn('</script>',data)
        self.assertEqual(post['title'],json.loads(data)['headline'])

    def test_optional_share_fields_load_and_validate(self):
        source=(Path(__file__).parent/'fixtures/example.md').read_text()
        with TemporaryDirectory() as directory:
            path=Path(directory)/'example.md'
            path.write_text(source.replace('cover:', 'share_image: assets/share-default.png\nshare_image_alt: 站点分享图\ncover:'))
            post=build.load_posts(Path(directory),build.OUT)[0]
            self.assertEqual('站点分享图',post['share_image_alt'])
            path.write_text(source.replace('cover:', 'share_image: ../outside.png\ncover:'))
            with self.assertRaisesRegex(ValueError,'share_image'):build.load_posts(Path(directory),build.OUT)
