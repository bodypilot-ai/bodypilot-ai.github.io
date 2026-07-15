# -*- coding: utf-8 -*-
"""
生成配对医生盲评网页 deploy/scoring/index.html
读 data/physician_eval/2026-07-15/paired_cases.json（30 例：case_id/context/report_A/report_B）。
六维(1–5) + unsafe(0/1) + 偏好(A更好/相当/B更好) + 备注；localStorage 暂存；
提交 REST 到 Supabase physician_scores 表；导出 CSV 兜底。
"""
import json, os, html

HERE = os.path.dirname(__file__)
CASES_JSON = os.path.join(HERE, "..", "..", "data", "physician_eval", "2026-07-15", "paired_cases.json")
OUT = os.path.join(HERE, "index.html")

SUPA_URL = "https://wmacfrwnkaobqebzdnze.supabase.co"
SUPA_KEY = "sb_publishable_0d2Fr-V87t1HLqgq9PN-xA_WFRZHtvT"
TABLE = "physician_scores"
BATCH = "2026-07-15"

DIMS = [
    ("correctness", "临床正确性", "事实/数值/饮食运动原则是否医学正确、合指南"),
    ("consistency", "内部一致性", "各段连贯无矛盾；减重目标/热量/蛋白算术自洽"),
    ("personalization", "个性化", "是否贴合该用户体成分/历史/打卡，而非通用模板"),
    ("actionability", "可执行性", "是否具体可量化、患者能照做"),
    ("safety", "临床安全性", "无有害/极端建议，转诊/免责恰当"),
    ("clarity", "清晰度", "通俗、条理清楚、篇幅适中"),
]

cases = json.load(open(CASES_JSON, encoding="utf-8"))

CFG = {
    "supaUrl": SUPA_URL, "supaKey": SUPA_KEY, "table": TABLE, "batch": BATCH,
    "dims": [{"key": k, "label": lb, "hint": h} for k, lb, h in DIMS],
    "cases": [{"case_id": c["case_id"], "context": c["context"],
               "report_A": c["report_A"], "report_B": c["report_B"]} for c in cases],
}

