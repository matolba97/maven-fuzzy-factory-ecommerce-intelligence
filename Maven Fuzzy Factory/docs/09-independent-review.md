# Independent source and semantic review

The independent source-to-prepared audit passes **54 of 54 checks**. It compares 299 month/device/product/refund-month aggregate cells and every prepared order, item, refund and session against the supplied source CSVs. Exact integer cents reconcile; native primary keys are unique and their sets match the sources. The six source data-file SHA-256 hashes match the preparation manifest. The data dictionary is additionally fingerprinted in the independent audit.

Reproduce with `scripts/independent_validate.py`. The script uses Python's CSV reader, Decimal-to-integer cents, and SQLite to sort all 1,188,124 pageviews. It does not import or call the preparation implementation. Detailed evidence and filtered November 2014/March 2015 samples are in `qa/independent_validation.json`.

| Verified full-extract measure | Value |
|---|---:|
| Recorded orders | 32,313 |
| Sold items | 40,025 |
| Sessions | 472,871 |
| Recorded sales | $1,938,509.75 |
| Recorded COGS | $722,370.25 |
| Gross profit before refunds | $1,216,139.50 |
| Recorded refunds | $85,338.69 |
| Revenue after all recorded refunds | $1,853,171.06 |
| Observed buyer IDs | 31,696 |
| Buyer IDs with at least two orders | 591 |

## Funnel verification

An independently coded one-pass state machine processes each session's sorted events and records the earliest valid progression. Repeated pageviews never multiply a session. The results match every prepared session flag:

| Sequential stage | Distinct sessions |
|---|---:|
| Landing | 472,871 |
| Product listing or detail | 261,231 |
| Cart | 94,953 |
| Shipping | 64,484 |
| Billing | 52,058 |
| Purchase with confirmation and linked order | 32,313 |

Strictly increasing timestamps yield the same counts as the deterministic timestamp/pageview-ID ordering. All 32,313 linked confirmation events share their associated order timestamp. The purchase criterion correctly allows an order at the billing/confirmation time rather than requiring it to occur strictly after confirmation.

## Date, channel and customer interpretation

- There are **237 orders whose order calendar date differs from the session-start date**. Session conversion and campaign revenue must share session-date attribution; recorded sales use order date. Combining order-date orders with session-date sessions would introduce a boundary mismatch.
- Refund event-date cash flow and original-sale-cohort refunds are separate legitimate questions. Full-extract net revenue above includes refund events through **1 April 2015**. A selection ending on the last sales date, 19 March 2015, excludes subsequent refund events and therefore produces a different period-flow result.
- The first and final sales months, March 2012 and March 2015, are partial. The initial complete-month flag incorrectly included January–March 2012; this was corrected and the independent calendar check now passes. Complete interior months run April 2012–February 2015.
- The boundary calendar days are also partial: first order **19 March 2012 10:42:46**; final order **19 March 2015 05:38:31**. A growth comparison claiming complete calendar-day coverage should use fully interior dates or disclose boundary-day exposure.
- Observed elapsed timestamp refund lags are 2–16 days, median 9.25 days and 95th percentile 15.25 days. These elapsed-time statistics differ from the model's `Refund Lag Days`, which subtracts normalized calendar dates. The latter is independently verified against every raw refund/item date: zero mismatches, range **2–16 calendar days**, mean **9.086655 calendar days**. Latest March sales have less than 16 days of follow-up by the refund cutoff. Recorded product refund incidence is right-censored and must not be described as a final defect rate. Observed maximum lag is evidence about this extract, not a guaranteed future refund window.
- Source missing marketing fields contain the literal `NULL`; the prepared `(not tagged)` normalization matches them. Tagged search/social and untagged search-referral labels are defensible observed-data classifications. The dictionary does not establish ad spend, paid status, verified organic status, acquisition cost, or marketing ROI.
- Every prepared first-purchase date, calendar-month cohort and observed lifetime order count matches independently sorted source orders. Buyer IDs are observed website IDs. First purchase is first observed purchase; prior history outside the extract and cross-device identity resolution are unavailable.

## Semantic-model review scope

Read-only inspection of `scripts/build_model.py` found distinct financial, session, item and refund grains, single-direction dimension relationships, and appropriately separated event-date versus sale-cohort refund measures. Full-month MoM/YoY guards exclude partial extract months. Cohort activity blanks incomplete/future calendar months; month zero is the first observed purchase month. This static inspection is separate from live engine validation.

Two semantic safeguards were communicated for implementation review:

