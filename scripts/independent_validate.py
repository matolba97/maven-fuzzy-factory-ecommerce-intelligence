"""Independent source-to-prepared audit, using csv, sqlite and exact integer cents.

Does not import the preparation code or alter the sources or prepared model.
"""
from pathlib import Path
from collections import Counter, defaultdict
from decimal import Decimal
from datetime import datetime
import csv, hashlib, json, sqlite3

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'Dataset'
OUT = ROOT / 'Maven Fuzzy Factory'
PREP = OUT / 'data' / 'prepared'
checks = []

def rows(path):
    with path.open(newline='', encoding='utf-8-sig') as f:
        yield from csv.DictReader(f)

def money(value):
    return int(Decimal(str(value)) * 100)

def check(name, actual, expected):
    checks.append({'check': name, 'actual': actual, 'expected': expected,
                   'status': 'PASS' if actual == expected else 'FAIL'})

def indexed(name, key):
    result = {}
    duplicates = 0
    for row in rows(SRC / (name + '.csv')):
        ident = int(row[key])
        duplicates += ident in result
        result[ident] = row
    check(name + ' unique keys', duplicates, 0)
    return result

orders = indexed('orders', 'order_id')
items = indexed('order_items', 'order_item_id')
refunds = indexed('order_item_refunds', 'order_item_refund_id')
sessions = indexed('website_sessions', 'website_session_id')
products = indexed('products', 'product_id')
by_session = defaultdict(list)
by_customer = defaultdict(list)
by_order = defaultdict(list)
refund_by_item = Counter()
for oid, row in orders.items():
    by_session[int(row['website_session_id'])].append(row)
    by_customer[int(row['user_id'])].append((row['created_at'], oid))
for iid, row in items.items():
    by_order[int(row['order_id'])].append(row)
for row in refunds.values():
    refund_by_item[int(row['order_item_id'])] += money(row['refund_amount_usd'])

source = {
    'orders': len(orders), 'items': len(items), 'refund_events': len(refunds),
    'sessions': len(sessions), 'products': len(products),
    'sales_cents': sum(money(r['price_usd']) for r in orders.values()),
    'cogs_cents': sum(money(r['cogs_usd']) for r in orders.values()),
    'refund_cents': sum(money(r['refund_amount_usd']) for r in refunds.values()),
    'buyers': len(by_customer),
    'users': len(set(r['user_id'] for r in sessions.values())),
    'converted_sessions': len(by_session),
    'repeat_buyers': sum(len(v) > 1 for v in by_customer.values()),
}
source['gross_profit_cents'] = source['sales_cents'] - source['cogs_cents']
source['net_revenue_cents'] = source['sales_cents'] - source['refund_cents']
check('Order and item revenue reconciles in integer cents',
      sum(money(r['price_usd']) for r in items.values()), source['sales_cents'])
check('Order and item COGS reconciles in integer cents',
      sum(money(r['cogs_usd']) for r in items.values()), source['cogs_cents'])
check('Every order has exact item revenue, COGS and quantity', sum(
    (sum(money(i['price_usd']) for i in by_order[oid]) != money(o['price_usd']) or
     sum(money(i['cogs_usd']) for i in by_order[oid]) != money(o['cogs_usd']) or
     len(by_order[oid]) != int(o['items_purchased'])) for oid, o in orders.items()), 0)

# SQLite provides an independent event sort. A single-pass state machine records
# the earliest valid chain rather than joining stage tables or copying pandas code.
db = sqlite3.connect(':memory:')
db.execute('CREATE TABLE pageviews (session INTEGER, stamp TEXT, id INTEGER PRIMARY KEY, url TEXT)')
batch = []
for row in rows(SRC / 'website_pageviews.csv'):
    batch.append((int(row['website_session_id']), row['created_at'],
                  int(row['website_pageview_id']), row['pageview_url']))
    if len(batch) == 25000:
        db.executemany('INSERT INTO pageviews VALUES (?,?,?,?)', batch)
        batch.clear()
