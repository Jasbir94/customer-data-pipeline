"""
generate_data.py
Generates realistic but messy sample CSVs for the data pipeline assignment.
"""
import random
import csv
import os
from datetime import datetime, timedelta

random.seed(42)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "raw")
os.makedirs(DATA_DIR, exist_ok=True)

# ── helpers ──────────────────────────────────────────────────────────────────

FIRST_NAMES = ["Alice","Bob","Carol","David","Eva","Frank","Grace","Henry",
               "Iris","Jack","Karen","Leo","Mia","Noah","Olivia","Paul",
               "Quinn","Rachel","Sam","Tina","Uma","Victor","Wendy","Xander",
               "Yara","Zoe"]
LAST_NAMES  = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller",
               "Davis","Wilson","Moore","Taylor","Anderson","Thomas","Jackson",
               "White","Harris","Martin","Thompson","Young","Lewis"]
REGIONS     = ["North","South","East","West","Central"]
PRODUCTS    = {
    "Laptop Pro":     ("Electronics", 1299.99),
    "Wireless Mouse": ("Electronics",   29.99),
    "USB-C Hub":      ("Electronics",   49.99),
    "Desk Chair":     ("Furniture",    349.99),
    "Standing Desk":  ("Furniture",    499.99),
    "Monitor 27in":   ("Electronics",  399.99),
    "Keyboard Mech":  ("Electronics",   89.99),
    "Webcam HD":      ("Electronics",   79.99),
    "Notebook Set":   ("Stationery",    12.99),
    "Pen Pack":       ("Stationery",     5.99),
    "Headphones Pro": ("Electronics",  249.99),
    "Phone Stand":    ("Accessories",   19.99),
    "Cable Pack":     ("Accessories",   14.99),
    "Backpack":       ("Accessories",   89.99),
    "Water Bottle":   ("Lifestyle",     24.99),
    "Whiteboard":     ("Stationery",    59.99),
    "Router WiFi 6":  ("Electronics",  129.99),
    "Smart Bulb":     ("Smart Home",    15.99),
    "Power Strip":    ("Accessories",   34.99),
    "Plant Pot":      ("Lifestyle",      9.99),
}
STATUS_VARIANTS = ["completed","pending","cancelled","refunded",
                   "done","complete","Complete","canceled","CANCELLED","Refunded",
                   "PENDING","Completed"]

def rand_date(start_year=2022, end_year=2025):
    start = datetime(start_year, 1, 1)
    end   = datetime(end_year, 12, 31)
    return start + timedelta(days=random.randint(0, (end-start).days))

def fmt_date(d, style):
    if style == 0: return d.strftime("%Y-%m-%d")
    if style == 1: return d.strftime("%d/%m/%Y")
    return d.strftime("%m-%d-%Y")

def rand_email(name):
    domains = ["gmail.com","yahoo.com","outlook.com","hotmail.com","company.org"]
    clean = name.lower().replace(" ",".")
    return f"{clean}@{random.choice(domains)}"


# ── products.csv ─────────────────────────────────────────────────────────────

def gen_products():
    path = os.path.join(DATA_DIR, "products.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["product_id","product_name","category","unit_price"])
        for i, (name, (cat, price)) in enumerate(PRODUCTS.items(), 1):
            w.writerow([f"P{i:03d}", name, cat, price])
    print(f"  products.csv  → {len(PRODUCTS)} rows")


# ── customers.csv ─────────────────────────────────────────────────────────────

def gen_customers():
    path = os.path.join(DATA_DIR, "customers.csv")
    rows = []
    cust_ids = [f"C{i:04d}" for i in range(1, 81)]   # 80 unique customers

    for cid in cust_ids:
        name   = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        region = random.choice(REGIONS + [None, "  South ", " North"])
        d      = rand_date(2021, 2024)
        # vary date format slightly
        date_s = d.strftime("%Y-%m-%d") if random.random() > 0.15 else d.strftime("%d-%b-%Y")
        email  = rand_email(name)

        # introduce issues
        if random.random() < 0.08:
            email = None                        # missing email
        elif random.random() < 0.06:
            email = email.replace("@","")      # malformed (no @)
        elif random.random() < 0.04:
            email = email.replace(".com","")   # no dot after TLD

        rows.append([cid, name, email, region, date_s])

    # add ~15 duplicate customer_ids (different signup dates — keep newest)
    for _ in range(15):
        orig = random.choice(rows)
        dup  = list(orig)
        dup[4] = rand_date(2023, 2025).strftime("%Y-%m-%d")
        rows.append(dup)

    # shuffle
    random.shuffle(rows)

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["customer_id","name","email","region","signup_date"])
        w.writerows(rows)
    print(f"  customers.csv → {len(rows)} rows (including {15} duplicates)")


# ── orders.csv ───────────────────────────────────────────────────────────────

def gen_orders():
    path = os.path.join(DATA_DIR, "orders.csv")
    cust_ids   = [f"C{i:04d}" for i in range(1, 81)]
    prod_names = list(PRODUCTS.keys())
    rows = []

    for i in range(1, 301):
        oid    = f"O{i:05d}"
        cid    = random.choice(cust_ids)
        prod   = random.choice(prod_names)
        _, price = PRODUCTS[prod]
        qty    = random.randint(1, 5)
        amount = round(price * qty, 2)
        d      = rand_date(2023, 2025)
        status = random.choice(STATUS_VARIANTS)

        # vary date format
        date_s = fmt_date(d, random.randint(0, 2))

        # introduce issues
        if random.random() < 0.06:
            amount = None   # null amount
        if random.random() < 0.02:
            cid    = None   # null customer_id (but keep order_id)

        rows.append([oid, cid, prod, amount, date_s, status])

    # add 3 fully-null rows (should be dropped)
    for _ in range(3):
        rows.append([None, None, "Laptop Pro", 1299.99, "2024-01-01", "completed"])

    random.shuffle(rows)

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["order_id","customer_id","product","amount","order_date","status"])
        w.writerows(rows)
    print(f"  orders.csv    → {len(rows)} rows")


if __name__ == "__main__":
    print("Generating sample datasets …")
    gen_products()
    gen_customers()
    gen_orders()
    print("Done. Files saved to data/")
