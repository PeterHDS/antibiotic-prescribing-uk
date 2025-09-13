"""
Fetch prescribing and list size data for antibiotic analysis.

This script reads a configuration file (`config/datasets.csv`) listing data sources
for each month and downloads the corresponding CSVs into `data/raw/`.  Each row
in the configuration should have the columns:

```
month,url,file_name,type
```

where `month` is a YYYY-MM string, `url` is the download URL, `file_name` is
the name to save the file as, and `type` is either ``prescribing`` or
``list_size``.  Rows with missing URLs are skipped, allowing you to
selectively download files you have access to.

Note: Many NHS prescribing datasets require manual download or API keys.  If
you cannot automate the download, download the file manually and place it
into `data/raw/` with the specified file_name.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

import requests


def _read_config(config_path: Path) -> Iterable[dict[str, str]]:
    """Yield configuration rows from a CSV file.

    Each row is returned as a dictionary with keys: month, url, file_name, type.
    Rows with missing headers are skipped.
    """
    with config_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader((row for row in f if not row.startswith("#")))
        for row in reader:
            # ensure required fields exist
            if not all(key in row for key in ("month", "url", "file_name", "type")):
                continue
            yield row


def download_file(url: str, dest: Path) -> None:
    """Download a file from ``url`` and save it to ``dest``.

    If the URL is empty or None, the download is skipped.  Existing files are
    overwritten.
    """
    if not url:
        print(f"No URL provided for {dest.name}; skipping download.")
        return
    try:
        print(f"Fetching {url} → {dest}…")
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(resp.content)
    except Exception as exc:
        print(f"Warning: failed to download {url}: {exc}")


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    config_path = project_root / "config" / "datasets.csv"
    raw_dir = project_root / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    for row in _read_config(config_path):
        month = row.get("month")
        url = row.get("url")
        file_name = row.get("file_name")
        if not file_name:
            print(f"Skipping row for month {month} with no file_name")
            continue
        dest = raw_dir / file_name
        download_file(url, dest)
    print(f"Finished downloading files into {raw_dir}")


if __name__ == "__main__":
    main()