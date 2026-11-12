"""Create source-backed documentation and per-measure expected-value evidence."""
from pathlib import Path
import json,csv,re,shutil
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'Maven Fuzzy Factory'; DOC=OUT/'docs'; QA=OUT/'qa'; DATA=OUT/'data'/'prepared'
b=json.loads((QA/'baseline.json').read_text()); db=json.loads((QA/'model.bim').read_text()); model=db['model']; catalog=json.loads((QA/'measure_catalog.json').read_text())
facts={p.stem:pd.read_csv(p) for p in DATA.glob('*.csv')}; orders=facts['Fact_Orders']; items=facts['Fact_OrderItems']; refunds=facts['Fact_Refunds']; sessions=facts['Fact_Sessions']
def write(n,t): (DOC/n).write_text(t,encoding='utf-8')
source_dictionary=pd.read_csv(ROOT/'Dataset'/'maven_fuzzy_factory_data_dictionary.csv').fillna('')
source_dictionary.to_csv(DOC/'02-source-data-dictionary.csv',index=False)
native={'Fact_Orders':'orders','Fact_OrderItems':'order_items','Fact_Refunds':'order_item_refunds','Fact_Sessions':'website_sessions','Dim_Product':'products'}
colmap={'Order ID':'order_id','Website Session ID':'website_session_id','Customer ID':'user_id','Primary Product ID':'primary_product_id','Items Purchased':'items_purchased','Sales Amount':'price_usd','COGS Amount':'cogs_usd','Order Item ID':'order_item_id','Product ID':'product_id','Item Sales Amount':'price_usd','Item COGS Amount':'cogs_usd','Refund ID':'order_item_refund_id','Refund Amount':'refund_amount_usd','Product':'product_name','Launch Date':'created_at','Device':'device_type'}
derived={
 'Session Date':('website_sessions.created_at','Recorded timestamp reduced to calendar date; timestamps are timezone-naive.'),
 'Order Date':('orders.created_at','Recorded order timestamp reduced to calendar date.'),
 'Refund Date':('order_item_refunds.created_at','Recorded refund timestamp reduced to calendar date; role-playing refund cash-flow date.'),
 'Visitor Type':('website_sessions.is_repeat_session','Source flag 0 = new visitor session; 1 = repeat visitor session. Not purchase recurrence.'),
 'Landing Page':('website_pageviews.pageview_url + created_at + website_pageview_id','URL of the first pageview in deterministic (timestamp, pageview ID) order within session.'),
 'Channel ID':('website_sessions UTM fields + http_referer','Deterministic surrogate for observed source/campaign/content/referrer tuple; classifications do not prove paid status.'),
 'Pageviews':('website_pageviews','Native pageview count per session.'),
 'Bounced':('website_pageviews','One when the session has exactly one recorded pageview; no engagement-time rule.'),
 'Converted':('orders.website_session_id','One if a session has at least one linked order; prevents multiple orders inflating conversion.'),
 'Session Orders':('orders grouped by website_session_id','Number of linked orders, attributed to session start date.'),
 'Session Revenue':('orders.price_usd grouped by website_session_id','Order revenue aggregated per session before joining; session-date attribution.'),
 'Recorded Refund':('order_item_refunds.refund_amount_usd grouped by order_item_id','All recorded refunds for the sold item through source cutoff; original-sale cohort selection.'),
 'Refunded Item':('order_item_refunds.order_item_id','One if any recorded refund links to the item, regardless of number of events.'),
 'Item Role':('order_items.is_primary_item','Primary item for 1, cross-sell item for 0.'),
 'Refund Lag Days':('refund created_at date - original order created_at date','Calendar-day difference; distinct from fractional elapsed days.'),
 'Basket':('order_items.product_id + products.product_name','Sorted multiset of product names in one order. One signature per order; order values never duplicated.'),
 'Has Cross Sell':('orders.items_purchased','One when more than one item was purchased in the order.'),
 'Purchase Number':('orders sorted by created_at, order_id within user_id','One-based order sequence in the extract; not a lifetime claim.'),
 'Purchase Type':('Purchase Number','First observed purchase for sequence one; subsequent purchase otherwise.'),
 'Purchase Age Month':('order date - first observed purchase month','Calendar month difference, not rolling 30-day windows.'),
 'Launch Age Month':('order item date - product launch month','Calendar month difference; launch month may be partially observed.'),
 'First Session Date':('website_sessions.created_at per user_id','Earliest observed session date, not necessarily true first-ever visit.'),
 'First Purchase Date':('orders.created_at per user_id','Earliest observed purchase date; blank for observed nonbuyers.'),
 'Purchase Cohort':('First Purchase Date','YYYY-MM of first observed purchase; nonbuyers labeled separately.'),
 'Observed Lifetime Orders':('orders grouped by user_id','Complete-extract purchase count. Fixed at refresh; not recalculated by report date slicers.'),
 'Observed Frequency':('Observed Lifetime Orders','No purchase, one, two, three-to-four, or five-plus purchases in extract.'),
 'Customer Status':('Observed Lifetime Orders','Observed buyer vs no observed purchase.'),
 'Traffic Group':('website_sessions UTM/referrer','Tagged search, tagged social, untagged search referral, or direct/unknown; no paid/organic assertion.'),
 'Source':('utm_source or recognized http_referer','Tagged source preferred; recognized untagged search referrer otherwise; direct/unknown is residual.'),
 'Campaign':('website_sessions.utm_campaign','Source campaign text, with literal NULL/missing normalized to (not tagged).'),
 'Ad Content':('website_sessions.utm_content','Source ad/content label. No spend or exposure metric.'),
 'Referrer':('website_sessions.http_referer','Observed referrer URL; missing is (not tagged).'),
 'Channel':('Source + Campaign','Display grouping of source and campaign; ad-content variants roll up safely.'),
 'Stage':('website_pageviews observed URL inventory','Disconnected ordered-stage label; selects a distinct-session funnel measure.'),
 'Stage Order':('Stage','Landing 1, Product 2, Cart 3, Shipping 4, Billing 5, Purchase 6.'),
 'Month After First Purchase':('0 through 36','Disconnected cohort-age axis. Report displays ages zero through twelve by default.'),
 'Is Complete Sales Month':('observed order timestamp bounds','One only for Apr 2012–Feb 2015. Excludes both partial boundary months and all uncovered months.'),
 'Is In Sales Coverage':('observed order timestamp bounds','Date within inclusive observed order dates; boundary days remain partial.'),
 'ISO Year':('calendar date','ISO week-numbering year, paired with ISO week number.'),
 'Week':('calendar date','ISO week number; pair with ISO Year, not necessarily calendar Year.'),
}
rows=[]
for t in model['tables']:
    for c in t['columns']:
        n=c['name']; src=colmap.get(n); table=native.get(t['name'])
        if n in derived: lineage,meaning=derived[n]
        elif n.startswith('Reach '): lineage='website_pageviews.pageview_url'; meaning='One if any matching stage URL is observed in session, repeated views deduplicated; no ordering requirement.'
        elif n.startswith('Sequential '): lineage='website_pageviews ordered by timestamp/pageview ID, with orders linkage for purchase'; meaning='One only after all preceding stages were completed in order. Purchase also requires linked order at/after billing.'
        elif t['name']=='Dim_Date': lineage='contiguous calendar derived from source coverage years'; meaning='Calendar attribute: '+n+'. Full years enable unambiguous time context; no assertion of observations outside source coverage.'
        elif table and src:
            match=source_dictionary[(source_dictionary.Table==table)&(source_dictionary.Field==src)]
            lineage=table+'.'+src; meaning=match.Description.iloc[0] if len(match) else 'Conformed source attribute looked up through a validated many-to-one key.'
        else: lineage='Source-derived conformed dimension or utility'; meaning=c.get('description','Utility label.')
        rows.append({'Table':t['name'],'Column':n,'Model type':c['dataType'],'Hidden':c.get('isHidden',False),'Lineage':lineage,'Meaning':meaning})
