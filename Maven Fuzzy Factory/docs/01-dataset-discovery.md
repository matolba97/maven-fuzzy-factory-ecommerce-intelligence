# Initial dataset discovery

Source: the seven user-supplied CSV files in `../Dataset`; originals retained unchanged.

| Table | Rows | First timestamp | Last timestamp |
|---|---:|---|---|
| orders.csv | 32,313 | 2012-03-19 10:42:46 | 2015-03-19 05:38:31 |
| order_items.csv | 40,025 | 2012-03-19 10:42:46 | 2015-03-19 05:38:31 |
| order_item_refunds.csv | 1,731 | 2012-04-06 11:32:43 | 2015-04-01 18:11:08 |
| products.csv | 4 | 2012-03-19 08:00:00 | 2014-02-05 10:00:00 |
| website_sessions.csv | 472,871 | 2012-03-19 08:04:16 | 2015-03-19 07:59:08 |
| website_pageviews.csv | 1,188,124 | 2012-03-19 08:04:16 | 2015-03-19 07:59:32 |

Checks: 44 executed; 44 passed.

See `qa/column_profile.csv` for every actual source column, null count, distinct count and inferred type; `qa/source_manifest.json` records immutable SHA-256 fingerprints.

## Modeling decisions

- Facts retain their native grain. Orders and items reconcile in cents before enrichment. No raw pageview-to-order joins.
- Pageviews are reduced to one session row with distinct reach flags and strict ordered funnel flags. Raw pageviews remain in the source folder.
- Product means listing or one of the four observed detail URLs. Billing combines /billing and /billing-2. Purchase requires a later confirmation page plus a linked order at/after billing.
- The (timestamp, pageview ID) pair provides deterministic ordering for tied timestamps; repeated views count once per stage.
- Sessions and session-attributed revenue use session date. Sales use order date. Refund cash flow uses refund date; item refund incidence uses original sale date.
- Traffic labels describe observed tagging/referrers. Tagged traffic is not asserted to be paid; untagged search is a referral proxy, not verified organic traffic.
- Full calendar years are loaded. March 2012 and March 2015 are partial observation months; complete-month comparisons exclude them.
- Customer identifiers are observed website user IDs, not verified people or merged identities. First purchase/cohort means first observed purchase.

## Exceptions

[]