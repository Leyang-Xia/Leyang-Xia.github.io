(() => {
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
  const items = Array.from(dialog.querySelectorAll('.search-item'));
  const status = document.getElementById('search-status');
  const empty = document.getElementById('search-empty');

  function filterResults() {
    const terms = input.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
    let count = 0;
    for (const item of items) {
      const match = terms.every(term => item.dataset.search.includes(term));
      item.hidden = !match;
      if (match) count++;
    }
    status.textContent = terms.length ? `找到 ${count} 条结果` : '全部内容';
    empty.hidden = count !== 0;
  }

  function openSearch() {
    if (!dialog.open) dialog.showModal();
    input.focus();
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
