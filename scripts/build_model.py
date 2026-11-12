"""Author a complete TOM-compatible BIM for import/export through Power BI Modeling MCP."""
from pathlib import Path
import json,uuid,csv
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'Maven Fuzzy Factory'; QA=OUT/'qa'; PB=OUT/'powerbi'; SM=PB/'Maven Fuzzy Factory.SemanticModel'
SM.mkdir(exist_ok=True)
schema=json.loads((QA/'prepared_schema.json').read_text())
def uid(): return str(uuid.uuid4())
INT='#,##0'; USD='$#,##0.00;($#,##0.00);$0.00'; PCT='0.0%;(0.0%);0.0%'; DEC='0.00'
measures=[]
def add(name,expression,description,folder,fmt=INT):
    measures.append(dict(name=name,expression=expression,description=description,formatString=fmt,displayFolder=folder,lineageTag=uid()))

add('Gross Sales Revenue',"SUM('Fact_Orders'[Sales Amount])",'Recorded order sales in USD, filtered by order date and conformed dimensions. Before recorded refunds; product selections apply to product measures instead.','01 Financial',USD)
add('COGS',"SUM('Fact_Orders'[COGS Amount])",'Recorded cost of goods sold from orders, in USD. No refund-related COGS recovery is assumed.','01 Financial',USD)
add('Gross Profit','[Gross Sales Revenue] - [COGS]','Recorded sales less recorded COGS. Gross profit before refunds, operating costs, tax, shipping costs and advertising expense; not net profit.','01 Financial',USD)
add('Gross Margin %','DIVIDE([Gross Profit], [Gross Sales Revenue])','Gross profit divided by recorded sales; blank when sales are zero.','01 Financial',PCT)
add('Total Orders',"COUNTROWS('Fact_Orders')",'Number of orders at native order grain, by order date. Does not multiply with items or pageviews.','01 Financial')
add('Average Order Value','DIVIDE([Gross Sales Revenue], [Total Orders])','Recorded sales divided by orders in the selected order-date period; before refunds.','01 Financial',USD)
add('Average Items Per Order',"DIVIDE(SUM('Fact_Orders'[Items Purchased]), [Total Orders])",'Recorded item count from orders divided by native order count.','01 Financial',DEC)
add('Total Refund Amount',"SUM('Fact_Refunds'[Refund Amount])",'Recorded refund events in USD, selected by refund event date. This is cash-flow timing, not the original sale cohort.','07 Refunds',USD)
add('Net Revenue After Recorded Refunds','[Product Revenue] - [Total Refund Amount]','Item sales on order dates less refund events on refund dates within the selected period. Both sides share sold-product scope. Item sales reconcile to order sales when no product is selected. This is period flow, not a restated sale cohort.','01 Financial',USD)
add('Gross Profit After Refunds (No Recovery)','[Product Gross Profit] - [Total Refund Amount]','Item-level gross profit less recorded refunds with matching product scope, assuming no COGS recovery. Reconciles to order-level gross profit less refunds without product filters. Excludes operating costs; not net profit.','01 Financial',USD)
add('Refund Amount %','DIVIDE([Total Refund Amount], [Product Revenue])','Refund event dollars divided by same-period item sales dollars with matching product scope. Item sales reconcile to orders. Event dates differ from sale dates; can exceed 100% in a narrow refund-heavy period.','07 Refunds',PCT)
add('Refund Events',"COUNTROWS('Fact_Refunds')",'Count of recorded refund events by refund date; distinct from refunded items or refunded orders.','07 Refunds')
add('Refunded Orders (Event Date)',"DISTINCTCOUNT('Fact_Refunds'[Order ID])",'Orders with at least one refund event in the selected refund-date period.','07 Refunds')
add('Average Refund Lag Days',"AVERAGE('Fact_Refunds'[Refund Lag Days])",'Mean calendar days from original order date to recorded refund event date for selected refund events.','07 Refunds',DEC)
add('Recorded Refunds On Selected Sales',"SUM('Fact_OrderItems'[Recorded Refund])",'All recorded refunds attached to items sold in the selected order-date period, observed through the refund-file cutoff. Recent sales have shorter follow-up.','07 Refunds',USD)
add('Refunded Items (Sale Cohort)',"SUM('Fact_OrderItems'[Refunded Item])",'Number of sold items with any recorded refund through the source cutoff, filtered by original sale date. Each item counts at most once.','07 Refunds')
add('Product Refund Rate','DIVIDE([Refunded Items (Sale Cohort)], [Units Sold])','Refunded sold items divided by units sold in the original sale cohort. Right-censored at the refund cutoff; compare equally mature cohorts.','07 Refunds',PCT)
add('Sale Cohort Refund Amount %','DIVIDE([Recorded Refunds On Selected Sales], [Product Revenue])','Recorded refund dollars on the selected sold-item cohort divided by that cohort’s item sales dollars. Not refund event-date cash flow.','07 Refunds',PCT)

