"""Metadata and discovery documents for the public site; no build timestamps."""
from datetime import datetime, timezone
from email.utils import format_datetime
from html import escape
import json
import xml.etree.ElementTree as ET

SITE_URL = 'https://leyang-xia.github.io/'
DEFAULT_IMAGE = 'assets/share-default.png'


def absolute(path=''):
    return SITE_URL + path.lstrip('/')


def metadata(title, description, path, post=None, noindex=False):
    url = absolute(path)
    published = post is not None and post['status'] == 'published'
    image = (post.get('share_image') or post.get('cover')) if post else None
    if not image or not image.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
        image = DEFAULT_IMAGE
    image_alt = (post.get('share_image_alt') if post else None) or (post['title'] if post and image != DEFAULT_IMAGE else 'Leyang Xia · Notes')
    values = {
        'og:title': title + ' · Leyang Xia', 'og:description': description,
        'og:type': 'article' if published else 'website', 'og:url': url,
        'og:site_name': 'Leyang Xia', 'og:locale': 'zh_CN',
        'og:image': absolute(image), 'og:image:alt': image_alt,
        'twitter:card': 'summary_large_image', 'twitter:title': title + ' · Leyang Xia',
        'twitter:description': description, 'twitter:image': absolute(image),
        'twitter:image:alt': image_alt,
    }
    if image == DEFAULT_IMAGE:
        values.update({'og:image:width': '1200', 'og:image:height': '630'})
    lines = [f'<link rel="canonical" href="{escape(url, quote=True)}">',
             f'<link rel="alternate" type="application/rss+xml" title="Leyang Xia" href="{absolute("feed.xml")}">']
    if noindex or (post and not published):
        lines.append('<meta name="robots" content="noindex, follow">')
    for key, value in values.items():
        attr = 'property' if key.startswith('og:') else 'name'
        lines.append(f'<meta {attr}="{key}" content="{escape(value, quote=True)}">')
    data = None
    if path == '':
        data = {'@context': 'https://schema.org', '@graph': [
            {'@type': 'WebSite', 'name': 'Leyang Xia', 'url': SITE_URL},
            {'@type': 'Person', 'name': 'Leyang Xia', 'url': absolute('about/'),
             'sameAs': ['https://github.com/Leyang-Xia']}]}
    elif published:
        data = {'@context': 'https://schema.org', '@type': 'BlogPosting',
                'headline': post['title'], 'description': description,
                'datePublished': post['published_at'], 'url': url,
                'mainEntityOfPage': url, 'image': absolute(image),
                'author': {'@type': 'Person', 'name': 'Leyang Xia', 'url': absolute('about/')}}
    if data:
        # JSON must remain JSON; escape HTML delimiters to prevent closing script tags.
        payload = json.dumps(data, ensure_ascii=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
        lines.append(f'<script type="application/ld+json">{payload}</script>')
    return '\n  '.join(lines)


def discovery_files(posts):
    published = sorted((p for p in posts if p['status'] == 'published'),
                       key=lambda p: (p['published_at'], p['slug']), reverse=True)
    namespace = 'http://www.sitemaps.org/schemas/sitemap/0.9'
    ET.register_namespace('', namespace)
    sitemap = ET.Element(f'{{{namespace}}}urlset')
    for path in ['', 'writing/', 'about/', 'guestbook/'] + [f'writing/{p["slug"]}/' for p in published]:
        node = ET.SubElement(sitemap, f'{{{namespace}}}url')
        ET.SubElement(node, f'{{{namespace}}}loc').text = absolute(path)
        # Publication date is not a reliable modification date; omit lastmod.
    rss = ET.Element('rss', version='2.0')
    channel = ET.SubElement(rss, 'channel')
    for name, value in [('title', 'Leyang Xia'), ('link', SITE_URL),
                        ('description', '技术、学习与日常笔记。'), ('language', 'zh-CN')]:
        ET.SubElement(channel, name).text = value
    for post in published:
        item = ET.SubElement(channel, 'item')
        url = absolute(f'writing/{post["slug"]}/')
        for name, value in [('title', post['title']), ('link', url), ('description', post['summary']),
                            ('pubDate', format_datetime(datetime.fromisoformat(post['published_at']).replace(tzinfo=timezone.utc), usegmt=True))]:
            ET.SubElement(item, name).text = value
        ET.SubElement(item, 'guid', isPermaLink='true').text = url
        for tag in post['tags']:
            ET.SubElement(item, 'category').text = tag
    def xml(node):
        ET.indent(node, space='  ')
        return ET.tostring(node, encoding='utf-8', xml_declaration=True).decode('utf-8')
    return {'robots.txt': 'User-agent: *\nAllow: /\nSitemap: ' + absolute('sitemap.xml'),
            'sitemap.xml': xml(sitemap), 'feed.xml': xml(rss)}