db.executemany('INSERT INTO pageviews VALUES (?,?,?,?)', batch)
db.execute('CREATE INDEX pageview_sort ON pageviews(session, stamp, id)')
source['pageviews'] = db.execute('SELECT COUNT(*) FROM pageviews').fetchone()[0]
stage_urls = [
    {'/products','/the-original-mr-fuzzy','/the-forever-love-bear',
     '/the-birthday-sugar-panda','/the-hudson-river-mini-bear'},
    {'/cart'}, {'/shipping'}, {'/billing','/billing-2'}, {'/thank-you-for-your-order'},
]
url_stage = {url: n for n, urls in enumerate(stage_urls) for url in urls}
names = ['Product','Cart','Shipping','Billing','Confirmation']
computed = {}
strict_timestamp_counts = Counter()
confirmation_order_delta = Counter()
def finish(sid, rec):
    if sid is None:
        return
    linked = by_session.get(sid, [])
    rec['converted'] = int(bool(linked))
    rec['orders'] = len(linked)
    rec['revenue'] = sum(money(o['price_usd']) for o in linked)
    rec['purchase'] = int(rec['next_stage'] == 5 and any(
        o['created_at'] >= rec['billing'] for o in linked))
    for n in range(rec['strict_stage']):
        strict_timestamp_counts[names[n]] += 1
    if rec['next_stage'] == 5:
        for order in linked:
            delta = int((datetime.fromisoformat(rec['confirmation']) -
                         datetime.fromisoformat(order['created_at'])).total_seconds())
            confirmation_order_delta['confirmation_before_order' if delta < 0 else
                                     'same_second' if delta == 0 else 'confirmation_after_order'] += 1
    computed[sid] = rec

current = None
record = None
for sid, stamp, pid, url in db.execute('SELECT session, stamp, id, url FROM pageviews ORDER BY session, stamp, id'):
    if sid != current:
        finish(current, record)
        current = sid
        record = {'pageviews': 0, 'landing': url, 'reach': set(), 'next_stage': 0,
                  'strict_stage': 0, 'strict_stamp': '', 'billing': None, 'confirmation': None}
    record['pageviews'] += 1
    stage = url_stage.get(url)
    if stage is not None:
        record['reach'].add(stage)
        if stage == record['next_stage']:
            record['next_stage'] += 1
            if stage == 3:
                record['billing'] = stamp
            if stage == 4:
                record['confirmation'] = stamp
        if stage == record['strict_stage'] and stamp > record['strict_stamp']:
            record['strict_stage'] += 1
            record['strict_stamp'] = stamp
finish(current, record)
check('One computed pageview summary per source session', len(computed), len(sessions))
funnel = {'Landing': len(sessions)}
funnel.update({names[n]: sum(r['next_stage'] > n for r in computed.values()) for n in range(4)})
funnel['Purchase'] = sum(r['purchase'] for r in computed.values())
source['funnel'] = funnel
source['bounced'] = sum(r['pageviews'] == 1 for r in computed.values())

fact_mismatches = Counter()
prepared_counts = Counter()
prepared_totals = Counter()
prepared_keys = defaultdict(set)
prepared_duplicate_keys = Counter()
prepared_channels = {r['Channel ID']: r for r in rows(PREP / 'Dim_Channel.csv')}
def add_key(table, ident):
    prepared_duplicate_keys[table] += ident in prepared_keys[table]
    prepared_keys[table].add(ident)

def channel_agrees(prepared, session):
    channel = prepared_channels[prepared['Channel ID']]
    return all(channel[p] == ('(not tagged)' if session[s] in ('', 'NULL') else session[s]) for p, s in
               [('Campaign','utm_campaign'), ('Ad Content','utm_content'), ('Referrer','http_referer')])
source_groups = defaultdict(Counter)
prepared_groups = defaultdict(Counter)
purchase_num = {}
for history in by_customer.values():
    for n, (_, oid) in enumerate(sorted(history), 1):
        purchase_num[oid] = n
for oid, o in orders.items():
    s = sessions[int(o['website_session_id'])]
    key = 'order_month_device|' + o['created_at'][:7] + '|' + s['device_type']
    source_groups[key].update(orders=1, sales_cents=money(o['price_usd']), cogs_cents=money(o['cogs_usd']))
for iid, i in items.items():
    s = sessions[int(orders[int(i['order_id'])]['website_session_id'])]
    key = 'sale_month_device_product|' + i['created_at'][:7] + '|' + s['device_type'] + '|' + i['product_id']
    source_groups[key].update(units=1, sales_cents=money(i['price_usd']),
                              cogs_cents=money(i['cogs_usd']), refund_cents=refund_by_item[iid])
for rid, r in refunds.items():
    key = 'refund_month|' + r['created_at'][:7]
    source_groups[key].update(events=1, refund_cents=money(r['refund_amount_usd']))

