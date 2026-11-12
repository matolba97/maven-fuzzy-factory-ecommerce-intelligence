# Validation evidence and runtime acceptance

## Verified in this environment

- The source-to-prepared audit independently reconciles financial cents, native key sets, every session funnel flag, customer cohorts, source fingerprints and 299 filtered aggregate cells. See qa/independent_validation.json and 09-independent-review.md.
- The preparation audit checks source counts, dates, primary keys, foreign keys, order/item sales/COGS/count consistency, refund linkage/timing, session attribution and ordered funnel monotonicity. See qa/data_checks.csv.
- The complete model was imported using Power BI Modeling MCP, read back and exported into 18 TMDL files. An exported folder was loaded back successfully with 14 tables, 88 measures and 26 relationships. See qa/mcp-model-readback.json. This proves metadata serialization, not DAX execution.
- Static checks resolve DAX/report references, measure formats/descriptions, relationship types, date-table properties, fact isolation and page geometry. See qa/artifact_checks.json. Geometry checks do not establish that text fits at runtime.
- PBIR was validated against the installed report-authoring toolkit and its remote schemas. See qa/pbir-validation.json for the exact final result and any schema-fetch warning; a skipped schema must not be represented as passed.

## Live runtime evidence and remaining acceptance

Initial discovery found no running Desktop instance. The permitted open operation then successfully launched the project and connected a Desktop bridge (qa/desktop-preview-open.json). A live Modeling MCP connection completed full Import refresh. All 88 DAX measures executed successfully, and **903/903 live comparisons pass** against independently calculated references, including 185 cohort-age cells, complete-month/edge/noncontiguous guards, product matching and the full session funnel. See qa/live-all-measures.json, qa/live-contexts.json and qa/live-validation.json. The all-measure query took 159 ms locally; this is a smoke-query timing, not a broad end-to-end performance benchmark.

The delivered TMDL remains the tested authored definition. Desktop adds internal row-number metadata during processing; those engine-generated columns are not hand-authored model fields. Actual screenshot capture succeeded for all seven main pages, seven tooltip pages and the product detail page, with no capture failures. Every captured page was visually reviewed. qa/desktop-screenshot-capture.json records the native capture and docs/11-screenshot-review.md records its scope. Manual end-to-end interaction testing remains a separate acceptance step. No PBIX export is claimed.

## Reproduce and complete interactive acceptance in Power BI Desktop

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
