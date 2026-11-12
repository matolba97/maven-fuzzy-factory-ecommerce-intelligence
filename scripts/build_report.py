"""Build native data-bound PBIR pages. No screenshot or chart is simulated."""
from pathlib import Path
import json,uuid,math,urllib.request,hashlib
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'Maven Fuzzy Factory'; PB=OUT/'powerbi'; REPORT=PB/'Maven Fuzzy Factory.Report'; DEF=REPORT/'definition'; QA=OUT/'qa'
catalog=json.loads((QA/'measure_catalog.json').read_text()); measures={m['name']:m for m in catalog}
C={'canvas':'#F6F5F1','surface':'#FFFFFF','text':'#172337','muted':'#526074','border':'#DFE3E8','revenue':'#4F46A5','profit':'#087F80','refund':'#A36512','lavender':'#EDEAF8','teal':'#E3F2EF'}
def dump(p,o): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(o,indent=2,ensure_ascii=False),encoding='utf-8')
def nid(s): return hashlib.sha256(s.encode()).hexdigest()[:20]
def lit(x):
    if isinstance(x,bool): val='true' if x else 'false'
    elif isinstance(x,(float,int)): val=str(x)+'D'
    else: val="'"+str(x).replace("'","''")+"'"
    return {'expr':{'Literal':{'Value':val}}}
def fill(x): return {'solid':{'color':lit(x)}}
def obj(props,selector=None):
    d={'properties':props}
    if selector is not None: d['selector']={'id':selector}
    return d
def field(t,n): return {'Measure' if t=='_Measures' else 'Column':{'Expression':{'SourceRef':{'Entity':t}},'Property':n}}
def proj(t,n,label=None):
    return {'field':field(t,n),'queryRef':t+'.'+n,'nativeQueryRef':label or n,'displayName':label or n}
def meas(n,label=None): return proj('_Measures',n,label)
def cf_measure(n): return {'expr':field('_Measures',n)}
visuals={}; pages=[]; manifest=[]
names=['Executive Command Center','Revenue & Profitability','Marketing Acquisition','Conversion Funnel','Product & Basket','Customer Behavior','Refunds & Business Risks']
navlabels=['Executive','Revenue & profit','Acquisition','Conversion','Products & baskets','Customer behavior','Refunds & risks']
pageids=[nid('page-'+n) for n in names]; tips=[nid('tooltip-'+n) for n in names]
def page(pid,name,w=1920,h=1080,hidden=False,tooltip=False):
    d={'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json','name':pid,'displayName':name,'displayOption':'FitToPage','height':h,'width':w,'objects':{'background':[obj({'color':fill(C['canvas']),'transparency':lit(0)})],'outspace':[obj({'color':fill('#ECEDEB'),'transparency':lit(0)})]}}
    if hidden: d['visibility']='HiddenInViewMode'
    if tooltip:
        d['type']='Tooltip'; d['pageBinding']={'name':nid('binding-'+pid),'type':'Tooltip','parameters':[]}
    pages.append(d); visuals[pid]=[]
    return d
def vco(title=None,white=True,pad=16):
    d={'background':[obj({'show':lit(white),'color':fill(C['surface']),'transparency':lit(0)})], 'border':[obj({'show':lit(white),'color':fill(C['border']),'width':lit(1),'radius':lit(12)})], 'padding':[obj({k:lit(pad) for k in ['top','bottom','left','right']})], 'visualHeader':[obj({'show':lit(False)})], 'title':[obj({'show':lit(title is not None),'text':lit(title or ''),'fontSize':lit(14),'fontFamily':lit('Segoe UI Semibold'),'fontColor':fill(C['text']),'titleWrap':lit(False)})]}
    return d
def visual(pid,key,typ,rect,title=None,query=None,objects=None,vc=None):
    ident=nid(pid+'-'+key); x,y,w,h=rect
    v={'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.9.0/schema.json','name':ident,'position':{'x':x,'y':y,'z':len(visuals[pid])+1,'width':w,'height':h,'tabOrder':len(visuals[pid])+1},'visual':{'visualType':typ,'visualContainerObjects':vc if vc is not None else vco(title),'drillFilterOtherVisuals':True}}
    if query: v['visual']['query']=query
    if objects: v['visual']['objects']=objects
    v['visual']['visualContainerObjects'].setdefault('general',[obj({'altText':lit(title or key)})])
    visuals[pid].append(v); manifest.append({'page':pid,'key':key,'type':typ,'rectangle':rect,'title':title})
    return v