add('Total Sessions',"COUNTROWS('Fact_Sessions')",'Count of distinct native session rows by session start date. One row per source website session.','02 Website')
add('Unique Website Visitors',"DISTINCTCOUNT('Fact_Sessions'[Customer ID])",'Distinct observed website user IDs active in the selected session-date period. IDs are not verified people or identity-resolved customers.','02 Website')
add('New Visitor Sessions',"CALCULATE([Total Sessions], KEEPFILTERS('Dim_Visitor'[Visitor Type] = \"New visitor session\"))",'Sessions with source is_repeat_session = 0. Source flag is preserved; no invented visitor identity logic.','02 Website')
add('Repeat Visitor Sessions',"CALCULATE([Total Sessions], KEEPFILTERS('Dim_Visitor'[Visitor Type] = \"Repeat visitor session\"))",'Sessions with source is_repeat_session = 1; this does not imply a prior purchase.','02 Website')
add('Converted Sessions',"SUM('Fact_Sessions'[Converted])",'Sessions with at least one linked recorded order, attributed to session start date. Multiple orders would still count once.','02 Website')
add('Session-to-Order Conversion Rate','DIVIDE([Converted Sessions], [Total Sessions])','Converted sessions / total sessions, with both numerator and denominator on session date. This is not a ratio of order-date orders to session-date sessions.','02 Website',PCT)
add('Campaign Orders',"SUM('Fact_Sessions'[Session Orders])",'Linked recorded order count attributed to the acquiring session’s date, channel and campaign. May differ from order-date counts near midnight.','03 Marketing')
add('Campaign Revenue',"SUM('Fact_Sessions'[Session Revenue])",'Recorded linked order sales attributed to the acquiring session’s start date and tagging. Revenue is grouped to one session before enrichment.','03 Marketing',USD)
add('Revenue Per Session','DIVIDE([Campaign Revenue], [Total Sessions])','Session-attributed recorded sales / sessions in the same session-date context, in USD.','03 Marketing',USD)
add('Traffic Source Contribution',"DIVIDE([Total Sessions], CALCULATE([Total Sessions], REMOVEFILTERS('Dim_Channel')))",'Sessions for the current traffic selection divided by sessions across all channels; other conformed filters retained.','03 Marketing',PCT)
add('Revenue Per Tagged Marketing Session',"VAR _revenue = CALCULATE([Campaign Revenue], KEEPFILTERS('Dim_Channel'[Traffic Group] IN {\"Tagged search\", \"Tagged social\"}))\nVAR _sessions = CALCULATE([Total Sessions], KEEPFILTERS('Dim_Channel'[Traffic Group] IN {\"Tagged search\", \"Tagged social\"}))\nRETURN DIVIDE(_revenue, _sessions)",'Revenue per session restricted to observed tagged search/social traffic. Tagging is not proof of paid acquisition.','03 Marketing',USD)
add('Desktop Conversion',"CALCULATE([Session-to-Order Conversion Rate], KEEPFILTERS('Dim_Device'[Device] = \"desktop\"))",'Converted desktop sessions / desktop sessions on session date. Blank if an incompatible device filter is active.','03 Marketing',PCT)
add('Mobile Conversion',"CALCULATE([Session-to-Order Conversion Rate], KEEPFILTERS('Dim_Device'[Device] = \"mobile\"))",'Converted mobile sessions / mobile sessions on session date. Blank if an incompatible device filter is active.','03 Marketing',PCT)
add('Bounced Sessions',"SUM('Fact_Sessions'[Bounced])",'Sessions with exactly one recorded pageview. This is a pageview-count bounce definition; engagement time is unavailable.','02 Website')
add('Landing Page Bounce Rate','DIVIDE([Bounced Sessions], [Total Sessions])','Sessions with exactly one recorded pageview divided by all sessions, grouped by the earliest (timestamp, pageview ID) URL. No engagement threshold is available.','02 Website',PCT)
add('Total Pageviews',"SUM('Fact_Sessions'[Pageviews])",'Total source pageviews from per-session aggregation, filtered by session start date rather than individual pageview dates.','02 Website')
for stage in ['Product','Cart','Shipping','Billing']:
    add(stage+' Reach Sessions',f"SUM('Fact_Sessions'[Reach {stage}])",f'Sessions with any observed {stage.lower()} stage URL. Repeat views count once; this measure does not impose prior-stage ordering.','04 Funnel')
    add(stage+' Page Reach Rate' if stage=='Product' else stage+' Reach Rate',f'DIVIDE([{stage} Reach Sessions], [Total Sessions])',f'Any-reach {stage.lower()} sessions / all sessions. For ordered progression use the sequential funnel measures.','04 Funnel',PCT)
