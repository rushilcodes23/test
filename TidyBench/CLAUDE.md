# TidyBench

A Streamlit app: upload a messy CSV, diagnose what's wrong with it, fix it, download a clean file + a report.

## Architecture

- `cleaning.py` — all pandas/numpy logic. No Streamlit import. Every function takes a DataFrame (or Series) and returns one; no side effects, no printing. This is deliberate so it's testable on its own. Includes the Quick Insights functions (`numeric_columns`, `top_category_by_sum`, `average_value`, `extreme_value`) alongside the cleaning functions — same pattern, plain data in and out.
- `app.py` — Streamlit UI only. Calls into `cleaning.py`, never duplicates its logic. The Quick Insights section builds preset question strings from whatever columns are in the uploaded CSV, then dispatches to the `cleaning.py` functions above.
- `test_cleaning.py` — plain asserts against `sample_data/messy_sales.csv`. Run it after touching `cleaning.py`: `python test_cleaning.py`.

When adding a feature, keep this split: new data logic goes in `cleaning.py` as a plain function, new UI goes in `app.py`.

## Known gotcha

This runs on pandas 3.0+, which made `str` the default dtype for text columns instead of `object`. Use `pd.api.types.is_string_dtype(...)`, never `dtype == object`, to detect text columns. (This already bit us once — see `strip_whitespace` in `cleaning.py`.)

## Next task

`find_outliers_iqr()` in `cleaning.py` is written and tested but not wired into the UI. The natural next step: add an "Outliers" tab in `app.py` next to the existing three treatment tabs, using it to flag rows and let the user drop or cap them. Check the README's roadmap section for further ideas after that.

## Style

Keep functions small and named for what they do, not how they're implemented (`fill_missing`, not `apply_strategy_1`). Docstrings are one line. No comments explaining what a line does — only why, when it's non-obvious.
