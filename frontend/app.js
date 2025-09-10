async function fetchJSON(url, opts = {}) {
  const r = await fetch(url, opts);
  const t = await r.text();
  try { return { ok: r.ok, json: JSON.parse(t) }; }
  catch { return { ok: r.ok, json: { raw: t } }; }
}

async function refreshTables(){
  const out = document.getElementById('tables');
  out.textContent = 'Loading…';
  const { json } = await fetchJSON('/api/list');
  out.textContent = JSON.stringify(json, null, 2);
}

async function uploadFile(){
  const out = document.getElementById('upload');
  const f = document.getElementById('file').files[0];
  if(!f){ out.textContent = 'Pick a file first.'; return; }
  const fd = new FormData();
  fd.append('file', f);
  const { json } = await fetchJSON('/api/process', { method:'POST', body: fd });
  out.textContent = JSON.stringify(json, null, 2);
}

document.getElementById('btn-refresh').addEventListener('click', refreshTables);
document.getElementById('btn-upload').addEventListener('click', uploadFile);
refreshTables();
