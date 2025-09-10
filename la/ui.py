from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

HTML = r"""<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>Local Authority – Matters</title>
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial; margin:20px; }
    .row { display:flex; gap:16px; }
    .col { flex:1; border:1px solid #ddd; border-radius:8px; padding:12px; }
    .links a, .links button { margin-right:8px; }
    textarea { width:100%; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
    .pill { display:inline-block; padding:2px 8px; border-radius:999px; border:1px solid #999; margin:2px 4px 0 0; font-size:12px;}
    .risk-high { background:#ffe5e5; border-color:#e00; }
    .risk-medium { background:#fff3cd; border-color:#e6a400; }
  </style>
</head>
<body>
  <h2>Matters</h2>
  <div class="row">
    <div class="col" style="flex:0 0 320px;">
      <div class="links">
        <button onclick="reloadMatters()">Reload</button>
        <button onclick="createMatter()">New Matter</button>
      </div>

      <div style="margin:10px 0;">
        <textarea id="llc1Text" rows="4" placeholder="Paste LLC1 text here..."></textarea>
        <textarea id="con29Text" rows="6" style="margin-top:6px" placeholder="Paste CON29 text here..."></textarea>
        <button onclick="ingestText()">Ingest Text</button>
      </div>
      <div id="drop" style="border:1px dashed #aaa;padding:10px;border-radius:8px;margin-top:6px">Drag & drop LLC1/CON29 PDFs here</div>
      <ul id="list"></ul>
    </div>

    <div class="col">
      <div class="links">
        <button onclick="loadDetail()">Refresh Detail</button>
        <a id="dl_report" href="#" target="_blank">Download DOCX Report</a>
        <a id="dl_json" href="#" target="_blank">Download JSON Export</a>
      </div>
      <div id="detail"></div>
    </div>
  </div>

  <script>
    let current = null;

    async function api(path, opts={}) {
      const res = await fetch(path, opts);
      if(!res.ok) throw new Error(await res.text());
      return res.json();
    }

    async function reloadMatters() {
      const data = await api('/la/matters/list');
      const ul = document.getElementById('list');
      ul.innerHTML = '';
      (data.matters || []).forEach(m => {
        const li = document.createElement('li');
        const a = document.createElement('a');
        a.href = '#';
        a.textContent = `${m.ref} – ${m.created_at}`;
        a.onclick = () => select(m);
        li.appendChild(a);
        ul.appendChild(li);
      });
    }

    function select(m) {
      current = m;
      document.getElementById('dl_report').href = `/la/matters/${m.id}/report.docx`;
      document.getElementById('dl_json').href = `/la/matters/${m.id}/export.json`;
      loadDetail();
    }

    async function loadDetail() {
      if(!current) return;
      const data = await api(`/la/matters/${current.id}/detail`);
      const d = document.getElementById('detail');
      const risks = (data.risks || []).map(r => {
        const cls = r.level === 'HIGH' ? 'risk-high' : (r.level === 'MEDIUM' ? 'risk-medium' : '');
        return `<span class="pill ${cls}">${r.level}: ${r.code}</span>`;
      }).join(' ');
      const findings = (data.findings || []).map(f => `<li><code>${f.kind}</code> – ${f.value || ''}</li>`).join('');
      d.innerHTML = `
        <h3>${current.ref}</h3>
        <div>${risks || '<em>No risks yet.</em>'}</div>
        <h4>Findings</h4>
        <ul>${findings}</ul>
      `;
    }

    async function createMatter() {
      const res = await api('/la/matters/ingest', { method:'POST' });
      current = res.matter;
      reloadMatters();
  const drop = document.getElementById('drop');
  drop.ondragover = (e)=>{e.preventDefault(); drop.style.background='#f7f7f7';};
  drop.ondragleave = ()=>{drop.style.background='';};
  drop.ondrop = async (e)=>{
    e.preventDefault(); drop.style.background='';
    if(!current){ alert('Create/select a matter first'); return; }
    const form = new FormData();
    form.append('ref', current.ref || 'AUTO');
    for(const f of e.dataTransfer.files){
      if(/llc1/i.test(f.name)) form.append('llc1_file', f);
      else if(/con29/i.test(f.name)) form.append('con29_file', f);
      else form.append('con29_file', f);
    }
    const res = await fetch('/api/process', { method:'POST', body: form });
    const data = await res.json();
    if(data.job_id){
      // poll job
      const poll = async ()=>{
        const s = await fetch('/jobs/'+data.job_id+'/status').then(r=>r.json());
        if(s.status === 'finished'){ loadDetail(); }
        else if(s.status === 'failed'){ alert('Processing failed'); }
        else { setTimeout(poll, 1000); }
      }; poll();
    } else {
      loadDetail();
    }
  };
    }

    async function ingestText(){
      if(!current) { alert('Select or create a matter first'); return; }
      const form = new FormData();
      form.append('ref', current.ref || 'AUTO');
      const llc1 = document.getElementById('llc1Text').value;
      const con29 = document.getElementById('con29Text').value;
      if (llc1) form.append('llc1_text', llc1);
      if (con29) form.append('con29_text', con29);
      const res = await fetch('/api/process', { method:'POST', body: form });
      if (!res.ok){
        alert('Upload failed: ' + await res.text());
        return;
      }
      document.getElementById('llc1Text').value='';
      document.getElementById('con29Text').value='';
      loadDetail();
    }

    reloadMatters();
  const drop = document.getElementById('drop');
  drop.ondragover = (e)=>{e.preventDefault(); drop.style.background='#f7f7f7';};
  drop.ondragleave = ()=>{drop.style.background='';};
  drop.ondrop = async (e)=>{
    e.preventDefault(); drop.style.background='';
    if(!current){ alert('Create/select a matter first'); return; }
    const form = new FormData();
    form.append('ref', current.ref || 'AUTO');
    for(const f of e.dataTransfer.files){
      if(/llc1/i.test(f.name)) form.append('llc1_file', f);
      else if(/con29/i.test(f.name)) form.append('con29_file', f);
      else form.append('con29_file', f);
    }
    const res = await fetch('/api/process', { method:'POST', body: form });
    const data = await res.json();
    if(data.job_id){
      // poll job
      const poll = async ()=>{
        const s = await fetch('/jobs/'+data.job_id+'/status').then(r=>r.json());
        if(s.status === 'finished'){ loadDetail(); }
        else if(s.status === 'failed'){ alert('Processing failed'); }
        else { setTimeout(poll, 1000); }
      }; poll();
    } else {
      loadDetail();
    }
  };
  </script>
</body>
</html>
"""

@router.get("/la/ui", response_class=HTMLResponse)
def ui_root():
    return HTML
