"""
Analyse antibiotic prescribing rates, detect outliers and produce summary statistics.

This module reads the tidy CSV produced by ``clean.py`` and calculates
prescribing rates per 1 000 patients, computes funnel plot control limits and
flags outliers.  The resulting metrics are written to ``data/metrics.csv``.

The analysis operates at the practice level.  For each practice, we sum
prescription items and list sizes across all available months and compute
items per 1 000 patients.  Funnel plot control limits are calculated using
the overall mean prescribing rate and the normal approximation to the Poisson
distribution.  Practices above or below the 99.8% limit are labelled
``high`` or ``low`` outliers, respectively.
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

import pandas as pd
import numpy as np


def compute_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Compute prescribing rates and outlier flags.

    Parameters
    ----------
    df: pandas.DataFrame
        Tidy DataFrame with columns: practice_code, month, items, list_size.

    Returns
    -------
    pandas.DataFrame
        DataFrame with practice-level metrics: total_items, total_list_size,
        rate_per_1000, mean_rate, ucl95, ucl998, lcl95, lcl998, outlier.
    """
    if df.empty:
        return pd.DataFrame(columns=[
            "practice_code", "total_items", "total_list_size",
            "rate_per_1000", "mean_rate", "ucl95", "ucl998",
            "lcl95", "lcl998", "outlier"
        ])

    # Filter out rows without list size or items
    df = df.dropna(subset=["items"]).copy()
    df["list_size"] = df.get("list_size").fillna(0)
    # Convert to numeric
    df["items"] = pd.to_numeric(df["items"], errors="coerce").fillna(0)
    df["list_size"] = pd.to_numeric(df["list_size"], errors="coerce").fillna(0)

    # Aggregate by practice
    grouped = df.groupby("practice_code").agg(
        total_items=("items", "sum"),
        total_list_size=("list_size", "sum")
    ).reset_index()
    # Compute rate per 1000 patients
    grouped["rate_per_1000"] = np.where(
        grouped["total_list_size"] > 0,
        grouped["total_items"] / grouped["total_list_size"] * 1000.0,
        np.nan
    )

    # Overall mean rate across all practices
    mean_rate = grouped["rate_per_1000"].mean(skipna=True)

    # Compute control limits: for funnel plot, approximate variance = mean_rate/size
    def limits(size: float, z: float) -> Tuple[float, float]:
        if size <= 0 or np.isnan(mean_rate):
            return (np.nan, np.nan)
        se = np.sqrt(mean_rate / size)
        return (
            mean_rate + z * se,
            mean_rate - z * se,
        )

    ucl95, lcl95, ucl998, lcl998 = [], [], [], []
    for _, row in grouped.iterrows():
        upper95, lower95 = limits(row["total_list_size"] / 1000.0, 1.96)
        upper998, lower998 = limits(row["total_list_size"] / 1000.0, 3.09)
        ucl95.append(upper95)
        lcl95.append(lower95)
        ucl998.append(upper998)
        lcl998.append(lower998)

    grouped["mean_rate"] = mean_rate
    grouped["ucl95"] = ucl95
    grouped["lcl95"] = lcl95
    grouped["ucl998"] = ucl998
    grouped["lcl998"] = lcl998

    # Determine outliers
    def classify(row):
        rate = row["rate_per_1000"]
        if np.isnan(rate):
            return ""
        if rate > row["ucl998"]:
            return "high"
        if rate < row["lcl998"]:
            return "low"
        return ""

    grouped["outlier"] = grouped.apply(classify, axis=1)

    return grouped


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    tidy_path = project_root / "data" / "tidy.csv"
    if not tidy_path.exists():
        raise FileNotFoundError(
            f"{tidy_path} not found. Have you run clean.py?"
        )
    df = pd.read_csv(tidy_path)
    metrics = compute_metrics(df)
    metrics_path = project_root / "data" / "metrics.csv"
    metrics.to_csv(metrics_path, index=False)
    print(f"Wrote metrics to {metrics_path} ({len(metrics)} rows)")


if __name__ == "__main__":
    main()