const assert = require('node:assert/strict');
const { canLoadComments, commentStatus } = require('../dist/assets/comments.js');

assert.equal(canLoadComments('leyang-xia.github.io', 'https://comments.example.net'), true);
assert.equal(canLoadComments('leyang-xia-notes.spicycurrykk.chatgpt.site', 'https://comments.example.net'), false);
assert.equal(canLoadComments('', 'https://comments.example.net'), false);
assert.equal(canLoadComments('leyang-xia.github.io', ''), false);
assert.equal(commentStatus('preview'), '预览站不开放留言；请前往正式站点。');
assert.equal(commentStatus('error'), '评论暂不可用，请稍后再试。');
console.log('Comment client checks passed');
