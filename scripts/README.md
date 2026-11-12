# Reproducible build tools

Install the workspace requirements into your chosen Python environment. The original sources remain in `../Dataset/`; generated deliverables live in `../Maven Fuzzy Factory/`.

1. `profile_and_prepare.py` fingerprints/profile-checks raw files and creates native-grain prepared analytical CSVs, source audits and baseline summaries. Run when source data changes.
2. `build_model.py` creates the complete `qa/model.bim` authoring interchange model, documented DAX catalog and PBIP model metadata. **It does not serialize TMDL itself.** Import that BIM through Power BI Modeling MCP, then run `ExportToTmdlFolder` targeting `powerbi/Maven Fuzzy Factory.SemanticModel/definition` before opening Desktop. The delivered TMDL has already been exported and reloaded successfully.
3. `build_report.py` creates the seven visible PBIR pages, seven hidden report tooltips, product drillthrough page and theme. Its deterministic visual/page IDs preserve binding names, and duplicate visual identifiers are rejected.
4. `independent_validate.py` independently reconstructs the funnel and financials using CSV, Decimal and SQLite. It does not import the preparation code.
5. `verify_artifacts.py` checks model/reference/relationship metadata, report geometry, source integrity and modeling safeguards. It does not execute DAX or render the report.
6. `finalize_docs.py` generates dictionaries, case-study documentation, all-measure expected reference values and DAX runtime acceptance queries.

Run the report authoring toolkit's `validate` on the final `.Report` folder after edits, then complete actual Desktop refresh/DAX/render/screenshot acceptance. Do not infer runtime success from a JSON or TMDL parse. A local source rebuild does not change an already-open Desktop model until its definitions and data are reloaded.
