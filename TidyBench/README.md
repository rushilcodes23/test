# 🩺 TidyBench

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Streamlit](https://img.shields.io/badge/streamlit-app-FF4B4B)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

Upload a messy CSV, see exactly what's wrong with it, fix it in a few clicks, and leave with a clean file plus a plain-English report of what changed.

## Why

Real-world spreadsheets are rarely clean — duplicate rows, half-filled columns, inconsistent text, wrong data types. This tool automates the first, most repetitive hour of any data task: figuring out what's wrong before you can do anything useful with it.

## Features

- **Diagnose** — rows, columns, missing values, duplicates, and dtypes at a glance
- **Treat** — fix missing values (mean, median, mode, custom, or drop), remove duplicates, strip whitespace, and convert column types, all from the UI
- **Report** — a before/after summary of everything that changed, downloadable as markdown alongside the cleaned CSV
- **Quick Insights** — once the data's cleaned, pick a preset question (top category by total, average, highest/lowest value) and get a plain-English answer, with an optional deeper breakdown

## Demo

*(add a screenshot or short gif here once you've run it locally — that's the single best thing you can add to this README)*

## Quickstart

```bash
git clone <your-repo-url>
cd data-doctor
pip install -r requirements.txt
streamlit run app.py
```

Upload your own CSV, or try the included `sample_data/messy_sales.csv` — it has duplicate rows, missing values, inconsistent casing, and one obvious outlier baked in.

## Project structure

```
data-doctor/
├── app.py               # Streamlit UI
├── cleaning.py          # pandas/numpy logic, no Streamlit dependency
├── test_cleaning.py     # quick checks for cleaning.py
├── requirements.txt
├── sample_data/
│   └── messy_sales.csv
├── .streamlit/
│   └── config.toml      # app theme
└── README.md
```

Keeping `cleaning.py` free of any Streamlit import means the logic can be tested and reused on its own — run `python test_cleaning.py` to see it work against the sample data.

## What I learned

*(a starter list based on what's already here — keep adding to this as you extend the project)*

- Reading data: `read_csv`
- Inspecting: `.shape`, `.dtypes`, `.isnull()`, `.duplicated()`
- Cleaning: `.fillna()`, `.dropna()`, `.drop_duplicates()`, `.astype()`, `.str.strip()`
- numpy: `np.percentile` for IQR-based outlier bounds
- Streamlit: session state, tabs, columns, metrics, download buttons
- pandas 3.0 quietly changed the default dtype for text columns from `object` to a dedicated `str` type — `pd.api.types.is_string_dtype()` is the version-safe way to check for text columns now

## Roadmap — messier things to handle later

`cleaning.py` already has a tested `find_outliers_iqr()` function that isn't wired into the UI yet — a good first feature to add yourself. Beyond that:

- [ ] Outlier tab: flag rows with `find_outliers_iqr`, let the user drop or cap them
- [ ] Standardize inconsistent categories (e.g. "NY" / "New York" / "ny" as the same value)
- [ ] Handle mixed date formats within a single column
- [ ] Strip currency symbols and commas from numbers stored as text (e.g. `"$1,200"`)
- [ ] Clean up column names (spaces → underscores, consistent casing)
- [ ] Support multi-sheet Excel uploads
- [ ] Fuzzy/near-duplicate detection, not just exact duplicates
- [ ] Export the summary report as a PDF

## License

MIT — see [LICENSE](LICENSE).