for stage in ['Product','Cart','Shipping','Billing','Purchase']:
    add('Sequential '+stage+' Sessions',f"SUM('Fact_Sessions'[Sequential {stage}])",f'Sessions completing every stage through {stage.lower()} in strict (timestamp, pageview ID) order. Purchase additionally requires a linked order at/after billing. Count once per session.','04 Funnel')
add('Checkout Reach Rate','DIVIDE([Shipping Reach Sessions], [Total Sessions])','Sessions reaching /shipping at any point divided by sessions. Shipping is the first observed checkout step.','04 Funnel',PCT)
add('Purchase Completion Rate','DIVIDE([Sequential Purchase Sessions], [Sequential Billing Sessions])','Strict sequential purchases divided by strict sequential billing sessions. Both use the session-start cohort.','04 Funnel',PCT)
add('Stage Sessions',"// Disconnected stage axis selects distinct session flags; never count pageview rows.\nVAR _stage = SELECTEDVALUE('Dim_FunnelStage'[Stage Order])\nRETURN SWITCH(_stage, 1, [Total Sessions], 2, [Sequential Product Sessions], 3, [Sequential Cart Sessions], 4, [Sequential Shipping Sessions], 5, [Sequential Billing Sessions], 6, [Sequential Purchase Sessions])",'Distinct sessions completing every stage up to the selected ordered stage. Blank for a total spanning multiple stages.','04 Funnel')
add('Previous Stage Sessions',"VAR _stage = SELECTEDVALUE('Dim_FunnelStage'[Stage Order])\nRETURN SWITCH(_stage, 1, [Total Sessions], 2, [Total Sessions], 3, [Sequential Product Sessions], 4, [Sequential Cart Sessions], 5, [Sequential Shipping Sessions], 6, [Sequential Billing Sessions])",'Distinct sessions at the preceding sequential stage; landing uses all sessions as its baseline.','04 Funnel')
add('Stage Conversion %','DIVIDE([Stage Sessions], [Previous Stage Sessions])','Current ordered stage sessions / previous stage sessions. Landing is 100% when sessions exist.','04 Funnel',PCT)
add('Stage Reach %','DIVIDE([Stage Sessions], [Total Sessions])','Current ordered stage sessions / all selected sessions.','04 Funnel',PCT)
add('Funnel Abandonment Sessions','[Previous Stage Sessions] - [Stage Sessions]','Previous-stage sessions less current-stage sessions. These are observed stage drop-offs, not inferred causes.','04 Funnel')
add('Funnel Abandonment %','DIVIDE([Funnel Abandonment Sessions], [Previous Stage Sessions])','Drop-off sessions / preceding ordered-stage sessions; zero at landing.','04 Funnel',PCT)

