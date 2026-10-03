'use strict';
const assert = require('assert');
const normalize = require('../addons/senaite.trimeta.samplefields/senaite/trimeta/samplefields/browser/resources/numeric_fields.js');
[['12,5','12.5'], ['-12,5','-12.5'], ['+12,5','+12.5'],
 ['1,25e-3','1.25e-3'], ['0,00','0.00'], ['12.5','12.5'],
 ['1,234.5','1,234.5'], ['1,2,3','1,2,3']].forEach(([input, expected]) => {
  assert.strictEqual(normalize(input), expected);
});
console.log('8 controles de conversion decimale passes');
