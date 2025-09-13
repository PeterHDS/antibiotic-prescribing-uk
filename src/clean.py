"""
Clean and merge prescribing, list size and deprivation data for antibiotic analysis.

This script reads configuration files and raw data downloaded by ``get_data.py``,
standardises column names, filters to oral antibacterial drugs (BNF chapter 5.1)
and combines prescribing data with practice list sizes and optional deprivation
quintiles.  The tidy dataset is written to ``data/tidy.csv``.

If no raw data are present, the script will emit an informative message and
create an empty tidy file.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List

import pandas as pd
import yaml


def _read_config(config_path: Path) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    with config_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader((row for row in f if not row.startswith("#")))
        for row in reader:
            if not all(k in row for k in ("month", "file_name", "type")):
                continue
            rows.append(row)
    return rows


def _load_column_map(columns_path: Path) -> Dict[str, Dict[str, str]]:
    if not columns_path.exists():
        return {}
    with columns_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    raw_dir = project_root / "data" / "raw"
    tidy_path = project_root / "data" / "tidy.csv"
    config_path = project_root / "config" / "datasets.csv"
    columns_path = project_root / "config" / "columns.yaml"
    imd_path = project_root / "config" / "imd_lookup.csv"

    # Read configuration and column mapping
    config_rows = _read_config(config_path) if config_path.exists() else []
    column_map = _load_column_map(columns_path)
    presc_map = column_map.get("prescribing", {})
    list_map = column_map.get("list_size", {})

    prescribing_frames: List[pd.DataFrame] = []
    list_frames: List[pd.DataFrame] = []

    for row in config_rows:
        month = row.get("month")
        file_name = row.get("file_name")
        ftype = row.get("type")
        if not file_name:
            continue
        file_path = raw_dir / file_name
        if not file_path.exists():
            print(f"Warning: raw file {file_path} not found; skipping")
            continue
        try:
            df = pd.read_csv(file_path)
        except Exception as exc:
            print(f"Warning: failed to read {file_path}: {exc}")
            continue
        # Standardise column names
        if ftype == "prescribing":
            rename_dict = {v: k for k, v in presc_map.items() if v in df.columns}
            df = df.rename(columns=rename_dict)
            # Add month if not present
            if "month" not in df.columns:
                df["month"] = month
            # Filter to antibiotics (BNF code starting with 0501) if column exists
            if "bnf_code" in df.columns:
                df = df[df["bnf_code"].astype(str).str.startswith("0501")]
            prescribing_frames.append(df[[c for c in df.columns if c in {"practice_code", "month", "items", "bnf_code"} or c not in {"practice_code", "month", "items", "bnf_code"}]].copy())
        elif ftype == "list_size":
            rename_dict = {v: k for k, v in list_map.items() if v in df.columns}
            df = df.rename(columns=rename_dict)
            if "month" not in df.columns:
                df["month"] = month
            list_frames.append(df[[c for c in df.columns if c in {"practice_code", "month", "list_size"}]].copy())

    # Concatenate data
    presc_df = pd.concat(prescribing_frames, ignore_index=True) if prescribing_frames else pd.DataFrame()
    list_df = pd.concat(list_frames, ignore_index=True) if list_frames else pd.DataFrame()

    # Merge prescribing with list size
    if not presc_df.empty and not list_df.empty:
        tidy = presc_df.merge(list_df, on=["practice_code", "month"], how="left")
    else:
        tidy = presc_df if not presc_df.empty else pd.DataFrame(columns=["practice_code", "month", "items", "list_size"])

    # Add IMD quintile if available
    if imd_path.exists() and not tidy.empty:
        try:
            imd_df = pd.read_csv(imd_path)
            # Expect columns practice_code, imd_quintile
            if {"practice_code", "imd_quintile"}.issubset(imd_df.columns):
                tidy = tidy.merge(imd_df[["practice_code", "imd_quintile"]], on="practice_code", how="left")
        except Exception as exc:
            print(f"Warning: failed to read IMD lookup: {exc}")

    tidy.to_csv(tidy_path, index=False)
    print(f"Wrote tidy data to {tidy_path} ({len(tidy)} rows)")


if __name__ == "__main__":
    main()