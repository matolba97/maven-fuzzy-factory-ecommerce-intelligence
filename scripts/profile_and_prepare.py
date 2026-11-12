"""Rebuild derived analytical tables from immutable source CSVs. No synthetic data."""
from pathlib import Path
import hashlib, json, itertools
import pandas as pd
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'Dataset'; OUT=ROOT/'Maven Fuzzy Factory'; DATA=OUT/'data'/'prepared'; DOC=OUT/'docs'; QA=OUT/'qa'
for p in [DATA,DOC,QA,OUT/'_brief']: p.mkdir(parents=True,exist_ok=True)
names=['orders','order_items','order_item_refunds','products','website_sessions','website_pageviews']
frames={n:pd.read_csv(SRC/(n+'.csv'),parse_dates=['created_at']) for n in names}
o,i,r,p,s,v=[frames[n] for n in names]
checks=[]
def check(name,failures,detail=''):
    checks.append(dict(check=name,failures=int(failures),status='PASS' if failures==0 else 'FAIL',detail=detail))
def cents(x): return (x*100).round().astype('int64')
manifest=[]; profiles=[]
for n,d in frames.items():
    f=SRC/(n+'.csv'); key={'orders':'order_id','order_items':'order_item_id','order_item_refunds':'order_item_refund_id','products':'product_id','website_sessions':'website_session_id','website_pageviews':'website_pageview_id'}[n]
    check(n+' primary key unique',d[key].duplicated().sum())
    check(n+' timestamp valid',d.created_at.isna().sum())
    manifest.append(dict(file=f.name,rows=len(d),bytes=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest(),min_date=str(d.created_at.min()),max_date=str(d.created_at.max())))
    for c in d:
        profiles.append(dict(table=n,column=c,dtype=str(d[c].dtype),nulls=int(d[c].isna().sum()),distinct=int(d[c].nunique()),min=str(d[c].min()) if d[c].dtype!='object' else '',max=str(d[c].max()) if d[c].dtype!='object' else ''))
for child,ck,parent,pk in [(o,'website_session_id',s,'website_session_id'),(o,'user_id',s,'user_id'),(o,'primary_product_id',p,'product_id'),(i,'order_id',o,'order_id'),(i,'product_id',p,'product_id'),(r,'order_item_id',i,'order_item_id'),(r,'order_id',o,'order_id'),(v,'website_session_id',s,'website_session_id')]:
    check(ck+' foreign key '+str(len(child)),(~child[ck].isin(parent[pk])).sum())
for d in [o,i]:
    for c in ['price_usd','cogs_usd']: check(str(len(d))+' nonnegative '+c,(d[c]<0).sum())
check('Nonnegative refunds',(r.refund_amount_usd<0).sum())
ia=i.groupby('order_id').agg(items=('order_item_id','size'),sales=('price_usd','sum'),cogs=('cogs_usd','sum'),primary=('is_primary_item','sum'))
recon=o.merge(ia,on='order_id',validate='one_to_one')
check('Order/item sales reconcile', (cents(recon.price_usd)!=cents(recon.sales)).sum())
check('Order/item COGS reconcile', (cents(recon.cogs_usd)!=cents(recon.cogs)).sum())
check('Order item counts reconcile',(recon.items_purchased!=recon['items']).sum())
check('One primary item per order',(recon.primary!=1).sum())
ri=r.merge(i[['order_item_id','order_id','product_id','price_usd','created_at']],on='order_item_id',suffixes=('','_item'),validate='many_to_one')
check('Refund order linkage',(ri.order_id!=ri.order_id_item).sum())
check('Refund follows item timestamp',(ri.created_at<ri.created_at_item).sum())
refund_by_item=ri.groupby('order_item_id').refund_amount_usd.sum()
check('Refund cumulative not above item price',(refund_by_item>i.set_index('order_item_id').price_usd.reindex(refund_by_item.index)+0.001).sum())
os=o.merge(s[['website_session_id','user_id','created_at']],on='website_session_id',suffixes=('','_session'),validate='many_to_one')
check('Order/session user agrees',(os.user_id!=os.user_id_session).sum())
check('Order follows session',(os.created_at<os.created_at_session).sum())
check('Every session has pageviews',(~s.website_session_id.isin(v.website_session_id)).sum())
check('Pageviews follow session',(v.merge(s[['website_session_id','created_at']],on='website_session_id',suffixes=('','_session'),validate='many_to_one').eval('created_at < created_at_session')).sum())
for d,c in [(s,'is_repeat_session'),(i,'is_primary_item')]: check(c+' binary',(~d[c].isin([0,1])).sum())