add('Product Revenue',"SUM('Fact_OrderItems'[Item Sales Amount])",'Recorded item sales by product and original order date. Additive across sold products; includes primary and cross-sell items.','05 Product',USD)
add('Product COGS',"SUM('Fact_OrderItems'[Item COGS Amount])",'Recorded item-level cost by product and original order date, before any assumed recovery.','05 Product',USD)
add('Product Gross Profit','[Product Revenue] - [Product COGS]','Item sales less item COGS; product-level estimated gross profit before refunds and operating costs.','05 Product',USD)
add('Product Margin %','DIVIDE([Product Gross Profit], [Product Revenue])','Product gross profit / recorded product revenue.','05 Product',PCT)
add('Units Sold',"COUNTROWS('Fact_OrderItems')",'Native item row count. Source has no item-quantity column; each row is one sold item, reconciled to order item counts.','05 Product')
add('Product Revenue Contribution %',"DIVIDE([Product Revenue], CALCULATE([Product Revenue], REMOVEFILTERS('Dim_Product')))",'Current product revenue divided by revenue across all products, retaining date and acquisition filters.','05 Product',PCT)
add('Orders Containing Selected Product',"DISTINCTCOUNT('Fact_OrderItems'[Order ID])",'Distinct orders containing selected sold items. Totals are distinct orders, not sum of product order counts.','05 Product')
add('Primary Item Revenue',"CALCULATE([Product Revenue], KEEPFILTERS('Fact_OrderItems'[Item Role] = \"Primary item\"))",'Revenue from items with source is_primary_item = 1, by item product; not whole basket revenue.','05 Product',USD)
add('Cross-Sell Revenue',"CALCULATE([Product Revenue], KEEPFILTERS('Fact_OrderItems'[Item Role] = \"Cross-sell item\"))",'Revenue from items with source is_primary_item = 0.','05 Product',USD)
add('Cross-Sell Units',"CALCULATE([Units Sold], KEEPFILTERS('Fact_OrderItems'[Item Role] = \"Cross-sell item\"))",'Sold item rows designated non-primary by the source.','05 Product')
add('Orders With Cross Sell',"SUM('Fact_Orders'[Has Cross Sell])",'Orders with more than one recorded item. This is a basket-level count on order date.','05 Product')
add('Cross-Sell Attach Rate','DIVIDE([Orders With Cross Sell], [Total Orders])','Orders containing more than one item / orders. Does not imply a causal recommendation effect.','05 Product',PCT)

add('Paying Customers',"DISTINCTCOUNT('Fact_Orders'[Customer ID])",'Distinct observed user IDs placing an order in the selected order-date period; separate from all website visitors.','06 Customers')
add('Repeat Purchasing Customers',"COUNTROWS(FILTER(VALUES('Fact_Orders'[Customer ID]), CALCULATE(COUNTROWS('Fact_Orders')) >= 2))",'Observed user IDs with at least two orders within the current order-date and acquisition filters. This is period purchase frequency, not a lifetime flag.','06 Customers')
add('Repeat Purchasing Customer %','DIVIDE([Repeat Purchasing Customers], [Paying Customers])','Customers with at least two selected-period orders divided by customers with any selected-period order.','06 Customers',PCT)
add('Orders Per Paying Customer','DIVIDE([Total Orders], [Paying Customers])','Selected-period orders / distinct paying user IDs.','06 Customers',DEC)
add('Revenue Per Paying Customer','DIVIDE([Gross Sales Revenue], [Paying Customers])','Selected-period recorded order sales / paying user IDs.','06 Customers',USD)
add('Subsequent Purchase Orders',"CALCULATE([Total Orders], KEEPFILTERS('Fact_Orders'[Purchase Type] = \"Subsequent purchase\"))",'Orders whose user already placed a prior observed order in the complete extract. Classification is fixed at preparation, not reset by date slicers.','06 Customers')
add('Subsequent Purchase Revenue',"CALCULATE([Gross Sales Revenue], KEEPFILTERS('Fact_Orders'[Purchase Type] = \"Subsequent purchase\"))",'Recorded sales from subsequent observed purchases, by order date. Left-censored before the extract begins.','06 Customers',USD)
add('Repeat Visitor Session Share','DIVIDE([Repeat Visitor Sessions], [Total Sessions])','Source repeat-visitor sessions / all sessions; visitor recurrence is not buyer recurrence.','06 Customers',PCT)
add('Cohort Customers',"CALCULATE(COUNTROWS('Dim_Customer'), KEEPFILTERS('Dim_Customer'[First Purchase Date] <> BLANK()))",'All observed first-purchase customers in the selected cohort. Cohort analysis ignores the report date slicer and retains its fixed original customer cohort.','06 Customers')
add('Cohort Active Customers',"// Hide cells without a complete observation month to avoid future zero retention.\nVAR _age = SELECTEDVALUE('Dim_CohortAge'[Month After First Purchase])\nVAR _cohort = SELECTEDVALUE('Dim_Customer'[Purchase Cohort])\nVAR _start = IF(_cohort <> \"No observed purchase\" && NOT ISBLANK(_cohort), DATE(VALUE(LEFT(_cohort,4)), VALUE(RIGHT(_cohort,2)), 1))\nVAR _mature = NOT ISBLANK(_start) && EOMONTH(_start, _age) < DATE(2015,3,19)\nRETURN IF(NOT ISBLANK(_age) && _mature, COALESCE(CALCULATE(DISTINCTCOUNT('Fact_Orders'[Customer ID]), REMOVEFILTERS('Dim_Date'), REMOVEFILTERS('Dim_Channel'), REMOVEFILTERS('Dim_Device'), REMOVEFILTERS('Dim_Visitor'), REMOVEFILTERS('Dim_Landing'), 'Fact_Orders'[Purchase Age Month] = _age),0))",'Distinct customers purchasing at selected months since first observed purchase. Calendar-month cohorts; date and acquisition slicers deliberately ignored to preserve the original customer cohort denominator. Incomplete/future cohort-month cells are blank.','06 Customers')
add('Cohort Retention %',"IF(NOT ISBLANK([Cohort Active Customers]), DIVIDE([Cohort Active Customers], [Cohort Customers]))",'Active customers / original first-purchase cohort size at selected month age. Month zero is the acquisition month. Blank until a full month is observed; no inference about churn.','06 Customers',PCT)