def text(pid,key,rect,content,size=16,color=None,bold=False,white=False):
    paragraphs=[{'textRuns':[{'value':line,'textStyle':{'fontFamily':'Segoe UI Semibold' if bold else 'Segoe UI','fontSize':str(size)+'pt','color':color or C['text']}}]} for line in content.split('\n')]
    return visual(pid,key,'textbox',rect,objects={'general':[obj({'paragraphs':paragraphs})]},vc=vco(None,white,16 if white else 0))
def button(pid,key,label,rect,target=None,action='PageNavigation',active=False):
    vc=vco(None,False,0); link={'show':lit(True),'type':lit(action),'tooltip':lit(label)}
    if target: link['navigationSection']=lit(target)
    vc['visualLink']=[obj(link)]
    objects={
      'text':[obj({'show':lit(True)}),obj({'text':lit(label),'fontSize':lit(12),'fontFamily':lit('Segoe UI Semibold'),'fontColor':fill(C['surface'] if active else C['muted']),'horizontalAlignment':lit('center')},'default'),obj({'fontColor':fill(C['text'])},'hover')],
      'icon':[obj({'show':lit(False)}),obj({'placement':lit('left'),'shapeType':lit('blank')},'default')],
      'fill':[obj({'show':lit(True)}),obj({'fillColor':fill(C['revenue'] if active else '#E9EAE7'),'transparency':lit(0)},'default'),obj({'fillColor':fill('#DEDBF2')},'hover')],
      'outline':[obj({'show':lit(False)})],
      'shape':[obj({'tileShape':lit('rectangleRounded'),'roundEdge':{'expr':{'Literal':{'Value':'12L'}}}}),obj({'tileShape':lit('rectangleRounded')},'default')]}
    return visual(pid,key,'actionButton',rect,objects=objects,vc=vc)
def slicer(pid,key,t,n,rect,mode='Dropdown',label=None):
    return visual(pid,key,'slicer',rect,query={'queryState':{'Values':{'projections':[proj(t,n)]}}},objects={'data':[obj({'mode':lit(mode)})],'header':[obj({'show':lit(True),'text':lit(label or n),'textSize':lit(11),'fontColor':fill(C['muted'])})],'items':[obj({'textSize':lit(11),'fontColor':fill(C['text'])})],'selection':[obj({'singleSelect':lit(False),'strictSingleSelect':lit(False),'selectAllCheckboxEnabled':lit(True)})]},vc=vco(None,True,8))
def card(pid,key,measure,rect,color='revenue',tooltip=None,label=None,text_value=False):
    vc=vco(None,True,8)
    if tooltip: vc['visualTooltip']=[obj({'show':lit(True),'type':lit('Canvas'),'section':lit(tooltip)})]
    vc['spacing']=[obj({'customizeSpacing':lit(True),'verticalSpacing':lit(2)})]
    value={'fontSize':lit(14 if text_value else 28),'fontFamily':lit('Segoe UI Semibold' if not text_value else 'Segoe UI'),'fontColor':fill(C[color]),'textWrap':lit(text_value),'showBlankAs':lit('No data'),'labelDisplayUnits':lit('0'),'horizontalAlignment':lit('left')}
    objects={'value':[obj(value,'default')],'label':[obj({'show':lit(not text_value),'text':lit(label or measure),'fontSize':lit(14),'fontColor':fill(C['muted']),'position':lit('belowValue')},'default')],'padding':[obj({'paddingUniform':lit(8)},'default')],'layout':[obj({'paddingUniform':lit(0)},'default')],'fillCustom':[obj({'show':lit(True),'fillColor':fill(C['surface'])},'default')]}
    return visual(pid,key,'cardVisual',rect,query={'queryState':{'Data':{'projections':[meas(measure,label)]}}},objects=objects,vc=vc)
