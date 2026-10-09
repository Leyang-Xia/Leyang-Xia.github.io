"""Stable inputs: editing real articles must never require editing unit tests."""
from copy import deepcopy
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
import build

FIXTURES = Path(__file__).parent / 'fixtures'


def sample_posts():
    first = build.load_posts(FIXTURES, build.OUT)[0]
    posts = [deepcopy(first) for _ in range(3)]
    for post, slug, number, tags in zip(posts, ('example', 'second', 'third'),
                                        ('01', '02', '03'), (['实验方法'], ['实时音频'], ['随笔'])):
        post.update(slug=slug, number=number, tags=tags)
    return posts


class SiteTestCase(TestCase):
    def setUp(self):
        context = patch.object(build, 'POSTS', sample_posts())
        context.start()
        self.addCleanup(context.stop)