pd.DataFrame(rows).to_csv(DOC/'03-data-dictionary.csv',index=False,encoding='utf-8-sig')
rels=model['relationships']; lines=['# Model architecture and relationships','', 'Import model with four independent native-grain facts and conformed dimensions. All 26 relationships are active, one-to-many, and filter from dimension to fact. There are no fact-to-fact relationships.','', '| Fact | Grain | Date role | Rows |','|---|---|---|---:|']
for t,grain,date in [('Fact_Orders','One recorded order','Order Date'),('Fact_OrderItems','One sold item','Order Date'),('Fact_Refunds','One recorded refund event','Refund Date'),('Fact_Sessions','One website session with journey flags','Session Date')]: lines.append(f'| {t} | {grain} | {date} | {len(facts[t]):,} |')
lines += ['', 'Product filters items and refunds. It does not classify whole orders by primary product. Gross Sales, COGS, Orders and AOV are whole-order metrics. Product measures use sold-item values. Net Revenue, Gross Profit After Refunds and Refund Amount % use matching item financials and refund scope so product selections cannot mix all-product sales with selected-product refunds. Without a product filter item sales/COGS reconcile exactly to orders.', '', 'On the Revenue page, product comparisons do not cross-filter whole-order headline cards, financial trend or monthly comparisons; the product evidence zone remains interactive. On the Product page, whole-order basket/attach-rate metrics remain whole-order metrics and the page footnote states that scope.', '', '```mermaid','flowchart LR']
for dt in ['Dim_Date','Dim_Customer','Dim_Channel','Dim_Device','Dim_Visitor','Dim_Landing']:
    lines.append(f'  {dt} --> Fact_Orders & Fact_OrderItems & Fact_Refunds & Fact_Sessions')