def chart(pid,key,typ,rect,title,t,cat,ms,colors=None,series=None,tooltip=None,sort_by=None,ascending=False,dynamic=None):
    qs={'Category':{'projections':[proj(t,cat)]},'Y':{'projections':[meas(m) for m in ms]}}
    if series: qs['Series']={'projections':[proj(*series)]}
    if tooltip: qs['Tooltips']={'projections':[meas(x) for x in tooltip]}
    query={'queryState':qs,'sortDefinition':{'sort':[{'field':field(*(sort_by or ((t,cat) if typ=='lineChart' else ('_Measures',ms[0])))),'direction':'Ascending' if ascending or typ=='lineChart' else 'Descending'}],'isDefaultSort':True}}
    axis={'show':lit(True),'fontSize':lit(11),'fontFamily':lit('Segoe UI'),'labelColor':fill(C['muted']),'showAxisTitle':lit(False)}
    objs={'categoryAxis':[obj(axis)],'valueAxis':[obj({**axis,'start':lit(0),'gridlineShow':lit(True),'gridlineColor':fill('#E8EBEF'),'gridlineThickness':lit(1),'labelDisplayUnits':lit(0)})], 'legend':[obj({'show':lit(len(ms)>1 or series is not None),'position':lit('Top'),'fontSize':lit(11),'labelColor':fill(C['muted']),'showTitle':lit(False)})], 'dataPoint':[] if series or len(ms)>1 else [obj({'defaultColor':fill(C[(colors or ['revenue'])[0]])})]}
    if colors and not series:
        for m,c in zip(ms,colors): objs['dataPoint'].append({'properties':{'fill':fill(C[c])},'selector':{'metadata':'_Measures.'+m}})
    if typ in ['barChart','clusteredBarChart','clusteredColumnChart']: objs['labels']=[obj({'show':lit(True),'fontSize':lit(11),'color':fill(C['text']),'labelDisplayUnits':lit(0)})]
    if typ=='funnel':
        objs={'dataPoint':[obj({'defaultColor':fill(C['profit'])})],'labels':[obj({'show':lit(True),'fontSize':lit(12),'color':fill(C['text'])})],'categoryAxis':[obj({'show':lit(True),'fontSize':lit(12),'color':fill(C['text'])})]}
    vc=vco(title)
    vc['visualTooltip']=[obj({'show':lit(True),'type':lit('Default')})]
    if dynamic: vc['title'][0]['properties']['text']=cf_measure(dynamic)
    return visual(pid,key,typ,rect,title,query,objs,vc)
def table(pid,key,rect,title,cols,sort=None,matrix=False,rows=None,columns=None):
    dimensions=[c for c in cols if not isinstance(c,str)]
    matrix=matrix or bool(dimensions)
    values=[meas(c) for c in cols if isinstance(c,str)]
    qs={'Values':{'projections':values}}
    if rows: qs['Rows']={'projections':[proj(*rows)]}
    elif dimensions: qs['Rows']={'projections':[proj(*c) for c in dimensions]}
    if columns: qs['Columns']={'projections':[proj(*columns)]}
    query={'queryState':qs}
    if sort: query['sortDefinition']={'sort':[{'field':field('_Measures',sort),'direction':'Descending'}],'isDefaultSort':True}
    objects={'values':[obj({'fontSize':lit(11),'fontColorPrimary':fill(C['text']),'fontColorSecondary':fill(C['text']),'backColorPrimary':fill('#FFFFFF'),'backColorSecondary':fill('#F6F7F9'),'wordWrap':lit(True)})], 'columnHeaders':[obj({'fontSize':lit(11),'fontFamily':lit('Segoe UI Semibold'),'fontColor':fill(C['muted']),'backColor':fill('#FFFFFF'),'wordWrap':lit(True),'autoSizeColumnWidth':lit(True)})], 'grid':[obj({'gridVertical':lit(False),'gridHorizontal':lit(False),'rowPadding':lit(7)})]}
    objects['columnHeaders'][0]['properties']['columnAdjustment']=lit('growToFit')
    if matrix: objects['rowHeaders']=[obj({'fontSize':lit(11),'fontColor':fill(C['text']),'stepped':lit(False)})]
    for measure,driver in [('MoM Revenue Growth','Growth Color'),('Product Refund Rate','Refund Risk Color')]:
        if measure in cols:
            objects['values'].append({'properties':{'fontColor':{'solid':{'color':cf_measure(driver)}}},'selector':{'data':[{'dataViewWildcard':{'matchingOption':1}}],'metadata':'_Measures.'+measure}})
    vc=vco(title); vc['stylePreset']=[obj({'name':lit('None')})]
    return visual(pid,key,'pivotTable' if matrix else 'tableEx',rect,title,query,objects,vc)
