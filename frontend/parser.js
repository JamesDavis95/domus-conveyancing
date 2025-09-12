async function j(url, opts={}){
  const r = await fetch(url, opts);
  const t = await r.text();
  try { return {ok:r.ok, status:r.status, json: JSON.parse(t)}; } catch { return {ok:r.ok, status:r.status, text:t}; }
}
function h(tag, attrs={}, children=[]){
  const el = document.createElement(tag);
  for (const [k,v] of Object.entries(attrs||{})){
    if (k==="class") el.className=v;
    else if(k==="html") el.innerHTML=v;
    else el.setAttribute(k,v);
  }
  (children||[]).forEach(c=> el.appendChild(typeof c==="string"? document.createTextNode(c): c));
  return el;
}
function setSummary(data){
  const p = document.getElementById('summaryPanel');
  p.innerHTML="";
  if(!data){ p.appendChild(h('div',{class:'muted'},["No data"])); return; }
  const gridTop = h('div',{class:'grid'},[
    field("Filename", data.filename || "—"),
    field("Council", data.council || "—"),
    field("Property Address", (data.property?.address_text || "—")),
    field("Flood Zone (normalised)", (data.llc1?.FLOOD_ZONE || "—")),
  ]);
  const riskRow = h('div',{class:'field'},[
    h('h4',{},["Risk"]),
    h('div',{},[ (data.risk_score===0? "Low": data.risk_score<0.5? "Low/Med": data.risk_score<0.8? "Medium":"High"),
      " ", h('span',{class:'pill'},[`(score ${data.risk_score ?? 0})`]) ])
  ]);

  // LLC1
  const ll = data.llc1 || {};
  const llcGrid = h('div',{class:'grid'},[
    field("Listed Building", ll.LISTED_BUILDING || "—"),
    field("Grade", ll.GRADE || "—"),
    field("Conservation Area", ll.CONSERVATION_AREA || "—"),
    field("TPO", ll.TREE_PRESERVATION_ORDER || "—"),
    field("Section 106", ll.FINANCIAL_CHARGES || "—"),
    field("CIL", ll.CIL || "—"),
  ]);

  // CON29 (light)
  const c29 = data.con29 || {};
  const c29Grid = h('div',{class:'grid'},[
    field("Road Status", c29.ROAD_STATUS || "—"),
    field("Planning Refs (strict)", c29.PLANNING_REFS_STRICT || "—"),
    field("Enforcement Notices", c29.ENFORCEMENT_NOTICES || "—"),
    field("Public Sewer within 3m", c29.DRAINAGE_WITHIN_3M || "—"),
    field("Build Over Agreement", c29.BUILD_OVER_AGREEMENT || "—"),
    field("Historic Landfill (<250m)", c29.LANDFILL_WITHIN_250M || "—"),
  ]);

  p.appendChild(gridTop);
  p.appendChild(riskRow);
  p.appendChild(h('h2',{},["LLC1"]));
  p.appendChild(llcGrid);
  p.appendChild(h('h2',{},["CON29"]));
  p.appendChild(c29Grid);
}
function field(label, value){
  return h('div',{class:'field'},[
    h('h4',{},[label]),
    h('div',{},[String(value || "—")])
  ]);
}

async function loadRecent(){
  const {json} = await j('/la/matters/recent?limit=50');
  const tbody = document.querySelector('#recent tbody');
  tbody.innerHTML="";
  (json?.items||[]).forEach(row=>{
    const tr = h('tr',{},[
      h('td',{},[String(row.id)]),
      h('td',{},[row.filename || "—"]),
      h('td',{},[row.council || "—"]),
      h('td',{},[String(row.risk ?? 0)]),
    ]);
    tr.style.cursor='pointer';
    tr.addEventListener('click', async ()=>{
      const d = await j(`/la/matters/${row.id}/summary`);
      setSummary(d.json);
    });
    tbody.appendChild(tr);
  });
}

async function set_property(mid){
  const payload = {
    uprn: document.getElementById('uprn').value.trim(),
    title_no: document.getElementById('titleNo').value.trim(),
    address_text: document.getElementById('addr').value.trim(),
    postcode: document.getElementById('pc').value.trim()
  };
  const r = await fetch(`/la/matters/${mid}/property`, {method:'POST', headers:{'content-type':'application/json'}, body: JSON.stringify(payload)});
  return r.ok;
}

async function processFiles(){
  const files = document.getElementById('files').files;
  const council = document.getElementById('council').value.trim();
  if(!files || files.length===0){ alert("Choose at least one PDF"); return; }

  for (const f of files){
    // 1) Create matter
    let body = { council };
    const r1 = await j('/api/matters', { method:'POST', headers:{'content-type':'application/json'}, body: JSON.stringify(body) });
    if (r1?.json?.matter?.id) { await set_property(r1.json.matter.id); }
    const mid = r1?.json?.matter?.id;
    if(!mid){ alert("Failed to create matter"); continue; }

    // 2) Upload
    const fd = new FormData(); fd.append('file', f);
    const up = await fetch(`/api/matters/${mid}/upload?kind=search&async_ocr=0`, { method:'POST', body: fd });
    if(!up.ok){ console.warn("upload failed", await up.text()); continue; }

    // 3) Risk scan (multipart)
    const fd2 = new FormData(); fd2.append('file', f);
    const rs = await fetch(`/api/matters/${mid}/risk-scan`, { method:'POST', body: fd2 });
    if(!rs.ok){ console.warn("scan failed", await rs.text()); }

    // 4) show summary
    const d = await j(`/la/matters/${mid}/summary`);
    setSummary(d.json);
  }
  await loadRecent();
}

document.getElementById('process').addEventListener('click', processFiles);
document.getElementById('refresh').addEventListener('click', loadRecent);
document.getElementById('downloadPack').addEventListener('click', async ()=>{
  const val = prompt("Enter Matter ID to download bundle:");
  if(!val) return;
  window.open(`/la/matters/${encodeURIComponent(val)}/bundle.zip`, '_blank');
});
loadRecent();
