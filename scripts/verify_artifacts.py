"""Static semantic/report checks. These do not execute DAX or render Power BI."""
from pathlib import Path
import json,re,hashlib,csv
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'Maven Fuzzy Factory'; QA=OUT/'qa'; REPORT=OUT/'powerbi'/'Maven Fuzzy Factory.Report'
db=json.loads((QA/'model.bim').read_text()); model=db['model']; tables={t['name']:t for t in model['tables']}; measures={m['name']:m for t in tables.values() for m in t.get('measures',[])}
checks=[]
def check(n,ok,detail=''): checks.append({'check':n,'pass':bool(ok),'detail':detail})
check('Model has 88 documented explicit measures',len(measures)==88 and all(m.get('description') and m.get('formatString') and m.get('displayFolder') for m in measures.values()))
check('Four native fact tables',len([n for n in tables if n.startswith('Fact_')])==4)
check('26 one-direction many-to-one relationships',len(model['relationships'])==26 and all(r['crossFilteringBehavior']=='oneDirection' and r['fromCardinality']=='many' and r['toCardinality']=='one' for r in model['relationships']))
check('No fact-to-fact relationships',all(not(r['fromTable'].startswith('Fact_') and r['toTable'].startswith('Fact_')) for r in model['relationships']))
check('Marked contiguous date dimension',tables['Dim_Date'].get('dataCategory')=='Time' and next(c for c in tables['Dim_Date']['columns'] if c['name']=='Date').get('isKey'))
check('Automatic dates disabled',any(a['name']=='__PBI_TimeIntelligenceEnabled' and a['value']=='0' for a in model['annotations']))
check('Power Query parameter uses M string escaping',model['expressions'][0]['expression'].startswith('"'+str(OUT/'data'/'prepared')+'"'))
badrefs=[]
for m in measures.values():
    expr=m['expression']
    for t,c in re.findall(r"'([^']+)'\[([^\]]+)\]",expr):
        if t not in tables or c not in {x['name'] for x in tables[t]['columns']}: badrefs.append((m['name'],t,c))
    without=re.sub(r"'([^']+)'\[([^\]]+)\]",'',expr)
    for n in re.findall(r'\[([^\]]+)\]',without):
        if n not in measures: badrefs.append((m['name'],'measure',n))
check('All DAX references resolve statically',not badrefs,str(badrefs))
for r in model['relationships']:
    fcols={c['name']:c['dataType'] for c in tables[r['fromTable']]['columns']}; tcols={c['name']:c['dataType'] for c in tables[r['toTable']]['columns']}
    check('Relationship type '+r['fromTable']+'.'+r['fromColumn'],fcols[r['fromColumn']]==tcols[r['toColumn']])
pagesjson=json.loads((REPORT/'definition'/'pages'/'pages.json').read_text()); pglist=[]; allids=[]; unresolved=[]; overlaps=[]; outs=[]; nvisual=0
def refs(o):
    if isinstance(o,dict):
        for kind in ['Measure','Column']:
            if kind in o and isinstance(o[kind],dict):
                x=o[kind]; t=x.get('Expression',{}).get('SourceRef',{}).get('Entity'); n=x.get('Property')
                if t:
                    if t not in tables or (n not in measures if kind=='Measure' else n not in {c['name'] for c in tables[t]['columns']}): unresolved.append((kind,t,n))
        for value in o.values(): refs(value)
    elif isinstance(o,list):
        for value in o: refs(value)
for pid in pagesjson['pageOrder']:
    p=REPORT/'definition'/'pages'/pid; pg=json.loads((p/'page.json').read_text()); pglist.append(pg); vs=[]
    for f in (p/'visuals').glob('*/visual.json'):
        v=json.loads(f.read_text(encoding='utf-8')); nvisual+=1; allids.append(v['name']); refs(v); pos=v['position']; vs.append(v)
        if pos['x']<0 or pos['y']<0 or pos['x']+pos['width']>pg['width'] or pos['y']+pos['height']>pg['height']: outs.append((pid,v['name']))
    for j,a in enumerate(vs):
        for b in vs[j+1:]:
            x,y=a['position'],b['position']
            ix=min(x['x']+x['width'],y['x']+y['width'])-max(x['x'],y['x']); iy=min(x['y']+x['height'],y['y']+y['height'])-max(x['y'],y['y'])
            if ix>0.01 and iy>0.01: overlaps.append((pg['displayName'],a['name'],b['name'],round(ix*iy)))
visible=[p for p in pglist if p.get('visibility')!='HiddenInViewMode']
check('Exactly seven visible 16:9 pages',len(visible)==7 and all(p['width']==1920 and p['height']==1080 for p in visible))
check('Seven hidden explanatory tooltip pages',len([p for p in pglist if p.get('type')=='Tooltip'])==7)
check('Configured product drillthrough',len([p for p in pglist if p.get('type')=='Drillthrough' and p.get('pageBinding',{}).get('parameters')])==1)
check('All visual identifiers unique',len(allids)==len(set(allids)))
check('Every report field resolves',not unresolved,str(unresolved))
check('No out-of-canvas visuals',not outs,str(outs))
check('No visual overlaps',not overlaps,str(overlaps))
check('Financial product comparison is clustered',any(json.loads(f.read_text(encoding='utf-8'))['visual']['visualType']=='clusteredBarChart' for f in (REPORT/'definition'/'pages').glob('*/visuals/*/visual.json')))
check('Refund-adjusted calculations share product scope',measures['Net Revenue After Recorded Refunds']['expression']=='[Product Revenue] - [Total Refund Amount]' and measures['Refund Amount %']['expression']=='DIVIDE([Total Refund Amount], [Product Revenue])')
check('Noncontiguous/partial-day growth guarded','_contiguous' in measures['Revenue Growth %']['expression'] and 'DATE(2012,3,20)' in measures['Revenue Growth %']['expression'])
check('Cohort acquisition/date filters intentionally removed',all("REMOVEFILTERS('"+n+"')" in measures['Cohort Active Customers']['expression'] for n in ['Dim_Date','Dim_Channel','Dim_Device','Dim_Visitor','Dim_Landing']))
for src in json.loads((QA/'source_manifest.json').read_text()): check('Unchanged source '+src['file'],hashlib.sha256((ROOT/'Dataset'/src['file']).read_bytes()).hexdigest()==src['sha256'])
result={'scope':'Static metadata, bindings, geometry and source integrity; does not establish live DAX or rendering correctness.','checks':checks,'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'pages':len(pglist),'visuals':nvisual}
(QA/'artifact_checks.json').write_text(json.dumps(result,indent=2))
print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2)); print('Failures:',[x for x in checks if not x['pass']])
raise SystemExit(1 if result['failed'] else 0)