lines += ['  Dim_Product --> Fact_OrderItems & Fact_Refunds','  Dim_FunnelStage -. measure switch .-> Fact_Sessions','  Dim_CohortAge -. age filter in measure .-> Fact_Orders','```','','## Relationship inventory','','| Dimension key | Fact key | Cardinality | Direction |','|---|---|---|---|']
for r in rels: lines.append(f"| {r['toTable']}[{r['toColumn']}] | {r['fromTable']}[{r['fromColumn']}] | 1 → many | Dimension → fact |")
lines += ['', '## Date and filter semantics','', '- Dim_Date is contiguous, marked using its unique Date key and Time table category; automatic date/time is disabled. Month names and Year-Month labels have explicit sort keys. The hierarchy is Year → Quarter → Month → Date.', '- Sessions and campaign measures use the acquiring session date; order/item values use the recorded order date. Refund events use refund date. There are 237 cross-calendar-day session/order pairs.', '- Refund incidence and recorded refunds on selected sales are original-sale-cohort measures. They observe all linked refund events through the extract cutoff, even when an event occurs after the selected sale period.', '- Cohort retention ignores calendar-date and acquisition slicers. It retains first-purchase cohort/customer filters and blanks any age cell without a fully observed calendar month. Age 0 means purchase-month activity; a retained customer is a customer purchasing in a later month, not merely visiting.', '- Dim_Customer lifetime frequency is fixed over the entire observed extract. The Repeat Purchasing Customers measure instead counts customers with at least two purchases inside the selected period.', '- Disconnected utilities are deliberate. Funnel stage selection changes the stage-switch measure; it does not directly filter native facts. Cohort age acts only inside the cohort activity measure.','', '## Power Query and preparation boundary','', 'Power Query reads the deterministic prepared CSVs using a single PreparedFolder parameter, promotes headers and applies explicit culture-aware integer, currency, date and text types. Raw event ordering, safe many-to-one enrichments, basket signatures and cohort derivation are implemented in the reproducible preparation script, not hidden in DAX. The heavy 1.19-million-row event table is retained as raw evidence and reduced to 472,871 session rows for Import performance. This is a deliberate hybrid ETL design; refresh the preparation step when sources change, then refresh Power BI.']
write('05-model-and-relationships.md','\n'.join(lines))
stage=b['funnel']; stage_names=list(stage); funnelrows=[]
for idx,n in enumerate(stage_names):
    prior=b['sessions'] if idx==0 else stage[stage_names[idx-1]]; current=stage[n]
    funnelrows.append(f'| {n} | {current:,} | {current/prior:.2%} | {prior-current:,} |')
