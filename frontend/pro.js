async function fetchJSON(url, opts={}){
  const key = document.getElementById('apiKey')?.value?.trim();
  const headers = Object.assign({}, opts.headers||{});
  if(key) headers['X-Api-Key'] = key;
  const r = await fetch(url, Object.assign({}, opts, { headers }));
  const t = await r.text(); let j; try{ j = JSON.parse(t) }catch{ j = {raw:t} }
  return { ok:r.ok, status:r.status, json:j, text:t };
}

function setText(id, val){ const el = document.getElementById(id); if(el) el.textContent = (val ?? '—'); }
function pick(v, def='—'){ return (v===undefined||v===null||v==='')?def:v; }
function setStatus(s){ const el = document.getElementById('status'); if(el) el.textContent = s; }

// ---------- Actions ----------
async function createMatter(){
  const council = document.getElementById('council').value.trim();
  console.log('Council value:', council);
  const body = { council };
  console.log('Sending to /api/matters:', body);
  const {ok, json} = await fetchJSON('/api/matters', { method:'POST', headers:{'content-type':'application/json'}, body: JSON.stringify(body) });
  console.log('Create matter response:', {ok, json});
  if(!ok){ setStatus('Create matter failed'); return null; }
  return json?.matter?.id;
}

async function setProperty(mid){
  const payload = {
    uprn: document.getElementById('uprn').value.trim(),
    title_no: document.getElementById('titleNo').value.trim(),
    address_text: document.getElementById('addr').value.trim(),
    postcode: document.getElementById('pc').value.trim()
  };
  await fetchJSON(`/la/matters/${mid}/property`, { method:'POST', headers:{'content-type':'application/json'}, body: JSON.stringify(payload) });
}

async function uploadFiles(mid){
  const files = document.getElementById('files').files;
  if(!files.length) return {count:0};
  let uploaded=0;
  for(const f of files){
    const fd = new FormData(); fd.append('file', f, f.name);
    const res = await fetchJSON(`/api/matters/${mid}/upload?kind=search&async_ocr=0`, { method:'POST', body:fd });
    if(res.ok) uploaded++;
  }
  return {count:uploaded};
}

async function scanRisks(mid){
  const files = document.getElementById('files').files;
  if(!files.length) return;
  // risk-scan endpoint requires a multipart PDF – send the last file
  const file = files[files.length-1];
  const fd = new FormData(); fd.append('file', file, file.name);
  await fetchJSON(`/api/matters/${mid}/risk-scan`, { method:'POST', body: fd });
}

async function loadSummary(mid){
  const res = await fetchJSON(`/la/matters/${mid}/summary`);
  const json = res.json || {};
  // top
  setText('sumFilename', pick(json?.filename));
  setText('sumCouncil', pick(json?.council));
  setText('sumAddr', pick(json?.property?.address_text));
  setText('sumPc', pick(json?.property?.postcode));
  // risk (fallback to simple heuristic)
  const risks = json?.risks || [];
  const score = json?.risk_score ?? (risks.length ? Math.min(1, risks.length * 0.25) : 0);
  const label = score===0 ? 'Low' : score<0.5 ? 'Low/Med' : score<0.8 ? 'Medium' : 'High';
  document.getElementById('sumRisk').innerHTML = `${label} <span class="pill">score ${Number(score).toFixed(2)}</span>`;

  const llc1 = json.llc1 || {};
  setText('llcListed', pick(llc1.LISTED_BUILDING));
  setText('llcGrade', pick(llc1.GRADE));
  setText('llcCons', pick(llc1.CONSERVATION_AREA));
  setText('llcTpo', pick(llc1.TREE_PRESERVATION_ORDER));
  setText('llcS106', pick(llc1.FINANCIAL_CHARGES || llc1.SECTION_106));
  setText('llcCil', pick(llc1.CIL));

  const c29 = json.con29 || {};
  setText('c29Road', pick(c29.ROAD_STATUS));
  setText('c29Plan', pick(c29.PLANNING_REFS_STRICT));
  setText('c29Enf', pick(c29.ENFORCEMENT_NOTICES));
  setText('c29Sewer', pick(c29.DRAINAGE_WITHIN_3M));
  setText('c29Boa', pick(c29.BUILD_OVER_AGREEMENT));
  setText('c29Landfill', pick(c29.LANDFILL_WITHIN_250M));
}

async function loadRecent(){
  const tbody = document.querySelector('#recentTbl tbody');
  if(!tbody) return;
  // Prefer /la/matters/list if present
  let rows = [];
  let res = await fetchJSON('/la/matters/list');
  if(res.ok && Array.isArray(res.json?.matters)){
    rows = res.json.matters.map(m=>{
      const when = m.created_at || m.createdAt || '';
      const risk = (m.risk_score!=null? m.risk_score : (m.risks?.length||0)).toString();
      return { id:m.id, filename:(m.filename||m.ref||''), council:(m.council||''), risk, when };
    });
  } else {
    // fallback: /api/searches.csv (very simple parse)
    const csv = (await (await fetch('/api/searches.csv')).text()).trim().split(/\r?\n/).slice(1);
    rows = csv.map(line=>{
      const [id, file, council, risk, when] = line.split(',');
      return {id, filename:file, council, risk, when};
    });
  }
  tbody.innerHTML = rows.slice(0,50).map(r=>(
    `<tr><td>${r.id||''}</td><td>${r.filename||''}</td><td>${r.council||''}</td><td>${r.risk||''}</td><td>${r.when||''}</td></tr>`
  )).join('') || `<tr><td colspan="5" class="muted">No items</td></tr>`;
}

// ---------- Wiring ----------
console.log('pro.js loaded successfully!');
document.getElementById('processBtn').addEventListener('click', async ()=>{
  console.log('Process button clicked!');
  setStatus('Creating matter…');
  console.log('About to create matter...');
  const mid = await createMatter(); 
  console.log('Matter created with ID:', mid);
  if(!mid){ setStatus('Failed to create matter'); return; }
  setStatus(`Matter ${mid} created. Saving property…`);
  await setProperty(mid);
  setStatus('Uploading files…');
  console.log('About to upload files...');
  const up = await uploadFiles(mid);
  console.log('Upload result:', up);
  setStatus(`Uploaded ${up.count} file(s). Loading summary…`);
  await loadSummary(mid);
  await loadRecent();
});

document.getElementById('scanBtn').addEventListener('click', async ()=>{
  setStatus('Scanning risks…');
  // naive: ask backend for most recent matter (from list)
  let mid = null;
  const res = await fetchJSON('/la/matters/list');
  const arr = res?.json?.matters || [];
  if(arr.length) mid = arr[arr.length-1].id; // last created
  if(!mid){ setStatus('No matter to scan'); return; }
  await scanRisks(mid);
  setStatus('Scan complete.');
  await loadSummary(mid);
  await loadRecent();
});

document.getElementById('refreshBtn').addEventListener('click', async ()=>{
  await loadRecent();
  // try get last matter for summary
  const res = await fetchJSON('/la/matters/list');
  const arr = res?.json?.matters || [];
  if(arr.length){ await loadSummary(arr[arr.length-1].id); }
});

// Initial load
loadRecent().catch(()=>{});
