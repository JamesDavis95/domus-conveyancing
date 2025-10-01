// --- Planning AI Analysis Handlers ---
async function runPlanningAIAnalysis() {
  const statusDiv = document.getElementById('planning-ai-analysis-status');
  statusDiv.innerHTML = `<span style=\"color:var(--primary);\">Running AI analysis...</span>`;
  // Example site data; in production, collect from UI or context
  const site_data = {
    address: '123 Example St',
    postcode: 'EX1 2PL',
    council: 'Example Council',
    // ...add more fields as needed
  };
  try {
    const {json, ok} = await fetchJSON('/planning-ai/analyze', {
      method: 'POST',
      headers: {'content-type':'application/json'},
      body: JSON.stringify(site_data)
    });
    if (!ok || json.error) {
      statusDiv.innerHTML = `<span style='color:var(--danger);'>Error: ${json.error || 'Failed to run analysis.'}</span>`;
      return;
    }
    statusDiv.innerHTML = `<pre style='max-height:300px;overflow:auto;background:var(--panel);padding:12px;'>${JSON.stringify(json,null,2)}</pre>`;
  } catch (e) {
    statusDiv.innerHTML = `<span style='color:var(--danger);'>Error: ${e.message||e}</span>`;
  }
}

document.addEventListener('DOMContentLoaded', function() {
  const aiBtn = document.getElementById('run-planning-ai-analysis-btn');
  if(aiBtn) aiBtn.onclick = runPlanningAIAnalysis;
  // Optionally, wire up the other two buttons to show specific parts of the analysis result
});
// --- Document Generation Handlers ---
async function generateDocument(documentType) {
  const statusDiv = document.getElementById('doc-generation-status');
  statusDiv.innerHTML = `<span style="color:var(--primary);">Generating <b>${documentType.replace('_',' ')}</b>...</span>`;
  // Example site data; in production, collect from UI or context
  const site_data = {
    address: '123 Example St',
    postcode: 'EX1 2PL',
    council: 'Example Council',
    // ...add more fields as needed
  };
  try {
    const {json, ok} = await fetchJSON('/api/auto-docs/generate', {
      method: 'POST',
      headers: {'content-type':'application/json'},
      body: JSON.stringify({
        document_type: documentType,
        site_data: site_data,
        output_format: 'html'
      })
    });
    if (!ok || json.error) {
      statusDiv.innerHTML = `<span style='color:var(--danger);'>Error: ${json.error || 'Failed to generate document.'}</span>`;
      return;
    }
    // Show result (for now, just show JSON; can render HTML if available)
    if(json.html) {
      statusDiv.innerHTML = `<div style='border:1px solid var(--primary);padding:16px;margin:8px 0;'>${json.html}</div>`;
    } else {
      statusDiv.innerHTML = `<pre style='max-height:300px;overflow:auto;background:var(--panel);padding:12px;'>${JSON.stringify(json,null,2)}</pre>`;
    }
  } catch (e) {
    statusDiv.innerHTML = `<span style='color:var(--danger);'>Error: ${e.message||e}</span>`;
  }
}

document.addEventListener('DOMContentLoaded', function() {
  const planBtn = document.getElementById('generate-planning-statement-btn');
  if(planBtn) planBtn.onclick = ()=>generateDocument('planning_statement');
  const daBtn = document.getElementById('generate-da-statement-btn');
  if(daBtn) daBtn.onclick = ()=>generateDocument('design_access_statement');
});
async function fetchJSON(url, opts={}){
  const key = document.getElementById('api-key')?.value?.trim();
  const headers = Object.assign({}, opts.headers||{});
  if(key) headers['X-Api-Key']=key;
  const r = await fetch(url, Object.assign({}, opts, { headers }));
  const t = await r.text(); let j; try{j=JSON.parse(t)}catch{j={raw:t}};
  return {ok:r.ok,status:r.status,json:j};
}
function set(id, val){ document.getElementById(id).textContent = (typeof val==='string')? val : JSON.stringify(val,null,2); }
function setText(id, text){ document.getElementById(id).textContent = text; }

