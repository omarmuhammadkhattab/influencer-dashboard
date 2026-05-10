"""
seed_data.py
Populates the Shopify development store with:
- 1 test product
- 30 influencer price rules + discount codes
- ~1,000 realistic orders across 3 months with return tags
"""

import os
import json
import time
import random
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv

load_dotenv()

STORE = os.getenv("SHOPIFY_STORE")
TOKEN = os.getenv("SHOPIFY_TOKEN")
BASE  = f"https://{STORE}/admin/api/2024-01"
HEADERS = {
    "X-Shopify-Access-Token": TOKEN,
    "Content-Type": "application/json"
}

# ── Influencer definitions ────────────────────────────────────────────────────
INFLUENCERS = [
    # Tier A — high volume, low returns (worth it)
    {"name": "Sarah",    "code": "SARAH15",   "discount": 15, "weight": 9, "return_rate": 0.07},
    {"name": "Emma",     "code": "EMMA20",    "discount": 20, "weight": 8, "return_rate": 0.09},
    {"name": "Lena",     "code": "LENA12",    "discount": 12, "weight": 8, "return_rate": 0.08},
    {"name": "Max",      "code": "MAX10",     "discount": 10, "weight": 7, "return_rate": 0.06},
    {"name": "Julia",    "code": "JULIA15",   "discount": 15, "weight": 7, "return_rate": 0.10},
    {"name": "Felix",    "code": "FELIX10",   "discount": 10, "weight": 6, "return_rate": 0.08},
    {"name": "Hannah",   "code": "HANNAH20",  "discount": 20, "weight": 6, "return_rate": 0.09},
    {"name": "Nico",     "code": "NICO12",    "discount": 12, "weight": 5, "return_rate": 0.07},
    {"name": "Sophie",   "code": "SOPHIE15",  "discount": 15, "weight": 5, "return_rate": 0.11},
    {"name": "Tom",      "code": "TOM10",     "discount": 10, "weight": 5, "return_rate": 0.06},
    # Tier B — medium volume, medium returns (borderline)
    {"name": "Laura",    "code": "LAURA15",   "discount": 15, "weight": 4, "return_rate": 0.14},
    {"name": "Ben",      "code": "BEN10",     "discount": 10, "weight": 4, "return_rate": 0.16},
    {"name": "Mia",      "code": "MIA20",     "discount": 20, "weight": 4, "return_rate": 0.15},
    {"name": "Jonas",    "code": "JONAS12",   "discount": 12, "weight": 3, "return_rate": 0.13},
    {"name": "Lisa",     "code": "LISA10",    "discount": 10, "weight": 3, "return_rate": 0.17},
    {"name": "Kevin",    "code": "KEVIN15",   "discount": 15, "weight": 3, "return_rate": 0.14},
    {"name": "Anna",     "code": "ANNA10",    "discount": 10, "weight": 3, "return_rate": 0.16},
    {"name": "Marco",    "code": "MARCO20",   "discount": 20, "weight": 3, "return_rate": 0.18},
    {"name": "Lea",      "code": "LEA15",     "discount": 15, "weight": 2, "return_rate": 0.15},
    {"name": "David",    "code": "DAVID10",   "discount": 10, "weight": 2, "return_rate": 0.13},
    # Tier C — low volume, high returns (not worth it)
    {"name": "Nina",     "code": "NINA20",    "discount": 20, "weight": 2, "return_rate": 0.28},
    {"name": "Chris",    "code": "CHRIS15",   "discount": 15, "weight": 2, "return_rate": 0.31},
    {"name": "Tanja",    "code": "TANJA10",   "discount": 10, "weight": 1, "return_rate": 0.26},
    {"name": "Stefan",   "code": "STEFAN12",  "discount": 12, "weight": 1, "return_rate": 0.29},
    {"name": "Karina",   "code": "KARINA20",  "discount": 20, "weight": 1, "return_rate": 0.33},
    {"name": "Rene",     "code": "RENE10",    "discount": 10, "weight": 1, "return_rate": 0.27},
    {"name": "Petra",    "code": "PETRA15",   "discount": 15, "weight": 1, "return_rate": 0.30},
    {"name": "Oliver",   "code": "OLIVER10",  "discount": 10, "weight": 1, "return_rate": 0.25},
    {"name": "Sabine",   "code": "SABINE20",  "discount": 20, "weight": 1, "return_rate": 0.32},
    {"name": "Frank",    "code": "FRANK12",   "discount": 12, "weight": 1, "return_rate": 0.28},
]

