'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const { parseCsv, analyze, resultCsv } = require('../web/app.js');

const sample = 'cell_id,cell_type,x,y\n1,T,0,0\n2,M,3,4\n3,T,6,8\n4,F,100,100\n';

test('paired cells at inclusive boundary counted once', () => {
  const result = analyze(parseCsv(sample), 5);
  assert.equal(result.n_cells, 4);
  assert.equal(result.n_pairs, 2);
  assert.deepEqual(result.pair_counts, [
    {type_a: 'M', type_b: 'T', contacts: 2, mean_distance: 5}
  ]);
});
test('same type and negative coordinate bins', () => {
  const rows = parseCsv('cell_id,cell_type,x,y\n1,T,-1,-1\n2,T,-1,-1\n3,M,10,10\n');
  const result = analyze(rows, 1);
  assert.equal(result.n_pairs, 1);
  assert.equal(result.pair_counts[0].mean_distance, 0);
});
test('quoted fields and UTF-8 BOM', () => {
  const rows = parseCsv('\uFEFFcell_id,cell_type,x,y\n"1","T, memory",0,0\n"2","T, memory",0,1\n');
  assert.equal(rows[0].cell_type, 'T, memory');
  assert.equal(analyze(rows, 1).n_pairs, 1);
});
test('invalid coordinates, identifiers and radius rejected', () => {
  for (const s of ['cell_id,cell_type,x,y\n1,T,NaN,0\n',
    'cell_id,cell_type,x,y\n1,T,0,0\n1,M,0,0\n',
    'cell_id,cell_type,x,y\n1,T,,0\n']) {
    assert.throws(() => analyze(parseCsv(s), 5));
  }
  for (const radius of [0, -1, Infinity, NaN]) {
    assert.throws(() => analyze(parseCsv(sample), radius));
  }
});
test('CSV formula injection neutralized on export', () => {
  const rows = parseCsv('cell_id,cell_type,x,y\n1,=1+1,0,0\n2,M,1,0\n');
  const result = resultCsv(analyze(rows, 2));
  assert.ok(result.includes('"\'=1+1"'));
});
test('empty, unterminated, and invalid header CSV rejected', () => {
  assert.throws(() => parseCsv(''));
  assert.throws(() => parseCsv('cell_id,cell_type,x,y\n"1,T,0,0'));
  assert.throws(() => parseCsv('cell_id,cell_type,x\n1,T,0'));
});
test('cell cap enforced', () => {
  assert.throws(() => analyze(parseCsv(sample), 5, 1), /limit/);
});