for r in rows(PREP / 'Fact_Orders.csv'):
    prepared_counts['orders'] += 1
    oid = int(r['Order ID'])
    add_key('orders', oid)
    o = orders[oid]
    prepared_totals['sales_cents'] += money(r['Sales Amount'])
    prepared_totals['cogs_cents'] += money(r['COGS Amount'])
    fact_mismatches['order row financials/date/sequence'] += any([
        money(r['Sales Amount']) != money(o['price_usd']), money(r['COGS Amount']) != money(o['cogs_usd']),
        r['Order Date'] != o['created_at'][:10], int(r['Purchase Number']) != purchase_num[oid]])
    fact_mismatches['order attribution/customer/primary product'] += any([
        r['Customer ID'] != o['user_id'], r['Primary Product ID'] != o['primary_product_id'],
        r['Website Session ID'] != o['website_session_id'],
        not channel_agrees(r, sessions[int(o['website_session_id'])])])
    key = 'order_month_device|' + r['Order Date'][:7] + '|' + r['Device']
    prepared_groups[key].update(orders=1, sales_cents=money(r['Sales Amount']), cogs_cents=money(r['COGS Amount']))
for r in rows(PREP / 'Fact_OrderItems.csv'):
    prepared_counts['items'] += 1
    iid = int(r['Order Item ID'])
    add_key('items', iid)
    i = items[iid]
    fact_mismatches['item row financials/date/refund/product'] += any([
        money(r['Item Sales Amount']) != money(i['price_usd']), money(r['Item COGS Amount']) != money(i['cogs_usd']),
        money(r['Recorded Refund']) != refund_by_item[iid], r['Order Date'] != i['created_at'][:10],
        r['Product ID'] != i['product_id']])
    key = 'sale_month_device_product|' + r['Order Date'][:7] + '|' + r['Device'] + '|' + r['Product ID']
    prepared_groups[key].update(units=1, sales_cents=money(r['Item Sales Amount']),
                                cogs_cents=money(r['Item COGS Amount']), refund_cents=money(r['Recorded Refund']))
for r in rows(PREP / 'Fact_Refunds.csv'):
    prepared_counts['refund_events'] += 1
    add_key('refund_events', int(r['Refund ID']))
    raw = refunds[int(r['Refund ID'])]
    prepared_totals['refund_cents'] += money(r['Refund Amount'])
    fact_mismatches['refund row financials/date/original sale date'] += any([
        money(r['Refund Amount']) != money(raw['refund_amount_usd']), r['Refund Date'] != raw['created_at'][:10],
        r['Order Date'] != orders[int(raw['order_id'])]['created_at'][:10]])
    key = 'refund_month|' + r['Refund Date'][:7]
    prepared_groups[key].update(events=1, refund_cents=money(r['Refund Amount']))
for r in rows(PREP / 'Fact_Sessions.csv'):
    prepared_counts['sessions'] += 1
    sid = int(r['Website Session ID'])
    add_key('sessions', sid)
    raw = sessions[sid]
    c = computed[sid]
    expected = {'Pageviews': c['pageviews'], 'Bounced': int(c['pageviews'] == 1), 'Converted': c['converted'],
                'Session Orders': c['orders'], 'Session Revenue': c['revenue']}
    for field, value in expected.items():
        actual = money(r[field]) if field == 'Session Revenue' else int(r[field])
        fact_mismatches['session ' + field] += actual != value
    fact_mismatches['session date/landing/customer/device'] += any([
        r['Session Date'] != raw['created_at'][:10], r['Landing Page'] != c['landing'],
        r['Customer ID'] != raw['user_id'], r['Device'] != raw['device_type']])
    fact_mismatches['session channel/source flag'] += any([
        not channel_agrees(r, raw),
        r['Visitor Type'] != ('Repeat visitor session' if raw['is_repeat_session'] == '1' else 'New visitor session')])
    for n, name in enumerate(names):
        fact_mismatches['reach ' + name] += int(r['Reach ' + name]) != int(n in c['reach'])
        if n < 4:
            fact_mismatches['sequential ' + name] += int(r['Sequential ' + name]) != int(c['next_stage'] > n)
    fact_mismatches['sequential Purchase'] += int(r['Sequential Purchase']) != c['purchase']
for key, count in prepared_counts.items():
    check('Prepared native row count ' + key, count, source[key])
    check('Prepared primary key unique ' + key, prepared_duplicate_keys[key], 0)
for name, original in [('orders', orders), ('items', items), ('refund_events', refunds), ('sessions', sessions)]:
    check('Prepared primary key set matches source ' + name, len(prepared_keys[name] ^ set(original)), 0)
for key, amount in prepared_totals.items():
    check('Prepared financial total ' + key, amount, source[key])
for name, count in fact_mismatches.items():
    check('All rows: ' + name, count, 0)
group_keys = set(source_groups) | set(prepared_groups)
check('Every month/device/product/refund-month cell reconciles',
      sum(source_groups[k] != prepared_groups[k] for k in group_keys), 0)

