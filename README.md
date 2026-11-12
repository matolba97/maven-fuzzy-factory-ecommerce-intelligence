# Maven Fuzzy Factory — E-commerce Performance Analysis

Power BI analysis of a fictional online teddy-bear retailer, covering sales, profitability, marketing acquisition, purchase conversion, customer behavior, and refunds.

**[View Interactive Dashboard](https://app.powerbi.com/view?r=eyJrIjoiYWM4NmM1ODctMzNkMS00YWYxLWI1NWQtNTgxZWY5YTQyNTM5IiwidCI6IjJiYjZlNWJjLWMxMDktNDdmYi05NDMzLWMxYzZmNGZhMzNmZiIsImMiOjl9)**

## Project Overview

The dashboard connects website activity with orders, product sales, and refunds to examine how traffic becomes revenue. Seven report pages move from overall performance to acquisition channels, shopping stages, product combinations, and customer purchase cohorts.

The extract contains **472,871 sessions, 32,313 orders, 40,025 sold items, and four products**. Sales and sessions cover March 19, 2012–March 19, 2015; refund events extend through April 1, 2015. This is an educational case study using a fictional business.

## Business Problem

- How do sales, gross profit, and average order value change over time?
- Which traffic sources, campaigns, and devices generate converting sessions?
- Where do sessions leave the shopping journey before purchase?
- Which products and baskets contribute revenue, and where are recorded refunds concentrated?
- How often do observed buyers purchase again, and how does this vary by first-purchase cohort?

## Dashboard Objectives

Provide a consistent view of financial and website performance, compare segments under selected filters, and identify areas for further investigation. The analysis separates traffic volume from conversion quality, product sales from whole-order totals, and refund cash flow from refund incidence among items sold in a particular period.

## Key Metrics & KPIs

Values below describe the full supplied extract. Interactive selections change the displayed context.

| KPI | What it measures | Why it matters |
|---|---|---|
| Recorded sales — **$1,938,509.75** | Order sales before refunds | Establishes sales scale and supports period comparisons. |
| Gross profit — **$1,216,139.50** | Sales less **$722,370.25** in COGS | Shows contribution before refunds and operating expenses; it is not net profit. |
| Gross margin — **62.74%** | Gross profit / sales | Compares profitability relative to sales rather than volume alone. |
| Orders — **32,313** | Number of orders | Separates transaction growth from changes in basket value. |
| Average order value — **$59.99** | Sales / orders | Shows average spend per order before refunds. |
| Sessions — **472,871** | Number of website sessions | Provides the traffic denominator for acquisition and conversion analysis. |
| Session conversion — **6.83%** | Converted sessions / sessions | Measures how often a visit results in an order. |
| Revenue per session | Sales attributed to selected sessions / sessions | Compares traffic value across sources, campaigns, and devices. |
| Stage conversion and abandonment | Sessions progressing to the next ordered stage, and those lost | Locates transitions with the greatest observed drop-off. |
| Recorded refunds — **$85,338.69** | Refund amounts by refund event date | Shows when refunded revenue is recorded. |
| Revenue after recorded refunds — **$1,853,171.06** | Item sales on sale dates less refunds on refund dates | Shows period revenue after refund flows, with matching product scope. |
| Product refund rate | Refunded sold items / units sold in the selected sale cohort | Compares recorded refund incidence; recent sales have less follow-up. |
| Repeat buyer rate — **1.86%** | Buyer IDs with at least two observed purchases / buyer IDs | Describes repeat purchasing within this extract, separately from repeat visits. |

[Full KPI definitions and DAX](Maven%20Fuzzy%20Factory/docs/04-kpi-reference.csv)

## Dashboard Analysis

| Report page | Analytical views |
|---|---|
| Executive Command Center | Sales, gross profit, margin, orders, sessions, and conversion; monthly trends, acquisition value, and leading products. |
| Revenue & Profitability | Sales and profit trends, product contribution, monthly AOV, and valid complete-month MoM/YoY comparisons. |
| Marketing Acquisition | Revenue per session by source, channel trends, campaign comparisons, and desktop/mobile conversion. |
| Conversion Funnel | Ordered Landing → Product → Cart → Shipping → Billing → Purchase journey; stage losses, landing-page outcomes, and conversion over time. |
| Product & Basket | Product sales and gross profit, primary/additional items, observed product combinations, and performance by calendar launch age. |
| Customer Behavior | New/repeat visitor trends, buyer purchase frequency, and monthly first-purchase cohorts. |
| Refunds & Business Risks | Refund amounts over time, product concentration, and refunded-item incidence by original sale cohort. |

Date, year, device, visitor type, and traffic group slicers support segment comparisons. Filters are page-local, so check selections after navigating. KPI tooltips explain definitions; product data points support a Product detail drillthrough page. See the [report walkthrough](Maven%20Fuzzy%20Factory/docs/07-report-walkthrough.md) for interaction details.

## Key Insights

- **Complete-month sales increased:** February 2015 sales were **$129,212.94**, up **95.74%** from February 2014 (**$66,012.52**). March 2012 and March 2015 are partial months and require different treatment.
- **Conversion differs by device:** desktop sessions converted at **8.50%**, compared with **3.09%** on mobile. Comparing source, campaign, and month can help investigate the gap; the aggregate difference does not establish its cause.
- **Product-to-cart progression is a major loss point:** **94,953 of 261,231** product-reaching sessions progressed to cart (**36.35%**); **63.65%** did not. Product includes listing and detail views, and each stage counts a session once in order.
- **Sales are concentrated in one product:** The Original Mr. Fuzzy generated **$1,211,057.74**, or **62.47%** of item sales. Products launched at different dates, so lifetime totals alone do not establish relative performance.
- **Repeat purchasing is limited within the observed window:** **591 of 31,696** buyer IDs made at least two purchases (**1.86%**). This is observed recurrence, not lifetime loyalty or a churn estimate.

These are descriptive findings. Advertising spend, refund reasons, and operating expenses are unavailable, so the report cannot establish ROAS, causes of returns, or net profitability. [Supporting observations and investigation questions](Maven%20Fuzzy%20Factory/docs/06-business-insights.md)

## Dashboard Preview

Actual captures from the Power BI Desktop report.

![Executive page: financial KPIs, monthly sales and profit, acquisition value, and product rankings](docs/screenshots/Executive%20Command%20Center.png)

<details>
<summary>Conversion funnel and product analysis</summary>

![Conversion page: ordered session funnel, stage drop-off, and landing-page comparisons](docs/screenshots/Conversion%20Funnel.png)

![Product page: sales and gross profit comparisons, baskets, and launch-age trends](docs/screenshots/Product%20%26%20Basket.png)

</details>

[Browse all report screenshots](docs/screenshots/)

## Tools & Techniques

- **Power BI Desktop:** interactive report pages, slicers, conditional formatting, report-page tooltips, and product drillthrough.
- **Power Query:** parameterized CSV import and explicit data types.
- **DAX:** financial ratios, acquisition metrics, ordered-stage comparisons, complete-month growth, and customer cohorts.
- **Data modeling:** separate order, item, refund, and session facts with shared dimensions and single-direction relationships to avoid duplicated totals.
- **Python, pandas, NumPy, and SQLite:** data profiling, session-event preparation, basket/cohort derivation, and independent reconciliation.

[Model and relationships](Maven%20Fuzzy%20Factory/docs/05-model-and-relationships.md) · [Validation evidence and limits](Maven%20Fuzzy%20Factory/docs/08-validation-and-runtime.md)

To explore locally, install the Python dependencies, run `python scripts/configure_local.py`, then open [Maven Fuzzy Factory.pbip](Maven%20Fuzzy%20Factory/powerbi/Maven%20Fuzzy%20Factory.pbip) in Power BI Desktop and refresh. Prepared data is included. [Setup and refresh details](Maven%20Fuzzy%20Factory/README.md)

## Data Source

**365 Data Science** is credited as the dataset provider identified by the project owner: [official website](https://365datascience.com/). The specific 365 Data Science dataset or course page could not be confirmed from the supplied files or official-site searches.

The local filenames, data dictionary, and teddy-bear products identify the extract as **Maven Fuzzy Factory**. The verified official matching dataset is [Maven Analytics — Toy Store E-Commerce Database](https://mavenanalytics.io/data-playground/toy-store-e-commerce-database), which credits Maven Analytics and lists a **Public Domain** license. This attribution is retained; distribution through 365 Data Science has not been independently verified.

Six CSV tables contain orders, order items, item refunds, products, website sessions, and pageviews, plus a data dictionary. Transactions support financial and basket analysis; sessions and pageviews support acquisition and ordered conversion analysis. [Source and licensing details](Maven%20Fuzzy%20Factory/SOURCE-AND-LICENSE.md)

## Live Dashboard

[View Interactive Dashboard](https://app.powerbi.com/view?r=eyJrIjoiYWM4NmM1ODctMzNkMS00YWYxLWI1NWQtNTgxZWY5YTQyNTM5IiwidCI6IjJiYjZlNWJjLWMxMDktNDdmYi05NDMzLWMxYzZmNGZhMzNmZiIsImMiOjl9)

Explore the report in Power BI using the corrected sharing URL supplied by the project owner. The same URL is available in this repository's Website field.
