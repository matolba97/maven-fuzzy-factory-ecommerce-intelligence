# Maven Fuzzy Factory — E-Commerce Intelligence

A seven-page Power BI portfolio case study for a **fictional Maven Analytics retailer**. Native PBIP/PBIR report, documented TMDL semantic model, ordered session funnel and independently audited financial evidence.

**Start here:** open [Maven Fuzzy Factory.pbip](powerbi/Maven%20Fuzzy%20Factory.pbip) in Power BI Desktop, confirm PreparedFolder in Manage parameters, then Refresh. Full setup and runtime acceptance: [validation guide](docs/08-validation-and-runtime.md).

## Delivery status

Built: **7 main pages, 7 explanatory tooltip pages, 1 product drillthrough page, 14 model tables, 88 documented DAX measures and 26 single-direction relationships**. Source data is preserved. Metadata import/export and report structural checks have been performed; exact evidence is in qa/.

**Live model verified:** Desktop opened the PBIP, connected its bridge and completed a full Import refresh. All 88 measures executed successfully; 903/903 comparisons across whole-extract, month, product, device, stage, cohort and guard contexts match independently calculated references. The all-measure query elapsed 159 ms in this local run. All 15 report/support pages were captured from the actual refreshed Desktop report and visually reviewed. Manual end-to-end hover/click/drillthrough acceptance remains separate; no PBIX export is claimed.

## Verified full-extract results

| Metric | Value |
|---|---:|
| Recorded sales | $1,938,509.75 |
| Gross profit before refunds/operating costs | $1,216,139.50 |
| Gross margin | 62.74% |
| Orders | 32,313 |
| Sessions | 472,871 |
| Session conversion | 6.83% |
| Recorded refunds | $85,338.69 |
| Revenue after all recorded refunds | $1,853,171.06 |

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

## Actual Power BI screenshots

![Executive Command Center](screenshots/Executive%20Command%20Center.png)

[All captured pages](screenshots/) · [Screenshot review](docs/11-screenshot-review.md)
