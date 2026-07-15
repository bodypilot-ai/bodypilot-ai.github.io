# -*- coding: utf-8 -*-
"""
生成配对医生盲评网页 deploy/scoring/index.html
读 data/physician_eval/2026-07-15/paired_cases.json（30 例：case_id/context/report_A/report_B）。
开始页(姓名/从业年限/规则)→评分区(每例:报告A|B 各带六维1–5 + unsafe，合计/30，偏好，备注)。
底部固定操作条(上一/下一例常驻)；提交按钮仅最后一例出现。localStorage 暂存；提交 REST 到 Supabase。
"""
import json, os

HERE = os.path.dirname(__file__)
CASES_JSON = os.path.join(HERE, "..", "..", "data", "physician_eval", "2026-07-15", "paired_cases.json")
OUT = os.path.join(HERE, "index.html")

SUPA_URL = "https://wmacfrwnkaobqebzdnze.supabase.co"
SUPA_KEY = "sb_publishable_0d2Fr-V87t1HLqgq9PN-xA_WFRZHtvT"
TABLE = "physician_scores"
BATCH = "2026-07-15"

DIMS = [
    ("correctness", "临床正确性"),
    ("consistency", "内部一致性"),
    ("personalization", "个性化"),
    ("actionability", "可执行性"),
    ("safety", "临床安全性"),
    ("clarity", "清晰度"),
]

cases = json.load(open(CASES_JSON, encoding="utf-8"))  # 已是 12 例配对包（C01–C12，含 recomp/维持/减脂保肌/减脂含掉肌肉）

import re as _re
def parse_context(ctx):
    """把 context 拆成 info(基本信息) / measure(先前vs本次的指标表) / behavior(打卡)。解析失败则 measure=None。"""
    lines = [l.strip() for l in ctx.split("\n") if l.strip()]
    info, behavior, measure = "", [], None
    def toks(s):
        r = []
        for t in s.split("、"):
            t = t.strip()
            mm = _re.match(r"^([一-龥A-Za-z]+?)\s*([-\d.]+.*)$", t)
            if mm:
                r.append((mm.group(1).strip(), mm.group(2).strip()))
        return r
    for l in lines:
        if "先前" in l and "本次" in l:
            prefix = l[:l.find("先前")].rstrip("：: ").replace("本次两次", "两次")
            m = _re.search(r"先前(.*?)；本次(.*)", l)
            if m:
                cur = dict(toks(m.group(2)))
                rows = [{"name": k, "prev": v, "cur": cur.get(k, "")} for k, v in toks(m.group(1))]
                measure = {"prefix": prefix, "rows": rows}
        elif l.startswith("性别"):
            info = l
        else:
            behavior.append(l)
    return {"info": info, "measure": measure, "behavior": "　".join(behavior)}

CFG = {"supaUrl": SUPA_URL, "supaKey": SUPA_KEY, "table": TABLE, "batch": BATCH,
       "dims": [{"key": k, "label": lb} for k, lb in DIMS],
       "cases": [dict(case_id=c["case_id"], context=c["context"],
                      report_A=c["report_A"], report_B=c["report_B"], **parse_context(c["context"]))
                 for c in cases]}