for label,unit in [('MoM','MONTH'),('YoY','YEAR')]:
    offset=1 if label=='MoM' else 12
    add(label+' Revenue Growth',f'''// Compare complete calendar months only; exclude partial edge months.
VAR _month = SELECTEDVALUE('Dim_Date'[Month Start])
VAR _priorMonth = EDATE(_month, -{offset})
VAR _ok = HASONEVALUE('Dim_Date'[Month Start]) && _month >= DATE(2012,4,1) && _month <= DATE(2015,2,1) && _priorMonth >= DATE(2012,4,1)
VAR _current = CALCULATE([Gross Sales Revenue], REMOVEFILTERS('Dim_Date'), DATESBETWEEN('Dim_Date'[Date], _month, EOMONTH(_month,0)))
VAR _prior = CALCULATE([Gross Sales Revenue], REMOVEFILTERS('Dim_Date'), DATESBETWEEN('Dim_Date'[Date], _priorMonth, EOMONTH(_priorMonth,0)))
RETURN IF(_ok, DIVIDE(_current - _prior, _prior))''',f'Full-calendar-month revenue change against the {"preceding month" if offset==1 else "same month last year"}. Requires one month and complete current/prior coverage; daily slice is expanded to full months. Partial extract boundary months are blank.','08 Comparisons',PCT)
add('Revenue Growth %',"// Compare only contiguous windows of fully observed interior calendar days.\nVAR _from = MIN('Dim_Date'[Date])\nVAR _to = MAX('Dim_Date'[Date])\nVAR _days = DATEDIFF(_from, _to, DAY) + 1\nVAR _priorFrom = _from - _days\nVAR _priorTo = _from - 1\nVAR _contiguous = COUNTROWS(VALUES('Dim_Date'[Date])) = _days\nVAR _valid = _contiguous && _from >= DATE(2012,3,20) && _to <= DATE(2015,3,18) && _priorFrom >= DATE(2012,3,20)\nVAR _prior = CALCULATE([Gross Sales Revenue], REMOVEFILTERS('Dim_Date'), DATESBETWEEN('Dim_Date'[Date], _priorFrom, _priorTo))\nRETURN IF(_valid, DIVIDE([Gross Sales Revenue] - _prior, _prior))",'Change vs the same-length immediately preceding calendar-day window. Requires contiguous selected dates and fully observed interior days (2012-03-20 through 2015-03-18); source boundary days are partial. Separate from complete-month MoM/YoY.','08 Comparisons',PCT)
add('Selected Period Label',"VAR _min = MIN('Dim_Date'[Date])\nVAR _max = MAX('Dim_Date'[Date])\nRETURN FORMAT(_min, \"dd MMM yyyy\") & \" – \" & FORMAT(_max, \"dd MMM yyyy\")",'Dynamic selected calendar range. The underlying data coverage is separately disclosed.','09 Report UX','@')
add('Data Coverage Note','"Sales/sessions: 19 Mar 2012–19 Mar 2015 | Refunds: through 01 Apr 2015 | USD"','Observed source bounds, not a claim of current data freshness.','09 Report UX','@')
add('Revenue Trend Title','"Recorded sales · " & [Selected Period Label]','Dynamic chart title showing the selected calendar range.','09 Report UX','@')
add('Conversion Chart Title','"Session conversion · " & [Selected Period Label]','Dynamic conversion chart title with selected calendar dates.','09 Report UX','@')
add('Growth Color',"IF(ISBLANK([MoM Revenue Growth]), \"#526074\", IF([MoM Revenue Growth]>=0, \"#087F80\", \"#A36512\"))",'Semantic formatting color for full-month MoM growth; blank comparison uses neutral text.','09 Report UX','@')
add('Refund Risk Color',"IF(ISBLANK([Product Refund Rate]), \"#526074\", IF([Product Refund Rate] > CALCULATE([Product Refund Rate], REMOVEFILTERS('Dim_Product')), \"#A36512\", \"#087F80\"))",'Amber when product sale-cohort refund incidence exceeds the all-product incidence under the same remaining filters; descriptive comparison, not a risk threshold.','09 Report UX','@')
add('Executive Decision Note',"IF(ISBLANK([Gross Sales Revenue]), \"No recorded sales in the selected context. Adjust the date or acquisition filters.\", \"Recorded sales are \" & FORMAT([Gross Sales Revenue], \"$#,##0\") & \" at \" & FORMAT([Gross Margin %], \"0.0%\") & \" gross margin before refunds and operating expenses. Selected sessions convert at \" & FORMAT([Session-to-Order Conversion Rate], \"0.0%\") & \". Compare acquisition efficiency on the Marketing page and journey losses on Conversion.\")",'Filter-responsive executive narrative; reports observed values without inferring causes.','09 Report UX','@')

