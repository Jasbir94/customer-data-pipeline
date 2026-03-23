"""
analyze.py  —  Part 2: Data Merging & Analysis
Usage:
    python analyze.py [--processed-dir ./data/processed] [--raw-dir ./data/raw]
"""

import argparse
import pathlib
import pandas as pd

# ── config ───────────────────────────────────────────────────────────────────

ROOT = pathlib.Path(__file__).parent
CONFIG = {
    "processed_dir": ROOT / "data" / "processed",
    "raw_dir": ROOT / "data" / "raw",
}

# ── helpers ───────────────────────────────────────────────────────────────────


def load_csv(path: pathlib.Path) -> pd.DataFrame:
    """Load a CSV with explicit error handling."""
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    df = pd.read_csv(path)
    if df.empty:
        raise pd.errors.EmptyDataError(f"File is empty: {path}")
    return df


def _print_section(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ── 2.1 merging ───────────────────────────────────────────────────────────────


def build_full_data(
    processed_dir: pathlib.Path, raw_dir: pathlib.Path
) -> pd.DataFrame:
    """Load cleaned CSVs, perform explicit left-joins, report unmatched rows."""
    customers = load_csv(processed_dir / "customers_clean.csv")
    orders = load_csv(processed_dir / "orders_clean.csv")
    products = load_csv(raw_dir / "products.csv")

    _print_section("2.1 — Merging")

    # orders LEFT JOIN customers
    orders_with_customers = pd.merge(
        orders,
        customers,
        on="customer_id",
        how="left",
    )
    unmatched_customers = orders_with_customers["name"].isna().sum()
    print(f"  Orders with no matching customer : {unmatched_customers}")

    # orders_with_customers LEFT JOIN products  (orders.product → products.product_name)
    full_data = pd.merge(
        orders_with_customers,
        products,
        left_on="product",
        right_on="product_name",
        how="left",
    )
    unmatched_products = full_data["category"].isna().sum()
    print(f"  Orders with no matching product  : {unmatched_products}")

    full_data["order_date"] = pd.to_datetime(full_data["order_date"], errors="coerce")
    return full_data


# ── 2.2 analysis tasks ────────────────────────────────────────────────────────


def monthly_revenue(full_data: pd.DataFrame, out_dir: pathlib.Path) -> pd.DataFrame:
    """Task 1 — Monthly Revenue Trend (completed orders only)."""
    completed = full_data[full_data["status"] == "completed"]
    result = (
        completed.groupby("order_year_month", as_index=False)["amount"]
        .sum()
        .rename(columns={"amount": "total_revenue"})
        .sort_values("order_year_month")
    )
    path = out_dir / "monthly_revenue.csv"
    result.to_csv(path, index=False)
    print(f"\n  [1] Monthly Revenue  → {path}  ({len(result)} rows)")
    return result


def top_customers(full_data: pd.DataFrame, out_dir: pathlib.Path) -> pd.DataFrame:
    """Task 2 + 5 — Top 10 customers by spend, with churn flag."""
    completed = full_data[full_data["status"] == "completed"].copy()
    latest_date = full_data["order_date"].max()
    cutoff = latest_date - pd.Timedelta(days=90)

    spend = (
        completed.groupby(["customer_id", "name", "region"], as_index=False)["amount"]
        .sum()
        .rename(columns={"amount": "total_spend"})
        .sort_values("total_spend", ascending=False)
        .head(10)
    )

    recent = completed[completed["order_date"] >= cutoff]["customer_id"].unique()
    spend["churned"] = ~spend["customer_id"].isin(recent)

    path = out_dir / "top_customers.csv"
    spend.to_csv(path, index=False)
    print(f"  [2] Top Customers    → {path}  ({len(spend)} rows)")
    print(f"      Latest order date : {latest_date.date() if pd.notna(latest_date) else 'N/A'}")
    print(f"      90-day cutoff     : {cutoff.date() if pd.notna(cutoff) else 'N/A'}")
    return spend


def category_performance(full_data: pd.DataFrame, out_dir: pathlib.Path) -> pd.DataFrame:
    """Task 3 — Category Performance."""
    completed = full_data[full_data["status"] == "completed"]
    result = (
        completed.groupby("category", as_index=False)
        .agg(
            total_revenue=("amount", "sum"),
            avg_order_value=("amount", "mean"),
            num_orders=("order_id", "count"),
        )
        .sort_values("total_revenue", ascending=False)
    )
    result["avg_order_value"] = result["avg_order_value"].round(2)
    result["total_revenue"] = result["total_revenue"].round(2)
    path = out_dir / "category_performance.csv"
    result.to_csv(path, index=False)
    print(f"  [3] Category Perf    → {path}  ({len(result)} rows)")
    return result


def regional_analysis(full_data: pd.DataFrame, out_dir: pathlib.Path) -> pd.DataFrame:
    """Task 4 — Regional Analysis."""
    cust_counts = (
        full_data.dropna(subset=["customer_id"])
        .drop_duplicates(subset="customer_id")[["customer_id", "region"]]
        .groupby("region")["customer_id"]
        .count()
        .rename("num_customers")
    )
    agg = full_data.groupby("region", as_index=False).agg(
        num_orders=("order_id", "count"),
        total_revenue=("amount", "sum"),
    )
    agg = agg.merge(cust_counts, on="region", how="left")
    agg["avg_revenue_per_customer"] = (agg["total_revenue"] / agg["num_customers"]).round(2)
    agg["total_revenue"] = agg["total_revenue"].round(2)
    path = out_dir / "regional_analysis.csv"
    agg.to_csv(path, index=False)
    print(f"  [4] Regional Anal.   → {path}  ({len(agg)} rows)")
    return agg


# ── main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge and analyse cleaned datasets.")
    parser.add_argument(
        "--processed-dir",
        type=pathlib.Path,
        default=CONFIG["processed_dir"],
        help="Directory containing cleaned CSV files (default: ./data/processed)",
    )
    parser.add_argument(
        "--raw-dir",
        type=pathlib.Path,
        default=CONFIG["raw_dir"],
        help="Directory containing raw CSV files (default: ./data/raw)",
    )
    args = parser.parse_args()
    args.processed_dir.mkdir(parents=True, exist_ok=True)

    full_data = build_full_data(args.processed_dir, args.raw_dir)

    _print_section("2.2 — Analysis Outputs")
    monthly_revenue(full_data, args.processed_dir)
    top_customers(full_data, args.processed_dir)
    category_performance(full_data, args.processed_dir)
    regional_analysis(full_data, args.processed_dir)
    print()


if __name__ == "__main__":
    main()