1. `Revenue Growth %` must reject noncontiguous date selections or explicitly expand both periods to their complete envelopes. Otherwise its selected-date numerator can be compared with a contiguous prior MIN–MAX window of a different exposure. Partial boundary days also need a deliberate coverage rule.
2. Cohort denominators describe original first-purchase cohorts. Channel/device filters on subsequent order facts instead describe activity attributed to those later orders, not first-acquisition-channel retention. The cohort view should disable those acquisition interactions, remove those filters consistently, or state that interpretation explicitly.

## Verified business observations

- Desktop session conversion is **8.50%** (27,805/327,027), versus **3.09%** on mobile (4,508/145,844). This supports investigating mobile experience and traffic mix; it does not isolate a causal device effect.
- February 2015 recorded sales were **$129,212.94**, **95.74% above February 2014**. Both are fully observed months; March's incomplete period should not be used as the next full-month decline.
- The Original Mr. Fuzzy contributed **$1,211,057.74**, or approximately 62.47% of recorded item sales. The Birthday Sugar Panda has the highest full-extract recorded item refund incidence, **6.04%** (301/4,985), compared with **5.11%** for the Original Mr. Fuzzy. Product launch timing and refund follow-up differ, so investigate mature cohorts before attributing the difference to quality.
- Only **1.86%** of observed buyer IDs placed at least two recorded orders (591/31,696). This is distinct from repeat website sessions and describes the available observation window rather than lifetime loyalty.

## Final model/report review and resolution status

The growth measure now requires contiguous dates and fully observed interior calendar days, 20 March 2012–18 March 2015. Cohort activity now removes date, channel, device, visitor and landing filters; its denominator remains the original observed first-purchase cohort. The customer-page footnote explicitly discloses that behavior. Both earlier semantic safeguards are resolved in the inspected scripts.

The authored report contains seven visible pages, seven hidden tooltip pages, and a hidden product drillthrough page. An initial read-only recursive binding check found **216 bound column/measure references and zero unresolved references** against the generated semantic model. The final generated report contains **302 actual visuals with 302 unique IDs**, exactly matching its 302-entry manifest; the executive chart/slicer ID collision is resolved. The saved PBIR validation result has **zero errors and zero warnings**, and the final artifact QA file records **50 of 50 static checks passing**. Funnel stage labels have the model's `Stage Order` sort binding. Their disconnected axis intentionally chooses among precomputed session flags; selecting a stage does not itself filter other visuals to the sessions that reached that stage. No pageview-row counting or arithmetic funnel inversion was found.

The three concrete report/model findings are now **resolved in the inspected scripts and generated artifacts**:

1. **Matched product scope in refund-adjusted financials.** `Net Revenue After Recorded Refunds` now uses `[Product Revenue] - [Total Refund Amount]`; `Gross Profit After Refunds (No Recovery)` uses `[Product Gross Profit] - [Total Refund Amount]`; `Refund Amount %` divides refunds by product revenue. Item sales and COGS reconcile to orders across all products, while product selections now filter both sides consistently. The Revenue page additionally contains **16 explicit `NoFilter` interactions**: its two product evidence visuals do not filter the six financial headline cards, order-date trend, or monthly table. This keeps that overview's financial scope consistent.
2. **Product sales/profit comparison.** The generated two-measure product visual now uses `clusteredBarChart`, comparing sales and gross profit side by side without adding profit on top of sales.
3. **Drillthrough refund tooltip.** The generated `Product Refund Rate` drillthrough card now targets the Refunds page's tooltip section, which includes that rate's definition and refund-follow-up caveat.

No remaining concrete issue was found within this final repair review.

## Confirmed live model validation; visual acceptance pending

The desktop bridge subsequently connected and the full Import refresh succeeded. The `PreparedFolder` parameter now uses literal M backslashes rather than JSON string escaping; the successful refresh confirms the repaired source paths resolve in the live model.

Reviewed `qa/live-all-measures.json`, `qa/live-contexts.json`, `qa/live-validation.json`, and `scripts/verify_live.py`. **All 88 measures executed in the actual Desktop DAX engine. All 903 reference comparisons passed, with zero failures**, covering the whole extract, sequential funnel stages, monthly revenue/profit and MoM/YoY, product scope and refunds, device conversion, customer cohorts/maturity, and noncontiguous/partial/empty-context guards. The references are grounded in the source-audited prepared data and baselines described above. Currency division comparisons allow 0.0001001 USD absolute tolerance for fixed-decimal DAX arithmetic; monetary sums reconcile to the recorded cents. The saved all-measure query reports **159 ms** execution time for that run; this is one query observation, not a report performance benchmark.

**Remaining acceptance scope:** screenshots, visual layout/formatting, and manual report interactions are pending. Confirmed refresh and DAX results establish live model execution and the tested numerical contexts; they do not independently establish visual rendering, hover behavior, drillthrough/navigation, or actual click interactions.