# Metadata and Power Query partitions. Prepared facts preserve source monetary values.
grains={'Fact_Orders':'One row per recorded order. Financial measures use this grain; no fact-to-fact relationships.','Fact_OrderItems':'One row per recorded sold item; one item per source row. Refund linkage is aggregated per item before enrichment.','Fact_Refunds':'One row per recorded refund event. Product and acquisition attributes are many-to-one lookups.','Fact_Sessions':'One row per source session with ordered journey flags and one-to-one linked order aggregates. Optimizes raw pageviews.'}
visible_num={'Year','Month Number','Week','ISO Year','Day','Stage Order','Month After First Purchase','Launch Age Month','Purchase Age Month','Observed Lifetime Orders'}
hide_cols={'First Session Date','First Purchase Date'}
tables=[]
for n,cols in schema.items():
    data_types=[]; columns=[]
    for c in cols:
        name=c['name']; typ=c['type']; mtype={'int64':'Int64.Type','decimal':'Currency.Type','dateTime':'type date','string':'type text'}[typ]
        data_types.append('{'+json.dumps(name)+', '+mtype+'}')
        col=dict(name=name,dataType=typ,sourceColumn=name,summarizeBy='none',lineageTag=uid(),description=f'{name} at {n} grain. See docs/03-data-dictionary.csv for source lineage and meaning.')
        if typ in ['int64','decimal'] and name not in visible_num: col['isHidden']=True
        if name.endswith(' ID') or name in hide_cols or (n.startswith('Fact_') and name.endswith(' Date')): col['isHidden']=True
        if typ=='decimal': col['formatString']=USD
        if typ=='dateTime': col['formatString']='dd MMM yyyy'
        if n=='Dim_Date' and name=='Date': col.update(isKey=True,dataCategory='Date')
        sort={'Month':'Month Number','Year-Month':'Year Month Sort','Quarter':None,'Stage':'Stage Order'}.get(name)
        if sort: col['sortByColumn']=sort
        columns.append(col)
    m='''let
    Raw = Csv.Document(File.Contents(PreparedFolder & "\\%s.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Raw, [PromoteAllScalars=true]),
    Typed = Table.TransformColumnTypes(Headers, {%s}, "en-US")
in
    Typed'''%(n,', '.join(data_types))
    table=dict(name=n,description=grains.get(n,f'Conformed dimension: {n}. Disconnected utility only for FunnelStage and CohortAge.'),columns=columns,partitions=[dict(name=n,mode='import',source=dict(type='m',expression=m))],lineageTag=uid())
    if n=='Dim_Date':
        table['dataCategory']='Time'
        table['hierarchies']=[dict(name='Calendar',levels=[dict(name=a,ordinal=k,column=a) for k,a in enumerate(['Year','Quarter','Month','Date'])])]
    tables.append(table)
