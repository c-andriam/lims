"use strict";
const assert = require("assert");
const migrate = require("../browser/resources/analyst_columns.js");
function store(value) {
  return {value: value, writes: 0,
    getItem: function () { return this.value; },
    setItem: function (key, data) { this.value = data; this.writes += 1; }};
}
const saved = [{key: "Result", toggle: true}, {key: "Method", toggle: false, custom: 4}];
const existing = store(JSON.stringify(saved));
assert.strictEqual(migrate(existing, "columns-test"), true);
assert.deepStrictEqual(JSON.parse(existing.value), saved.concat([{key: "AssignedLabAnalyst", toggle: true}]));
assert.strictEqual(migrate(existing, "columns-test"), false);
assert.strictEqual(existing.writes, 1);
const hidden = store(JSON.stringify([{key: "AssignedLabAnalyst", toggle: false}]));
assert.strictEqual(migrate(hidden, "columns-test"), false);
assert.strictEqual(hidden.writes, 0);
for (const value of [null, "[]", "{}", "invalid", "[null]", '[{"name":"Result"}]']) {
  const bad = store(value);
  assert.strictEqual(migrate(bad, "columns-test"), false);
  assert.strictEqual(bad.writes, 0);
}
assert.strictEqual(migrate({getItem: function () { throw Error("denied"); }}, "columns-test"), false);
console.log("Worksheet column preferences: migration, preservation, idempotence and invalid storage OK");