desktop=27805/327027; mobile=4508/145844; panda=301/4985
write('06-business-insights.md',f'''# Verified business insights and decisions

All figures below describe the full supplied extract unless a month is named. They are independently reconciled source observations, not claims of causal impact or realized business improvements.

| Metric | Verified value |
|---|---:|
| Recorded sales | ${b['sales']:,.2f} |
| Recorded COGS | ${b['cogs']:,.2f} |
| Gross profit before refunds and operating costs | ${b['gross_profit']:,.2f} |
| Gross margin before refunds | {b['gross_margin']:.2%} |
| Recorded refunds, through 1 Apr 2015 | ${b['refunds']:,.2f} |
| Revenue after all recorded refunds | ${b['net_revenue']:,.2f} |
| Average order value | ${b['aov']:,.2f} |
| Session conversion | {b['conversion']:.2%} |

## Conversion: investigate the largest observed losses

| Ordered stage | Distinct sessions | Conversion from prior | Sessions lost from prior |
|---|---:|---:|---:|
{chr(10).join(funnelrows)}

The largest stage-to-stage proportional drop after product reach is product-to-cart: {(1-stage['Cart']/stage['Product']):.2%} of product-reaching sessions do not progress to cart. Investigate product-detail relevance, offer clarity, loading performance and acquisition intent. These are hypotheses for testing, not established causes. Listing and detail views are deliberately grouped into the observed Product stage; a future deeper funnel could separate them.

Desktop sessions convert at {desktop:.2%} versus {mobile:.2%} for mobile, a {(desktop-mobile)*100:.2f} percentage-point difference. Prioritize device-specific journey investigation, stratified by source/campaign and month. The aggregate difference is not a causal device effect and must not be presented as guaranteed recoverable revenue.

## Revenue: compare complete exposure periods

February 2015 recorded sales were $129,212.94, 95.74% above February 2014. Both are complete months. March 2015 ends on March 19 and should not be presented as a full-month collapse. The model blanks complete-month MoM/YoY comparisons at both extract edges.

## Product concentration and refunds

The Original Mr. Fuzzy contributes $1,211,057.74, {1211057.74/b['sales']:.2%} of recorded item sales. This creates observed revenue concentration; compare newer launches at comparable calendar ages before treating lower lifetime sales as weak product performance.

The Birthday Sugar Panda has the highest recorded sold-item refund incidence, {panda:.2%} (301 of 4,985), compared with {1237/24226:.2%} for the Original Mr. Fuzzy. Investigate mature sale cohorts, campaign/device mix and refund reasons before attributing the difference to product quality. Refund reasons are absent. Recorded refunds occur 2–16 calendar days after sale in this extract; the latest sales have less follow-up, so these are observed rates rather than final defect rates.

## Customer behavior and cross-sell

{b['repeat_buyers']:,} of {b['buyers']:,} observed buyer IDs made at least two recorded purchases ({b['repeat_buyers']/b['buyers']:.2%}). This differs from repeat visitor sessions ({b['repeat_sessions']:,}). Evaluate post-purchase retention with mature first-purchase cohorts; do not infer lifetime loyalty, merged people or churn from a bounded user-ID extract.

{b['cross_sell_orders']:,} orders contain more than one item ({b['cross_sell_orders']/b['orders']:.2%} of orders). Use primary vs additional-item economics and observed basket combinations to propose merchandising experiments. No causal uplift is established by co-purchase frequency.

## Acquisition decisions and evidence limits

Tagged search supplies 378,858 of 472,871 sessions ({378858/472871:.2%}) and $1,544,817.39 in acquired-session sales. This indicates dependence on this observed source group, not verified paid-media ROI. Campaign labels and referrers support traffic segmentation but no advertising spend, ROAS, CAC or budget allocation can be calculated. Require actual cost and attribution data before recommending spend changes.

## Recommended next work

1. Inspect mobile and product-to-cart paths within matched month/channel cohorts, then design randomized tests where feasible.
2. Review Panda refund incidence on equally mature sale cohorts; obtain refund reasons and operational context.
3. Compare launch-age performance and additional-item margins before proposing basket placement experiments.
4. Connect actual marketing costs before moving from session efficiency to investment decisions.
5. Expand customer observation and identity documentation before a retention program business case.
''')
write('07-report-walkthrough.md','''# Report walkthrough and interaction guide

The report has seven visible pages, seven hidden KPI-definition tooltip pages, and one hidden Product detail drillthrough page. Every visible page uses native Power BI visuals, a 1920 × 1080 canvas, seven navigation buttons, date/year/device/visitor/traffic controls, and a Clear filters button. Buttons require Ctrl+click while editing in Desktop; normal click in reading mode.

| Page | Main decision | Native analytical content |
|---|---|---|
| Executive Command Center | Where should management look next? | Six KPIs, sales/profit trend, acquired-session channel value, product rankings, dynamic selected-context decision note |
| Revenue & Profitability | How do revenue and estimated gross profit evolve? | Sales/profit trend, product share, monthly AOV/MoM/YoY comparison matrix, product economics |
| Marketing Acquisition | Which observed traffic generates valuable sessions? | Source revenue/session, channel session trends, campaign value matrix, device conversion |
| Conversion Funnel | Which ordered transition loses sessions? | Strict distinct-session funnel, stage conversion/drop-off matrix, landing-page outcomes, conversion trend |
| Product & Basket | What is sold, together and at what gross margin? | Clustered sales/profit bars, primary/additional-item economics, product combinations, calendar launch-age trend |
| Customer Behavior | How do observed users return and purchase? | First-purchase monthly cohort matrix, new/repeat session trend, revenue by complete-extract customer frequency |
| Refunds & Business Risks | Where is recorded refund exposure concentrated? | Event-date refund trend and product concentration, original-sale-cohort incidence, timing/interpretation notes |

## Filtering and empty states

Date ranges apply through the shared date dimension according to each fact's date role. Slicers are page-local, intentionally not silently synchronized; navigation may change the selected context. Read the visible date control on every page. Year and date controls intersect; Clear filters removes slicer restrictions if their intersection becomes empty. Page selection in charts follows Power BI's native cross-filter/highlight behavior, except the documented product-zone isolation on the Revenue page. Clear filters clears slicers, not necessarily a selected chart mark; click empty chart space to clear that selection.

Native blank measures preserve missing denominators and unsupported comparisons. KPI cards show No data for blanks. Rates are not coerced to zero. The date dimension spans complete years; dates outside source coverage are available but contain no transactions. The full unfiltered view includes all recorded refunds through Apr 1 even though sales end Mar 19.

## Tooltips, drillthrough and formatting

Hover KPI cards and main charts for the corresponding domain definition page. It lists exact methodology and limitations and includes two context-sensitive values. The funnel tooltip includes the selected ordered-stage count/rate. Right-click a product data point and choose Product detail drillthrough, then use Back to return. The hidden detail page includes a product selector for direct inspection.

The Revenue comparison matrix colors valid MoM growth teal/amber; unavailable comparisons are neutral. The refund-incidence matrix compares each product with the all-product observed incidence in the remaining filter context. Color is descriptive, not an invented business target. All rates retain labels and numbers so color is not the only information channel.

Bookmarks and field parameters were not added: navigation, clear-slicer actions, separate pages and focused native comparisons already support the required decisions. A single cohort-age utility table supports the retention matrix without field-parameter or calculation-group complexity.

## Runtime acceptance still required

Structural checks cannot verify Desktop rendering, tooltip sizing, native interactions, refresh latency or DAX engine execution. Complete the checklist in 08-validation-and-runtime.md before representing screenshots or runtime behavior as verified. No HTML recreation or simulated screenshot is substituted for a Power BI capture.
''')
write('08-validation-and-runtime.md','''# Validation evidence and runtime acceptance

## Verified in this environment

- The source-to-prepared audit independently reconciles financial cents, native key sets, every session funnel flag, customer cohorts, source fingerprints and 299 filtered aggregate cells. See qa/independent_validation.json and 09-independent-review.md.
- The preparation audit checks source counts, dates, primary keys, foreign keys, order/item sales/COGS/count consistency, refund linkage/timing, session attribution and ordered funnel monotonicity. See qa/data_checks.csv.
- The complete model was imported using Power BI Modeling MCP, read back and exported into 18 TMDL files. An exported folder was loaded back successfully with 14 tables, 88 measures and 26 relationships. See qa/mcp-model-readback.json. This proves metadata serialization, not DAX execution.
- Static checks resolve DAX/report references, measure formats/descriptions, relationship types, date-table properties, fact isolation and page geometry. See qa/artifact_checks.json. Geometry checks do not establish that text fits at runtime.
- PBIR was validated against the installed report-authoring toolkit and its remote schemas. See qa/pbir-validation.json for the exact final result and any schema-fetch warning; a skipped schema must not be represented as passed.

## Runtime boundary

Power BI Desktop is installed, but preview host discovery found no reachable Desktop bridge. Offline Modeling MCP connections do not support DAX query validation/execution. Live import refresh, engine calculations, visual rendering, interactive filtering, performance and screenshots are therefore not verified by the offline checks. The final selected-host attempt, if performed, is logged in qa/desktop-preview-status.json / qa/desktop-preview-open.json. No PBIX or actual-report screenshots are included unless a later successful capture is recorded.

## Finish in Power BI Desktop

1. Open powerbi/Maven Fuzzy Factory.pbip. Confirm the local semantic model is bound by path.
2. Transform data → Manage parameters: PreparedFolder should point to this project's data/prepared folder. At the original workspace location it is already configured.
3. Refresh all Import tables and confirm no Power Query errors. The source preparation must run before refreshing Power BI whenever raw CSVs change.
4. Verify Dim_Date is marked with Date, the hierarchy is present, all 26 relationships are single-direction and automatic date tables are disabled.
5. Run qa/runtime-smoke.dax in DAX Query View. Full unfiltered source baselines are in qa/baseline.json. Full-extract sales = 1,938,509.75; COGS = 722,370.25; gross profit = 1,216,139.50; all recorded refunds = 85,338.69; net = 1,853,171.06; sessions = 472,871; orders = 32,313; conversion = 32,313 / 472,871.
6. Verify every measure with qa/runtime-all-measures.dax plus the filtered cases in qa/runtime-contexts.dax. qa/measure-validation.csv lists independent reference expectations and explicitly distinguishes them from engine execution.
7. Check Jan/Feb 2015 full-month comparisons, blank partial March comparisons, noncontiguous selected windows, product-selected refund ratios, empty device/date intersections, customer cohorts and all six funnel stages. Cohort retention ignores acquisition/date controls by design.
8. Test all seven navigation destinations, all slicers, Clear filters, chart cross-highlighting, explanatory tooltips and product drillthrough/back. Confirm labels, tables, cards and filter panes are readable with no clipping or error icons.
9. Capture the actual seven visible Power BI pages at full resolution after refresh and review each image. Screenshots belong to the report only after a successful actual capture; do not relabel a wireframe or web mockup as Power BI output.
10. Record source refresh time, DAX timings, screenshot paths, tested filters and any remaining issues. Save the PBIP after live changes. Optional: Save As PBIX through Desktop once runtime acceptance passes.

## Reproduction

Run scripts/profile_and_prepare.py, scripts/build_model.py, scripts/build_report.py, scripts/independent_validate.py, scripts/verify_artifacts.py and scripts/finalize_docs.py using Python with pandas and numpy. The first two preparation/model scripts generate a BIM; import it and export TMDL through Modeling MCP before opening Desktop. A pure rebuild does not silently update an already-open Desktop instance. Keep source files unchanged. The build scripts live in the workspace scripts folder, outside this artifact folder.

The semantic-model M partitions include explicit types and a configurable PreparedFolder. This hybrid pipeline computes the ordered event journey in Python, then loads prepared data with Power Query; it is not a single-click raw-CSV Power Query-only refresh solution.
''')
write('10-portfolio-case-study.md','''# Maven Fuzzy Factory — portfolio case study

## Business problem

A fictional teddy-bear e-commerce retailer needs a joined-up view of recorded revenue, estimated gross profitability, acquisition quality, website progression, merchandising, observed customer recurrence and refunds. The portfolio challenge is to connect these decisions while preserving the correct grain and temporal meaning of every metric.

## Data source and license

User-supplied copies of Maven Analytics' Toy Store E-Commerce Database: six native tables and a source data dictionary. The official dataset listing identifies the source as Maven Analytics and its license as Public Domain: https://mavenanalytics.io/data-playground/toy-store-e-commerce-database (verified 21 October 2026). The listing's generic record/field preview is not used as the supplied extract's row-count authority; local CSV profiles and fingerprints are the evidence. This educational case study is not a real client engagement.

## Analytical approach

Start with source discovery, schema profiling, key validation and exact-cent reconciliation. Enrich facts only through validated many-to-one joins. Aggregate pageviews into one session row with both any-reach and strict sequential-stage flags. Preserve separate order-date financials, session-date acquisition and refund-event-date cash flow. Build conformed dimensions and explicit DAX measures, then bind native report visuals to the documented model.

## Technical challenges addressed

- Prevented one-to-many pageview/item joins from multiplying sales and sessions.
- Reconciled order and item financials independently, with exact integer-cent checks.
- Engineered and independently reconstructed a deterministic, repeated-event-safe session funnel.
- Preserved 237 session/order date-boundary differences rather than forcing a misleading common date.
- Separated recorded refund cash flow from original-sale-cohort incidence, with censoring disclosures.
- Guarded incomplete-month, incomplete-day and noncontiguous-window comparisons.
- Kept product scope matched for refund-adjusted values and isolated whole-order headline interactions.
- Differentiated website identifiers, active visitors, buyers, subsequent purchases and first-observed cohorts.

## Power BI techniques

PBIP/PBIR authoring, TOM-compatible model import and TMDL serialization, configurable Power Query Import partitions, a marked Date dimension, explicit measure folders/descriptions/formats, context-aware DAX narratives and titles, complete-month comparisons, disconnected stage/cohort-age dimensions, report-page tooltips, conditional formatting, drillthrough/back and native slicer-clear actions.

## Verified observations

Recorded sales total $1,938,509.75 and gross profit before refunds/operating costs is $1,216,139.50. Session conversion is 6.83%. Desktop conversion is 8.50% versus 3.09% on mobile, warranting further stratified investigation. February 2015 sales are 95.74% above February 2014. Product-to-cart progression is a large observed funnel loss, and recent refund cohorts need more follow-up. Detailed figures, denominators and recommendations are in 06-business-insights.md.

## Portfolio presentation guidance

Lead with the business question and model architecture, then walk through Executive → Acquisition → Funnel → Product → Refunds. Show the validation evidence alongside each key claim. Describe recommendations as proposed tests, not realized gains. Use only screenshots captured from the refreshed actual report. State the remaining runtime validation status accurately; offline metadata validation is not evidence that the report opened or rendered. Credit Maven Analytics and label the company fictional in the README, presentation and portfolio listing.
''')

