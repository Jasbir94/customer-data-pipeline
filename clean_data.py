"""
clean_data.py  —  Part 1: Data Cleaning
Usage:
    python clean_data.py [--raw-dir ./data/raw] [--out-dir ./data/processed]
"""

import os
import re
import logging
import argparse
import warnings
import pathlib
import pandas as pd

# ── config ───────────────────────────────────────────────────────────────────

ROOT = pathlib.Path(__file__).parent
CONFIG = {
    "raw_dir": ROOT / "data" / "raw",
    "out_dir": ROOT / "data" / "processed",
}

STATUS_MAP = {
    "done":      "completed",
    "complete":  "completed",
    "completed": "completed",
    "canceled":  "cancelled",
    "cancelled": "cancelled",
    "pending":   "pending",
    "refunded":  "refunded",
}

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ── helpers ───────────────────────────────────────────────────────────────────


def _null_counts(df: pd.DataFrame) -> dict:
    return df.isnull().sum().to_dict()


def _print_section(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def parse_order_date(date_str) -> pd.Timestamp:
    """Parse order_date supporting YYYY-MM-DD, DD/MM/YYYY, and MM-DD-YYYY."""
    if pd.isna(date_str):
        return pd.NaT
    s = str(date_str).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m-%d-%Y"):
        try:
            return pd.to_datetime(s, format=fmt)
        except (ValueError, TypeError):
            continue
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return pd.to_datetime(s, infer_datetime_format=True)
    except Exception:
        logger.warning("Could not parse order_date value: %r — replacing with NaT", s)
        return pd.NaT


def validate_email(email) -> bool:
    """Return True if email contains '@' and at least one '.' after '@'."""
    if pd.isna(email) or not isinstance(email, str) or email.strip() == "":
        return False
    return bool(re.match(r"^[^@]+@[^@]+\.[^@]+$", email.strip()))


# ── 1.1 customers cleaning ────────────────────────────────────────────────────


def clean_customers(raw_dir: pathlib.Path) -> pd.DataFrame:
    df = pd.read_csv(raw_dir / "customers.csv")

    _print_section("customers.csv — Cleaning Report")
    rows_before = len(df)
    nulls_before = _null_counts(df)
    print(f"  Rows before cleaning : {rows_before}")

    # 1. Parse signup_date (warn on failures)
    def _parse_signup(val):
        if pd.isna(val):
            return pd.NaT
        try:
            return pd.to_datetime(str(val).strip())
        except Exception:
            logger.warning("Could not parse signup_date: %r — replacing with NaT", val)
            return pd.NaT

    df["signup_date"] = df["signup_date"].apply(_parse_signup)

    # 2. Strip whitespace from name & region
    df["name"] = df["name"].astype(str).str.strip()
    df["region"] = df["region"].apply(lambda x: x.strip() if isinstance(x, str) else x)

    # 3. Fill missing region
    df["region"] = df["region"].fillna("Unknown").replace({"": "Unknown"})

    # 4. Dedup on customer_id — keep most recent signup_date
    before_dedup = len(df)
    df = (
        df.sort_values("signup_date", ascending=False, na_position="last")
        .drop_duplicates(subset="customer_id", keep="first")
        .reset_index(drop=True)
    )
    dups_removed = before_dedup - len(df)

    # 5. Lowercase & validate email
    df["email"] = df["email"].apply(
        lambda x: x.lower().strip() if isinstance(x, str) else x
    )
    df["is_valid_email"] = df["email"].apply(validate_email)

    # 6. Standardize signup_date to YYYY-MM-DD
    df["signup_date"] = df["signup_date"].dt.strftime("%Y-%m-%d")

    rows_after = len(df)
    nulls_after = _null_counts(df)

    print(f"  Rows after  cleaning : {rows_after}")
    print(f"  Duplicate rows removed : {dups_removed}")
    print(f"\n  Null counts before:")
    for col, cnt in nulls_before.items():
        print(f"    {col:<22} {cnt}")
    print(f"\n  Null counts after:")
    for col in nulls_before:
        print(f"    {col:<22} {nulls_after.get(col, 0)}")
    print(f"  is_valid_email=False : {(~df['is_valid_email']).sum()}")
    return df


# ── 1.2 orders cleaning ───────────────────────────────────────────────────────


def clean_orders(raw_dir: pathlib.Path) -> pd.DataFrame:
    df = pd.read_csv(raw_dir / "orders.csv")

    _print_section("orders.csv — Cleaning Report")
    rows_before = len(df)
    nulls_before = _null_counts(df)
    print(f"  Rows before cleaning : {rows_before}")

    # 1. Drop rows where BOTH customer_id AND order_id are null
    mask = df["customer_id"].isna() & df["order_id"].isna()
    dropped = mask.sum()
    df = df[~mask].copy()
    print(f"  Dropped (both ids null) : {dropped}")

    # 2. Multi-format order_date parse
    df["order_date"] = df["order_date"].apply(parse_order_date)

    # 3. Fill missing amount with per-product median
    null_amounts = df["amount"].isna().sum()
    df["amount"] = df["amount"].fillna(
        df.groupby("product")["amount"].transform("median")
    )
    print(f"  Amount nulls filled via median : {null_amounts}")

    # 4. Normalize status
    df["status"] = (
        df["status"]
        .astype(str)
        .str.strip()
        .str.lower()
        .map(lambda s: STATUS_MAP.get(s, "pending"))
    )

    # 5. Derive order_year_month
    df["order_year_month"] = df["order_date"].dt.strftime("%Y-%m")

    rows_after = len(df)
    nulls_after = _null_counts(df)
    print(f"  Rows after  cleaning : {rows_after}")
    print(f"\n  Null counts before:")
    for col, cnt in nulls_before.items():
        print(f"    {col:<22} {cnt}")
    print(f"\n  Null counts after:")
    for col in nulls_before:
        print(f"    {col:<22} {nulls_after.get(col, 0)}")
    return df


# ── main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean raw CSV datasets.")
    parser.add_argument(
        "--raw-dir",
        type=pathlib.Path,
        default=CONFIG["raw_dir"],
        help="Directory containing raw CSV files (default: ./data/raw)",
    )
    parser.add_argument(
        "--out-dir",
        type=pathlib.Path,
        default=CONFIG["out_dir"],
        help="Directory to write cleaned CSV files (default: ./data/processed)",
    )
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    customers_clean = clean_customers(args.raw_dir)
    orders_clean = clean_orders(args.raw_dir)

    customers_clean.to_csv(args.out_dir / "customers_clean.csv", index=False)
    orders_clean.to_csv(args.out_dir / "orders_clean.csv", index=False)

    _print_section("Output Files Saved")
    print(f"  {args.out_dir / 'customers_clean.csv'}")
    print(f"  {args.out_dir / 'orders_clean.csv'}\n")


if __name__ == "__main__":
    main()