def value_filter(v,t,col,values):
    cond={'In':{'Expressions':[{'Column':{'Expression':{'SourceRef':{'Source':'s'}},'Property':col}}],'Values':[[{'Literal':{'Value':str(val)+'L' if isinstance(val,int) else "'"+val+"'"}}] for val in values]}}
    v['filterConfig']={'filters':[{'name':nid(t+col+str(values)),'field':field(t,col),'type':'Categorical','filter':{'Version':2,'From':[{'Name':'s','Entity':t,'Type':0}],'Where':[{'Condition':cond}]}}]}
def header(k,title,subtitle,footnote):
    pid=pageids[k]; page(pid,names[k]);
    for j,(label,target) in enumerate(zip(navlabels,pageids)): button(pid,'nav-'+str(j),label,(40+j*264,16,256 if j<6 else 256,48),target,active=j==k)
    text(pid,'heading',(40,80,1280,64),title,30,bold=True)
    text(pid,'brand',(1416,88,464,48),'MAVEN FUZZY FACTORY  /  USD',13,C['muted'])
    slicer(pid,'date','Dim_Date','Date',(40,160,420,104),'Between','Date range')
    slicer(pid,'year','Dim_Date','Year',(484,160,160,104))
    slicer(pid,'device','Dim_Device','Device',(668,160,180,104))
    slicer(pid,'visitor','Dim_Visitor','Visitor Type',(872,160,280,104))
    slicer(pid,'channel','Dim_Channel','Traffic Group',(1176,160,480,104))
    button(pid,'reset','Clear filters',(1680,184,200,48),action='ClearAllSlicers')
    text(pid,'footnote',(40,1032,1840,32),footnote,11,C['muted'])
    return pid
def kpis(k,items):
    pid=pageids[k]; h=math.ceil((16+16+2+math.ceil(28*1.5)+math.ceil(14*1.5))/8)*8
    for j,(m,label,c) in enumerate(items): card(pid,'kpi-'+str(j),m,(40+j*310,280,286,h),c,tips[k],label)
    # Reusable domain tooltip explicitly lists the metric, methodology and limitations.
    t=page(tips[k],names[k]+' — KPI definitions',1120,904,True,True)
    text(t['name'],'tip-title',(32,24,1056,48),'How to read these metrics',23,bold=True)
    yy=88
    for j,(m,label,c) in enumerate(items):
        text(t['name'],'metric-'+str(j),(32,yy,1056,32),label+'  ·  '+m,13,C[c],True)
        text(t['name'],'definition-'+str(j),(32,yy+36,1056,64),measures[m]['description'],12,C['muted'])
        yy+=104
    contextual=[items[0][0],items[1][0]] if k!=3 else ['Stage Sessions','Stage Conversion %']
    for j,m in enumerate(contextual): card(t['name'],'context-'+str(j),m,(32+j*536,728,520,104),'profit' if j else 'revenue')
    text(t['name'],'tip-footer',(32,856,1056,24),'Hover context is inherited. Full DAX: docs/04-kpi-reference.csv. Blank rates mean no valid denominator or comparable period.',10,C['muted'])