# Session dimension enrichment is one-to-one. Facts never join to raw pageviews.
for c in ['utm_source','utm_campaign','utm_content','http_referer']: s[c]=s[c].fillna('(not tagged)')
s['Traffic Group']=np.select([s.utm_source.isin(['gsearch','bsearch']),s.utm_source.eq('socialbook'),s.http_referer.isin(['https://www.gsearch.com','https://www.bsearch.com'])],['Tagged search','Tagged social','Untagged search referral'],default='Direct / unknown')
s['Source']=np.where(s.utm_source.ne('(not tagged)'),s.utm_source,np.select([s.http_referer.eq('https://www.gsearch.com'),s.http_referer.eq('https://www.bsearch.com')],['gsearch referral','bsearch referral'],default='Direct / unknown'))
channel_cols=['Traffic Group','Source','utm_campaign','utm_content','http_referer']
channels=s[channel_cols].drop_duplicates().sort_values(channel_cols).reset_index(drop=True)
channels.insert(0,'Channel ID',range(1,len(channels)+1))
channels['Channel']=channels['Source']+' | '+channels['utm_campaign']
s=s.merge(channels,on=channel_cols,validate='many_to_one')
s=s.sort_values(['created_at','website_session_id'])
ss=s.groupby('user_id').created_at.min()
check('Repeat flag on first observed session', (s.drop_duplicates('user_id').is_repeat_session!=0).sum(), 'Nonzero may indicate left censoring; do not overwrite source flag.')

# Ordinal is a stable, strict (timestamp, pageview_id) ordering within a session.
v=v.sort_values(['website_session_id','created_at','website_pageview_id']).copy()
v['ordinal']=v.groupby('website_session_id').cumcount()
landing=v.drop_duplicates('website_session_id').set_index('website_session_id')
pvcount=v.groupby('website_session_id').size()
sf=s.set_index('website_session_id').copy()
sf['Landing Page']=landing.pageview_url; sf['Pageviews']=pvcount
product_urls=['/products','/the-original-mr-fuzzy','/the-forever-love-bear','/the-birthday-sugar-panda','/the-hudson-river-mini-bear']
stage_urls={'Product':product_urls,'Cart':['/cart'],'Shipping':['/shipping'],'Billing':['/billing','/billing-2'],'Confirmation':['/thank-you-for-your-order']}
prev=pd.Series(-1,index=sf.index,dtype='int64'); seq_times={}
for stage,urls in stage_urls.items():
    events=v[v.pageview_url.isin(urls)][['website_session_id','ordinal','created_at']].copy()
    sf['Reach '+stage]=sf.index.isin(events.website_session_id).astype(int)
    events['previous']=events.website_session_id.map(prev)
    eligible=events[(events.previous.notna())&(events.ordinal>events.previous)]
    first=eligible.drop_duplicates('website_session_id').set_index('website_session_id')
    sf['Sequential '+stage]=sf.index.isin(first.index).astype(int)
    seq_times[stage]=first.created_at
    prev=first.ordinal.reindex(sf.index)
order_first=o.groupby('website_session_id').created_at.min()
billing=sf.index.to_series().map(seq_times['Billing'])
sf['Sequential Purchase']=((sf['Sequential Confirmation']==1)&(sf.index.to_series().map(order_first)>=billing)).astype(int)
sf['Session Date']=sf.created_at.dt.normalize()
sf['Visitor Type']=sf.is_repeat_session.map({0:'New visitor session',1:'Repeat visitor session'})
sf['Device']=sf.device_type
sf['Bounced']=(sf.Pageviews==1).astype(int)
session_orders=o.groupby('website_session_id').agg(**{'Session Orders':('order_id','size'),'Session Revenue':('price_usd','sum')})
sf=sf.join(session_orders).fillna({'Session Orders':0,'Session Revenue':0})
sf['Session Orders']=sf['Session Orders'].astype(int)
sf['Converted']=(sf['Session Orders']>0).astype(int)
sf['Website Session ID']=sf.index; sf['Customer ID']=sf.user_id
check('One session row after enrichment',len(sf)-len(s))
check('Session revenue reconciles',abs(int(cents(sf['Session Revenue']).sum())-int(cents(o.price_usd).sum())))
check('Session orders reconcile',int(sf['Session Orders'].sum())-len(o))
funnel_counts=[len(sf)]+[int(sf['Sequential '+x].sum()) for x in ['Product','Cart','Shipping','Billing','Purchase']]
check('Sequential funnel nonincreasing',sum(a<b for a,b in zip(funnel_counts,funnel_counts[1:])))
check('Sequential purchase has an order',((sf['Sequential Purchase']==1)&(sf.Converted==0)).sum())

