"""Compare actual Power BI DAX results with source-audited references and contexts."""
from pathlib import Path
import json, math
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'Maven Fuzzy Factory'; QA=OUT/'qa'; D=OUT/'data'/'prepared'
raw=json.loads((QA/'live-all-measures.json').read_text()); result=json.loads(next(c['text'] for c in raw['content'] if c['type']=='text')); row=result['data']['rows'][0]
refs=pd.read_csv(QA/'measure-validation.csv').fillna(''); catalog={m['name']:m for m in json.loads((QA/'measure_catalog.json').read_text())}; checks=[]
def eq(name,actual,expected,tol=1e-10):
    ok=actual is None and expected is None or actual==expected
    if actual is not None and expected is not None and isinstance(expected,(int,float)): ok=math.isclose(float(actual),float(expected),rel_tol=1e-12,abs_tol=tol)
    checks.append({'check':name,'pass':bool(ok),'actual':actual,'expected':expected})
for _,r in refs.iterrows():
    name=r.Measure; actual=row['['+name+']']; val=r['Independent expected result']
    if name=='Executive Decision Note': expected='Recorded sales are $1,938,510 at 62.7% gross margin before refunds and operating expenses. Selected sessions convert at 6.8%. Compare acquisition efficiency on the Marketing page and journey losses on Conversion.'
    elif str(val).startswith('BLANK'): expected=None
    else:
        try: expected=float(val)
        except ValueError: expected=val
    eq('Whole-extract DAX: '+name,actual,expected,0.0001001 if catalog[name]['formatString'].startswith('$') else 1e-10)
ctx=json.loads((QA/'live-contexts.json').read_text())
baseline=json.loads((QA/'baseline.json').read_text()); stage=baseline['funnel']; prev=baseline['sessions']
for r in ctx['funnel']['data']['rows']:
    s=r['Dim_FunnelStage[Stage]']; count=stage[s]
    eq('Funnel count '+s,r['[Sessions]'],count); eq('Funnel prior '+s,r['[Prior]'],prev); eq('Funnel conversion '+s,r['[Conversion]'],count/prev); eq('Funnel drop '+s,r['[Dropoff]'],prev-count); prev=count
monthly=pd.read_csv(QA/'monthly_baseline.csv').set_index('Month')
for r in ctx['monthly']['data']['rows']:
    m=r['Dim_Date[Year-Month]']; b=monthly.loc[m]
    eq('Month sales '+m,r['[Sales]'],b.Revenue,0.001); eq('Month profit '+m,r['[Profit]'],b['Gross Profit'],0.001); eq('Month AOV '+m,r['[AOV]'],b.AOV,0.0001001)
    period=pd.Period(m); valid=period>=pd.Period('2012-04') and period<=pd.Period('2015-02')
    for label,offset in [('MoM',1),('YoY',12)]:
        prior=period-offset; expected=None
        if valid and prior>=pd.Period('2012-04'):
            previous=monthly.loc[str(prior)].Revenue; expected=(b.Revenue-previous)/previous
        eq(label+' '+m,r['['+label+']'],expected)
prod=pd.read_csv(QA/'product_baseline.csv').set_index('product_id')
for r in ctx['product']['data']['rows']:
    pid=r['Dim_Product[Product ID]']; p=prod.loc[pid]
    for name,e in [('Sales',p.Revenue),('GP',p.Revenue-p.COGS),('Units',int(p.Units)),('Refunded',int(p.Refunded)),('Refunds',p.Refunds),('Net',p.Revenue-p.Refunds),('Refund ratio',p.Refunds/p.Revenue),('Refund rate',p.Refunded/p.Units)]: eq('Product '+str(pid)+' '+name,r['['+name+']'],e,0.000001)
devices=pd.read_csv(QA/'device_baseline.csv').set_index('Device')
for r in ctx['device']['data']['rows']:
    n=r['Dim_Device[Device]']; d=devices.loc[n]
    for k,e in [('Sessions',int(d.Sessions)),('Converted',int(d.Converted)),('Revenue',d.Revenue),('CVR',d.Converted/d.Sessions)]: eq('Device '+n+' '+k,r['['+k+']'],e,0.000001)
customers=pd.read_csv(D/'Dim_Customer.csv').set_index('Customer ID'); orders=pd.read_csv(D/'Fact_Orders.csv')
orders['Cohort']=orders['Customer ID'].map(customers['Purchase Cohort'])
sizes=customers[customers['Customer Status']=='Observed buyer'].groupby('Purchase Cohort').size()
active=orders.groupby(['Cohort','Purchase Age Month'])['Customer ID'].nunique()
for r in ctx['cohort']['data']['rows']:
    cohort=r['Dim_Customer[Purchase Cohort]']; age=r['Dim_CohortAge[Month After First Purchase]']; size=int(sizes.get(cohort,0)); mature=(pd.Period(cohort)+age).end_time<pd.Timestamp('2015-03-19') if cohort!='No observed purchase' else False
    a=int(active.get((cohort,age),0)) if mature else None
    eq('Cohort size '+cohort+' age '+str(age),r['[CohortSize]'],size)
    eq('Cohort active '+cohort+' age '+str(age),r['[Active]'],a)
    eq('Cohort retention '+cohort+' age '+str(age),r['[Retention]'],a/size if mature and size else None)
for r in ctx['guards']['data']['rows']:
    case=r['[Case]']
    if case in ['Noncontiguous','Partial March','Empty context']:
        for metric in ['Growth','MoM','YoY']: eq(case+' '+metric,r['['+metric+']'],None)
    if case=='Empty context':
        eq('Empty sales',r['[Sales]'],None); eq('Empty conversion',r['[CVR]'],None)
failures=[x for x in checks if not x['pass']]
output={'scope':'Actual DAX engine results against source-audited whole-extract, stage, month, product, device, cohort and guard references. Currency divisions allow 0.0001001 USD tolerance for fixed-decimal DAX arithmetic.','total':len(checks),'passed':len(checks)-len(failures),'failed':len(failures),'all_measure_query_elapsed_ms':result['data']['executionTimeMs'],'checks':checks}
(QA/'live-validation.json').write_text(json.dumps(output,indent=2))
refs['DAX engine status']=['PASS — executed in Desktop; independent reference matched' if not any(m['check']=='Whole-extract DAX: '+n and not m['pass'] for m in checks) else 'FAIL — see live-validation.json' for n in refs.Measure]
refs.to_csv(QA/'measure-validation.csv',index=False,encoding='utf-8-sig')
print(json.dumps({k:v for k,v in output.items() if k!='checks'},indent=2)); print('Failures:',failures)
raise SystemExit(1 if failures else 0)