pid=header(0,'E-commerce intelligence','', 'Sales and sessions: 19 Mar 2012–19 Mar 2015. Refunds through 01 Apr 2015. Gross profit precedes refunds and operating expenses.')
kpis(0,[('Gross Sales Revenue','Recorded sales','revenue'),('Gross Profit','Gross profit','profit'),('Gross Margin %','Gross margin','profit'),('Total Orders','Orders','revenue'),('Total Sessions','Sessions','revenue'),('Session-to-Order Conversion Rate','Session conversion','profit')])
chart(pid,'revenue-trend','lineChart',(40,408,1000,320),'Sales and gross profit','Dim_Date','Year-Month',['Gross Sales Revenue','Gross Profit'],['revenue','profit'],dynamic='Revenue Trend Title')
chart(pid,'channel-performance','barChart',(1064,408,816,320),'Acquisition value by traffic group','Dim_Channel','Traffic Group',['Campaign Revenue'],['revenue'],tooltip=['Total Sessions','Session-to-Order Conversion Rate','Revenue Per Session'])
chart(pid,'products','barChart',(40,752,1000,264),'Leading products by recorded item sales','Dim_Product','Product',['Product Revenue'],['revenue'],tooltip=['Product Gross Profit','Product Margin %','Units Sold'])
v=card(pid,'insight','Executive Decision Note',(1064,752,816,264),'text',text_value=True); v['visual']['visualContainerObjects']['title']=[obj({'show':lit(True),'text':lit('Decision focus'),'fontSize':lit(14),'fontColor':fill(C['text'])})]

pid=header(1,'Revenue & profitability intelligence','','MoM/YoY use complete months only. March 2012 and March 2015 are partial. Net revenue subtracts refund events in the selected period.')
kpis(1,[('Gross Sales Revenue','Recorded sales','revenue'),('COGS','Recorded COGS','muted'),('Gross Profit','Gross profit','profit'),('Gross Margin %','Gross margin','profit'),('Average Order Value','Average order value','revenue'),('Net Revenue After Recorded Refunds','Net recorded revenue','profit')])
chart(pid,'financial-trend','lineChart',(40,408,1184,320),'Sales and gross profit by month','Dim_Date','Year-Month',['Gross Sales Revenue','Gross Profit'],['revenue','profit'],dynamic='Revenue Trend Title')
chart(pid,'contribution','barChart',(1248,408,632,320),'Product share of recorded sales','Dim_Product','Product',['Product Revenue Contribution %'],['revenue'])
table(pid,'monthly',(40,752,1184,264),'Complete-month comparisons and basket value',[('Dim_Date','Year-Month'),'Gross Sales Revenue','Gross Profit','Average Order Value','MoM Revenue Growth','YoY Revenue Growth'])
table(pid,'product-profit',(1248,752,632,264),'Product economics',[('Dim_Product','Product'),'Product Revenue','Product Gross Profit','Product Margin %'],sort='Product Gross Profit')

pid=header(2,'Marketing acquisition intelligence','','Campaign sales/orders use the acquiring session date. Tagged search/social are observed labels; spend and paid/organic status are not verified.')
kpis(2,[('Total Sessions','Sessions','revenue'),('Session-to-Order Conversion Rate','Session conversion','profit'),('Campaign Revenue','Acquired-session sales','revenue'),('Revenue Per Session','Revenue per session','profit'),('Desktop Conversion','Desktop conversion','profit'),('Mobile Conversion','Mobile conversion','profit')])
chart(pid,'source-value','barChart',(40,408,1000,320),'Revenue per session by source','Dim_Channel','Source',['Revenue Per Session'],['profit'],tooltip=['Total Sessions','Campaign Orders','Campaign Revenue'])
chart(pid,'channel-trend','lineChart',(1064,408,816,320),'Sessions over time by traffic group','Dim_Date','Year-Month',['Total Sessions'],['revenue'],series=('Dim_Channel','Traffic Group'))
table(pid,'campaigns',(40,752,1184,264),'Campaign reach and value',[('Dim_Channel','Channel'),'Total Sessions','Campaign Orders','Session-to-Order Conversion Rate','Campaign Revenue','Revenue Per Session'],sort='Campaign Revenue')
chart(pid,'device-conversion','barChart',(1248,752,632,264),'Device conversion, same session cohort','Dim_Device','Device',['Session-to-Order Conversion Rate'],['profit'],tooltip=['Total Sessions','Revenue Per Session'])

