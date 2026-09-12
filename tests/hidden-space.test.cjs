const assert = require('node:assert/strict');
const { test } = require('node:test');
let policy;
try { policy = require('../hidden-space.uc.js'); } catch (error) {
  if (error.code !== 'MODULE_NOT_FOUND') throw error;
}
const spaces = [{ uuid: 'home' }, { uuid: 'work' }, { uuid: 'other' }];
test('hidden selections preserve a visible fallback and never modify synced spaces', () => {
  assert.ok(policy, 'Hidden Space policy is implemented');
  const before = JSON.stringify(spaces);
  assert.deepEqual(policy.visibleSpaces(spaces, ' work, missing, work '), [spaces[0], spaces[2]]);
  assert.deepEqual(policy.visibleSpaces(spaces, 'home,work,other'), [spaces[0]]);
  assert.deepEqual(policy.visibleSpaces(spaces, 'work', true), spaces);
  assert.deepEqual(policy.visibleSpaces([], 'work'), []);
  assert.equal(JSON.stringify(spaces), before);
});
test('navigation skips hidden spaces in both directions and respects wrapping', () => {
  assert.ok(policy, 'Hidden Space policy is implemented');
  const visible = [spaces[0], spaces[2]];
  assert.equal(policy.nextSpace(visible, 'home', 1, true), spaces[2]);
  assert.equal(policy.nextSpace(visible, 'home', -1, true), spaces[2]);
  assert.equal(policy.nextSpace(visible, 'home', -1, false), spaces[0]);
  assert.equal(policy.nextSpace(visible, 'other', 1, false), spaces[2]);
  assert.equal(policy.nextSpace(visible, 'work', 1, true), spaces[0]);
  assert.equal(policy.nextSpace([], 'work', 1, true), undefined);
});