# Independent reference expectations for each measure: no claim of live DAX evaluation.
expected={
 'Gross Sales Revenue':b['sales'],'COGS':b['cogs'],'Gross Profit':b['gross_profit'],'Gross Margin %':b['gross_margin'],'Total Orders':b['orders'],'Average Order Value':b['aov'],'Average Items Per Order':b['items']/b['orders'],
 'Total Refund Amount':b['refunds'],'Net Revenue After Recorded Refunds':b['net_revenue'],'Gross Profit After Refunds (No Recovery)':b['gross_profit']-b['refunds'],'Refund Amount %':b['refunds']/b['sales'],'Refund Events':b['refund_events'],'Refunded Orders (Event Date)':refunds['Order ID'].nunique(),'Average Refund Lag Days':refunds['Refund Lag Days'].mean(),
 'Recorded Refunds On Selected Sales':b['refunds'],'Refunded Items (Sale Cohort)':int(items['Refunded Item'].sum()),'Product Refund Rate':items['Refunded Item'].sum()/b['items'],'Sale Cohort Refund Amount %':b['refunds']/b['sales'],
 'Total Sessions':b['sessions'],'Unique Website Visitors':b['users'],'New Visitor Sessions':b['new_sessions'],'Repeat Visitor Sessions':b['repeat_sessions'],'Converted Sessions':b['converted_sessions'],'Session-to-Order Conversion Rate':b['conversion'],'Campaign Orders':b['orders'],'Campaign Revenue':b['sales'],'Revenue Per Session':b['sales']/b['sessions'],'Traffic Source Contribution':1.0,
 'Desktop Conversion':desktop,'Mobile Conversion':mobile,'Bounced Sessions':b['bounced'],'Landing Page Bounce Rate':b['bounced']/b['sessions'],'Total Pageviews':b['pageviews'],
 'Checkout Reach Rate':stage['Shipping']/b['sessions'],'Purchase Completion Rate':stage['Purchase']/stage['Billing'],
 'Product Revenue':b['sales'],'Product COGS':b['cogs'],'Product Gross Profit':b['gross_profit'],'Product Margin %':b['gross_margin'],'Units Sold':b['items'],'Product Revenue Contribution %':1.0,'Orders Containing Selected Product':b['orders'],'Primary Item Revenue':float(items.loc[items['Item Role']=='Primary item','Item Sales Amount'].sum()),'Cross-Sell Revenue':float(items.loc[items['Item Role']=='Cross-sell item','Item Sales Amount'].sum()),'Cross-Sell Units':int(items['Item Role'].eq('Cross-sell item').sum()),'Orders With Cross Sell':b['cross_sell_orders'],'Cross-Sell Attach Rate':b['cross_sell_orders']/b['orders'],
 'Paying Customers':b['buyers'],'Repeat Purchasing Customers':b['repeat_buyers'],'Repeat Purchasing Customer %':b['repeat_buyers']/b['buyers'],'Orders Per Paying Customer':b['orders']/b['buyers'],'Revenue Per Paying Customer':b['sales']/b['buyers'],'Subsequent Purchase Orders':int(orders['Purchase Type'].eq('Subsequent purchase').sum()),'Subsequent Purchase Revenue':float(orders.loc[orders['Purchase Type']=='Subsequent purchase','Sales Amount'].sum()),'Repeat Visitor Session Share':b['repeat_sessions']/b['sessions'],'Cohort Customers':b['buyers'],'Cohort Active Customers':None,'Cohort Retention %':None,
 'MoM Revenue Growth':None,'YoY Revenue Growth':None,'Revenue Growth %':None,'Stage Sessions':None,'Previous Stage Sessions':None,'Stage Conversion %':None,'Stage Reach %':None,'Funnel Abandonment Sessions':None,'Funnel Abandonment %':None,
 'Selected Period Label':'01 Jan 2012 – 31 Dec 2015','Data Coverage Note':'Sales/sessions: 19 Mar 2012–19 Mar 2015 | Refunds: through 01 Apr 2015 | USD','Revenue Trend Title':'Recorded sales · 01 Jan 2012 – 31 Dec 2015','Conversion Chart Title':'Session conversion · 01 Jan 2012 – 31 Dec 2015','Growth Color':'#526074','Refund Risk Color':'#087F80'
}
channels=facts['Dim_Channel']; tagids=set(channels.loc[channels['Traffic Group'].isin(['Tagged search','Tagged social']),'Channel ID']); tagged=sessions[sessions['Channel ID'].isin(tagids)]
expected['Revenue Per Tagged Marketing Session']=tagged['Session Revenue'].sum()/len(tagged)
for x in ['Product','Cart','Shipping','Billing']:
    expected[x+' Reach Sessions']=int(sessions['Reach '+x].sum()); expected[x+' Page Reach Rate' if x=='Product' else x+' Reach Rate']=expected[x+' Reach Sessions']/b['sessions']
