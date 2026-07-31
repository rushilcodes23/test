import time

import pandas as pd
import streamlit as st

from cleaning import (
    profile_data,
    fill_missing,
    drop_missing_rows,
    drop_duplicate_rows,
    strip_whitespace,
    fix_dtype,
    text_columns,
    numeric_columns,
    top_category_by_sum,
    average_value,
    extreme_value,
    build_summary_report,
)

st.set_page_config(page_title="TidyBench", page_icon="🩺", layout="wide")

# Cards are plain st.container(border=True) blocks with an invisible marker as their
# first child; :has() finds the container that holds that marker so we can restyle
# just that one, since every Streamlit layout block shares the same data-testid.
st.markdown(
    """
    <style>
    :root {
        --td-accent: #0F6E56;
        --td-accent-soft: #E4F0EC;
        --td-radius: 16px;
    }

    div[data-testid="stVerticalBlock"]:has(> div.stMarkdown span.card-anchor),
    div[data-testid="stVerticalBlock"]:has(> div > div.stMarkdown span.card-anchor),
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stMarkdown"] span.card-anchor),
    div[data-testid="stVerticalBlock"]:has(> div > div[data-testid="stMarkdown"] span.card-anchor) {
        background: #FFFFFF;
        border-radius: var(--td-radius) !important;
        padding: 1.5rem 1.75rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 14px rgba(15, 110, 86, 0.09), 0 1px 2px rgba(0, 0, 0, 0.04);
        border: 1px solid rgba(15, 110, 86, 0.08) !important;
    }
    .card-anchor {
        display: none;
    }

    section[data-testid="stSidebar"] {
        border-right: 1px solid rgba(15, 110, 86, 0.15);
    }
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: var(--td-accent);
    }

    .stButton > button,
    .stDownloadButton > button {
        border-radius: 10px;
        border: 1px solid var(--td-accent);
        color: var(--td-accent);
        background: #FFFFFF;
        transition: background 0.15s ease, color 0.15s ease;
    }
    .stButton > button:hover,
    .stDownloadButton > button:hover {
        background: var(--td-accent);
        color: #FFFFFF;
        border-color: var(--td-accent);
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 10px 10px 0 0;
    }
    .stTabs [aria-selected="true"] {
        color: var(--td-accent) !important;
    }

    [data-testid="stMetric"] {
        background: var(--td-accent-soft);
        border-radius: 12px;
        padding: 0.6rem 0.9rem;
    }

    [data-testid="stFileUploader"],
    [data-testid="stFileUploaderDropzone"],
    [data-testid="stExpander"],
    [data-testid="stDataFrame"] {
        border-radius: var(--td-radius) !important;
        overflow: hidden;
    }

    h2 {
        border-bottom: 2px solid var(--td-accent-soft);
        padding-bottom: 0.35rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🩺 TidyBench")
st.caption("Upload a messy CSV, see what's wrong with it, fix it in a few clicks, and leave with a clean file and a report.")

# --- session state ---
if "df" not in st.session_state:
    st.session_state.df = None
if "original_profile" not in st.session_state:
    st.session_state.original_profile = None
if "actions_log" not in st.session_state:
    st.session_state.actions_log = []
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

with st.sidebar:
    st.subheader("Upload")
    uploaded_file = st.file_uploader(
        "Upload a CSV file", type=["csv"], key=f"uploader_{st.session_state.uploader_key}"
    )

    st.divider()
    st.subheader("How to use")
    st.markdown(
        "1. **Upload** — drop in your CSV, or try the sample data\n"
        "2. **Diagnose** — see rows, missing values, duplicates, and dtypes at a glance\n"
        "3. **Treat** — fix missing values, duplicates, whitespace, and column types\n"
        "4. **Download & Insights** — grab the cleaned file and report, then ask quick questions about your data"
    )

if uploaded_file is not None and st.session_state.df is None:
    try:
        uploaded_file.seek(0)
        st.session_state.df = pd.read_csv(uploaded_file)
        st.session_state.original_profile = profile_data(st.session_state.df)
        st.session_state.actions_log = []
    except Exception as e:
        st.error(
            "Couldn't read that as a CSV. Likely causes:\n"
            "- **Wrong delimiter** — it's separated by semicolons, tabs, or something other than a comma\n"
            "- **Empty file** — there's no data (or no header row) to read\n"
            "- **Bad encoding** — it's saved as something other than UTF-8 (try re-saving as UTF-8 CSV)\n\n"
            f"Details: {e}"
        )
        st.stop()

if st.session_state.df is None:
    st.info("Upload a CSV to get started, or point it at `sample_data/messy_sales.csv` to try it out first.")
    st.stop()

if st.button("Start over with a new file"):
    st.session_state.df = None
    st.session_state.original_profile = None
    st.session_state.actions_log = []
    st.session_state.uploader_key += 1
    st.rerun()

df = st.session_state.df
profile = profile_data(df)

# --- diagnosis ---
with st.container(border=True):
    st.markdown('<span class="card-anchor"></span>', unsafe_allow_html=True)
    st.header("Diagnosis")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Rows", profile["rows"])
    col2.metric("Columns", profile["columns"])
    col3.metric("Missing values", profile["missing_total"])
    col4.metric("Duplicate rows", profile["duplicate_rows"])

    with st.expander("See column details"):
        details = pd.DataFrame({
            "dtype": profile["dtypes"],
            "missing values": profile["missing_by_column"],
        })
        st.dataframe(details, use_container_width=True)

    if profile["missing_total"] > 0:
        st.caption("Missing values by column")
        st.bar_chart(pd.Series(profile["missing_by_column"]))

# --- treatment ---
with st.container(border=True):
    st.markdown('<span class="card-anchor"></span>', unsafe_allow_html=True)
    st.header("Treatment")
    tab1, tab2, tab3 = st.tabs(["Missing values", "Duplicates & text", "Column types"])

    with tab1:
        col = st.selectbox("Column to fix", df.columns, key="missing_col")
        is_numeric = pd.api.types.is_numeric_dtype(df[col])
        strategy_options = ["mean", "median", "mode", "custom", "drop rows"] if is_numeric else ["mode", "custom", "drop rows"]
        strategy = st.radio("Strategy", strategy_options, horizontal=True)
        custom_val = None
        if strategy == "custom":
            custom_val = st.text_input("Fill with")
        if st.button("Apply fix", key="apply_missing"):
            try:
                if strategy == "drop rows":
                    st.session_state.df = drop_missing_rows(df, column=col)
                    st.session_state.actions_log.append(f"Dropped rows with missing values in '{col}'")
                else:
                    st.session_state.df = fill_missing(df, col, strategy=strategy, custom_value=custom_val)
                    st.session_state.actions_log.append(f"Filled missing values in '{col}' using {strategy}")
                st.rerun()
            except Exception as e:
                st.error(f"That fix didn't work: {e}")

    with tab2:
        left, right = st.columns(2)
        with left:
            st.write("Exact duplicate rows")
            if st.button("Remove duplicate rows"):
                before_count = len(df)
                st.session_state.df = drop_duplicate_rows(df)
                removed = before_count - len(st.session_state.df)
                st.session_state.actions_log.append(f"Removed {removed} duplicate rows")
                st.rerun()
        with right:
            st.write("Stray whitespace in text")
            cols = text_columns(df)
            if cols:
                text_col = st.selectbox("Column", cols, key="strip_col")
                if st.button("Strip whitespace"):
                    st.session_state.df = strip_whitespace(df, text_col)
                    st.session_state.actions_log.append(f"Stripped whitespace in '{text_col}'")
                    st.rerun()
            else:
                st.caption("No text columns found.")

    with tab3:
        type_col = st.selectbox("Column", df.columns, key="type_col")
        new_type = st.selectbox("Convert to", ["numeric", "datetime", "text"])
        if st.button("Convert"):
            try:
                st.session_state.df = fix_dtype(df, type_col, new_type)
                st.session_state.actions_log.append(f"Converted '{type_col}' to {new_type}")
                st.rerun()
            except Exception as e:
                st.error(f"That conversion didn't work: {e}")

# --- result ---
with st.container(border=True):
    st.markdown('<span class="card-anchor"></span>', unsafe_allow_html=True)
    st.header("Result")
    st.dataframe(st.session_state.df.head(20), use_container_width=True)

    csv_bytes = st.session_state.df.to_csv(index=False).encode("utf-8")
    st.download_button("Download cleaned CSV", csv_bytes, "cleaned_data.csv", "text/csv")

# --- summary report ---
with st.container(border=True):
    st.markdown('<span class="card-anchor"></span>', unsafe_allow_html=True)
    st.header("Summary report")
    after_profile = profile_data(st.session_state.df)
    report_md = build_summary_report(st.session_state.original_profile, after_profile, st.session_state.actions_log)
    st.markdown(report_md)
    st.download_button("Download report (.md)", report_md, "cleaning_report.md", "text/markdown")

# --- quick insights ---
with st.container(border=True):
    st.markdown('<span class="card-anchor"></span>', unsafe_allow_html=True)
    st.header("Quick Insights")

    clean_df = st.session_state.df
    num_cols = numeric_columns(clean_df)
    cat_cols = text_columns(clean_df)

    if not num_cols:
        st.caption("No numeric columns to build insights from.")
    else:
        presets = []
        for cat_col in cat_cols:
            for num_col in num_cols:
                presets.append({
                    "label": f"Which {cat_col} has the highest total {num_col}?",
                    "kind": "top_category",
                    "category_col": cat_col,
                    "numeric_col": num_col,
                })
        for num_col in num_cols:
            presets.append({
                "label": f"What's the average {num_col}?",
                "kind": "average",
                "numeric_col": num_col,
            })
        for num_col in num_cols:
            presets.append({
                "label": f"What's the highest single {num_col}?",
                "kind": "extreme",
                "numeric_col": num_col,
                "which": "highest",
            })
            presets.append({
                "label": f"What's the lowest single {num_col}?",
                "kind": "extreme",
                "numeric_col": num_col,
                "which": "lowest",
            })

        chosen_label = st.selectbox("Pick a question", [p["label"] for p in presets], key="insight_preset")
        chosen = next(p for p in presets if p["label"] == chosen_label)

        if st.button("Get answer", key="insight_compute"):
            with st.spinner("Crunching the numbers..."):
                time.sleep(0.3)
                if chosen["kind"] == "top_category":
                    raw = top_category_by_sum(clean_df, chosen["category_col"], chosen["numeric_col"])
                    headline_label = f"Top {chosen['category_col']}: {raw['top_category']}"
                    headline_value = raw["top_total"]
                    sentence = (
                        f"**{raw['top_category']}** has the highest total **{chosen['numeric_col']}** "
                        f"at **{raw['top_total']:,.2f}**."
                    )
                    easy_sentence = f"{raw['top_category']} has the most {chosen['numeric_col']}."
                    diff_pct = (raw["top_total"] / raw["average_total"] - 1) * 100 if raw["average_total"] else 0.0
                    better_note = (
                        f"That's {diff_pct:,.0f}% above the average {chosen['category_col']} total "
                        f"of {raw['average_total']:,.2f}."
                    )
                    breakdown = raw["breakdown"].rename("total").reset_index()
                elif chosen["kind"] == "average":
                    raw = average_value(clean_df, chosen["numeric_col"])
                    headline_label = f"Average {chosen['numeric_col']}"
                    headline_value = raw["mean"]
                    sentence = f"The average **{chosen['numeric_col']}** is **{raw['mean']:,.2f}**."
                    easy_sentence = f"{chosen['numeric_col']} averages around {raw['mean']:,.0f}."
                    better_note = f"Values range from {raw['min']:,.2f} to {raw['max']:,.2f}."
                    breakdown = pd.DataFrame({"stat": ["min", "mean", "max"], "value": [raw["min"], raw["mean"], raw["max"]]})
                else:
                    raw = extreme_value(clean_df, chosen["numeric_col"], chosen["which"])
                    headline_label = f"{chosen['which'].title()} {chosen['numeric_col']}"
                    headline_value = raw["value"]
                    sentence = f"The {chosen['which']} single **{chosen['numeric_col']}** is **{raw['value']:,.2f}**."
                    easy_sentence = f"{raw['value']:,.0f} is the {chosen['which']} {chosen['numeric_col']} recorded."
                    diff_pct = (raw["value"] / raw["average"] - 1) * 100 if raw["average"] else 0.0
                    better_note = f"That's {diff_pct:,.0f}% relative to the average of {raw['average']:,.2f}."
                    breakdown = pd.DataFrame([raw["row"]])

            st.session_state.insight = {
                "headline_label": headline_label,
                "headline_value": headline_value,
                "sentence": sentence,
                "easy_sentence": easy_sentence,
                "better_note": better_note,
                "breakdown": breakdown,
            }
            st.session_state.insight_show_easy = False
            st.session_state.insight_show_better = False
            st.session_state.insight_just_computed = True
            st.rerun()

        insight = st.session_state.get("insight")
        if insight is not None:
            placeholder = st.empty()
            if st.session_state.get("insight_just_computed"):
                steps = 20
                target = insight["headline_value"]
                for i in range(1, steps + 1):
                    placeholder.metric(insight["headline_label"], f"{target * i / steps:,.2f}")
                    time.sleep(0.02)
                st.session_state.insight_just_computed = False
            placeholder.metric(insight["headline_label"], f"{insight['headline_value']:,.2f}")
            st.write(insight["sentence"])

            easy_col, better_col = st.columns(2)
            if easy_col.button("Easy understanding"):
                st.session_state.insight_show_easy = True
            if better_col.button("Better answer"):
                st.session_state.insight_show_better = True

            if st.session_state.get("insight_show_easy"):
                st.info(insight["easy_sentence"])
            if st.session_state.get("insight_show_better"):
                st.write(insight["better_note"])
                st.dataframe(insight["breakdown"], use_container_width=True)