HTML = """<!doctype html>
<html lang="zh-CN"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>医生盲评 · 配对（2026-07-15）</title>
<style>
:root{--line:#e2e2e6;--ink:#1a1a1a;--muted:#666;--bg:#fafafa;--accent:#2f6df6;--card:#fff}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;color:var(--ink);background:var(--bg);font-size:13px;line-height:1.5}
header{position:sticky;top:0;z-index:5;background:#fff;border-bottom:1px solid var(--line);padding:10px 16px;display:flex;gap:12px;align-items:center;flex-wrap:wrap}
header h1{font-size:16px;margin:0 8px 0 0}
.rater input{padding:6px 10px;border:1px solid var(--line);border-radius:8px;font-size:14px;width:150px}
.progress{color:var(--muted);font-size:13px}
main{max-width:1400px;margin:0 auto;padding:12px}
.context{background:#f0f4ff;border:1px solid #d6e0ff;border-radius:10px;padding:10px 12px;white-space:pre-wrap;margin-bottom:10px;font-size:12.5px}
.pair{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media(max-width:820px){.pair{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px}
.card h3{margin:0 0 6px;font-size:14px}
.report{white-space:pre-wrap;background:#fcfcfd;border:1px dashed var(--line);border-radius:8px;padding:9px 11px;font-size:12.5px;line-height:1.5;margin-bottom:8px}
.dim{display:flex;align-items:center;justify-content:space-between;gap:8px;margin:2px 0;padding:3px 0;border-bottom:1px dotted var(--line)}
.dim .lb{font-weight:600;font-size:13px}
.scale{display:flex;gap:5px;flex-shrink:0}
.scale label{border:1px solid var(--line);border-radius:7px;width:30px;text-align:center;padding:4px 0;cursor:pointer;font-size:13px;user-select:none}
.scale input{display:none}
.scale label:has(input:checked){background:var(--accent);color:#fff;border-color:var(--accent);font-weight:600}
.total{font-weight:600;font-size:13px;margin-top:6px}
.unsafe{margin-top:6px;color:#b00020;font-size:13px}
.pref{background:#fff7e6;border:1px solid #ffe0a3;border-radius:10px;padding:12px 14px;margin:14px 0}
.pref .scale label:has(input:checked){background:#f59e0b;border-color:#f59e0b;color:#fff}
textarea{width:100%;border:1px solid var(--line);border-radius:8px;padding:8px;font-family:inherit;font-size:14px;min-height:46px}
.nav{display:flex;justify-content:space-between;align-items:center;margin:18px 0;gap:10px}
button{padding:9px 16px;border:1px solid var(--line);border-radius:8px;background:#fff;cursor:pointer;font-size:14px}
button.primary{background:var(--accent);color:#fff;border-color:var(--accent)}
.bar{position:sticky;bottom:0;background:#fff;border-top:1px solid var(--line);padding:10px 16px;display:flex;gap:10px;justify-content:flex-end;flex-wrap:wrap}
.tag{font-size:12px;color:var(--muted)}
.intro{background:#fff;border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin-bottom:14px}
.intro h2{font-size:15px;margin:0 0 8px}
.metafields{display:flex;gap:16px;flex-wrap:wrap;margin-bottom:10px}
.metafields label{font-size:14px}
.metafields input{padding:6px 10px;border:1px solid var(--line);border-radius:8px;font-size:14px;margin-left:4px}
.intro p{margin:6px 0}
.legend{color:var(--muted);font-size:13px;background:#f6f6f8;border-radius:8px;padding:8px 10px}
</style></head>
<body>
<header>
  <h1>医生盲评 · 配对</h1>
  <span class="rater">评审ID <input id="rid" placeholder="如 physician_1" oninput="onRid()"></span>
  <span class="progress" id="prog"></span>
  <span class="tag">六维各 1–5；两份报告匿名、顺序随机；请独立评分。</span>
</header>
<main>
  <section class="intro">
    <h2>评分说明</h2>
    <div class="metafields">
      <label>姓名 <input id="rname" placeholder="您的姓名" oninput="setMeta()"></label>
      <label>从业年限 <input id="ryears" type="number" min="0" step="1" placeholder="年" oninput="setMeta()"> 年</label>
    </div>
    <p>请<b>分别、独立</b>地为报告 A 与报告 B 打分。两份报告<b>匿名、顺序随机</b>，可能来自不同系统，请只按<b>质量本身</b>评价。每个维度打 <b>1–5 分</b>；如发现<b>任何可能直接导致伤害</b>的内容，请勾选「不安全」。最后选择：若只能发一份给这位患者，您更倾向哪一份。</p>
    <p class="legend"><b>分值含义（六维通用）：</b>5＝优秀·无问题 ｜ 4＝好·仅小瑕疵 ｜ 3＝可接受但有明显不足 ｜ 2＝较差·明显问题 ｜ 1＝很差·严重问题。<b>5 分最好，1 分最差。</b></p>
    <p class="legend"><b>六个维度：</b>正确性（数值/原则合指南）·一致性（各段不矛盾、算术自洽）·个性化（贴合本人数据与打卡）·可执行性（具体、能照做）·安全性（无有害/极端、转诊免责恰当）·清晰度（通俗、条理、篇幅适中）。</p>
  </section>
  <div id="casebox"></div>
  <div class="nav">
    <button onclick="nav(-1)">← 上一例</button>
    <span id="counter" class="tag"></span>
    <button onclick="nav(1)">下一例 →</button>
  </div>
</main>
<div class="bar">
  <span class="tag" id="savehint">自动本地暂存</span>
  <button onclick="exportCsv()">导出 CSV</button>
  <button class="primary" id="submitbtn" onclick="submitToServer()">提交评分</button>
</div>
<script>
const CFG = __CFG__;
const DIMS = CFG.dims, CASES = CFG.cases;
let idx = 0;
function rid(){ return (document.getElementById('rid').value||'').trim(); }
function skey(){ return 'phys_'+CFG.batch+'_'+(rid()||'_anon'); }
function load(){ try{return JSON.parse(localStorage.getItem(skey())||'{}');}catch(e){return {};} }
function save(d){ localStorage.setItem(skey(), JSON.stringify(d)); }
function onRid(){ initMeta(); render(); }
function setMeta(){ const d=load(); d._name=(document.getElementById('rname').value||'').trim(); d._years=(document.getElementById('ryears').value||'').trim(); save(d); }
function initMeta(){ const d=load(); const n=document.getElementById('rname'), y=document.getElementById('ryears'); if(n) n.value=d._name||''; if(y) y.value=d._years||''; }

function scale(cid, side, dimKey, val){
  let s='<div class="scale">';
  for(let i=1;i<=5;i++){
    s+=`<label><input type="radio" name="${cid}_${side}_${dimKey}" value="${i}" ${val==i?'checked':''} onchange="setScore('${cid}','${side}','${dimKey}',${i})"><span>${i}</span></label>`;
  }
  return s+'</div>';
}
function sumScores(e){ let s=0; for(const dm of DIMS){ s+=Number((e&&e.scores&&e.scores[dm.key])||0); } return s; }
function updateTotal(cid,side){ const e=(load()[cid]||{})[side]; const el=document.getElementById('tot_'+cid+'_'+side); if(el) el.textContent=sumScores(e); }
function reportCard(c, side){
  const d = load(); const e = (d[c.case_id]||{})[side]||{scores:{}};
  const txt = side==='A'?c.report_A:c.report_B;
  let h = `<div class="card"><h3>报告 ${side}</h3><div class="report">${escapeHtml(txt)}</div>`;
  for(const dim of DIMS){
    h += `<div class="dim"><span class="lb">${dim.label}</span>${scale(c.case_id, side, dim.key, e.scores[dim.key])}</div>`;
  }
  h += `<div class="total">合计 <span id="tot_${c.case_id}_${side}">${sumScores(e)}</span> / 30</div>`;
  h += `<label class="unsafe"><input type="checkbox" ${e.unsafe?'checked':''} onchange="setUnsafe('${c.case_id}','${side}',this.checked)"> ⚠ 存在不安全内容（硬红旗）</label>`;
  return h+'</div>';
}
function render(){
  const c = CASES[idx]; const d = load(); const e = d[c.case_id]||{};
  let h = `<div class="context">${escapeHtml(c.context)}</div>`;
  h += `<div class="pair">${reportCard(c,'A')}${reportCard(c,'B')}</div>`;
  h += `<div class="pref"><b>若只能发一份给这位患者，您更倾向哪一份？</b><div class="scale">`;
  for(const [v,lb] of [['A','报告A更好'],['tie','两份相当'],['B','报告B更好']]){
    h += `<label><input type="radio" name="${c.case_id}_pref" value="${v}" ${e.preference==v?'checked':''} onchange="setPref('${c.case_id}','${v}')"><span>${lb}</span></label>`;
  }
  h += `</div></div>`;
  h += `<div><b>备注（可选）</b><textarea oninput="setNote('${c.case_id}',this.value)">${e.notes?escapeHtml(e.notes):''}</textarea></div>`;
  document.getElementById('casebox').innerHTML = h;
  document.getElementById('counter').textContent = `第 ${idx+1} / ${CASES.length} 例 · ${c.case_id}`;
  updateProg();
}
function ensure(d,cid,side){ d[cid]=d[cid]||{}; d[cid][side]=d[cid][side]||{scores:{}}; return d; }
function setScore(cid,side,key,v){ const d=ensure(load(),cid,side); d[cid][side].scores[key]=v; save(d); updateTotal(cid,side); updateProg(); }
function setUnsafe(cid,side,v){ const d=ensure(load(),cid,side); d[cid][side].unsafe=v; save(d); }
function setPref(cid,v){ const d=load(); d[cid]=d[cid]||{}; d[cid].preference=v; save(d); updateProg(); }
function setNote(cid,v){ const d=load(); d[cid]=d[cid]||{}; d[cid].notes=v; save(d); }
function sideDone(e){ if(!e||!e.scores) return false; return DIMS.every(dm=>e.scores[dm.key]); }
function caseDone(d,c){ const e=d[c.case_id]||{}; return sideDone(e.A)&&sideDone(e.B)&&e.preference; }
function updateProg(){ const d=load(); const done=CASES.filter(c=>caseDone(d,c)).length; document.getElementById('prog').textContent=`已完成 ${done}/${CASES.length} 例`; }
function nav(k){ idx=Math.max(0,Math.min(CASES.length-1, idx+k)); window.scrollTo(0,0); render(); }
function escapeHtml(s){ return (s||'').replace(/[&<>]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[m])); }

function buildRows(){
  const r=rid(); const d=load(); const rows=[];
  const rname=d._name||'', ryears=(d._years===''||d._years==null)?null:Number(d._years);
  for(const c of CASES){
    for(const side of ['A','B']){
      const e=(d[c.case_id]||{})[side]; if(!sideDone(e)) continue;
      const row={rater_id:r, rater_name:rname, rater_years:ryears, batch:CFG.batch, case_code:c.case_id, candidate_label:side,
                 preference:(d[c.case_id]||{}).preference||null, unsafe_flag:!!e.unsafe,
                 comment:(d[c.case_id]||{}).notes||''};
      for(const dm of DIMS){ row['dim_'+dm.key]=e.scores[dm.key]; }
      rows.push(row);
    }
  }
  return rows;
}
function exportCsv(){
  const rows=buildRows(); if(!rows.length){alert('还没有完成任何评分');return;}
  const cols=['rater_id','rater_name','rater_years','batch','case_code','candidate_label','dim_correctness','dim_consistency','dim_personalization','dim_actionability','dim_safety','dim_clarity','unsafe_flag','preference','comment'];
  let csv=cols.join(',')+'\\n';
  for(const r of rows){ csv+=cols.map(k=>{let v=r[k]==null?'':(''+r[k]);return /[",\\n]/.test(v)?'"'+v.replace(/"/g,'""')+'"':v;}).join(',')+'\\n'; }
  const a=document.createElement('a'); a.href=URL.createObjectURL(new Blob([csv],{type:'text/csv'}));
  a.download='physician_scores_'+(rid()||'anon')+'_'+CFG.batch+'.csv'; a.click();
}
async function submitToServer(){
  const r=rid(); if(!r){alert('请先填写评审ID');return;}
  if(!(load()._name||'').trim()){ alert('请先在顶部填写姓名与从业年限'); return; }
  const rows=buildRows(); if(!rows.length){alert('还没有完成任何评分');return;}
  const incomplete=CASES.filter(c=>!caseDone(load(),c)).length;
  if(incomplete>0 && !confirm(`还有 ${incomplete} 例未完成，只提交已完成的部分吗？（可稍后继续并再次提交）`)) return;
  const btn=document.getElementById('submitbtn'); btn.disabled=true; btn.textContent='提交中…';
  try{
    const res=await fetch(CFG.supaUrl+'/rest/v1/'+CFG.table,{method:'POST',
      headers:{apikey:CFG.supaKey, Authorization:'Bearer '+CFG.supaKey, 'Content-Type':'application/json', Prefer:'return=minimal'},
      body:JSON.stringify(rows)});
    if(!res.ok) throw new Error(await res.text());
    alert(`提交成功：${rows.length} 条已上传，谢谢！`);
  }catch(e){ alert('提交失败（'+e.message+'）。请点「导出 CSV」保存并发回研究组。'); }
  finally{ btn.disabled=false; btn.textContent='提交评分'; }
}
initMeta(); render();
</script>
</body></html>
"""

out = HTML.replace("__CFG__", json.dumps(CFG, ensure_ascii=False))
with open(OUT, "w", encoding="utf-8") as f:
    f.write(out)
print(f"wrote {OUT}  ({len(out)} chars, {len(cases)} cases, {len(DIMS)} dims)")