async function createOrg(){
  const {json}=await fetchJSON('/api/orgs',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({name:'Demo '+Date.now()})});
  if(json?.org?.api_key){ document.getElementById('api-key').value = json.org.api_key; document.getElementById('org-out').textContent='Org created'; }
}
async function createMatter(){
  const council=document.getElementById('council').value.trim();
  const uprn=document.getElementById('uprn').value.trim();
  const title_no=document.getElementById('title_no').value.trim();
  const address=document.getElementById('address').value.trim();
  const postcode=document.getElementById('postcode').value.trim();
  const payload = { council: council||undefined, property: { uprn, title_no, address_text: address, postcode } };
  const {json}=await fetchJSON('/api/matters',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(payload)});
  if(json?.matter?.id){ document.getElementById('matter-id').value = json.matter.id; await getMatter(); await loadMetrics(); }
}
async function getMatter(){
  const mid=document.getElementById('matter-id').value.trim();
  if(!mid) return;
  const {json}=await fetchJSON('/api/matters/'+mid);
  set('matter', json);
  setExportLinks(mid, json);
  await loadEnquiries();
}
function setExportLinks(mid, data){
  const base = `/la/matters/${mid}`;
  document.getElementById('dl-report').onclick = ()=> window.open(`${base}/report.docx`, '_blank');
  document.getElementById('dl-llc1').onclick   = ()=> window.open(`${base}/llc1.docx`, '_blank');
  document.getElementById('dl-bundle').onclick = ()=> window.open(`${base}/bundle.zip`, '_blank');
}
async function approve(){
  const mid=document.getElementById('matter-id').value.trim();
  if(!mid) return;
  const {json}=await fetchJSON('/la/matters/'+mid+'/approve');
  setText('status', 'Approved');
  await getMatter();
  await loadMetrics();
}
async function uploadPDF(){
  const mid=document.getElementById('matter-id').value.trim();
  const f=document.getElementById('file').files[0];
  const asyncOCR = document.getElementById('async-ocr').checked;
  if(!mid||!f) return;
  const fd=new FormData(); fd.append('file', f);
  const res=await fetchJSON(`/api/matters/${mid}/upload?kind=search&async_ocr=${asyncOCR?'1':'0'}`,{method:'POST',body:fd});
  set('upload-out', res.json);
  if(res?.json?.job_id){
    const statusEl = document.getElementById('scan-status');
    setText('scan-status','OCR queued…'); statusEl.classList.add('spinner');
    await pollJob(res.json.job_id, async (final)=>{
      statusEl.classList.remove('spinner'); setText('scan-status','OCR done');
      await getMatter();
    }, async (err)=>{
      statusEl.classList.remove('spinner'); setText('scan-status','OCR failed');
    });
  } else {
    await getMatter();
  }
}
async function scanRisks(){
  const mid=document.getElementById('matter-id').value.trim();
  const statusEl = document.getElementById('scan-status');
  if(!mid){ setText('scan-status','No matter selected'); return; }

  // latest doc
  const m = await fetchJSON('/api/matters/'+mid);
  const docs = m?.json?.matter?.documents || m?.json?.spine?.docs || [];
  if(!docs.length){ setText('scan-status','No docs to scan'); return; }
  const docId = docs[docs.length-1].id;

  setText('scan-status','Queued…'); statusEl.classList.add('spinner');
  const res = await fetchJSON('/api/matters/'+mid+'/risk-scan-async',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({doc_id:docId})});

  const jobId = res?.json?.job_id;
  if(jobId && String(jobId).trim()){
    await pollJob(jobId, async (final)=>{
      set('upload-out', final);
      statusEl.classList.remove('spinner'); setText('scan-status','Done');
      await getMatter(); await loadEnquiries(); await loadMetrics();
    }, async (err)=>{
      statusEl.classList.remove('spinner'); setText('scan-status','Failed');
      set('upload-out', err || {error:true});
    });
  } else {
    statusEl.classList.remove('spinner'); setText('scan-status','Done (sync)');
    set('upload-out', res.json);
    await getMatter(); await loadEnquiries(); await loadMetrics();
  }
}

