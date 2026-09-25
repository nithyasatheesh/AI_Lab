import streamlit as st
import pandas as pd
import duckdb
import io
import contextlib
import numpy as np

st.set_page_config(
    page_title="AI DataLab",
    page_icon="💻",
    layout="wide"
)

st.title("💻 AI DataLab")
st.caption("Python & SQL Practice Lab")

if "python_output" not in st.session_state:
    st.session_state.python_output = ""

lab = st.sidebar.radio(
    "Select Lab",
    ["Home", "Python Lab", "SQL Lab"]
)

st.sidebar.markdown("---")
st.sidebar.info("Prototype for controlled training use. Python execution is intentionally limited to the supplied dataframe and common libraries.")

if lab == "Home":
    st.header("Welcome to AI DataLab")
    st.markdown("""
### Practice Environment

Use this lab to:
- Upload CSV or Excel datasets
- Practice Python and Pandas
- Practice SQL using DuckDB
- View results and execution errors

### Suggested Training Flow
**Day 1:** Python + Pandas  
**Day 2:** SQL + Data Analytics
""")

elif lab == "Python Lab":
    st.header("🐍 Python Practice Lab")

    uploaded_file = st.file_uploader(
        "Upload CSV or Excel Dataset",
        type=["csv", "xlsx"],
        key="python_file"
    )

    if uploaded_file:
        try:
            if uploaded_file.name.lower().endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            st.success(f"Loaded: {uploaded_file.name}")

            c1, c2, c3 = st.columns(3)
            c1.metric("Rows", f"{df.shape[0]:,}")
            c2.metric("Columns", f"{df.shape[1]:,}")
            c3.metric("Missing Values", f"{int(df.isna().sum().sum()):,}")

            with st.expander("Preview Dataset", expanded=True):
                st.dataframe(df.head(10), use_container_width=True)

            st.markdown("### Python Exercise")
            st.info("Try: Display the first 5 rows, calculate the average of a numeric column, or group the data by a category.")

            default_code = """# Example
print(df.head())
print("\\nShape:", df.shape)

# Example aggregation:
# print(df["Sales"].mean())
"""

            code = st.text_area(
                "Python Code",
                value=default_code,
                height=260,
                key="python_code"
            )

            if st.button("▶ Run Python Code", type="primary"):
                output = io.StringIO()

                # This is a training prototype. Do not expose unrestricted exec()
                # to untrusted/public users. A production deployment should use
                # an isolated sandbox/container execution service.
                safe_globals = {
                    "__builtins__": {
                        "print": print,
                        "len": len,
                        "range": range,
                        "sum": sum,
                        "min": min,
                        "max": max,
                        "abs": abs,
                        "round": round,
                    },
                    "pd": pd,
                    "np": np,
                    "df": df,
                }

                try:
                    with contextlib.redirect_stdout(output):
                        exec(code, safe_globals, {})
                    st.session_state.python_output = output.getvalue() or "Code executed successfully. No printed output."
                    st.success("Code executed successfully.")
                except Exception as e:
                    st.session_state.python_output = ""
                    st.error(f"{type(e).__name__}: {e}")

            st.markdown("### Output")
            st.code(st.session_state.python_output or "Run your code to see output.", language="text")

        except Exception as e:
            st.error(f"Unable to read the uploaded file: {type(e).__name__}: {e}")

elif lab == "SQL Lab":
    st.header("🗄️ SQL Practice Lab")

    uploaded_file = st.file_uploader(
        "Upload CSV Dataset",
        type=["csv"],
        key="sql_file"
    )

    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)

            st.success(f"Loaded: {uploaded_file.name}")

            with st.expander("Preview Dataset", expanded=True):
                st.dataframe(df.head(10), use_container_width=True)

            st.markdown("### SQL Exercise")
            st.info("The uploaded CSV is available as the SQL table: sales")

            con = duckdb.connect(database=":memory:")
            con.register("sales", df)

            query = st.text_area(
                "SQL Query",
                value="""SELECT *
FROM sales
LIMIT 10;""",
                height=220,
                key="sql_query"
            )

            if st.button("▶ Run SQL", type="primary"):
                try:
                    result = con.execute(query).df()
                    st.success(f"Query executed successfully. {len(result):,} rows returned.")
                    st.dataframe(result, use_container_width=True)

                    csv_result = result.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        "Download Result as CSV",
                        data=csv_result,
                        file_name="sql_result.csv",
                        mime="text/csv"
                    )
                except Exception as e:
                    st.error(f"{type(e).__name__}: {e}")

            con.close()

        except Exception as e:
            st.error(f"Unable to read the uploaded CSV: {type(e).__name__}: {e}")
