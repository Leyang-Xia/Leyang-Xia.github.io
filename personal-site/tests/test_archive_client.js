const assert = require('node:assert/strict');
const { visibleForTag } = require('../dist/assets/site.js');

assert.equal(visibleForTag(['随笔'], '随笔', ['随笔', '实时音频']), true);
assert.equal(visibleForTag(['实时音频'], '随笔', ['随笔', '实时音频']), false);
assert.equal(visibleForTag(['实时音频'], '不存在', ['随笔', '实时音频']), true);
assert.equal(visibleForTag(['实时音频'], null, ['随笔', '实时音频']), true);
console.log('Archive filter checks passed');
