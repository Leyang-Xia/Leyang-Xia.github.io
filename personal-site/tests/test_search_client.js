const assert = require('node:assert/strict');
const { createSearchLoader, matchingSearchItems, renderSearchResults } = require('../dist/assets/site.js');

const index = [{ path: 'writing/example/', category: '文章', title: '音频 <script>', summary: '固定输入', text: '实验方法 接收缓冲' }];

async function run() {
  assert.equal(typeof createSearchLoader, 'function', 'lazy search loader is required');
  let calls = 0;
  let release;
  const load = createSearchLoader('../assets/search-index.json', async url => {
    assert.equal(url, '../assets/search-index.json');
    calls++;
    await new Promise(resolve => { release = resolve; });
    return { ok: true, json: async () => index };
  });
  assert.equal(calls, 0);
  const first = load();
  const second = load();
  release();
  assert.deepEqual(await first, index);
  assert.deepEqual(await second, index);
  assert.deepEqual(await load(), index);
  assert.equal(calls, 1, 'concurrent and later searches share one request');
  assert.deepEqual(matchingSearchItems(index, '音频 实验方法'), index);
  assert.deepEqual(matchingSearchItems(index, '接收缓冲'), index);
  assert.deepEqual(matchingSearchItems(index, '固定输入'), index);
  assert.deepEqual(matchingSearchItems(index, 'missing'), []);
  assert.deepEqual(matchingSearchItems(index, '  '), index);

  let attempt = 0;
  const retry = createSearchLoader('/index.json', async () => {
    attempt++;
    if (attempt === 1) throw new Error('offline');
    return { ok: true, json: async () => index };
  });
  await assert.rejects(retry(), /offline/);
  assert.deepEqual(await retry(), index);
  assert.equal(attempt, 2);
  await assert.rejects(createSearchLoader('/index.json', async () => ({ ok: false, status: 404 }))(), /404/);
  for (const invalid of [{}, [null], [{ ...index[0], path: 'javascript:alert(1)' }],
                         [{ ...index[0], path: '//evil.example/' }], [{ ...index[0], text: null }]]) {
    await assert.rejects(createSearchLoader('/index.json', async () => ({ ok: true, json: async () => invalid }))());
  }

  // A minimal DOM boundary: malicious text must be assigned as text, never HTML.
  const document = { createElement(tag) { return { tag, children: [], append(...nodes) { this.children.push(...nodes); } }; } };
  const list = { ownerDocument: document, children: [], replaceChildren(...nodes) { this.children = nodes; } };
  renderSearchResults(list, index, 'https://example.com/');
  const link = list.children[0].children[0];
  assert.equal(link.href, 'https://example.com/writing/example/');
  assert.equal(link.children[1].textContent, '音频 <script>');
  renderSearchResults(list, [], 'https://example.com/');
  assert.equal(list.children.length, 0);
  console.log('Search client checks passed');
}
run().catch(error => { console.error(error); process.exitCode = 1; });