# Role-playing conformed dimensions, no relationships between fact tables.
session_attrs=sf[['Website Session ID','Customer ID','Channel ID','Device','Visitor Type','Landing Page']].reset_index(drop=True)
orders=o.merge(session_attrs.drop(columns='Customer ID'),left_on='website_session_id',right_on='Website Session ID',validate='many_to_one')
orders=orders.drop(columns='Website Session ID')
orders=orders.sort_values(['created_at','order_id'])
orders['Purchase Number']=orders.groupby('user_id').cumcount()+1
orders['Purchase Type']=np.where(orders['Purchase Number']==1,'First observed purchase','Subsequent purchase')
orders['Order Date']=orders.created_at.dt.normalize()
orders['Customer ID']=orders.user_id
basket=i.merge(p[['product_id','product_name']],on='product_id',validate='many_to_one').sort_values(['order_id','product_id']).groupby('order_id').product_name.agg(' + '.join)
orders['Basket']=orders.order_id.map(basket)
orders['Has Cross Sell']=(orders.items_purchased>1).astype(int)
first_purchase=orders.groupby('user_id')['Order Date'].min()
orders['Purchase Age Month']=(orders['Order Date'].dt.year-orders.user_id.map(first_purchase).dt.year)*12+orders['Order Date'].dt.month-orders.user_id.map(first_purchase).dt.month
order_attrs=orders[['order_id','Customer ID','Channel ID','Device','Visitor Type','Landing Page','Order Date']]
items=i.merge(order_attrs,on='order_id',validate='many_to_one')
items['Item Role']=items.is_primary_item.map({1:'Primary item',0:'Cross-sell item'})
refunded=r.groupby('order_item_id').refund_amount_usd.sum()
items['Recorded Refund']=items.order_item_id.map(refunded).fillna(0)
items['Refunded Item']=items.order_item_id.isin(refunded.index).astype(int)
launch=p.set_index('product_id').created_at
items['Launch Age Month']=(items.created_at.dt.year-items.product_id.map(launch).dt.year)*12+items.created_at.dt.month-items.product_id.map(launch).dt.month
refunds=r.merge(i[['order_item_id','product_id']],on='order_item_id',validate='many_to_one').merge(order_attrs,on='order_id',validate='many_to_one')
refunds['Refund Date']=refunds.created_at.dt.normalize()
refunds['Refund Lag Days']=(refunds['Refund Date']-refunds['Order Date']).dt.days
customers=pd.DataFrame({'Customer ID':sorted(s.user_id.unique())})
customers['First Session Date']=customers['Customer ID'].map(ss).dt.normalize()
customers['First Purchase Date']=customers['Customer ID'].map(first_purchase)
customers['Purchase Cohort']=customers['First Purchase Date'].dt.strftime('%Y-%m').fillna('No observed purchase')
customers['Observed Lifetime Orders']=customers['Customer ID'].map(o.groupby('user_id').size()).fillna(0).astype(int)
customers['Observed Frequency']=pd.cut(customers['Observed Lifetime Orders'],[-1,0,1,2,4,np.inf],labels=['No purchase','1 purchase','2 purchases','3–4 purchases','5+ purchases']).astype(str)
customers['Customer Status']=np.where(customers['Observed Lifetime Orders']>0,'Observed buyer','No observed purchase')
dates=pd.DataFrame({'Date':pd.date_range(min(s.created_at.min(),o.created_at.min()).normalize().replace(month=1,day=1),max(r.created_at.max(),s.created_at.max()).normalize().replace(month=12,day=31))})
dt=dates.Date.dt
dates['Year']=dt.year; dates['Quarter']='Q'+dt.quarter.astype(str); dates['Month']=dt.month_name(); dates['Month Number']=dt.month
dates['Year-Month']=dt.strftime('%Y-%m'); dates['Year Month Sort']=dt.year*100+dt.month
dates['Week']=dt.isocalendar().week.astype(int); dates['ISO Year']=dt.isocalendar().year.astype(int)
dates['Month Start']=dt.to_period('M').dt.to_timestamp(); dates['Day']=dt.day
dates['Is Complete Sales Month']=((dates['Month Start']>o.created_at.min().to_period('M').start_time)&(dates['Month Start']<o.created_at.max().to_period('M').start_time)).astype(int)
dates['Is In Sales Coverage']=((dates.Date>=o.created_at.min().normalize())&(dates.Date<=o.created_at.max().normalize())).astype(int)
rename_o={'order_id':'Order ID','website_session_id':'Website Session ID','primary_product_id':'Primary Product ID','items_purchased':'Items Purchased','price_usd':'Sales Amount','cogs_usd':'COGS Amount'}
rename_i={'order_item_id':'Order Item ID','order_id':'Order ID','product_id':'Product ID','price_usd':'Item Sales Amount','cogs_usd':'Item COGS Amount'}
rename_r={'order_item_refund_id':'Refund ID','order_item_id':'Order Item ID','order_id':'Order ID','product_id':'Product ID','refund_amount_usd':'Refund Amount'}
facts={
 'Fact_Orders':orders.rename(columns=rename_o)[list(rename_o.values())+['Order Date','Customer ID','Channel ID','Device','Visitor Type','Landing Page','Purchase Number','Purchase Type','Basket','Has Cross Sell','Purchase Age Month']],
 'Fact_OrderItems':items.rename(columns=rename_i)[list(rename_i.values())+['Order Date','Customer ID','Channel ID','Device','Visitor Type','Landing Page','Item Role','Recorded Refund','Refunded Item','Launch Age Month']],
 'Fact_Refunds':refunds.rename(columns=rename_r)[list(rename_r.values())+['Refund Date','Order Date','Customer ID','Channel ID','Device','Visitor Type','Landing Page','Refund Lag Days']],
 'Fact_Sessions':sf[['Website Session ID','Customer ID','Session Date','Channel ID','Device','Visitor Type','Landing Page','Pageviews','Bounced','Converted','Session Orders','Session Revenue']+['Reach '+x for x in stage_urls]+['Sequential '+x for x in ['Product','Cart','Shipping','Billing','Purchase']]].reset_index(drop=True),
 'Dim_Product':p.rename(columns={'product_id':'Product ID','product_name':'Product','created_at':'Launch Date'}),
 'Dim_Date':dates,'Dim_Customer':customers,
 'Dim_Channel':channels.rename(columns={'utm_campaign':'Campaign','utm_content':'Ad Content','http_referer':'Referrer'}),
 'Dim_Device':pd.DataFrame({'Device':sorted(sf.Device.unique())}),
 'Dim_Visitor':pd.DataFrame({'Visitor Type':sorted(sf['Visitor Type'].unique())}),
 'Dim_Landing':pd.DataFrame({'Landing Page':sorted(sf['Landing Page'].unique())}),
 'Dim_FunnelStage':pd.DataFrame({'Stage':['Landing','Product','Cart','Shipping','Billing','Purchase'],'Stage Order':range(1,7)}),
 'Dim_CohortAge':pd.DataFrame({'Month After First Purchase':range(37)}),
}
schema={}
for n,d in facts.items():
    d.to_csv(DATA/(n+'.csv'),index=False,date_format='%Y-%m-%d')
    schema[n]=[{'name':c,'type':('dateTime' if pd.api.types.is_datetime64_any_dtype(d[c]) else 'int64' if pd.api.types.is_integer_dtype(d[c]) else 'decimal' if pd.api.types.is_float_dtype(d[c]) else 'string')} for c in d]