async function pollJob(jobId, onDone, onFail){
  const maxAttempts = 60;
  let attempts = 0;
  while(attempts < maxAttempts){
    attempts++;
    const st = await fetchJSON('/api/jobs/'+jobId+'/status');
    if(!st.ok){ await sleep(1500); continue; }
    const js = st.json || {};
    if(js.status === 'finished'){
      return onDone ? onDone(js.result || js) : null;
    }
    if(js.status === 'failed'){
      return onFail ? onFail(js.error || js) : null;
    }
    await sleep(1500);
  }
  return onFail ? onFail({timeout:true}) : null;
}
function sleep(ms){ return new Promise(res=>setTimeout(res, ms)); }

async function loadEnquiries(){
  const mid=document.getElementById('matter-id').value.trim();
  if(!mid) return;
  const {json}=await fetchJSON('/api/matters/'+mid+'/enquiries');
  const el=document.getElementById('enquiries');
  const items=json?.items||[];
  document.getElementById('enq-count').textContent = items.length;
  if(items.length===0){ el.textContent='No enquiries.'; return; }
  el.innerHTML = `<table><thead><tr><th>ID</th><th>Risk</th><th>Status</th><th>Draft</th><th>Actions</th></tr></thead><tbody>${
    items.map(e=>`<tr><td>${e.id}</td><td>${e.risk_id??''}</td><td>${e.status}</td><td><pre>${(e.draft_text||'').replace(/</g,'&lt;')}</pre></td><td><button data-promote="${e.id}" data-to="ready">Mark Ready</button> <button data-promote="${e.id}" data-to="sent">Mark Sent</button></td></tr>`).join('')
  }</tbody></table>`;
  el.querySelectorAll('button[data-promote]').forEach(btn=>{
    btn.addEventListener('click', async ()=>{
      const id=btn.getAttribute('data-promote'); const to=btn.getAttribute('data-to');
      await fetchJSON('/api/enquiries/'+id+'/promote',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({status:to})});
      await loadEnquiries();
    });
  });
}
async function loadMetrics(){
  const {json}=await fetchJSON('/la/metrics/summary');
  set('metrics', json);
  const tbody = document.querySelector('#metrics-table tbody');
  tbody.innerHTML = '';
  const t = json?.totals || {}; const sla = json?.sla || {};
  const tr = document.createElement('tr');
  tr.innerHTML = `<td>${t.matters ?? 0}</td><td>${t.approved ?? 0}</td><td>${sla.avg_seconds_received_to_approved ?? 0}</td><td>${sla.p50_seconds ?? 0}</td><td>${sla.p90_seconds ?? 0}</td>`;
  tbody.appendChild(tr);
}

document.getElementById('new-org').addEventListener('click', createOrg);
document.getElementById('new-matter').addEventListener('click', createMatter);
document.getElementById('get-matter').addEventListener('click', getMatter);
document.getElementById('approve').addEventListener('click', approve);
document.getElementById('passport').addEventListener('click', async ()=>{
  const mid=document.getElementById('matter-id').value.trim();
  if(!mid) return;
  const {json}=await fetchJSON('/api/passport/'+mid);
  set('matter', json);
  setExportLinks(mid, json);
});
document.getElementById('upload').addEventListener('click', uploadPDF);
document.getElementById('scan').addEventListener('click', scanRisks);

// Export buttons disabled until a matter is loaded
['dl-report','dl-llc1','dl-bundle'].forEach(id=>{
  document.getElementById(id).addEventListener('click', e=>{
    const mid=document.getElementById('matter-id').value.trim();
    if(!mid){ e.preventDefault(); alert('Select a matter first'); }
  });
});

// Initial metrics
loadMetrics().catch(()=>{});