pid=header(3,'Conversion funnel intelligence','','Ordered stages count each session once. Product = listing/detail. Purchase requires confirmation and a linked order after billing. Bounce = one pageview.')
kpis(3,[('Total Sessions','Landing sessions','revenue'),('Product Page Reach Rate','Product reach','profit'),('Cart Reach Rate','Cart reach','profit'),('Checkout Reach Rate','Checkout reach','profit'),('Purchase Completion Rate','Billing to purchase','profit'),('Landing Page Bounce Rate','One-pageview bounce','refund')])
chart(pid,'funnel','funnel',(40,408,920,320),'Ordered journey · unique sessions','Dim_FunnelStage','Stage',['Stage Sessions'],['profit'],tooltip=['Stage Conversion %','Stage Reach %','Funnel Abandonment Sessions'],sort_by=('Dim_FunnelStage','Stage Order'),ascending=True)
table(pid,'dropoff',(984,408,896,320),'Stage conversion and observed drop-off',[('Dim_FunnelStage','Stage'),'Stage Sessions','Stage Conversion %','Funnel Abandonment Sessions','Funnel Abandonment %'])
table(pid,'landing',(40,752,1184,264),'Landing page comparisons · observational',[('Dim_Landing','Landing Page'),'Total Sessions','Session-to-Order Conversion Rate','Landing Page Bounce Rate','Revenue Per Session'],sort='Total Sessions')
chart(pid,'cvr-trend','lineChart',(1248,752,632,264),'Session conversion over time','Dim_Date','Year-Month',['Session-to-Order Conversion Rate'],['profit'],dynamic='Conversion Chart Title')

pid=header(4,'Product & basket intelligence','','Product metrics use sold-item grain and sale dates. Product selections filter item metrics; basket and attach-rate metrics remain whole-order measures.')
kpis(4,[('Product Revenue','Product sales','revenue'),('Product Gross Profit','Product gross profit','profit'),('Product Margin %','Product margin','profit'),('Units Sold','Units sold','revenue'),('Cross-Sell Attach Rate','Multi-item order share','profit'),('Average Items Per Order','Items per order','revenue')])
chart(pid,'product-sales','clusteredBarChart',(40,408,1000,320),'Product sales and gross profit','Dim_Product','Product',['Product Revenue','Product Gross Profit'],['revenue','profit'],tooltip=['Product Margin %','Product Refund Rate'])
table(pid,'item-roles',(1064,408,816,320),'Primary and additional item economics',[('Dim_Product','Product'),'Primary Item Revenue','Cross-Sell Revenue','Cross-Sell Units','Product Margin %'])
table(pid,'baskets',(40,752,1184,264),'Observed product combinations',[('Fact_Orders','Basket'),'Total Orders','Gross Sales Revenue','Average Order Value'],sort='Total Orders')
chart(pid,'launch','lineChart',(1248,752,632,264),'Units by calendar month since launch','Fact_OrderItems','Launch Age Month',['Units Sold'],['revenue'],series=('Dim_Product','Product'))

pid=header(5,'Customer behavior intelligence','','Visitors are observed user IDs; repeat sessions do not imply repeat purchases. Cohorts ignore date/acquisition slicers and blank incomplete months.')
kpis(5,[('Unique Website Visitors','Website user IDs','revenue'),('Paying Customers','Paying user IDs','profit'),('Repeat Visitor Session Share','Repeat session share','profit'),('Repeat Purchasing Customer %','Repeat buyer share','profit'),('Revenue Per Paying Customer','Revenue per buyer','revenue'),('Orders Per Paying Customer','Orders per buyer','revenue')])
v=table(pid,'cohorts',(40,408,1184,608),'First-purchase cohort retention · complete months only',['Cohort Retention %'],matrix=True,rows=('Dim_Customer','Purchase Cohort'),columns=('Dim_CohortAge','Month After First Purchase'))
value_filter(v,'Dim_CohortAge','Month After First Purchase',list(range(13)))
chart(pid,'visitor-trend','lineChart',(1248,408,632,320),'New and repeat visitor sessions','Dim_Date','Year-Month',['New Visitor Sessions','Repeat Visitor Sessions'],['revenue','profit'])
chart(pid,'customer-frequency','barChart',(1248,752,632,264),'Revenue by observed lifetime frequency','Dim_Customer','Observed Frequency',['Gross Sales Revenue'],['revenue'],tooltip=['Paying Customers','Total Orders'])

