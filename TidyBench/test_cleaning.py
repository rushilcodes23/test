import sys

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

from cleaning import (
    profile_data, fill_missing, drop_missing_rows, drop_duplicate_rows,
    strip_whitespace, fix_dtype, find_outliers_iqr, build_summary_report,
    numeric_columns, text_columns, top_category_by_sum, average_value, extreme_value,
)

df = pd.read_csv("sample_data/messy_sales.csv")
print("Loaded shape:", df.shape)

before = profile_data(df)
print("\n-- profile_data (before) --")
for k, v in before.items():
    print(f"{k}: {v}")

assert before["rows"] == 18
assert before["duplicate_rows"] == 2, f"expected 2 duplicate rows, got {before['duplicate_rows']}"
assert before["missing_total"] == 5, f"expected 5 missing values, got {before['missing_total']}"

actions = []

df2 = drop_duplicate_rows(df)
actions.append(f"Removed {len(df) - len(df2)} duplicate rows")
assert len(df2) == 16

df3 = fill_missing(df2, "quantity", strategy="median")
actions.append("Filled missing values in 'quantity' using median")
assert df3["quantity"].isnull().sum() == 0

df4 = fill_missing(df3, "unit_price", strategy="mean")
actions.append("Filled missing values in 'unit_price' using mean")
assert df4["unit_price"].isnull().sum() == 0

df5 = strip_whitespace(df4, "customer")
df5 = strip_whitespace(df5, "region")
actions.append("Stripped whitespace in 'customer' and 'region'")
assert df5["customer"].iloc[1] == "Jane Doe"
assert df5["region"].iloc[6] == "west"

df6 = fix_dtype(df5, "order_date", "datetime")
actions.append("Converted 'order_date' to datetime")
assert str(df6["order_date"].dtype).startswith("datetime")

after = profile_data(df6)
print("\n-- profile_data (after) --")
for k, v in after.items():
    print(f"{k}: {v}")

assert after["missing_total"] == 0
assert after["duplicate_rows"] == 0

report = build_summary_report(before, after, actions)
print("\n-- summary report --")
print(report)

outlier_mask = find_outliers_iqr(df6["quantity"])
print("\n-- outlier check on quantity --")
print(df6.loc[outlier_mask, ["customer", "quantity"]])
assert outlier_mask.sum() == 1, f"expected exactly 1 outlier, got {outlier_mask.sum()}"

print("\n-- quick insights --")
assert numeric_columns(df6) == ["order_id", "quantity", "unit_price"]
assert text_columns(df6) == ["customer", "region", "product"]

top = top_category_by_sum(df6, "product", "quantity")
print("top_category_by_sum(product, quantity):", top)
assert top["top_category"] == "Widget D"
assert round(top["top_total"], 2) == 513.0

avg = average_value(df6, "quantity")
print("average_value(quantity):", avg)
assert round(avg["mean"], 4) == 36.0625

highest = extreme_value(df6, "quantity", "highest")
lowest = extreme_value(df6, "quantity", "lowest")
print("extreme_value(quantity, highest):", highest)
print("extreme_value(quantity, lowest):", lowest)
assert highest["value"] == 500.0
assert lowest["value"] == 2.0

print("\nAll checks passed.")
