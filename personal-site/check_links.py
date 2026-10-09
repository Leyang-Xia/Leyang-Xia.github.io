"""Offline validation of local HTML links, assets, fragments and search routes."""
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import urljoin, urlsplit, unquote
import xml.etree.ElementTree as ET

from seo import SITE_URL


class References(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.ids = set()
        self.urls = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.add(attrs['id'])
        for key in ('href', 'src', 'data-search-index'):
            if attrs.get(key):
                self.urls.append(attrs[key])
        if tag == 'meta' and (attrs.get('property') == 'og:image' or attrs.get('name') == 'twitter:image'):
            self.urls.append(attrs['content'])


def check_site(root: Path) -> None:
    root = root.resolve()
    documents = {path.resolve(): References(path.read_text(encoding='utf-8'))
                 for path in root.rglob('*.html')}
    site = urlsplit(SITE_URL)
    failures = []

    def validate(source, reference):
        page = source.relative_to(root).as_posix()
        if page.endswith('index.html'):
            page = page[:-len('index.html')]
        resolved = urlsplit(urljoin(SITE_URL + page, reference))
        if (resolved.scheme, resolved.netloc) != (site.scheme, site.netloc):
            return
        target = (root / unquote(resolved.path).lstrip('/')).resolve()
        if not target.is_relative_to(root):
            failures.append(f'{source.relative_to(root)}: path escapes site: {reference}')
            return
        if target.is_dir() or resolved.path.endswith('/'):
            target = target / 'index.html'
        if not target.is_file():
            failures.append(f'{source.relative_to(root)}: missing target: {reference}')
            return
        if resolved.fragment and target in documents and unquote(resolved.fragment) not in documents[target].ids:
            failures.append(f'{source.relative_to(root)}: missing fragment: {reference}')

    for source, document in documents.items():
        for url in document.urls:
            validate(source, url)
    index = root / 'assets/search-index.json'
    if index.is_file():
        for item in json.loads(index.read_text(encoding='utf-8')):
            validate(root / 'index.html', item['path'])
    for name in ('sitemap.xml', 'feed.xml'):
        source = root / name
        if source.is_file():
            tree = ET.fromstring(source.read_text(encoding='utf-8'))
            for node in tree.iter():
                if node.tag.rsplit('}', 1)[-1] in {'loc', 'link'} and node.text:
                    validate(source, node.text)
    if failures:
        raise ValueError('Broken site links:\n' + '\n'.join(failures))


if __name__ == '__main__':
    import sys
    check_site(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / 'dist')
    print('Local links, images, fragments and search routes passed')
