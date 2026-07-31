"""Core data cleaning and diagnostic functions for Data Doctor.

These are plain pandas/numpy functions with no Streamlit dependency, so
they can be imported and tested on their own (see test_cleaning.py).
"""

import pandas as pd
import numpy as np


def profile_data(df: pd.DataFrame) -> dict:
    """Return a diagnostic summary: shape, missing values, duplicates, dtypes."""
    missing_by_column = df.isnull().sum().to_dict()
    return {
        "rows": len(df),
        "columns": len(df.columns),
        "missing_by_column": missing_by_column,
        "missing_total": int(sum(missing_by_column.values())),
        "duplicate_rows": int(df.duplicated().sum()),
        "dtypes": df.dtypes.astype(str).to_dict(),
    }


def fill_missing(df: pd.DataFrame, column: str, strategy: str = "mean", custom_value=None) -> pd.DataFrame:
    """Fill missing values in one column using mean, median, mode, or a custom value."""
    df = df.copy()
    if strategy == "mean":
        df[column] = df[column].fillna(df[column].mean())
    elif strategy == "median":
        df[column] = df[column].fillna(df[column].median())
    elif strategy == "mode":
        mode_values = df[column].mode()
        if not mode_values.empty:
            df[column] = df[column].fillna(mode_values.iloc[0])
    elif strategy == "custom":
        value = custom_value
        if pd.api.types.is_numeric_dtype(df[column]):
            try:
                value = float(custom_value)
            except (TypeError, ValueError):
                pass
        df[column] = df[column].fillna(value)
    else:
        raise ValueError(f"Unknown strategy: {strategy}")
    return df


def drop_missing_rows(df: pd.DataFrame, column: str = None) -> pd.DataFrame:
    """Drop rows with missing values, optionally restricted to one column."""
    if column:
        return df.dropna(subset=[column]).reset_index(drop=True)
    return df.dropna().reset_index(drop=True)


def drop_duplicate_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Remove exact duplicate rows, keeping the first occurrence."""
    return df.drop_duplicates().reset_index(drop=True)


def strip_whitespace(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Strip leading/trailing whitespace from a text column."""
    df = df.copy()
    if pd.api.types.is_string_dtype(df[column]):
        df[column] = df[column].str.strip()
    return df


def text_columns(df: pd.DataFrame) -> list:
    """Return column names that hold text, regardless of pandas' internal string dtype."""
    return [c for c in df.columns if pd.api.types.is_string_dtype(df[c])]


def numeric_columns(df: pd.DataFrame) -> list:
    """Return column names that hold numeric data."""
    return [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]


def top_category_by_sum(df: pd.DataFrame, category_col: str, numeric_col: str) -> dict:
    """Find which category has the highest running total of a numeric column."""
    totals = df.groupby(category_col)[numeric_col].sum().sort_values(ascending=False)
    return {
        "top_category": totals.index[0],
        "top_total": float(totals.iloc[0]),
        "average_total": float(totals.mean()),
        "breakdown": totals,
    }


def average_value(df: pd.DataFrame, numeric_col: str) -> dict:
    """Compute the average of a numeric column alongside its min and max."""
    series = df[numeric_col].dropna()
    return {
        "mean": float(series.mean()),
        "min": float(series.min()),
        "max": float(series.max()),
    }


def extreme_value(df: pd.DataFrame, numeric_col: str, which: str = "highest") -> dict:
    """Find the single highest or lowest value in a numeric column, and its full row."""
    series = df[numeric_col].dropna()
    idx = series.idxmax() if which == "highest" else series.idxmin()
    return {
        "value": float(series.loc[idx]),
        "average": float(series.mean()),
        "row": df.loc[idx].drop(labels=[numeric_col]).to_dict(),
    }


def fix_dtype(df: pd.DataFrame, column: str, new_type: str) -> pd.DataFrame:
    """Convert a column to numeric, datetime, or text. Bad values become blank."""
    df = df.copy()
    if new_type == "numeric":
        df[column] = pd.to_numeric(df[column], errors="coerce")
    elif new_type == "datetime":
        df[column] = pd.to_datetime(df[column], errors="coerce")
    elif new_type == "text":
        df[column] = df[column].astype(str)
    else:
        raise ValueError(f"Unknown type: {new_type}")
    return df


def find_outliers_iqr(series: pd.Series) -> pd.Series:
    """Flag values outside 1.5x the interquartile range. Returns a boolean mask.

    Not wired into the app yet -- a good first feature to add yourself.
    See the README roadmap for how this could plug into a new UI tab.
    """
    clean = series.dropna()
    if clean.empty:
        return pd.Series(False, index=series.index)
    q1, q3 = np.percentile(clean, [25, 75])
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return (series < lower) | (series > upper)


def build_summary_report(before: dict, after: dict, actions_log: list) -> str:
    """Build a short markdown report comparing before/after profiles."""
    lines = [
        "### Before → after",
        f"- **Rows:** {before['rows']} → {after['rows']}",
        f"- **Missing values:** {before['missing_total']} → {after['missing_total']}",
        f"- **Duplicate rows:** {before['duplicate_rows']} → {after['duplicate_rows']}",
        "",
        "### What changed",
    ]
    if actions_log:
        lines += [f"- {action}" for action in actions_log]
    else:
        lines.append("- No changes applied yet")
    return "\n".join(lines)
