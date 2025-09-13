"""
Generate plots for antibiotic prescribing trends and outliers.

This module produces figures such as national trend lines and funnel plots.
It uses matplotlib and saves outputs into ``outputs/figures/``.

The functions avoid specifying colours explicitly to ensure compatibility
with downstream theming.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


def plot_trends(df: pd.DataFrame, output_dir: Path) -> None:
    """Plot national antibiotic prescribing trends over time.

    Parameters
    ----------
    df: pandas.DataFrame
        DataFrame containing at least ``month`` and ``rate_per_1000`` columns.
        Multiple rows per month (different practices) are allowed; values are
        averaged across practices for plotting.
    output_dir: pathlib.Path
        Directory to save the figures.
    """
    # Convert month to datetime
    tmp = df.copy()
    try:
        tmp["month"] = pd.to_datetime(tmp["month"], format="%Y-%m")
    except Exception:
        tmp["month"] = pd.to_datetime(tmp["month"], errors="coerce")
    trend_df = tmp.groupby("month")["rate_per_1000"].mean().reset_index()
    fig, ax = plt.subplots()
    ax.plot(trend_df["month"], trend_df["rate_per_1000"], label="Mean items per 1k patients")
    ax.set_xlabel("Month")
    ax.set_ylabel("Items per 1k patients")
    ax.set_title("National antibiotic prescribing trend")
    ax.legend()
    output_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_dir / "trend.png", bbox_inches="tight")
    plt.close(fig)


def plot_funnel(df: pd.DataFrame, output_dir: Path) -> None:
    """Plot a funnel chart comparing practices.

    Each practice is represented by its total list size (denominator) and
    prescribing rate per 1 000 patients.  Control limits are drawn at 95% and
    99.8% confidence levels.

    Parameters
    ----------
    df: pandas.DataFrame
        DataFrame with columns ``total_list_size``, ``rate_per_1000``,
        ``ucl95``, ``lcl95``, ``ucl998`` and ``lcl998``.
    output_dir: pathlib.Path
        Directory to save the figure.
    """
    if df.empty:
        return
    fig, ax = plt.subplots()
    # Scatter points
    ax.scatter(df["total_list_size"], df["rate_per_1000"], s=10, alpha=0.6)
    # Plot control limit lines
    sizes = df["total_list_size"]
    ax.plot(sizes, df["ucl95"], linestyle="--", label="95% upper limit")
    ax.plot(sizes, df["lcl95"], linestyle="--", label="95% lower limit")
    ax.plot(sizes, df["ucl998"], linestyle=":", label="99.8% upper limit")
    ax.plot(sizes, df["lcl998"], linestyle=":", label="99.8% lower limit")
    # Mean line
    if "mean_rate" in df.columns:
        ax.axhline(df["mean_rate"].iloc[0], linestyle="-.", label="Mean rate")
    ax.set_xlabel("Total list size (patients)")
    ax.set_ylabel("Items per 1k patients")
    ax.set_title("Funnel plot of practice prescribing rates")
    ax.legend()
    output_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_dir / "funnel.png", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    metrics_path = project_root / "data" / "metrics.csv"
    if not metrics_path.exists():
        raise FileNotFoundError(
            f"{metrics_path} not found. Have you run analyze.py?"
        )
    df = pd.read_csv(metrics_path)
    output_dir = project_root / "outputs" / "figures"
    # Plot national trend using monthly average rates.  To avoid double counting,
    # convert metrics back to monthly using tidy file if available.
    tidy_path = project_root / "data" / "tidy.csv"
    if tidy_path.exists():
        tidy_df = pd.read_csv(tidy_path)
        # Merge list size into tidy if available
        if "list_size" not in tidy_df.columns:
            tidy_df = tidy_df.merge(
                df[["practice_code", "total_list_size"]], on="practice_code", how="left"
            )
        # Compute items per 1000 for each month
        tidy_df["rate_per_1000"] = (tidy_df["items"] / tidy_df["list_size"]) * 1000.0
        plot_trends(tidy_df, output_dir)
    else:
        # Fallback: compute trend using metrics aggregated per practice (mean of rates)
        df_trend = df.copy()
        # Without month, can't produce monthly trend; skip.
        pass
    # Funnel plot
    plot_funnel(df, output_dir)
    print(f"Saved figures to {output_dir}")


if __name__ == "__main__":
    main()