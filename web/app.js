/* Descriptive local-only spatial cell/spot proximity analysis. */
'use strict';

function parseCsv(source) {
  if (typeof source !== 'string' || !source.trim()) throw new Error('Provide a CSV file or paste CSV records.');
  const text = source.replace(/^\uFEFF/, '');
  const records = [];
  let record = [], field = '', quoted = false, closed = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (quoted) {
      if (ch === '"' && text[i + 1] === '"') { field += '"'; i++; }
      else if (ch === '"') { quoted = false; closed = true; }
      else { field += ch; }
    } else if (ch === '"') {
      if (field !== '' || closed) throw new Error('Invalid quoting in CSV.');
      quoted = true;
    } else if (ch === ',') {
      record.push(field); field = ''; closed = false;
    } else if (ch === '\n' || ch === '\r') {
      if (ch === '\r' && text[i + 1] === '\n') i++;
      record.push(field); field = ''; closed = false;
      if (record.some(v => v.trim() !== '')) records.push(record);
      record = [];
    } else {
      if (closed && ch !== ' ' && ch !== '\t') throw new Error('Unexpected characters after a quoted CSV field.');
      field += ch;
    }
  }
  if (quoted) throw new Error('Unterminated quoted CSV field.');
  record.push(field);
  if (record.some(v => v.trim() !== '')) records.push(record);
  if (records.length < 2) throw new Error('CSV must contain a header and at least one cell.');
  const header = records.shift().map(value => value.trim());
  const required = ['cell_id', 'cell_type', 'x', 'y'];
  if (new Set(header).size !== header.length || !required.every(key => header.includes(key))) {
    throw new Error('CSV must have distinct cell_id, cell_type, x and y columns.');
  }
  return records.map((values, index) => {
    if (values.length !== header.length) throw new Error('Row ' + (index + 2) + ': unexpected number of columns.');
    const row = {};
    header.forEach((key, i) => { row[key] = values[i].trim(); });
    return row;
  });
}

function analyze(rows, radius, limit = 3000) {
  const r = Number(radius);
  if (!Number.isFinite(r) || r <= 0) throw new Error('Radius must be a finite positive number.');
  if (!Array.isArray(rows) || !rows.length) throw new Error('No cells or spots to analyze.');
  if (rows.length > limit) throw new Error('Browser limit: ' + limit + ' cells/spots. Use the Python CLI for larger inputs.');
  const seen = new Set(), types = new Set(), grid = new Map(), counts = new Map(), cells = [];
  let totalPairs = 0;
  for (let i = 0; i < rows.length; i++) {
    const row = rows[i], cellId = String(row.cell_id ?? '').trim();
    const type = String(row.cell_type ?? '').trim();
    const rawX = String(row.x ?? '').trim(), rawY = String(row.y ?? '').trim();
    if (!cellId || !type || !rawX || !rawY) throw new Error('Row ' + (i + 2) + ': missing cell_id, cell_type or coordinate.');
    if (seen.has(cellId)) throw new Error('Row ' + (i + 2) + ': duplicate cell_id.');
    const x = Number(rawX), y = Number(rawY);
    if (!Number.isFinite(x) || !Number.isFinite(y)) throw new Error('Row ' + (i + 2) + ': coordinates must be finite numbers.');
    seen.add(cellId); types.add(type);
    const gx = Math.floor(x / r), gy = Math.floor(y / r);
    for (let dx = -1; dx <= 1; dx++) {
      for (let dy = -1; dy <= 1; dy++) {
        for (const other of grid.get((gx + dx) + ',' + (gy + dy)) || []) {
          const distance = Math.hypot(x - other.x, y - other.y);
          if (distance <= r) {
            const pair = [type, other.type].sort();
            const key = JSON.stringify(pair);
            const bucket = counts.get(key) || { type_a: pair[0], type_b: pair[1], contacts: 0, sum: 0 };
            bucket.contacts++;
            bucket.sum += distance;
            counts.set(key, bucket);
            totalPairs++;
          }
        }
      }
    }
    const key = gx + ',' + gy;
    const cell = { x, y, type };
    if (!grid.has(key)) grid.set(key, []);
    grid.get(key).push(cell); cells.push(cell);
  }
  const pairCounts = Array.from(counts.values())
    .map(({type_a, type_b, contacts, sum}) => ({ type_a, type_b, contacts, mean_distance: sum / contacts }))
    .sort((a, b) => a.type_a.localeCompare(b.type_a) || a.type_b.localeCompare(b.type_b));
  return {
    n_cells: cells.length, n_cell_types: types.size, n_pairs: totalPairs,
    radius: r, pair_counts: pairCounts, cells,
    method: 'Euclidean distance <= radius; unordered pairs counted once'
  };
}