tables.append(dict(name='_Measures',description='Dedicated organized business measures. Financial, session, product and refund date semantics are documented per measure.',columns=[dict(name='Label',dataType='string',sourceColumn='Label',isHidden=True)],partitions=[dict(name='_Measures',mode='import',source=dict(type='m',expression='#table(type table [Label = text], {{"Business measures"}})'))],measures=measures,lineageTag=uid()))
relationships=[]
def rel(ft,fc,dt,dc,active=True): relationships.append(dict(name=uid(),fromTable=ft,fromColumn=fc,toTable=dt,toColumn=dc,fromCardinality='many',toCardinality='one',crossFilteringBehavior='oneDirection',isActive=active))
for n in ['Fact_Orders','Fact_OrderItems','Fact_Refunds','Fact_Sessions']:
    rel(n,{'Fact_Sessions':'Session Date','Fact_Refunds':'Refund Date'}.get(n,'Order Date'),'Dim_Date','Date')
    for dt,c in [('Dim_Customer','Customer ID'),('Dim_Channel','Channel ID'),('Dim_Device','Device'),('Dim_Visitor','Visitor Type'),('Dim_Landing','Landing Page')]: rel(n,c,dt,c)
for n in ['Fact_OrderItems','Fact_Refunds']: rel(n,'Product ID','Dim_Product','Product ID')
prepared_parameter='"'+str(OUT/'data'/'prepared').replace('"','""')+'" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'
model=dict(name='Maven Fuzzy Factory',id='Maven Fuzzy Factory',compatibilityLevel=1702,model=dict(culture='en-US',sourceQueryCulture='en-US',defaultPowerBIDataSourceVersion='powerBI_V3',discourageImplicitMeasures=True,annotations=[dict(name='__PBI_TimeIntelligenceEnabled',value='0')],expressions=[dict(name='PreparedFolder',kind='m',expression=prepared_parameter,description='Folder containing deterministic derived CSVs created from the unchanged supplied sources.')],tables=tables,relationships=relationships))
(QA/'model.bim').write_text(json.dumps(model,indent=2),encoding='utf-8')
(SM/'definition.pbism').write_text(json.dumps({'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json','version':'4.2','settings':{'qnaEnabled':False}},indent=2))
(SM/'.platform').write_text(json.dumps({'$schema':'https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json','metadata':{'type':'SemanticModel','displayName':'Maven Fuzzy Factory'},'config':{'version':'2.0','logicalId':uid()}},indent=2))
(QA/'measure_catalog.json').write_text(json.dumps(measures,indent=2),encoding='utf-8')
with (OUT/'docs'/'04-kpi-reference.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=['name','displayFolder','description','expression','formatString']); w.writeheader(); w.writerows({k:m[k] for k in w.fieldnames} for m in measures)
(OUT/'docs'/'04-measures.dax').write_text('\n\n'.join('// '+m['description']+'\nMEASURE \'_Measures\'['+m['name']+'] =\n'+m['expression'] for m in measures),encoding='utf-8')
(QA/'model_contract.json').write_text(json.dumps({'tables':len(tables),'measures':len(measures),'relationships':len(relationships),'relationships_detail':relationships},indent=2))
print(f'Authored {len(tables)} tables, {len(measures)} measures, {len(relationships)} single-direction relationships.')
