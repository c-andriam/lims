/* Migration des preferences natives sans perte des colonnes masquees.
 * node tests/test_dashboard_column_migration.js
 */
"use strict";
var assert = require("assert");
var fs = require("fs");
var path = require("path");
var vm = require("vm");
var source = fs.readFileSync(path.join(__dirname, "../browser/resources/dashboard.js"), "utf8");
var desired = ["SampleCode", "Lot", "Client", "SampleType", "Origin", "ReceptionWeight",
    "DateReceived", "AnalysisStart", "AnalysisEnd", "DateVerified", "Vanillin", "GlucoVanillin",
    "VanillicAcid", "PHB", "PHBAcid", "HPLCOperator", "Moisture", "MoistureOperator",
    "WaterActivity", "WaterActivityOperator"];
var operators = ["HPLCOperator", "MoistureOperator", "WaterActivityOperator"];
var legacy = desired.filter(function (key) { return operators.indexOf(key) < 0; }).concat(operators);
var storageKey = "columns-AnalysisRequest-DashboardView";

function execute(saved, rootPresent) {
    var values = {};
    values[storageKey] = saved;
    values["columns-other-view"] = "other preferences";
    var root = {getAttribute: function (name) {
        if (name === "data-listing_identifier") { return "AnalysisRequest-DashboardView"; }
        return JSON.stringify(Object.fromEntries(desired.map(function (key) { return [key, {}]; })));
    }};
    vm.runInNewContext(source, {
        window: {TRIMETA_DASHBOARD: {}, console: {debug: function () {}}, localStorage: {
            getItem: function (key) { return values[key] || null; },
            setItem: function (key, value) { values[key] = value; }
        }},
        document: {readyState: "complete", getElementById: function () { return null; },
            querySelector: function () { return rootPresent === false ? null : root; },
            querySelectorAll: function () { return []; }}
    });
    assert.strictEqual(values["columns-other-view"], "other preferences");
    return values[storageKey];
}

var entries = legacy.map(function (key) { return {key: key, toggle: key !== "Origin", extra: key}; });
var migrated = JSON.parse(execute(JSON.stringify(entries)));
assert.deepStrictEqual(migrated.map(function (entry) { return entry.key; }), desired);
assert.strictEqual(migrated.find(function (entry) { return entry.key === "Origin"; }).toggle, false);
assert.strictEqual(migrated.find(function (entry) { return entry.key === "Origin"; }).extra, "Origin");
assert.strictEqual(execute(JSON.stringify(migrated)), JSON.stringify(migrated));
var custom = JSON.stringify(entries.slice().reverse());
assert.strictEqual(execute(custom), custom);
assert.strictEqual(execute("invalid JSON"), "invalid JSON");
assert.strictEqual(execute(JSON.stringify(entries), false), JSON.stringify(entries));
process.stdout.write("5 controles de migration des colonnes passent\n");
