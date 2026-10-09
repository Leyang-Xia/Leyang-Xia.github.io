"""Strict site front matter, article validation and Markdown loading."""

from datetime import date
import json
from pathlib import Path
import re
from markdown_renderer import render_markdown

FIELDS = {'slug', 'title', 'category', 'summary', 'number', 'status',
          'published_at', 'tags', 'cover'}


def scalar(value: str) -> str | None:
    value = value.strip()
    if not value:
        return None
    if value.startswith('"'):
        result = json.loads(value)
        if not isinstance(result, str):
            raise ValueError('expected a quoted string')
        return result
    if value.startswith("'"):
        if not value.endswith("'") or len(value) < 2:
            raise ValueError('unclosed quoted string')
        return value[1:-1].replace("''", "'")
    if value[0] in '[{&*!>|' or value in {'null', '~', 'true', 'false'}:
        raise ValueError('unsupported front matter value; use a string or blank')
    return value


def parse_front_matter(source: str) -> tuple[dict, str]:
    lines = source.splitlines()
    if not lines or lines[0] != '---':
        raise ValueError('front matter must start with ---')
    try:
        end = lines.index('---', 1)
    except ValueError:
        raise ValueError('front matter must end with ---') from None
    metadata = {}
    current = None
    for line in lines[1:end]:
        if not line.strip() or line.startswith('#'):
            continue
        if line.startswith('  - '):
            if current != 'tags':
                raise ValueError('list items are only supported under tags')
            metadata['tags'].append(scalar(line[4:]))
            continue
        match = re.fullmatch(r'([a-z_]+):(?:\s+(.*))?', line)
        if not match:
            raise ValueError(f'unsupported front matter line: {line}')
        key, value = match.groups()
        if key not in FIELDS or key in metadata:
            raise ValueError(f'unknown or duplicate field: {key}')
        current = key
        if key == 'tags':
            if value and value.strip():
                raise ValueError('tags must be an indented list')
            metadata[key] = []
        else:
            metadata[key] = scalar(value or '')
    missing = FIELDS - metadata.keys()
    if missing:
        raise ValueError('missing fields: ' + ', '.join(sorted(missing)))
    return metadata, '\n'.join(lines[end + 1:])


def validate_posts(posts: list[dict], assets_root: Path) -> None:
    seen = set()
    for post in posts:
        slug = post.get('slug')
        if not isinstance(slug, str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', slug):
            raise ValueError('invalid slug')
        if slug in seen:
            raise ValueError('duplicate slug: ' + slug)
        seen.add(slug)
        if post.get('status') not in {'sample', 'published'}:
            raise ValueError('invalid status')
        for field in ('title', 'summary', 'category'):
            if not isinstance(post.get(field), str) or not post[field].strip():
                raise ValueError('missing article metadata: ' + field)
        if not isinstance(post.get('number'), str) or not re.fullmatch(r'\d+', post['number']):
            raise ValueError('number must be a numeric string')
        tags = post.get('tags')
        if (not isinstance(tags, list) or not tags
                or any(not isinstance(tag, str) or not tag.strip() or '|' in tag for tag in tags)
                or len(set(tags)) != len(tags)):
            raise ValueError('tags must be unique nonempty strings without |')
        day = post.get('published_at')
        if post['status'] == 'published':
            if not isinstance(day, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', day):
                raise ValueError('published_at is required in YYYY-MM-DD format')
            date.fromisoformat(day)
        elif day is not None:
            raise ValueError('sample must not set published_at')
        value = post.get('cover')
        if value is not None:
            if not isinstance(value, str) or not value:
                raise ValueError('cover must be blank or an asset path')
            cover = Path(value)
            assets = (assets_root / 'assets').resolve()
            target = (assets_root / cover).resolve()
            if (cover.is_absolute() or '..' in cover.parts or '\\' in value
                    or not cover.parts or cover.parts[0] != 'assets'
                    or not target.is_relative_to(assets) or not target.is_file()):
                raise ValueError('cover must be an existing file in assets')


def load_posts(directory: Path, assets_root: Path) -> list[dict]:
    if not directory.is_dir():
        raise ValueError(f'content directory is missing: {directory}')
    posts = []
    seen = set()
    for path in sorted(directory.glob('*.md')):
        try:
            post, body = parse_front_matter(path.read_text(encoding='utf-8'))
            validate_posts([post], assets_root)
            if post['slug'] in seen:
                raise ValueError('duplicate slug: ' + post['slug'])
            seen.add(post['slug'])
            if not body.strip():
                raise ValueError('article body must not be empty')
            post['body_html'], post['body_text'] = render_markdown(body)
            posts.append(post)
        except ValueError as error:
            raise ValueError(f'{path}: {error}') from error
    return sorted(posts, key=lambda post: (int(post['number']), post['slug']))
