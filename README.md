# Antibiotic Prescribing in Primary Care (England)

## Purpose

This repository contains a **reproducible analytical pipeline** for monitoring oral antibiotic prescribing in general practice across England.  The goal is to turn monthly prescribing data into evidence that helps medicines‑optimisation teams and GP practices:

* identify **true outliers** in antibacterial prescribing rather than random noise;
* support **targeted antimicrobial stewardship (AMS) actions** that lower the risk of resistance;
* track improvement over time using statistical process control (SPC) and funnel plots instead of static league tables.

Antibiotics are vital for treating common and life‑threatening infections, but inappropriate use accelerates the emergence of resistance.  A standard measure defined by OpenPrescribing counts prescription items for all oral antibacterial drugs (excluding antituberculosis and antileprotic drugs) per 1 000 registered patients [1].  This pipeline implements that measure using official NHS data and provides a framework for deeper analyses.

## Why this matters

* **Policy alignment.**  The UK’s **5‑year Antimicrobial Resistance (AMR) action plan** commits to optimising the use of antimicrobials and improving surveillance of infections.  The plan notes that government will “optimise surveillance processes through effective, standardised systems” and “enhance technical capacity for surveillance … to inform interventions” [3].
* **Clinical guidance.**  The **NICE NG15** guideline on antimicrobial stewardship aims to change prescribing practice to slow the emergence of resistance and ensure antimicrobials remain effective treatments [2].
* **Analytics best practice.**  NHS England’s *Making Data Count* programme recommends statistical process control over simple red‑amber‑green ratings because SPC helps understand variation and guides appropriate action [4].  SPC highlights deteriorating or improving situations and avoids the false assurance that simple traffic‑light tables can give.

By linking national policy, clinical guidance and analytics standards, this project delivers insights that are meaningful to decision‑makers and actionable by practitioners.  It provides evidence to support targeted AMS interventions and contributes to the fight against AMR.

## Data sources

All data used here are aggregate and publicly available.

| Dataset | Description |
|---|---|
| **English Prescribing Dataset (EPD)** | Compiled from multiple NHS Business Services Authority (NHSBSA) sources to ensure accuracy and consistency in prescription records.  It combines BNF classification data, organisational data on GP practices and monthly prescription item counts.  The dataset is published monthly with a two‑month delay [5]. |
| **All oral antibacterial measure definition** | OpenPrescribing’s measure counts prescription items for oral antibacterial drugs (BNF chapter 5.1) per 1 000 patients and excludes antituberculosis and antileprotic drugs [1]. |
| **GP registered list size** | The number of patients registered at a GP practice on the first day of each month, available at practice, Primary Care Network (PCN) and Integrated Care Board (ICB) level [6].  These counts provide the denominator for per‑capita prescribing rates. |
| **Deprivation (IMD 2019)** | Index of Multiple Deprivation scores for Lower Layer Super Output Areas (LSOAs); used for optional stratification by deprivation quintile. |
| **Guidance and policy context** | NICE guideline **NG15** on antimicrobial stewardship [2]; **Making Data Count** SPC toolkit [4]; UK **AMR action plan 2024–2029** [3]. |

## Method overview

1. **Ingest.**  `src/get_data.py` reads `config/datasets.csv` to download each month’s prescribing and list‑size CSVs into `data/raw/` using the provided URLs.  You can populate this CSV with any number of months and sources.
2. **Clean and standardise.**  `src/clean.py` loads the raw prescribing files, selects relevant columns (month, practice code, BNF code, items, list size) and writes a tidy dataset to `data/tidy.csv`.  Columns are mapped using `config/columns.yaml`, and optional deprivation lookup tables can be joined using `config/imd_lookup.csv`.
3. **Analysis.**  `src/analyze.py` computes:
   - total antibacterial items and list size by month;
   - **items per 1 000 patients**: `(items / list_size) × 1 000`;
   - rolling three‑month averages for stability;
   - simple SPC and funnel‑plot limits to flag special‑cause variation.
   The resulting metrics are saved to `data/metrics.csv`.
4. **Visualisation.**  `src/charts.py` reads `data/metrics.csv` and generates time‑series and funnel charts showing national trends and practice variation.  Figures are saved to `outputs/figures/`.