customer_errors = 0
for r in rows(PREP / 'Dim_Customer.csv'):
    history = by_customer.get(int(r['Customer ID']), [])
    first = min(history)[0][:10] if history else ''
    customer_errors += any([r['First Purchase Date'] != first,
                           int(r['Observed Lifetime Orders']) != len(history),
                           r['Purchase Cohort'] != (first[:7] if first else 'No observed purchase')])
check('Every customer observed purchase/cohort/frequency input', customer_errors, 0)

start = min(r['created_at'] for r in orders.values())
end = max(r['created_at'] for r in orders.values())
partial_flagged = []
for r in rows(PREP / 'Dim_Date.csv'):
    # Only fully interior months can be certified from this extract.
    expected = int(start[:7] < r['Date'][:7] < end[:7])
    if int(r['Is Complete Sales Month']) != expected:
        partial_flagged.append(r['Date'])
check('Complete-month flag excludes partial and uncovered months', len(partial_flagged), 0)
manifest = json.loads((OUT / 'qa' / 'source_manifest.json').read_text())
hashes = {}
for path in SRC.glob('*.csv'):
    hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
for r in manifest:
    check('Source preservation fingerprint ' + r['file'], hashes[r['file']], r['sha256'])

channel_inventory = Counter()
for s in sessions.values():
    channel_inventory[(s['utm_source'], s['utm_campaign'], s['http_referer'])] += 1
lags = sorted((datetime.fromisoformat(r['created_at']) -
               datetime.fromisoformat(items[int(r['order_item_id'])]['created_at'])).total_seconds()/86400
              for r in refunds.values())
refund_sales_months = defaultdict(Counter)
for iid, i in items.items():
    m = i['created_at'][:7]
    refund_sales_months[m].update(items=1, refunded_items=int(iid in refund_by_item))
device_results = defaultdict(Counter)
for sid, s in sessions.items():
    linked = by_session.get(sid, [])
    device_results[s['device_type']].update(sessions=1, converted_sessions=int(bool(linked)),
                                           revenue_cents=sum(money(o['price_usd']) for o in linked))
product_results = defaultdict(Counter)
for iid, i in items.items():
    product_results[i['product_id']].update(units=1, revenue_cents=money(i['price_usd']),
        cogs_cents=money(i['cogs_usd']), refunded_items=int(iid in refund_by_item), refund_cents=refund_by_item[iid])
order_month_results = defaultdict(Counter)
for o in orders.values():
    order_month_results[o['created_at'][:7]].update(orders=1, sales_cents=money(o['price_usd']))
audit = {
    'method': 'Independent builtin csv reader, Decimal to integer cents, SQLite sorted pageviews and single-pass state machine; preparation script not imported.',
    'source_baseline': source, 'checks': checks,
    'group_cells_compared': len(group_keys),
    'filter_samples': [{'filter': k, 'source': dict(source_groups[k]), 'prepared': dict(prepared_groups[k])}
                       for k in sorted(group_keys) if ('2014-11|' in k or '2015-03|' in k or k.startswith('refund_month|2015'))],
    'strict_timestamp_stage_counts': dict(strict_timestamp_counts),
    'confirmation_relative_to_order': dict(confirmation_order_delta),
    'complete_month_mismatched_dates': partial_flagged,
    'coverage': {'first_order': start, 'last_order': end,
                 'last_refund': max(r['created_at'] for r in refunds.values()),
                 'refund_lag_days_min': min(lags), 'refund_lag_days_median': lags[len(lags)//2],
                 'refund_lag_days_p95': lags[int((len(lags)-1)*.95)], 'refund_lag_days_max': max(lags)},
    'recorded_item_refund_incidence_by_sale_month': [
        {'sale_month': m, **v, 'incidence': v['refunded_items']/v['items']}
        for m, v in sorted(refund_sales_months.items())],
    'channel_inventory': [{'utm_source': k[0], 'utm_campaign': k[1], 'http_referer': k[2], 'sessions': n}
                          for k, n in channel_inventory.most_common()],
    'source_device_results': dict(device_results),
    'source_product_results': dict(product_results),
    'source_order_month_results': dict(order_month_results),
    'orders_on_different_date_than_session': sum(o['created_at'][:10] != sessions[int(o['website_session_id'])]['created_at'][:10]
                                                for o in orders.values()),
    'source_sha256': hashes,
}
(OUT / 'qa' / 'independent_validation.json').write_text(json.dumps(audit, indent=2), encoding='utf-8')
print(json.dumps({'baseline': source, 'checks': len(checks), 'failures': [c for c in checks if c['status'] == 'FAIL'],
                  'group_cells': len(group_keys), 'coverage': audit['coverage'],
                  'strict_timestamp_counts': dict(strict_timestamp_counts),
                  'confirmation_relative_to_order': dict(confirmation_order_delta)}, indent=2))