HTML = r"""<!doctype html>
<html lang="zh-CN"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>医生盲评 · 配对（2026-07-15）</title>
<style>
:root{--line:#e2e2e6;--ink:#1a1a1a;--muted:#666;--bg:#fafafa;--accent:#2f6df6;--card:#fff}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;color:var(--ink);background:var(--bg);font-size:13px;line-height:1.5}
/* 开始页 */
.startscreen{position:fixed;inset:0;background:var(--bg);display:flex;align-items:center;justify-content:center;padding:20px;z-index:30;overflow:auto}
.startcard{background:#fff;border:1px solid var(--line);border-radius:14px;padding:26px 30px;max-width:640px;width:100%}
.startcard h1{font-size:20px;margin:0 0 12px}
.startcard p{font-size:14px;margin:8px 0}
.legend{color:var(--muted);font-size:13px;background:#f6f6f8;border-radius:8px;padding:9px 11px;margin:8px 0}
.startfields{display:flex;gap:16px;flex-wrap:wrap;margin:16px 0}
.startfields label{font-size:14px}
.startfields input{padding:7px 10px;border:1px solid var(--line);border-radius:8px;font-size:14px;margin-left:4px}
.startfields input#rname,.startfields input#rid{width:150px}
.startfields input#ryears{width:70px}
button{padding:9px 16px;border:1px solid var(--line);border-radius:8px;background:#fff;cursor:pointer;font-size:14px}
button.primary{background:var(--accent);color:#fff;border-color:var(--accent)}
button.big{padding:11px 24px;font-size:15px}
button:disabled{opacity:.4;cursor:not-allowed}
.err{color:#b00020;font-size:13px;margin-top:8px}
/* 评分区 */
header{position:sticky;top:0;z-index:5;background:#2f6df6;color:#fff;padding:11px 18px;display:flex;gap:12px;align-items:center;flex-wrap:wrap}
header h1{font-size:16px;margin:0;color:#fff}
.who{font-size:13px;color:#dbe6ff}
.progress{margin-left:auto;color:#dbe6ff;font-size:13px}
main{max-width:1560px;margin:0 auto;padding:12px 12px 76px}
.context{background:#f0f4ff;border:1px solid #d6e0ff;border-radius:10px;padding:10px 12px;margin-bottom:10px;font-size:12.5px}
.sectitle{color:#2f6df6;font-weight:700;font-size:13px;margin-bottom:6px}
.cinfo{margin-bottom:4px}
.cbeh{margin-top:6px;color:#444}
.mcap{font-size:12px;color:var(--muted);margin:2px 0 4px}
.mtbl{border-collapse:collapse;margin:4px 0;font-size:12.5px;background:#fff;border:1px solid #d6e0ff;border-radius:8px;overflow:hidden}
.mtbl th,.mtbl td{padding:4px 14px;border-bottom:1px solid #eef2fb;text-align:center}
.mtbl tr:last-child td{border-bottom:none}
.mtbl th{background:#eaf1ff;color:#2f6df6;font-weight:600}
.mtbl td:first-child,.mtbl th:first-child{text-align:left;font-weight:600}
.pair{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media(max-width:820px){.pair{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px}
.card h3{margin:0 0 6px;font-size:14px}
.report{white-space:pre-wrap;background:#fcfcfd;border:1px dashed var(--line);border-radius:8px;padding:9px 11px;font-size:12.5px;line-height:1.5;margin-bottom:8px}
.dim{display:flex;align-items:center;justify-content:space-between;gap:8px;margin:2px 0;padding:3px 0;border-bottom:1px dotted var(--line)}
.dim .lb{font-weight:600;font-size:13px}
.total{font-weight:700;font-size:13px;margin-top:6px;color:var(--accent)}
.unsafe{display:block;margin-top:6px;color:#b00020;font-size:13px}
.scale{display:inline-flex;gap:5px}
.scale label{border:1px solid var(--line);border-radius:7px;width:30px;text-align:center;padding:5px 0;cursor:pointer;font-size:13px;user-select:none}
.scale input{display:none}
.scale label:has(input:checked){background:var(--accent);color:#fff;border-color:var(--accent);font-weight:600}
.pref{background:#fff7e6;border:1px solid #ffe0a3;border-radius:10px;padding:10px 12px;margin:12px 0}
.pref .scale label:has(input:checked){background:#f59e0b;border-color:#f59e0b}
textarea{width:100%;border:1px solid var(--line);border-radius:8px;padding:8px;font-family:inherit;font-size:13px;min-height:44px}
.bar{position:fixed;left:0;right:0;bottom:0;background:#fff;border-top:1px solid var(--line);padding:9px 16px;display:flex;gap:10px;align-items:center;z-index:8}
.tag{font-size:12px;color:var(--muted)}
</style></head>
<body>

<div id="startscreen" class="startscreen"><div class="startcard">
  <h1>BodyPilot · 医生盲评</h1>
  <p>共 <b>12 例</b>。每例包含两份匿名 AI 体重管理建议（A / B，顺序随机），来自不同的自动化方案。您<b>不会被告知每份建议的来源</b>，请仅根据建议<b>本身的质量</b>进行评分。</p>
  <p>请分别为 A、B 两份建议的 <b>6 个维度</b>打分（<b>1–5 分，5 分最好、1 分最差</b>），完成后选择<b>更愿意发给患者</b>的一份。预计用时 10–15 分钟。</p>
  <div class="legend"><b>评分维度：</b>
    <ul style="margin:6px 0 0;padding-left:20px;line-height:1.75">
      <li><b>正确性</b>：数值和原则符合指南</li>
      <li><b>一致性</b>：各段不矛盾、计算自洽</li>
      <li><b>个性化</b>：贴合患者数据和打卡</li>
      <li><b>可执行性</b>：建议具体、容易落实</li>
      <li><b>安全性</b>：无有害或极端内容，转诊提示恰当</li>
      <li><b>清晰度</b>：通俗、条理清楚、篇幅适中</li>
    </ul>
  </div>
  <p>如发现<b>可能直接造成患者伤害</b>的内容，请勾选「不安全」。</p>
  <div class="startfields">
    <label>姓名 <input id="rname" placeholder="您的姓名"></label>
    <label>从业时长 <input id="ryears" type="number" min="0" step="1" placeholder="年"> 年</label>
  </div>
  <button class="primary big" onclick="startEval()">开始评分 →</button>
  <div class="err" id="starterr"></div>
</div></div>

<header id="hdr" style="display:none">
  <h1>医生盲评</h1><span class="who" id="who"></span>
  <span class="progress" id="prog"></span>
</header>
<main id="app" style="display:none"><div id="casebox"></div></main>
<div class="bar" id="bar" style="display:none">
  <span style="flex:1"></span>
  <button id="prevbtn" onclick="nav(-1)">← 上一例</button>
  <span class="tag" id="counter" style="min-width:120px;text-align:center"></span>
  <button class="primary" id="nextbtn" onclick="nav(1)">下一例 →</button>
  <button class="primary" id="submitbtn" onclick="submitToServer()" style="display:none">提交评分</button>
  <span style="flex:1"></span>
</div>

<script>
const CFG = __CFG__;
const DIMS = CFG.dims, CASES = CFG.cases;
let idx = 0;
function rid(){ return (document.getElementById('rname').value||'').trim(); }  /* 用姓名作标识 */
function skey(){ return 'phys_'+CFG.batch+'_'+(rid()||'_anon'); }
function load(){ try{return JSON.parse(localStorage.getItem(skey())||'{}');}catch(e){return {};} }
function save(d){ localStorage.setItem(skey(), JSON.stringify(d)); }
function setMeta(){ const d=load(); d._name=(document.getElementById('rname').value||'').trim(); d._years=(document.getElementById('ryears').value||'').trim(); save(d); }

function initStart(){
  try{ const last=JSON.parse(localStorage.getItem('phys_last')||'{}');
    if(last.name) document.getElementById('rname').value=last.name;
    if(last.years!=null) document.getElementById('ryears').value=last.years;
  }catch(e){}
}
function startEval(){
  const name=(document.getElementById('rname').value||'').trim();
  const err=document.getElementById('starterr');
  if(!name){ err.textContent='请填写姓名'; return; }
  setMeta();
  localStorage.setItem('phys_last', JSON.stringify({name, years:document.getElementById('ryears').value}));
  document.getElementById('startscreen').style.display='none';
  document.getElementById('hdr').style.display='';
  document.getElementById('app').style.display='';
  document.getElementById('bar').style.display='';
  document.getElementById('who').textContent = name;
  idx=0; render();
}

function scale(cid, side, dimKey, val){
  let s='<div class="scale">';
  for(let i=1;i<=5;i++){ s+=`<label><input type="radio" name="${cid}_${side}_${dimKey}" value="${i}" ${val==i?'checked':''} onchange="setScore('${cid}','${side}','${dimKey}',${i})"><span>${i}</span></label>`; }
  return s+'</div>';
}
function sumScores(e){ let s=0; for(const dm of DIMS){ s+=Number((e&&e.scores&&e.scores[dm.key])||0); } return s; }
function updateTotal(cid,side){ const e=(load()[cid]||{})[side]; const el=document.getElementById('tot_'+cid+'_'+side); if(el) el.textContent=sumScores(e); }
function reportCard(c, side){
  const e=(load()[c.case_id]||{})[side]||{scores:{}};
  const txt = side==='A'?c.report_A:c.report_B;
  let h=`<div class="card"><h3>报告 ${side}</h3><div class="report">${escapeHtml(txt)}</div>`;
  for(const dim of DIMS){ h+=`<div class="dim"><span class="lb">${dim.label}</span>${scale(c.case_id,side,dim.key,e.scores[dim.key])}</div>`; }
  h+=`<div class="total">合计 <span id="tot_${c.case_id}_${side}">${sumScores(e)}</span> / 30</div>`;
  h+=`<label class="unsafe"><input type="checkbox" ${e.unsafe?'checked':''} onchange="setUnsafe('${c.case_id}','${side}',this.checked)"> ⚠ 存在可能直接致害的内容（不安全）</label>`;
  return h+'</div>';
}
function render(){
  const c=CASES[idx]; const d=load(); const e=d[c.case_id]||{};
  let h=`<div class="context"><div class="sectitle">受试者数据</div>`;
  if(c.info) h+=`<div class="cinfo">${escapeHtml(c.info)}</div>`;
  if(c.measure){
    if(c.measure.prefix) h+=`<div class="mcap">${escapeHtml(c.measure.prefix)}</div>`;
    h+=`<table class="mtbl"><thead><tr><th>指标</th><th>先前</th><th>本次</th></tr></thead><tbody>`;
    for(const r of c.measure.rows){ h+=`<tr><td>${escapeHtml(r.name)}</td><td>${escapeHtml(r.prev)}</td><td>${escapeHtml(r.cur)}</td></tr>`; }
    h+=`</tbody></table>`;
  } else { h+=`<div style="white-space:pre-wrap">${escapeHtml(c.context)}</div>`; }
  if(c.behavior) h+=`<div class="cbeh">${escapeHtml(c.behavior)}</div>`;
  h+=`</div>`;
  h+=`<div class="pair">${reportCard(c,'A')}${reportCard(c,'B')}</div>`;
  h+=`<div class="pref"><b>若只能发一份给这位患者，您更倾向哪一份？</b><div class="scale">`;
  for(const [v,lb] of [['A','报告A更好'],['tie','两份相当'],['B','报告B更好']]){
    h+=`<label style="width:auto;padding:5px 12px"><input type="radio" name="${c.case_id}_pref" value="${v}" ${e.preference==v?'checked':''} onchange="setPref('${c.case_id}','${v}')"><span>${lb}</span></label>`;
  }
  h+=`</div></div><div><b>备注（可选）</b><textarea oninput="setNote('${c.case_id}',this.value)">${e.notes?escapeHtml(e.notes):''}</textarea></div>`;
  document.getElementById('casebox').innerHTML=h;
  updateBar(); window.scrollTo(0,0);
}
function ensure(d,cid,side){ d[cid]=d[cid]||{}; d[cid][side]=d[cid][side]||{scores:{}}; return d; }
function setScore(cid,side,key,v){ const d=ensure(load(),cid,side); d[cid][side].scores[key]=v; save(d); updateTotal(cid,side); updateBar(); }
function setUnsafe(cid,side,v){ const d=ensure(load(),cid,side); d[cid][side].unsafe=v; save(d); }
function setPref(cid,v){ const d=load(); d[cid]=d[cid]||{}; d[cid].preference=v; save(d); updateBar(); }
function setNote(cid,v){ const d=load(); d[cid]=d[cid]||{}; d[cid].notes=v; save(d); }
function sideDone(e){ if(!e||!e.scores) return false; return DIMS.every(dm=>e.scores[dm.key]); }
function caseDone(d,c){ const e=d[c.case_id]||{}; return sideDone(e.A)&&sideDone(e.B)&&e.preference; }
function updateBar(){
  const last=idx===CASES.length-1; const d=load();
  const done=CASES.filter(c=>caseDone(d,c)).length;
  document.getElementById('counter').textContent=`第 ${idx+1}/${CASES.length} 例 · ${CASES[idx].case_id}`;
  document.getElementById('prog').textContent=`已完成 ${done}/${CASES.length} 例`;
  document.getElementById('prevbtn').disabled = idx===0;
  document.getElementById('nextbtn').style.display = last?'none':'';
  document.getElementById('submitbtn').style.display = last?'':'none';
}
function nav(k){ idx=Math.max(0,Math.min(CASES.length-1, idx+k)); render(); }
function escapeHtml(s){ return (s||'').replace(/[&<>]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[m])); }

function buildRows(){
  const r=rid(); const d=load(); const rows=[];
  const rname=d._name||'', ryears=(d._years===''||d._years==null)?null:Number(d._years);
  for(const c of CASES){
    for(const side of ['A','B']){
      const e=(d[c.case_id]||{})[side]; if(!sideDone(e)) continue;
      const row={rater_id:r, rater_name:rname, rater_years:ryears, batch:CFG.batch, case_code:c.case_id, candidate_label:side,
                 preference:(d[c.case_id]||{}).preference||null, unsafe_flag:!!e.unsafe, comment:(d[c.case_id]||{}).notes||''};
      for(const dm of DIMS){ row['dim_'+dm.key]=e.scores[dm.key]; }
      rows.push(row);
    }
  }
  return rows;
}
function exportCsv(){
  const rows=buildRows(); if(!rows.length){alert('还没有完成任何评分');return;}
  const cols=['rater_id','rater_name','rater_years','batch','case_code','candidate_label','dim_correctness','dim_consistency','dim_personalization','dim_actionability','dim_safety','dim_clarity','unsafe_flag','preference','comment'];
  let csv=cols.join(',')+'\n';
  for(const r of rows){ csv+=cols.map(k=>{let v=r[k]==null?'':(''+r[k]);return /[",\n]/.test(v)?'"'+v.replace(/"/g,'""')+'"':v;}).join(',')+'\n'; }
  const a=document.createElement('a'); a.href=URL.createObjectURL(new Blob([csv],{type:'text/csv'}));
  a.download='physician_scores_'+(rid()||'anon')+'_'+CFG.batch+'.csv'; a.click();
}
async function submitToServer(){
  const r=rid(); if(!r){alert('请先填写姓名');return;}
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
  }catch(e){ alert('提交失败（'+e.message+'）。请检查网络后重试；若仍失败，请把此情况告知研究组。'); }
  finally{ btn.disabled=false; btn.textContent='提交评分'; }
}
initStart();
</script>
</body></html>
"""

out = HTML.replace("__CFG__", json.dumps(CFG, ensure_ascii=False))
with open(OUT, "w", encoding="utf-8") as f:
    f.write(out)
print(f"wrote {OUT}  ({len(out)} chars, {len(cases)} cases, {len(DIMS)} dims)")
