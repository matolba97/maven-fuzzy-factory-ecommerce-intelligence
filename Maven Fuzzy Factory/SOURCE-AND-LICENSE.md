# Data Source and Licensing

## Provider identified by the project owner

The project owner identifies **365 Data Science** as the provider through which the dataset was obtained: [official website](https://365datascience.com/).

The specific 365 Data Science dataset or course/project page could not be confirmed. No 365 source URL appears in the local data dictionary or existing source references, and official-site searches did not establish a matching page. Distribution through 365 Data Science therefore remains unverified.

## Verified matching dataset

The supplied filenames, `maven_fuzzy_factory_data_dictionary.csv`, six-table structure, and products such as The Original Mr. Fuzzy identify the extract as Maven Fuzzy Factory.

[Maven Analytics — Toy Store E-Commerce Database](https://mavenanalytics.io/data-playground/toy-store-e-commerce-database) describes the same fictional teddy-bear retailer, website sessions, pageviews, orders, and returns. The official listing credits **Maven Analytics** and lists the license as **Public Domain** (checked November 12, 2026). This verified attribution is preserved alongside the owner's stated provider.

## Contents and use

- `orders.csv`: transaction totals and order-level cost of goods sold.
- `order_items.csv`: individual sold items, products, and primary/additional-item economics.
- `order_item_refunds.csv`: recorded refunds linked to sold items.
- `products.csv`: four products and their creation dates.
- `website_sessions.csv`: visitor IDs, device types, campaigns, sources, and referrers.
- `website_pageviews.csv`: session-linked page events used to reconstruct ordered shopping stages.
- `maven_fuzzy_factory_data_dictionary.csv`: source field descriptions.

Source files were supplied by the owner and preserved unchanged. File fingerprints are recorded in `qa/source_manifest.json`. Financial, acquisition, basket, cohort, and refund analysis uses these files; the business is fictional and this is an educational portfolio case study.

## Project code

No separate open-source license has been granted for project code. The dataset's Public Domain listing does not automatically license the report, scripts, or other project assets.