for x in ['Product','Cart','Shipping','Billing','Purchase']: expected['Sequential '+x+' Sessions']=stage[x]
expected['Executive Decision Note']='Filter-responsive text; compare embedded sales, gross margin and conversion to the independent baseline.'
with (QA/'measure-validation.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=['Measure','Reference context','Independent expected result','Reference status','DAX engine status']); w.writeheader()
    for m in catalog:
        n=m['name']; val=expected.get(n,'MISSING')
        w.writerow({'Measure':n,'Reference context':'All dates/dimensions, no stage or cohort-age row selected','Independent expected result':'BLANK (requires one valid context)' if val is None else val,'Reference status':'REQUIRES REVIEW' if val=='MISSING' else 'Reference specified; numeric source bases independently audited','DAX engine status':'NOT EXECUTED — offline MCP has no DAX engine'})
smoke='EVALUATE\nROW(\n'+',\n'.join('  '+json.dumps(n)+', ['+n+']' for n in ['Gross Sales Revenue','COGS','Gross Profit','Gross Margin %','Total Refund Amount','Net Revenue After Recorded Refunds','Total Orders','Total Sessions','Session-to-Order Conversion Rate'])+'\n)\n'
(QA/'runtime-smoke.dax').write_text(smoke)
(QA/'runtime-all-measures.dax').write_text('EVALUATE\nROW(\n'+',\n'.join('  '+json.dumps(m['name'])+', ['+m['name']+']' for m in catalog)+'\n)\n',encoding='utf-8')
(QA/'runtime-contexts.dax').write_text('''// Run each EVALUATE independently, comparing to qa CSVs and independent_validation.json.
EVALUATE SUMMARIZECOLUMNS('Dim_FunnelStage'[Stage], "Sessions", [Stage Sessions], "Prior", [Previous Stage Sessions], "Conversion", [Stage Conversion %], "Drop off", [Funnel Abandonment Sessions]) ORDER BY 'Dim_FunnelStage'[Stage]

EVALUATE SUMMARIZECOLUMNS('Dim_Date'[Year-Month], "Sales", [Gross Sales Revenue], "MoM", [MoM Revenue Growth], "YoY", [YoY Revenue Growth]) ORDER BY 'Dim_Date'[Year-Month]

EVALUATE SUMMARIZECOLUMNS('Dim_Product'[Product], "Sales", [Product Revenue], "GP", [Product Gross Profit], "Refunds", [Total Refund Amount], "Net", [Net Revenue After Recorded Refunds], "Refund rate", [Product Refund Rate]) ORDER BY 'Dim_Product'[Product]

EVALUATE SUMMARIZECOLUMNS('Dim_Device'[Device], "Sessions", [Total Sessions], "CVR", [Session-to-Order Conversion Rate], "Acquired sales", [Campaign Revenue]) ORDER BY 'Dim_Device'[Device]

EVALUATE SUMMARIZECOLUMNS('Dim_Customer'[Purchase Cohort], 'Dim_CohortAge'[Month After First Purchase], "Cohort size", [Cohort Customers], "Active", [Cohort Active Customers], "Retention", [Cohort Retention %]) ORDER BY 'Dim_Customer'[Purchase Cohort], 'Dim_CohortAge'[Month After First Purchase]

// Noncontiguous complete month selection: Revenue Growth % must be BLANK.
EVALUATE CALCULATETABLE(ROW("Growth", [Revenue Growth %]), TREATAS({"2014-01", "2014-03"}, 'Dim_Date'[Year-Month]))
''',encoding='utf-8')
readme=f'''# Maven Fuzzy Factory — E-Commerce Intelligence

A seven-page Power BI portfolio case study for a **fictional Maven Analytics retailer**. Native PBIP/PBIR report, documented TMDL semantic model, ordered session funnel and independently audited financial evidence.

**Start here:** open [Maven Fuzzy Factory.pbip](powerbi/Maven%20Fuzzy%20Factory.pbip) in Power BI Desktop, confirm PreparedFolder in Manage parameters, then Refresh. Full setup and runtime acceptance: [validation guide](docs/08-validation-and-runtime.md).

## Delivery status

Built: **7 main pages, 7 explanatory tooltip pages, 1 product drillthrough page, 14 model tables, 88 documented DAX measures and 26 single-direction relationships**. Source data is preserved. Metadata import/export and report structural checks have been performed; exact evidence is in qa/.

**Runtime acceptance remains open:** host discovery found no reachable Desktop bridge, and offline MCP cannot execute DAX. Do not claim this project opened successfully or that report screenshots, refresh performance and live interactions passed until the checks in the validation guide are completed. No PBIX or simulated screenshots are presented as verified output.

## Verified full-extract results

| Metric | Value |
|---|---:|
| Recorded sales | ${b['sales']:,.2f} |
| Gross profit before refunds/operating costs | ${b['gross_profit']:,.2f} |
| Gross margin | {b['gross_margin']:.2%} |
| Orders | {b['orders']:,} |
| Sessions | {b['sessions']:,} |
| Session conversion | {b['conversion']:.2%} |
| Recorded refunds | ${b['refunds']:,.2f} |
| Revenue after all recorded refunds | ${b['net_revenue']:,.2f} |

Sales/sessions cover 19 March 2012–19 March 2015; refund events extend through 1 April 2015. Full-extract net revenue includes those later refunds. March 2012/March 2015 are partial months. Estimated gross profit excludes operating costs and does not imply net profitability.

## Explore the deliverables

- [Dataset discovery](docs/01-dataset-discovery.md)
- [Original data dictionary](docs/02-source-data-dictionary.csv) and [model dictionary](docs/03-data-dictionary.csv)
- [KPI definitions and DAX](docs/04-kpi-reference.csv) and [readable DAX listing](docs/04-measures.dax)
- [Model architecture and ERD](docs/05-model-and-relationships.md)
- [Verified insights and recommendations](docs/06-business-insights.md)
- [Seven-page walkthrough](docs/07-report-walkthrough.md)
- [Validation and remaining runtime steps](docs/08-validation-and-runtime.md)
- [Independent review](docs/09-independent-review.md)
- [Portfolio case study](docs/10-portfolio-case-study.md)
- [Reusable Material theme](Maven-Material-Theme.json)
- [_brief/report-spec.md](_brief/report-spec.md)

## Architecture and reproduction

The four independent facts are Orders, Order Items, Refund Events and Sessions. Pageviews are reduced to unique-session reach and ordered funnel flags. Product, Date, Customer, Channel, Device, Visitor and Landing dimensions filter at correct grains. No raw pageview/item join multiplies financial totals. Original CSVs remain in ../Dataset and the reproducible build/audit scripts in ../scripts.

Prepared CSVs are included under data/prepared. Power Query applies explicit typed Import partitions through a configurable PreparedFolder parameter. Regenerate prepared data when raw sources change, then refresh Desktop. This hybrid event-preparation/Power Query workflow is documented, including its two-step refresh boundary. qa/model.bim is the model-authoring interchange artifact; the actual PBIP uses the exported TMDL definition.

## Source and license

Credit: **Maven Analytics**, [Toy Store E-Commerce Database](https://mavenanalytics.io/data-playground/toy-store-e-commerce-database). The provider listing declares **Public Domain** (verified 21 October 2026). Local file counts and fingerprints are authoritative for this supplied extract. This is an educational portfolio project, not a real client engagement; no business outcomes or marketing costs were fabricated.

## Portfolio use

Present the business decision, native-grain model and validation evidence before visual styling. Use actual refreshed Power BI screenshots when available. Describe mobile/funnel/refund recommendations as proposed investigation or experiments; do not claim causal uplift, recovered revenue, paid-media ROI or real-client results.
'''
(OUT/'README.md').write_text(readme,encoding='utf-8')
(OUT/'SOURCE-AND-LICENSE.md').write_text('Data source: Maven Analytics — Toy Store E-Commerce Database.\nProvider: https://mavenanalytics.io/data-playground/toy-store-e-commerce-database\nProvider license listing: Public Domain (verified 2026-10-21).\nSource files were supplied by the user, preserved unchanged, and fingerprinted in qa/source_manifest.json.\nFictional educational business, not a real client. No license is invented for the generated project code; select your preferred code license before public distribution.\n',encoding='utf-8')
(ROOT/'README.md').write_text('# Maven Fuzzy Factory Power BI portfolio\n\nOpen [the project README](Maven%20Fuzzy%20Factory/README.md) for deliverables, verified results and runtime limitations. The original CSVs remain unchanged in Dataset/.\n',encoding='utf-8')
print('Documentation, dictionaries, 88 measure reference expectations, and runtime DAX queries written.')
print('Missing expected measures:',[m['name'] for m in catalog if m['name'] not in expected])
if (QA/'live-all-measures.json').exists():
    import subprocess,sys
    validated=subprocess.run([sys.executable,str(ROOT/'scripts'/'verify_live.py')],check=False)
    if validated.returncode==0: subprocess.run([sys.executable,str(ROOT/'scripts'/'update_runtime_docs.py')],check=True)
