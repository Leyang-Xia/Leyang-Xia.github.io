(() => {
  function visibleForTag(rowTags, selectedTag, allTags) {
    return !selectedTag || !allTags.includes(selectedTag) || rowTags.includes(selectedTag);
  }
  function createSearchLoader(url, request = fetch) {
    let pending;
    return function load() {
      if (!pending) {
        pending = (async () => {
          const response = await request(url);
          if (!response.ok) throw new Error(`Search index HTTP ${response.status}`);
          const items = await response.json();
          if (!Array.isArray(items) || !items.every(item => item &&
            ['path', 'category', 'title', 'summary', 'text'].every(key => typeof item[key] === 'string') &&
            /^(?:writing\/[a-z0-9]+(?:-[a-z0-9]+)*\/|guestbook\/|about\/)$/.test(item.path))) {
            throw new Error('Invalid search index');
          }
          return items;
        })().catch(error => {
          pending = undefined;
          throw error;
        });
      }
      return pending;
    };
  }

  function matchingSearchItems(items, query) {
    const terms = query.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
    return items.filter(item => {
      const text = [item.category, item.title, item.summary, item.text].join(' ').toLocaleLowerCase();
      return terms.every(term => text.includes(term));
    });
  }

  function renderSearchResults(list, items, root) {
    const doc = list.ownerDocument;
    list.replaceChildren(...items.map(item => {
      const row = doc.createElement('li');
      row.className = 'search-item';
      const anchor = doc.createElement('a');
      anchor.href = new URL(item.path, root).href;
      for (const [tag, value] of [['span', item.category], ['strong', item.title], ['small', item.summary]]) {
        const node = doc.createElement(tag);
        node.textContent = value;
        anchor.append(node);
      }
      row.append(anchor);
      return row;
    }));
  }

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { visibleForTag, createSearchLoader, matchingSearchItems, renderSearchResults };
  }
  if (typeof document === 'undefined') return;

  const archiveRows = Array.from(document.querySelectorAll('.listing-section [data-tags]'));
  if (archiveRows.length) {
    const selectedTag = new URLSearchParams(location.search).get('tag');
    const allTags = [...new Set(archiveRows.flatMap(row => row.dataset.tags.split('|')))];
    for (const row of archiveRows) {
      row.hidden = !visibleForTag(row.dataset.tags.split('|'), selectedTag, allTags);
    }
    for (const section of document.querySelectorAll('.archive-year, .sample-section')) {
      section.hidden = !section.querySelector('.post-row:not([hidden])');
    }
    for (const tagLink of document.querySelectorAll('.archive-tags a')) {
      const tag = new URL(tagLink.href).searchParams.get('tag');
      if (tag === selectedTag || (!selectedTag && !tag)) tagLink.setAttribute('aria-current', 'true');
    }
  }

  const themeButton = document.getElementById('theme-toggle');
  const themeColor = document.querySelector('meta[name="theme-color"]');

  function updateThemeButton() {
    const dark = document.documentElement.dataset.theme === 'dark';
    const label = dark ? '切换至浅色模式' : '切换至深色模式';
    themeButton.setAttribute('aria-label', label);
    themeButton.title = label;
    themeColor.content = dark ? '#121418' : '#f8f9fa';
  }

  themeButton.hidden = false;
  updateThemeButton();
  themeButton.addEventListener('click', () => {
    const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem('lx-theme', next); } catch (_) { /* Storage may be disabled. */ }
    try { document.cookie = `lx-theme=${next}; Max-Age=31536000; Path=/; SameSite=Lax; Secure`; } catch (_) { /* Cookies may be disabled. */ }
    updateThemeButton();
  });

  const dialog = document.getElementById('site-search');
  const searchButton = document.getElementById('search-toggle');
  if (!dialog || typeof dialog.showModal !== 'function') return;

  const closeButton = dialog.querySelector('.search-close');
  const input = document.getElementById('search-query');
  const results = document.getElementById('search-results');
  const indexURL = new URL(dialog.dataset.searchIndex, document.baseURI);
  const siteRoot = new URL('../', indexURL);
  const loadIndex = createSearchLoader(indexURL.href);
  let searchVersion = 0;
  const status = document.getElementById('search-status');
  const empty = document.getElementById('search-empty');

  async function filterResults() {
    const version = ++searchVersion;
    status.textContent = '加载搜索内容中…';
    empty.hidden = true;
    try {
      const items = await loadIndex();
      if (version !== searchVersion) return;
      const matches = matchingSearchItems(items, input.value);
      renderSearchResults(results, matches, siteRoot);
      status.textContent = input.value.trim() ? `找到 ${matches.length} 条结果` : '全部内容';
      empty.hidden = matches.length !== 0;
    } catch (_) {
      if (version !== searchVersion) return;
      results.replaceChildren();
      status.textContent = '搜索加载失败，请检查网络后重新打开搜索或输入关键词重试。';
    }
  }

  function openSearch() {
    if (!dialog.open) dialog.showModal();
    input.focus();
    filterResults();
  }

  searchButton.hidden = false;
  searchButton.addEventListener('click', openSearch);
  closeButton.addEventListener('click', () => dialog.close());
  input.addEventListener('input', filterResults);
  document.addEventListener('keydown', event => {
    const target = event.target;
    const typing = target instanceof HTMLElement && (
      target.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName)
    );
    if (event.key === '/' && !typing && !event.metaKey && !event.ctrlKey && !event.altKey) {
      event.preventDefault();
      openSearch();
    }
  });
})();
