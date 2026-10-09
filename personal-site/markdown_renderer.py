"""CommonMark with selected writing extensions, using pinned local dependencies."""

from html import escape
from html.parser import HTMLParser
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

# Upstream packages use absolute imports; prefer the checked-in copies over
# packages installed in the machine's Python environment.
sys.path.insert(0, str(Path(__file__).parent / 'vendor'))
from markdown_it import MarkdownIt
from markdown_it.renderer import RendererHTML
from markdown_it.token import Token
from mdit_py_plugins.footnote import footnote_plugin
from mdit_py_plugins.tasklists import tasklists_plugin


def allowed_url(value: str, *, image: bool = False) -> bool:
    try:
        parsed = urlsplit(value)
        decoded = unquote(value)
        return (parsed.scheme.lower() in ({'', 'http', 'https'} if image else {'', 'http', 'https', 'mailto'})
                and not value.startswith('//') and '\\' not in decoded
                and not any(ord(char) < 32 or ord(char) == 127 for char in decoded)
                and not parsed.username and not parsed.password)
    except ValueError:
        return False


class ArticleRenderer(RendererHTML):
    def renderToken(self, tokens, idx, options, env):
        result = super().renderToken(tokens, idx, options, env)
        # Keep existing paragraphs/sections byte-identical. Code blocks use
        # separate upstream render rules so their whitespace is never stripped.
        return result.strip('\n') if tokens[idx].block else result

    def softbreak(self, tokens, idx, options, env):
        return ' '

    def renderInlineAsText(self, tokens, options, env):
        # Include code spans in image descriptions as visible text.
        result = []
        for token in tokens or []:
            if token.type in {'text', 'code_inline'}:
                result.append(token.content)
            elif token.type == 'image':
                result.append(self.renderInlineAsText(token.children, options, env))
            elif token.type in {'softbreak', 'hardbreak'}:
                result.append(' ')
        return ''.join(result)

    def image(self, tokens, idx, options, env):
        token = tokens[idx]
        if not allowed_url(token.attrGet('src') or '', image=True):
            return escape(self.renderInlineAsText(token.children, options, env))
        token.attrSet('loading', 'lazy')
        token.attrSet('decoding', 'async')
        return super().image(tokens, idx, options, env)

    def table_open(self, tokens, idx, options, env):
        return '<div class="table-scroll" role="region" aria-label="表格" tabindex="0"><table>'

    def table_close(self, tokens, idx, options, env):
        return '</table></div>'


class PlainText(HTMLParser):
    """Visible prose, code, image descriptions and notes, without backlink noise."""
    BLOCKS = {'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li', 'pre', 'th', 'td', 'blockquote'}
    VOID = {'img', 'input', 'br', 'hr'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.ignored_depth = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if self.ignored_depth:
            if tag not in self.VOID:
                self.ignored_depth += 1
            return
        if {'footnote-ref', 'footnote-backref'} & set(attrs.get('class', '').split()):
            self.ignored_depth = 1
            return
        if tag in self.BLOCKS or tag in {'br', 'hr'}:
            self.parts.append(' ')
        if tag == 'img':
            self.parts.append(' ' + attrs.get('alt', '') + ' ')

    def handle_endtag(self, tag):
        if self.ignored_depth:
            self.ignored_depth -= 1
        elif tag in self.BLOCKS:
            self.parts.append(' ')

    def handle_data(self, data):
        if not self.ignored_depth:
            self.parts.append(data)


def render_markdown(source: str) -> tuple[str, str]:
    md = (MarkdownIt('commonmark', {'html': False}, renderer_cls=ArticleRenderer)
          .enable(['table', 'strikethrough'])
          .use(footnote_plugin)
          .use(tasklists_plugin))
    md.validateLink = allowed_url
    env = {}
    tokens = md.parse(source, env)
    section = False
    wrapped = []
    for token in tokens:
        if token.type == 'heading_open' and token.level == 0:
            if token.tag == 'h1':
                raise ValueError('top-level h1 belongs in front matter title; use ## in the body')
            if token.tag == 'h2':
                if section:
                    wrapped.append(Token('section_close', 'section', -1))
                wrapped.append(Token('section_open', 'section', 1))
                section = True
        if token.type == 'footnote_block_open' and section:
            wrapped.append(Token('section_close', 'section', -1))
            section = False
        wrapped.append(token)
    if section:
        wrapped.append(Token('section_close', 'section', -1))
    html = md.renderer.render(wrapped, md.options, env)
    text = PlainText()
    text.feed(html)
    return html, re.sub(r'\s+', ' ', ''.join(text.parts)).strip()