pid=header(6,'Refunds & business risks','','Refund cash flow uses event date; product incidence uses original sale cohort. Latest sales have less refund follow-up. No COGS recovery is assumed.')
kpis(6,[('Total Refund Amount','Recorded refunds','refund'),('Refund Amount %','Refund / period sales','refund'),('Refund Events','Refund events','refund'),('Product Refund Rate','Refunded item incidence','refund'),('Average Refund Lag Days','Average lag · days','muted'),('Gross Profit After Refunds (No Recovery)','Gross profit less refunds','profit')])
chart(pid,'refund-trend','lineChart',(40,408,1000,320),'Recorded refund amount by event month','Dim_Date','Year-Month',['Total Refund Amount'],['refund'])
chart(pid,'refund-product','barChart',(1064,408,816,320),'Recorded refund cash flow by product','Dim_Product','Product',['Total Refund Amount'],['refund'],tooltip=['Refund Events','Average Refund Lag Days'])
table(pid,'refund-incidence',(40,752,1184,264),'Refund incidence on selected sold-item cohorts',[('Dim_Product','Product'),'Units Sold','Refunded Items (Sale Cohort)','Product Refund Rate','Recorded Refunds On Selected Sales','Sale Cohort Refund Amount %'])
text(pid,'risk-notes',(1248,752,632,264),'Interpretation guardrails\n\nCompare equally mature sale cohorts before inferring product-quality changes. Refunds are observed 2–16 calendar days after sale in this extract.\n\nA refund-only period may have negative net revenue. Gross margin is not operating profit.',14,C['text'],white=True)

# Targeted product inspection is useful; a dedicated slicer lives in the right-side chart.
# Keep seven visible pages; add one hidden product drillthrough page with actual bound fields.
drillid=nid('product-drillthrough'); dp=page(drillid,'Product detail · drillthrough',1920,1080,True)
dp['type']='Drillthrough'
drillfilter=nid('product-drill-filter')
dp['filterConfig']={'filters':[{'name':drillfilter,'field':field('Dim_Product','Product'),'type':'Categorical','howCreated':'Drillthrough'}]}
dp['pageBinding']={'name':nid('product-drill-binding'),'type':'Drillthrough','acceptsFilterContext':'Default','parameters':[{'name':nid('product-drill-parameter'),'boundFilter':drillfilter,'fieldExpr':field('Dim_Product','Product')}]}
text(drillid,'title',(40,40,1400,64),'Product performance detail',30,bold=True)
button(drillid,'back','Back to report',(1640,48,240,48),action='Back')
text(drillid,'note',(40,120,1840,48),'Choose a product in the slicer, or drill through from a product visual. All values use original sold-item dates.',14,C['muted'])
slicer(drillid,'product','Dim_Product','Product',(40,184,800,104))
for j,(m,c) in enumerate([('Product Revenue','revenue'),('Product Gross Profit','profit'),('Product Margin %','profit'),('Product Refund Rate','refund')]): card(drillid,'metric'+str(j),m,(40+j*472,320,448,104),c,tips[6] if m=='Product Refund Rate' else tips[4])
chart(drillid,'product-monthly','lineChart',(40,456,1840,512),'Selected product sales and gross profit','Dim_Date','Year-Month',['Product Revenue','Product Gross Profit'],['revenue','profit'])

# Product selections on the financial overview remain in the product evidence zone.
# Order-level headline KPIs keep a common whole-order scope on that page.
revenue_page=next(pg for pg in pages if pg['name']==pageids[1])
product_sources=[v['name'] for v in visuals[pageids[1]] if v['name'] in [nid(pageids[1]+'-contribution'),nid(pageids[1]+'-product-profit')]]
financial_targets=[v['name'] for v in visuals[pageids[1]] if v['name'] in [nid(pageids[1]+'-kpi-'+str(j)) for j in range(6)]+[nid(pageids[1]+'-financial-trend'),nid(pageids[1]+'-monthly')]]
revenue_page['visualInteractions']=[{'source':src,'target':target,'type':'NoFilter'} for src in product_sources for target in financial_targets]
for k,pid in enumerate(pageids):
    for v in visuals[pid]:
        if v['visual']['visualType'] in ['lineChart','barChart','clusteredBarChart','funnel']:
            v['visual']['visualContainerObjects']['visualTooltip']=[obj({'show':lit(True),'type':lit('Canvas'),'section':lit(tips[k])})]

