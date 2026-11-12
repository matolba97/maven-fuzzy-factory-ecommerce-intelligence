# Maven Fuzzy Factory — portfolio case study

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
