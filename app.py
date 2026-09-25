import streamlit as st
import pandas as pd
import numpy as np
import io
import contextlib
import sqlite3
import builtins
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="AI DataLab", page_icon="💻", layout="wide")
st.title("💻 AI DataLab")
st.caption("Python & SQL Practice Lab")

lab = st.sidebar.radio("Select Lab", ["Home", "Python Lab", "SQL Lab"])

if lab == "Home":
    st.header("Welcome to AI DataLab")
    st.markdown("""
### Participant Practice Lab
- Upload CSV datasets
- Run Python / Pandas / NumPy code
- Create Matplotlib and Seaborn charts
- Practice SQL queries
- View results immediately

**Day 1:** Python + Pandas + Visualization  
**Day 2:** SQL + Data Analytics
""")

elif lab == "Python Lab":
    st.header("🐍 Python Practice Lab")
    uploaded_file = st.file_uploader("Upload a CSV dataset", type=["csv"], key="python_upload")

    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            st.success(f"Dataset loaded: {uploaded_file.name}")
            c1, c2, c3 = st.columns(3)
            c1.metric("Rows", f"{len(df):,}")
            c2.metric("Columns", f"{len(df.columns):,}")
            c3.metric("Missing Values", f"{int(df.isna().sum().sum()):,}")
            st.subheader("Dataset Preview")
            st.dataframe(df.head(10), use_container_width=True)

            code = st.text_area(
                "Python",
                value="# Example\nprint(df.head())\n\nimport matplotlib.pyplot as plt\n\nplt.hist(df[\"#Passengers\"])\nplt.xlabel(\"Passengers\")\nplt.ylabel(\"Frequency\")\nplt.title(\"Passenger Distribution\")\nplt.show()\n",
                height=300
            )

            if st.button("▶ Run Python Code", type="primary"):
                output = io.StringIO()
                original_import = builtins.__import__

                def restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
                    root = name.split(".")[0]
                    allowed = {"pandas", "numpy", "matplotlib", "seaborn"}
                    if root not in allowed:
                        raise ImportError(f"Import of '{name}' is not allowed in this training lab.")
                    return original_import(name, globals, locals, fromlist, level)

                safe_builtins = {
                    "print": print, "len": len, "range": range, "sum": sum,
                    "min": min, "max": max, "abs": abs, "round": round,
                    "sorted": sorted, "enumerate": enumerate,
                    "__import__": restricted_import
                }
                safe_globals = {
                    "__builtins__": safe_builtins,
                    "pd": pd, "np": np, "plt": plt, "sns": sns, "df": df
                }

                plt.close("all")
                try:
                    with contextlib.redirect_stdout(output):
                        exec(code, safe_globals, safe_globals)

                    result = output.getvalue()
                    st.success("Code executed successfully.")
                    if result:
                        st.subheader("Output")
                        st.code(result, language="text")

                    fig = plt.gcf()
                    if fig.get_axes():
                        st.subheader("Chart Output")
                        st.pyplot(fig)
                    plt.close("all")
                except Exception as e:
                    plt.close("all")
                    st.error(f"{type(e).__name__}: {e}")
        except Exception as e:
            st.error(f"Could not read the CSV: {type(e).__name__}: {e}")

elif lab == "SQL Lab":
    st.header("🗄️ SQL Practice Lab")
    uploaded_file = st.file_uploader("Upload a CSV dataset", type=["csv"], key="sql_upload")

    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            st.success(f"Dataset loaded: {uploaded_file.name}")
            st.dataframe(df.head(10), use_container_width=True)
            st.info("Your uploaded CSV is available as SQL table: sales")

            query = st.text_area("SQL Query", value="SELECT *\nFROM sales\nLIMIT 10;", height=220)

            if st.button("▶ Run SQL", type="primary"):
                try:
                    conn = sqlite3.connect(":memory:")
                    df.to_sql("sales", conn, index=False, if_exists="replace")
                    result = pd.read_sql_query(query, conn)
                    conn.close()
                    st.success(f"Query executed successfully. {len(result):,} rows returned.")
                    st.dataframe(result, use_container_width=True)
                    st.download_button(
                        "Download Result as CSV",
                        data=result.to_csv(index=False).encode("utf-8"),
                        file_name="sql_result.csv",
                        mime="text/csv"
                    )
                except Exception as e:
                    st.error(f"{type(e).__name__}: {e}")
        except Exception as e:
            st.error(f"Could not read the CSV: {type(e).__name__}: {e}")
