# Report walkthrough and interaction guide

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
