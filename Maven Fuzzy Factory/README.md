# Maven Fuzzy Factory — Project Guide

This Power BI project analyzes sales, gross profitability, website acquisition, purchase conversion, baskets, customer purchase cohorts, and refunds for a fictional teddy-bear retailer.

[Read the portfolio case study](../README.md) · [View Interactive Dashboard](https://app.powerbi.com/view?r=eyJrIjoiYWM4NmM1ODctMzNkMS00YWYxLWI1NWQtNTgxZWY5YTQyNTM5IiwidCI6IjJiYjZlNWJjLWMxMDktNDdmYi05NDMzLWMxYzZmNGZhMzNmZiIsImMiOjl9)

## Open locally

From the repository root:

```powershell
python -m pip install -r requirements.txt
python scripts/configure_local.py
```

Open [Maven Fuzzy Factory.pbip](powerbi/Maven%20Fuzzy%20Factory.pbip) in a Power BI Desktop version supporting PBIP/TMDL, then refresh. The configuration script sets `PreparedFolder` to this clone's prepared data folder. In Desktop editing mode, navigation buttons require Ctrl+click.

Prepared CSVs are included. If raw data changes, run `python scripts/profile_and_prepare.py` from the repository root before refreshing Power BI. Power Query imports and types the prepared tables; event ordering, basket derivation, and cohort preparation run in Python. See the [script guide](../scripts/README.md) for build and audit commands.

## Analytical documentation

- [Dataset discovery](docs/01-dataset-discovery.md)
- [Source dictionary](docs/02-source-data-dictionary.csv) and [model dictionary](docs/03-data-dictionary.csv)
- [KPI definitions](docs/04-kpi-reference.csv) and [DAX listing](docs/04-measures.dax)
- [Model and relationships](docs/05-model-and-relationships.md)
- [Observed findings and investigation questions](docs/06-business-insights.md)
- [Report pages and interactions](docs/07-report-walkthrough.md)
- [Validation evidence and limits](docs/08-validation-and-runtime.md)
- [Independent reconciliation](docs/09-independent-review.md)
- [Analytical approach](docs/10-portfolio-case-study.md)
- [Screenshots](screenshots/) and [capture review](docs/11-screenshot-review.md)
- [Data attribution and licensing](SOURCE-AND-LICENSE.md)

## Interpretation and validation

Sales and sessions span March 19, 2012–March 19, 2015; refund events extend through April 1, 2015. Both boundary sales months are partial. Gross profit precedes refunds and operating expenses. Refund cash flow follows event dates; product refund incidence follows the original sale cohort and is limited by the observation cutoff.

The saved October 21, 2026 Desktop run executed all 88 measures and passed 903 comparisons against independently calculated references. Source reconciliation passed 54 checks. These are historical validation results; `verify_live.py` compares saved engine evidence and does not query a running report. Exhaustive manual tooltip, filtering, and drillthrough acceptance remains a documented limitation.

## Data Source

The project owner identifies **[365 Data Science](https://365datascience.com/)** as the dataset provider; the specific dataset/course page could not be confirmed. The supplied files match **[Maven Analytics — Toy Store E-Commerce Database](https://mavenanalytics.io/data-playground/toy-store-e-commerce-database)**. Its official listing credits Maven Analytics and declares Public Domain. Both the owner's stated provider and the verified matching source are documented in the [attribution note](SOURCE-AND-LICENSE.md).
