"""
data_dictionary.py
------------------
Generates a data dictionary from any CSV file.

Outputs:
  - Console summary
  - data_dictionary.csv  (machine readable)
  - data_dictionary.md   (human readable, paste into docs)

Usage:
  python data_dictionary.py --file raw_data/covid_ecdc.csv
"""

import argparse
import pandas as pd
from pathlib import Path
from datetime import datetime


def generate_data_dictionary(file_path: str) -> None:
    path = Path(file_path)
    if not path.exists():
        print(f"ERROR: File not found — {file_path}")
        return

    print(f"\n{'='*60}")
    print(f"  Data Dictionary — {path.name}")
    print(f"{'='*60}\n")

    # Load CSV
    df = pd.read_csv(file_path, low_memory=False)

    rows, cols = df.shape
    print(f"  Rows     : {rows:,}")
    print(f"  Columns  : {cols}")
    print(f"  File size: {path.stat().st_size / 1024 / 1024:.2f} MB")

    # Date range if date column exists
    date_cols = [c for c in df.columns if 'date' in c.lower()]
    if date_cols:
        try:
            df[date_cols[0]] = pd.to_datetime(df[date_cols[0]])
            print(f"  Date range: {df[date_cols[0]].min().date()} → {df[date_cols[0]].max().date()}")
        except Exception:
            pass

    # Unique locations if location column exists
    loc_cols = [c for c in df.columns if 'location' in c.lower() or 'country' in c.lower()]
    if loc_cols:
        print(f"  Unique locations: {df[loc_cols[0]].nunique()}")

    print(f"\n{'─'*60}")
    print(f"  Column-level profile")
    print(f"{'─'*60}\n")

    records = []

    for col in df.columns:
        series = df[col]

        # Basic stats
        dtype        = str(series.dtype)
        null_count   = int(series.isnull().sum())
        null_pct     = round(null_count / rows * 100, 1)
        unique_count = int(series.nunique(dropna=True))
        sample_vals  = series.dropna().unique()[:3].tolist()
        sample_str   = " | ".join(str(v) for v in sample_vals)

        # Numeric stats
        min_val = max_val = mean_val = ""
        if pd.api.types.is_numeric_dtype(series):
            min_val  = round(float(series.min()), 4) if not series.isnull().all() else ""
            max_val  = round(float(series.max()), 4) if not series.isnull().all() else ""
            mean_val = round(float(series.mean()), 4) if not series.isnull().all() else ""

        # Null severity flag
        if null_pct == 0:
            null_flag = "✅ clean"
        elif null_pct < 20:
            null_flag = "🟡 low"
        elif null_pct < 60:
            null_flag = "🟠 medium"
        else:
            null_flag = "🔴 high"

        records.append({
            "column"       : col,
            "dtype"        : dtype,
            "null_count"   : null_count,
            "null_pct"     : null_pct,
            "null_flag"    : null_flag,
            "unique_values": unique_count,
            "min"          : min_val,
            "max"          : max_val,
            "mean"         : mean_val,
            "sample_values": sample_str,
        })

    dd = pd.DataFrame(records)

    # Print console table
    for _, row in dd.iterrows():
        print(f"  {row['column']:<45} {row['dtype']:<12} null: {row['null_pct']:>5}%  {row['null_flag']}")
        if row['min'] != "":
            print(f"    {'':45} min={row['min']}  max={row['max']}  mean={row['mean']}")
        if row['sample_values']:
            print(f"    {'':45} samples: {row['sample_values']}")
        print()

    # Save CSV
    out_csv = path.parent / "data_dictionary.csv"
    try:
        dd.to_csv(out_csv, index=False)
    except PermissionError:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_csv = path.parent / f"data_dictionary_{ts}.csv"
        dd.to_csv(out_csv, index=False)
        print("\n  ⚠ data_dictionary.csv is in use, wrote fallback file instead.")
    print(f"\n  ✅ Saved: {out_csv}")

    # Save Markdown
    out_md = path.parent / "data_dictionary.md"
    try:
        f = open(out_md, "w", encoding="utf-8")
    except PermissionError:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_md = path.parent / f"data_dictionary_{ts}.md"
        f = open(out_md, "w", encoding="utf-8")
        print("  ⚠ data_dictionary.md is in use, wrote fallback file instead.")

    with f:
        f.write(f"# Data Dictionary — {path.name}\n\n")
        f.write(f"**Rows:** {rows:,}  \n")
        f.write(f"**Columns:** {cols}  \n")
        f.write(f"**File:** {path.name}  \n\n")
        f.write("---\n\n")
        f.write("| Column | Type | Null % | Null Flag | Unique | Min | Max | Mean | Sample Values |\n")
        f.write("|--------|------|--------|-----------|--------|-----|-----|------|---------------|\n")
        for _, row in dd.iterrows():
            f.write(
                f"| {row['column']} | {row['dtype']} | {row['null_pct']}% | "
                f"{row['null_flag']} | {row['unique_values']} | "
                f"{row['min']} | {row['max']} | {row['mean']} | "
                f"`{row['sample_values']}` |\n"
            )
    print(f"  ✅ Saved: {out_md}")
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate data dictionary from CSV")
    parser.add_argument("--file", required=True, help="Path to CSV file")
    args = parser.parse_args()
    generate_data_dictionary(args.file)