The pipeline is orchestrated via a Makefile:

```bash
make data    # download raw CSVs
make clean   # build tidy dataset
make analyze # compute metrics
make figures # generate charts and manager brief
make all     # run the entire pipeline
```

## Reproducibility and ethics

This project follows the UK Government Analysis Function’s **Reproducible Analytical Pipeline (RAP)** principles.  All steps—from data download to chart generation—are scripted and version controlled.  Dependencies are pinned in `environment.yml` and `requirements.txt`, and a Makefile provides a single command to rebuild the entire workflow.  You can add unit tests and continuous‑integration workflows to ensure future changes do not break the pipeline.

Only aggregate, public data are used.  The EPD excludes medicines supplied under patient group directions or dental prescriptions and does not contain any patient identifiers.  Analyses are presented at practice or higher geographies; practices flagged as outliers are signals for review, not evidence of inappropriate prescribing.  The pipeline is designed to be transparent and auditable so that stakeholders can understand how metrics are derived.

## Limitations

* **Data lag:** EPD releases are typically two months in arrears, so recent months may not be available.
* **Coding exclusions:** Prescriptions supplied under patient group directions and some hospital‑originated prescriptions are not included in the EPD.  These omissions may bias comparison with local dispensing data.
* **STAR‑PU adjustments:** Age/sex‑adjusted denominators (STAR‑PU) are not used by default but can be incorporated by extending the code and providing STAR‑PU weightings.
* **Deprivation mapping:** Stratification by deprivation requires joining practice codes to LSOAs; this lookup file must be provided in `config/imd_lookup.csv`.

## Getting started

1. **Clone the repository**
   ```bash
   git clone git@github.com:<your‑username>/antibiotic-prescribing-uk.git
   cd antibiotic-prescribing-uk
   ```
2. **Create an environment** (pick one)
   ```bash
   # Using pip
   python -m venv venv && source venv/bin/activate
   pip install -r requirements.txt

   # Or using conda
   conda env create -f environment.yml
   conda activate antibiotic-prescribing-uk
   ```
3. **Configure data sources** by editing `config/datasets.csv` to list each month’s prescribing and list‑size CSV URL and output filename (e.g. `2025-05,https://opendata.nhsbsa.net/.../May-2025.csv,prescribing_2025_05.csv`).  Add `config/list_sizes.csv` and `config/imd_lookup.csv` if using population and deprivation adjustments.
4. **Run the pipeline**
   ```bash
   make all
   ```
   Outputs are written to `data/tidy.csv`, `data/metrics.csv` and `outputs/figures/`.  Use a notebook (e.g. Jupyter) for interactive exploration.

## Contributing

Contributions are welcome!  Please raise an issue or pull request if you have suggestions for improvements, additional analyses or bug fixes.  See the LICENSE file for terms of use.

## Citation

If you use this project in your research or quality‑improvement work, please cite it.  A machine‑readable citation file (CITATION.cff) is included.

---

## Footnotes

1. **OpenPrescribing measure definition:** The measure counts prescription items for all oral antibacterial drugs (BNF chapter 5.1) per 1 000 patients and excludes antituberculosis and antileprotic drugs【15314244486664†L37-L44】.
2. **NICE NG15 guideline:** The guideline on antimicrobial stewardship emphasises changing prescribing practice to slow resistance and ensure antimicrobials remain effective【403482376174995†L133-L138】.
3. **UK AMR 2024–2029 action plan:** The plan commits to optimising antimicrobial use and enhancing surveillance processes to inform interventions【638068673225811†L3799-L3813】.
4. **Making Data Count (SPC):** NHS England’s programme advocates statistical process control over simple red‑amber‑green tables for understanding variation and guiding action【168095423775736†L90-L102】【168095423775736†L121-L140】.
5. **English Prescribing Dataset (EPD) description:** The EPD combines BNF classification, organisational data and monthly prescription item counts and is published monthly with a two‑month delay【270676859359625†L129-L150】.
6. **GP registered list size dataset:** Records the number of patients registered at a GP practice on the first day of each month, used as the denominator for prescribing rates【185040881176881†L45-L50】.