function csvSafe(value) {
  const text = String(value);
  const neutralized = /^[=+\-@\t\r]/.test(text) ? "'" + text : text;
  return '"' + neutralized.replace(/"/g, '""') + '"';
}

function resultCsv(result) {
  return 'type_a,type_b,contacts,mean_distance\n' +
    result.pair_counts.map(p => [p.type_a, p.type_b, p.contacts, p.mean_distance.toFixed(6)].map(csvSafe).join(',')).join('\n') + '\n';
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { parseCsv, analyze, resultCsv };
}

if (typeof document !== 'undefined') {
  const byId = id => document.getElementById(id);
  const sample = 'cell_id,cell_type,x,y\nC001,T cell,0,0\nC002,Macrophage,3,4\nC003,T cell,6,8\nC004,Fibroblast,100,100\nC005,Macrophage,103,104\n';
  let lastResult = null;

  function message(text, error = false) {
    const node = byId('message');
    node.textContent = text; node.className = error ? 'message error' : 'message';
  }
  function plot(cells) {
    const canvas = byId('plot'), ctx = canvas.getContext('2d');
    const width = canvas.width, height = canvas.height, margin = 28;
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = '#111b2d'; ctx.fillRect(0, 0, width, height);
    const xs = cells.map(c => c.x), ys = cells.map(c => c.y);
    const minX = Math.min(...xs), maxX = Math.max(...xs);
    const minY = Math.min(...ys), maxY = Math.max(...ys);
    const spanX = Math.max(maxX - minX, 1e-9), spanY = Math.max(maxY - minY, 1e-9);
    const typeList = Array.from(new Set(cells.map(c => c.type))).sort();
    const colors = ['#60a5fa', '#fbbf24', '#34d399', '#f472b6', '#c4b5fd', '#fb923c', '#2dd4bf', '#f87171'];
    ctx.strokeStyle = '#475569'; ctx.strokeRect(margin, margin, width - 2 * margin, height - 2 * margin);
    cells.forEach(c => {
      const px = margin + ((c.x - minX) / spanX) * (width - 2 * margin);
      const py = height - margin - ((c.y - minY) / spanY) * (height - 2 * margin);
      ctx.fillStyle = colors[typeList.indexOf(c.type) % colors.length];
      ctx.beginPath(); ctx.arc(px, py, 4, 0, Math.PI * 2); ctx.fill();
    });
    const legend = byId('legend');
    legend.replaceChildren();
    typeList.forEach((type, i) => {
      const item = document.createElement('span');
      const swatch = document.createElement('i'); swatch.style.backgroundColor = colors[i % colors.length];
      item.append(swatch, document.createTextNode(type)); legend.append(item);
    });
  }

  function drawTable(result) {
    byId('n-cells').textContent = result.n_cells.toLocaleString();
    byId('n-types').textContent = result.n_cell_types.toLocaleString();
    byId('n-pairs').textContent = result.n_pairs.toLocaleString();
    const body = byId('pair-rows'); body.replaceChildren();
    if (!result.pair_counts.length) {
      const row = document.createElement('tr'), cell = document.createElement('td');
      cell.colSpan = 4; cell.textContent = 'No pairs within the chosen radius.';
      row.append(cell); body.append(row);
    } else {
      for (const pair of result.pair_counts) {
        const tr = document.createElement('tr');
        for (const value of [pair.type_a, pair.type_b, pair.contacts, pair.mean_distance.toFixed(3)]) {
          const td = document.createElement('td'); td.textContent = value; tr.append(td);
        }
        body.append(tr);
      }
    }
    plot(result.cells);
    byId('results').hidden = false;
    byId('download').disabled = false;
  }

  byId('sample').addEventListener('click', () => {
    byId('csv').value = sample; message('Example loaded. Select Analyze to calculate proximity.');
  });
  byId('file').addEventListener('change', async event => {
    const file = event.target.files?.[0];
    if (!file) return;
    if (file.size > 2 * 1024 * 1024) { message('CSV file must be smaller than 2 MB.', true); return; }
    try { byId('csv').value = await file.text(); message('CSV loaded locally: ' + file.name); }
    catch (error) { message('Unable to read selected file: ' + error.message, true); }
  });
  byId('analyze').addEventListener('click', () => {
    lastResult = null; byId('download').disabled = true;
    byId('results').hidden = true;
    try {
      const rows = parseCsv(byId('csv').value);
      const result = analyze(rows, byId('radius').value);
      lastResult = result; drawTable(result);
      message('Analysis completed locally. No files or coordinates were uploaded.');
    } catch (error) { message(error.message, true); }
  });
  byId('download').addEventListener('click', () => {
    if (!lastResult) return;
    const blob = new Blob([resultCsv(lastResult)], {type: 'text/csv;charset=utf-8'});
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a'); link.href = url; link.download = 'cell_proximity_pairs.csv';
    document.body.append(link); link.click(); link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  byId('csv').value = sample;
}