# Register theme using the scaffold's native base theme and explicit component safeguards.
theme_name='MavenMaterial-'+nid('maven-theme-v1')[:8]+'.json'
theme={'name':theme_name,'dataColors':[C['revenue'],C['profit'],C['refund'],'#647DA8','#7C679A','#5B8567'],'background':C['surface'],'foreground':C['text'],'foregroundNeutralSecondary':C['muted'],'foregroundNeutralTertiary':'#7B8490','backgroundLight':'#E8EBEF','backgroundNeutral':'#F4F5F7','tableAccent':C['revenue'],'good':C['profit'],'neutral':C['refund'],'bad':'#A34648','maximum':C['profit'],'center':'#B3D8D1','minimum':'#F3F8F6','textClasses':{'callout':{'fontFace':'Segoe UI Semibold','fontSize':28,'color':C['text']},'title':{'fontFace':'Segoe UI Semibold','fontSize':14,'color':C['text']},'header':{'fontFace':'Segoe UI Semibold','fontSize':12,'color':C['muted']},'label':{'fontFace':'Segoe UI','fontSize':11,'color':C['muted']}},'visualStyles':{'*':{'*':{'visualHeader':[{'show':False}],'title':[{'fontSize':14,'fontFamily':'Segoe UI Semibold','fontColor':{'solid':{'color':C['text']}}}]}},'textbox':{'*':{'padding':[{'top':0,'bottom':0,'left':0,'right':0}],'background':[{'show':False}],'border':[{'show':False}]}},'cardVisual':{'*':{'layout':[{'paddingUniform':0}],'padding':[{'paddingUniform':8}],'spacing':[{'verticalSpacing':2}]}},'tableEx':{'*':{'columnHeaders':[{'autoSizeColumnWidth':True,'columnAdjustment':'GrowToFit'}]}},'pivotTable':{'*':{'columnHeaders':[{'autoSizeColumnWidth':True}]}}}}
theme['visualStyles']['tableEx']['*']['columnHeaders'][0]['columnAdjustment']='growToFit'
theme['visualStyles']['pivotTable']['*']['columnHeaders'][0]['columnAdjustment']='growToFit'
new_theme_name='MavenMaterial-'+uuid.uuid4().hex[:8]+'.json'
old_theme=REPORT/'StaticResources'/'RegisteredResources'/theme_name
if old_theme.exists(): old_theme.rename(old_theme.with_name(new_theme_name))
theme_name=new_theme_name; theme['name']=theme_name
dump(REPORT/'StaticResources'/'RegisteredResources'/theme_name,theme); dump(OUT/'Maven-Material-Theme.json',theme)
report=json.loads((DEF/'report.json').read_text()); versions=report['themeCollection']['baseTheme']['reportVersionAtImport']
report['themeCollection']['customTheme']={'name':theme_name,'reportVersionAtImport':versions,'type':'RegisteredResources'}
report['resourcePackages']=[x for x in report['resourcePackages'] if x['name']!='RegisteredResources']+[{'name':'RegisteredResources','type':'RegisteredResources','items':[{'name':theme_name,'path':theme_name,'type':'CustomTheme'}]}]
dump(DEF/'report.json',report)

# Remove only the original empty scaffold page; known, verified workspace path.
for d in (DEF/'pages').iterdir():
    if d.is_dir() and d.name not in pageids+tips+[drillid]:
        existing=d/'page.json'
        if existing.exists() and not (d/'visuals').exists(): existing.unlink(); d.rmdir()
for pg in pages:
    pid=pg['name']; dump(DEF/'pages'/pid/'page.json',pg)
    assert len({v['name'] for v in visuals[pid]})==len(visuals[pid]), 'Duplicate visual ID on '+pid
    for v in visuals[pid]: dump(DEF/'pages'/pid/'visuals'/v['name']/'visual.json',v)
dump(DEF/'pages'/'pages.json',{'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json','pageOrder':pageids+tips+[drillid],'activePageName':pageids[0]})
dump(QA/'report_manifest.json',{'visible_pages':dict(zip(pageids,names)),'tooltip_pages':tips,'drillthrough_page':drillid,'visuals':manifest})
print('Built',len(pageids),'visible pages,',len(tips),'tooltip pages, 1 product detail page,',sum(map(len,visuals.values())),'native visuals.')