(QA/'prepared_schema.json').write_text(json.dumps(schema,indent=2))
(QA/'source_manifest.json').write_text(json.dumps(manifest,indent=2))
pd.DataFrame(profiles).to_csv(QA/'column_profile.csv',index=False)
pd.DataFrame(checks).to_csv(QA/'data_checks.csv',index=False)
v.pageview_url.value_counts().rename_axis('Page URL').reset_index(name='Pageviews').to_csv(QA/'page_url_inventory.csv',index=False)
summary={
 'orders':len(o),'items':len(i),'sessions':len(s),'pageviews':len(v),'refund_events':len(r),'products':len(p),
 'sales':int(cents(o.price_usd).sum())/100,'cogs':int(cents(o.cogs_usd).sum())/100,'refunds':int(cents(r.refund_amount_usd).sum())/100,
 'gross_profit':int((cents(o.price_usd)-cents(o.cogs_usd)).sum())/100,
 'users':int(s.user_id.nunique()),'buyers':int(o.user_id.nunique()),'converted_sessions':int(sf.Converted.sum()),
 'new_sessions':int(sf.is_repeat_session.eq(0).sum()),'repeat_sessions':int(sf.is_repeat_session.eq(1).sum()),'bounced':int(sf.Bounced.sum()),
 'cross_sell_orders':int(orders['Has Cross Sell'].sum()),'repeat_buyers':int((customers['Observed Lifetime Orders']>=2).sum()),
 'funnel':dict(zip(['Landing','Product','Cart','Shipping','Billing','Purchase'],funnel_counts)),
 'source_start':str(s.created_at.min()),'source_end':str(s.created_at.max()),'order_end':str(o.created_at.max()),'refund_end':str(r.created_at.max()),
 'failing_checks':[x for x in checks if x['status']!='PASS']
}
summary['net_revenue']=summary['sales']-summary['refunds']; summary['gross_margin']=summary['gross_profit']/summary['sales']
summary['aov']=summary['sales']/summary['orders']; summary['conversion']=summary['converted_sessions']/summary['sessions']
(QA/'baseline.json').write_text(json.dumps(summary,indent=2))
monthly=o.assign(Month=o.created_at.dt.strftime('%Y-%m')).groupby('Month').agg(Revenue=('price_usd','sum'),COGS=('cogs_usd','sum'),Orders=('order_id','size'))
monthly['Gross Profit']=monthly.Revenue-monthly.COGS; monthly['AOV']=monthly.Revenue/monthly.Orders
monthly['MoM']=monthly.Revenue.pct_change(); monthly['YoY']=monthly.Revenue.pct_change(12)
monthly.to_csv(QA/'monthly_baseline.csv')
product=items.groupby('product_id').agg(Revenue=('price_usd','sum'),COGS=('cogs_usd','sum'),Units=('order_item_id','size'),Refunded=('Refunded Item','sum'),Refunds=('Recorded Refund','sum')).join(p.set_index('product_id').product_name)
product.to_csv(QA/'product_baseline.csv')
sf.groupby('Device').agg(Sessions=('Website Session ID','size'),Converted=('Converted','sum'),Revenue=('Session Revenue','sum')).to_csv(QA/'device_baseline.csv')
sf.groupby('Traffic Group').agg(Sessions=('Website Session ID','size'),Converted=('Converted','sum'),Revenue=('Session Revenue','sum')).to_csv(QA/'channel_baseline.csv')
sf.groupby('Landing Page').agg(Sessions=('Website Session ID','size'),Converted=('Converted','sum'),Bounced=('Bounced','sum')).to_csv(QA/'landing_baseline.csv')
orders.groupby('Basket').agg(Orders=('order_id','size'),Revenue=('price_usd','sum')).sort_values('Orders',ascending=False).to_csv(QA/'basket_baseline.csv')
pd.DataFrame([{'Stage':stage,'Any reach':int(sf['Reach '+stage].sum()),'Sequential':int(sf['Sequential '+stage].sum())} for stage in ['Product','Cart','Shipping','Billing']]).to_csv(QA/'funnel_audit.csv',index=False)
report=['# Initial dataset discovery','', 'Source: the seven user-supplied CSV files in `../Dataset`; originals retained unchanged.','', '| Table | Rows | First timestamp | Last timestamp |','|---|---:|---|---|']
report += [f"| {x['file']} | {x['rows']:,} | {x['min_date']} | {x['max_date']} |" for x in manifest]
report += ['',f"Checks: {len(checks)} executed; {sum(x['status']=='PASS' for x in checks)} passed.", '', 'See `qa/column_profile.csv` for every actual source column, null count, distinct count and inferred type; `qa/source_manifest.json` records immutable SHA-256 fingerprints.', '', '## Modeling decisions','', '- Facts retain their native grain. Orders and items reconcile in cents before enrichment. No raw pageview-to-order joins.', '- Pageviews are reduced to one session row with distinct reach flags and strict ordered funnel flags. Raw pageviews remain in the source folder.', '- Product means listing or one of the four observed detail URLs. Billing combines /billing and /billing-2. Purchase requires a later confirmation page plus a linked order at/after billing.', '- The (timestamp, pageview ID) pair provides deterministic ordering for tied timestamps; repeated views count once per stage.', '- Sessions and session-attributed revenue use session date. Sales use order date. Refund cash flow uses refund date; item refund incidence uses original sale date.', '- Traffic labels describe observed tagging/referrers. Tagged traffic is not asserted to be paid; untagged search is a referral proxy, not verified organic traffic.', '- Full calendar years are loaded. March 2012 and March 2015 are partial observation months; complete-month comparisons exclude them.', '- Customer identifiers are observed website user IDs, not verified people or merged identities. First purchase/cohort means first observed purchase.', '', '## Exceptions', '', json.dumps(summary['failing_checks'],indent=2)]
(DOC/'01-dataset-discovery.md').write_text('\n'.join(report),encoding='utf-8')
print(json.dumps(summary,indent=2))
print('Prepared tables:',{n:len(d) for n,d in facts.items()})
