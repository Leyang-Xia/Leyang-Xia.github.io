(function () {
  function canLoadComments(hostname, envId) {
    return hostname === 'leyang-xia.github.io' && Boolean(envId);
  }

  function commentStatus(state) {
    if (state === 'preview') return '预览站不开放留言；请前往正式站点。';
    if (state === 'loading') return '正在加载留言…';
    return '评论暂不可用，请稍后再试。';
  }

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { canLoadComments, commentStatus };
  }
  if (typeof document === 'undefined') return;

  const shell = document.getElementById('comments');
  if (!shell) return;
  if (location.hostname !== 'leyang-xia.github.io') {
    shell.textContent = commentStatus('preview');
    return;
  }
  const envId = shell.dataset.envId;
  if (!canLoadComments(location.hostname, envId)) {
    shell.textContent = commentStatus('error');
    return;
  }

  const threadPath = shell.dataset.threadPath;
  shell.textContent = commentStatus('loading');
  const target = document.createElement('div');
  target.id = 'tcomment';
  shell.appendChild(target);
  const script = document.createElement('script');
  script.src = 'https://cdn.jsdelivr.net/npm/twikoo@2.0.9/dist/twikoo.min.js';
  script.async = true;
  script.onerror = () => { shell.textContent = commentStatus('error'); };
  script.onload = () => {
    try {
      if (!window.twikoo || typeof window.twikoo.init !== 'function') throw new Error('Twikoo unavailable');
      shell.firstChild.remove();
      Promise.resolve(window.twikoo.init({ envId, el: '#tcomment', path: threadPath, lang: 'zh-CN' }))
        .catch(() => { shell.textContent = commentStatus('error'); });
    } catch (_) {
      shell.textContent = commentStatus('error');
    }
  };
  document.head.appendChild(script);
})();