def api(method, path, payload=None, retries=5):
    """Make a rate-limited Shopify API call with retry on 429."""
    url = f"{BASE}/{path}"
    for attempt in range(retries):
        resp = getattr(requests, method)(url, headers=HEADERS, json=payload)
        if resp.status_code in (200, 201):
            time.sleep(2)  # conservative delay between calls
            return resp.json()
        elif resp.status_code == 429:
            wait = 65  # wait 65 seconds on rate limit
            print(f"  ⏳ Rate limited. Waiting {wait}s before retry ({attempt+1}/{retries})...")
            time.sleep(wait)
        else:
            print(f"  ⚠ {method.upper()} {path} → {resp.status_code}: {resp.text[:200]}")
            return None
    print(f"  ✗ Failed after {retries} retries.")
    return None

def create_product():
    print("Creating test product...")
    data = api("post", "products.json", {
        "product": {
            "title": "Premium Lifestyle Bundle",
            "body_html": "Test product for influencer analytics demo.",
            "vendor": "Demo Store",
            "product_type": "Bundle",
            "variants": [{"price": "89.99", "sku": "PLB-001", "inventory_management": None}]
        }
    })
    variant_id = data["product"]["variants"][0]["id"]
    print(f"  ✓ Product created, variant_id={variant_id}")
    return variant_id

def create_discount_codes(variant_id):
    print("Creating 30 influencer discount codes...")
    code_map = {}
    for inf in INFLUENCERS:
        # Create a price rule
        pr = api("post", "price_rules.json", {
            "price_rule": {
                "title": f"Influencer: {inf['name']}",
                "target_type": "line_item",
                "target_selection": "all",
                "allocation_method": "across",
                "value_type": "percentage",
                "value": f"-{inf['discount']}.0",
                "customer_selection": "all",
                "starts_at": "2026-01-01T00:00:00Z"
            }
        })
        if not pr:
            continue
        pr_id = pr["price_rule"]["id"]

        # Create the discount code under that rule
        dc = api("post", f"price_rules/{pr_id}/discount_codes.json", {
            "discount_code": {"code": inf["code"]}
        })
        if dc:
            code_map[inf["code"]] = pr_id
            print(f"  ✓ {inf['code']} ({inf['discount']}% off)")

    return code_map

def random_date(start, end):
    delta = end - start
    return start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))

def create_orders(variant_id, n=800):
    print(f"\nCreating {n} test orders (2s delay per order, ~{n*2//60} min)...")

    start_date = datetime(2026, 2, 1)
    end_date   = datetime(2026, 5, 1)

    # Build weighted influencer pool
    pool = []
    for inf in INFLUENCERS:
        pool.extend([inf] * inf["weight"])

    # 15% of orders are organic (no discount code)
    # 10% use a code via Meta Ads (tagged accordingly)
    created = 0
    for i in range(n):
        inf       = random.choice(pool)
        base_price = round(random.uniform(39.99, 149.99), 2)
        discount  = inf["discount"] / 100
        final     = round(base_price * (1 - discount), 2)
        order_date = random_date(start_date, end_date).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Determine channel
        r = random.random()
        if r < 0.12:
            # Organic — no code
            discount_code = None
            tags = "organic"
        elif r < 0.22:
            # Meta Ad using influencer code
            discount_code = inf["code"]
            tags = "meta_ad"
        else:
            # Direct influencer referral
            discount_code = inf["code"]
            tags = "influencer"

        # Add return tag to some orders
        if discount_code and random.random() < inf["return_rate"]:
            tags += ",retourniert" if random.random() > 0.3 else ",teilretourniert"

        order_payload = {
            "order": {
                "created_at": order_date,
                "financial_status": "paid",
                "tags": tags,
                "line_items": [{
                    "variant_id": variant_id,
                    "quantity": 1,
                    "price": str(base_price),
                    "name": "Premium Lifestyle Bundle"
                }],
                "discount_codes": [{"code": discount_code, "amount": str(round(base_price * discount, 2)), "type": "percentage"}] if discount_code else [],
                "subtotal_price": str(final),
                "total_price": str(final),
            }
        }

        result = api("post", "orders.json", order_payload)
        if result:
            created += 1
            if created % 50 == 0:
                print(f"  ✓ {created}/{n} orders created...")

    print(f"\n✅ Done! {created} orders created successfully.")

if __name__ == "__main__":
    print("🚀 Seeding influencer-analytics-demo store...\n")
    variant_id = create_product()
    create_discount_codes(variant_id)
    create_orders(variant_id, n=200)
    print("\n🎉 Store seeded! Run: streamlit run app.py")