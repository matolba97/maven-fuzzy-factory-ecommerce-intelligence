# Analytical Approach

## Business context

Maven Fuzzy Factory is a fictional online teddy-bear retailer. The report examines how acquisition traffic progresses to purchases, which products contribute sales and gross profit, and how repeat purchases and recorded refunds affect the picture of business performance. See the [main case study](../../README.md) for KPI definitions, report pages, screenshots, and the interactive dashboard.

## Preparing data for analysis

The analysis uses six source tables plus a data dictionary. Profiling checks dates, missing values, primary keys, and relationships before preparing analytical tables. Orders, sold items, refund events, and sessions retain separate row grains so that pageviews or multiple items cannot multiply transaction totals.

Website pageviews are reduced to one row per session with ordered shopping-stage flags. Product listing and detail views share the Product stage. Basket combinations and first-observed purchase cohorts are derived from the recorded transactions. The resulting tables are imported and typed through Power Query.

## Measurement choices

- Financial trends follow order dates; acquisition measures follow session dates. The extract includes 237 session/order pairs that cross calendar dates.
- Refund cash flow follows refund event dates. Refunded-item incidence follows original sale cohorts, including only refunds recorded by the extract cutoff.
- Complete-month growth measures exclude unsupported comparisons at the partial extract boundaries.
- Product refund-adjusted measures use matching sold-product scope. Whole-order headlines on the Revenue page are isolated from product-zone selections.
- Visitor IDs, buyers, repeat visits, and repeat purchases are separate populations. First purchase means first observed purchase in this extract.

## Observations and investigation

Recorded sales total $1,938,509.75, with $1,216,139.50 in gross profit before refunds and operating expenses. Session conversion is 6.83%. Desktop conversion is 8.50% versus 3.09% on mobile; product-to-cart progression is 36.35%. These differences identify useful segments and journey transitions to investigate, without establishing causes or recoverable revenue.

February 2015 sales are 95.74% above February 2014, comparing two complete months. The Original Mr. Fuzzy accounts for 62.47% of item sales, but newer products have shorter observation periods. Further comparisons should account for launch age and, for refunds, the maturity of sale cohorts.

[Detailed findings, denominators, and proposed investigations](06-business-insights.md)

## Evidence and limitations

Independent reconciliation checks exact monetary amounts, row keys, ordered-session flags, and filtered aggregates. Saved Desktop results provide DAX-engine comparisons; their dates and remaining manual acceptance work are documented in the [validation guide](08-validation-and-runtime.md).

Advertising spend, refund reasons, operating expenses, and customer history outside the extract are unavailable. Recommendations are proposed investigations, not measured business outcomes.

## Data attribution

The owner identifies [365 Data Science](https://365datascience.com/) as the dataset provider; its specific dataset/course page could not be confirmed. The local files match the officially published [Maven Analytics Toy Store E-Commerce Database](https://mavenanalytics.io/data-playground/toy-store-e-commerce-database). See [source and licensing details](../SOURCE-AND-LICENSE.md) for the provenance distinction and retained attribution.
