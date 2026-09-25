import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sqlite3
import io
import contextlib
import builtins
import ast
import re
import json

st.set_page_config(
    page_title="ICICI Data Analytics Lab",
    page_icon="💻",
    layout="wide"
)

st.title("💻 ICICI Data Analytics Lab")
st.caption("Browser-Based Python & SQL Practice Environment")


# ============================================================
# HELPERS
# ============================================================

def clean_name(filename):
    name = re.sub(r"\W+", "_", filename.rsplit(".", 1)[0])
    name = re.sub(r"_+", "_", name).strip("_") or "dataset"
    if name[0].isdigit():
        name = "dataset_" + name
    return name


def make_env(dataframes=None):
    dataframes = dataframes or {}
    original_import = builtins.__import__

    def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
        allowed = {"pandas", "numpy", "matplotlib"}
        if name.split(".")[0] not in allowed:
            raise ImportError(
                f"Import of '{name}' is not allowed in this training lab."
            )
        return original_import(name, globals, locals, fromlist, level)

    safe_builtins = {
        "print": print,
        "len": len,
        "range": range,
        "sum": sum,
        "min": min,
        "max": max,
        "abs": abs,
        "round": round,
        "sorted": sorted,
        "enumerate": enumerate,
        "list": list,
        "dict": dict,
        "set": set,
        "tuple": tuple,
        "__import__": safe_import
    }

    env = {
        "__builtins__": safe_builtins,
        "pd": pd,
        "np": np,
        "plt": plt
    }

    for name, df in dataframes.items():
        env[name] = df

    if dataframes:
        env["df"] = next(iter(dataframes.values()))

    return env


def execute_code(code, env):
    output = io.StringIO()
    result = None
    plt.close("all")

    try:
        tree = ast.parse(code)

        if tree.body and isinstance(tree.body[-1], ast.Expr):

            last_expression = tree.body[-1].value
            previous = tree.body[:-1]

            if previous:
                module = ast.Module(
                    body=previous,
                    type_ignores=[]
                )
                ast.fix_missing_locations(module)

                with contextlib.redirect_stdout(output):
                    exec(
                        compile(module, "<participant_code>", "exec"),
                        env,
                        env
                    )

            expression = ast.Expression(
                body=last_expression
            )
            ast.fix_missing_locations(expression)

            with contextlib.redirect_stdout(output):
                result = eval(
                    compile(
                        expression,
                        "<participant_code>",
                        "eval"
                    ),
                    env,
                    env
                )

        else:
            with contextlib.redirect_stdout(output):
                exec(code, env, env)

        fig = plt.gcf() if plt.get_fignums() else None

        return True, output.getvalue(), result, fig, None

    except Exception as e:

        plt.close("all")

        return (
            False,
            output.getvalue(),
            None,
            None,
            f"{type(e).__name__}: {e}"
        )


def display_result(result):

    if result is None:
        return

    if isinstance(result, pd.DataFrame):
        st.dataframe(
            result,
            use_container_width=True
        )

    elif isinstance(result, pd.Series):
        st.dataframe(
            result.to_frame(),
            use_container_width=True
        )

    else:
        st.write(result)


def extract_notebook_cells(data):

    notebook = json.loads(
        data.decode("utf-8")
    )

    cells = []

    for cell in notebook.get("cells", []):

        if cell.get("cell_type") == "code":

            source = cell.get("source", [])

            if isinstance(source, list):
                source = "".join(source)

            cells.append(source)

    return cells


# ============================================================
# SESSION STATE
# ============================================================

defaults = {
    "python_env": make_env(),
    "uploaded_dataframes": {},
    "python_code": "",
    "notebook_cells": [],
    "notebook_outputs": {},
    "notebook_loaded_name": None,
    "sql_tables": {}
}

for key, value in defaults.items():

    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# SIDEBAR
# ============================================================

page = st.sidebar.radio(
    "Select Lab",
    [
        "Home",
        "1. Python Coding",
        "2. Python Data Manipulation",
        "3. SQL Lab"
    ]
)


# ============================================================
# HOME
# ============================================================

if page == "Home":

    st.header("Welcome to ICICI Data Analytics Lab")

    st.markdown("""
### Browser-Based Hands-On Environment

Participants can:

- Write and run basic Python code
- Upload CSV datasets
- Upload Jupyter notebooks
- Run notebook cells individually
- Edit notebook cells
- Add new notebook cells
- Practice Python data manipulation
- Practice SQL using uploaded datasets
- Check whether task answers are correct

### Participant Flow

```text
Python Code
     ↓
Upload Data (if required)
     ↓
Upload Jupyter Notebook (if required)
     ↓
Run Code / Run Cells
     ↓
View Output
     ↓
Correct / Incorrect
```

No API key is required.
""")


# ============================================================
# 1. PYTHON CODING
# ============================================================

elif page == "1. Python Coding":

    st.header("🐍 Python Lab")

    st.info(
        "Start by writing and running Python code. "
        "Upload a dataset or Jupyter Notebook only when you need them."
    )

    # ========================================================
    # OPTION 1 — WRITE AND RUN PYTHON CODE FIRST
    # ========================================================

    st.subheader("Option 1 — Write & Run Python Code")

    code = st.text_area(
        "Python Code",
        value=st.session_state.python_code,
        height=250,
        placeholder='Example: print("Hello World!")',
        key="python_editor"
    )

    st.session_state.python_code = code

    if st.button(
        "▶ Run Python Code",
        type="primary",
        use_container_width=False
    ):

        ok, output, result, fig, error = execute_code(
            code,
            st.session_state.python_env
        )

        if ok:

            st.success("✅ Code executed successfully.")

            if output:
                st.subheader("Output")
                st.code(output, language="text")

            if result is not None:
                st.subheader("Result")
                display_result(result)

            if fig is not None:
                st.subheader("Chart")
                st.pyplot(fig)

        else:

            st.error("❌ Code execution failed.")
            st.code(error, language="text")

    st.divider()

    # ========================================================
    # OPTION 2 — UPLOAD DATASET
    # ========================================================

    st.subheader("Option 2 — Upload Dataset")

    st.caption(
        "Upload one or more CSV files when you want to work "
        "with real data."
    )

    data_files = st.file_uploader(
        "Upload CSV dataset(s)",
        type=["csv"],
        accept_multiple_files=True,
        key="basic_data_upload"
    )

    if data_files:

        dataframes = {}

        for file in data_files:

            try:
                dataframes[clean_name(file.name)] = pd.read_csv(file)
            except Exception as e:
                st.error(f"Could not read {file.name}: {e}")

        if dataframes:

            st.session_state.uploaded_dataframes = dataframes
            st.session_state.python_env = make_env(dataframes)

            st.success(
                f"✅ {len(dataframes)} dataset(s) uploaded successfully."
            )

            st.info(
                "The first dataset is available as `df`. "
                "Each dataset is also available using a variable "
                "based on its filename."
            )

            for name, df in dataframes.items():

                with st.expander(
                    f"📄 {name} — "
                    f"{len(df):,} rows × {len(df.columns):,} columns"
                ):

                    st.dataframe(
                        df.head(10),
                        use_container_width=True
                    )

                    st.write("Columns:", list(df.columns))

    # --------------------------------------------------------
    # RUN PYTHON USING DATA
    # --------------------------------------------------------

    if st.session_state.uploaded_dataframes:

        st.markdown("### Run Python Code Using Uploaded Data")

        st.caption(
            "Example: `df.head()` or `df.describe()`"
        )

        data_code = st.text_area(
            "Python Data Code",
            height=220,
            key="basic_data_code"
        )

        if st.button(
            "▶ Run Data Code",
            use_container_width=False
        ):

            ok, output, result, fig, error = execute_code(
                data_code,
                st.session_state.python_env
            )

            if ok:

                st.success("✅ Code executed successfully.")

                if output:
                    st.code(output, language="text")

                if result is not None:
                    display_result(result)

                if fig is not None:
                    st.pyplot(fig)

            else:

                st.error("❌ Code execution failed.")
                st.code(error, language="text")

    st.divider()

    # ========================================================
    # OPTION 3 — UPLOAD JUPYTER NOTEBOOK
    # ========================================================

    st.subheader("Option 3 — Upload Jupyter Notebook")

    st.caption(
        "Upload an `.ipynb` file to continue working with notebook cells."
    )

    notebook_file = st.file_uploader(
        "Upload Jupyter Notebook (.ipynb)",
        type=["ipynb"],
        key="basic_notebook_upload"
    )

    if notebook_file:

        try:

            file_id = (
                notebook_file.name,
                len(notebook_file.getvalue())
            )

            if st.session_state.notebook_loaded_name != file_id:

                cells = extract_notebook_cells(
                    notebook_file.getvalue()
                )

                st.session_state.notebook_cells = cells.copy()
                st.session_state.notebook_outputs = {}
                st.session_state.notebook_loaded_name = file_id

                st.session_state.python_env = make_env(
                    st.session_state.uploaded_dataframes
                )

            cells = st.session_state.notebook_cells

            if not cells:

                st.warning(
                    "No Python code cells were found in this notebook."
                )

            else:

                st.success(
                    f"✅ {len(cells)} Python code cell(s) loaded."
                )

                if st.button(
                    "▶ Run All Notebook Cells",
                    type="primary",
                    use_container_width=False
                ):

                    st.session_state.python_env = make_env(
                        st.session_state.uploaded_dataframes
                    )

                    st.session_state.notebook_outputs = {}

                    for i, cell_code in enumerate(cells):

                        ok, output, result, fig, error = execute_code(
                            cell_code,
                            st.session_state.python_env
                        )

                        if ok:

                            st.session_state.notebook_outputs[i] = {
                                "output": output,
                                "result": result,
                                "fig": fig
                            }

                        else:

                            st.session_state.notebook_outputs[i] = {
                                "error": error,
                                "output": output
                            }

                    st.rerun()

                st.divider()

                for i in range(len(st.session_state.notebook_cells)):

                    st.markdown(f"### Notebook Cell {i + 1}")

                    edited_code = st.text_area(
                        f"Cell {i + 1} Code",
                        value=st.session_state.notebook_cells[i],
                        height=180,
                        key=f"notebook_cell_{i}"
                    )

                    st.session_state.notebook_cells[i] = edited_code

                    c1, c2 = st.columns(2)

                    with c1:

                        if st.button(
                            f"▶ Run Cell {i + 1}",
                            key=f"run_notebook_{i}",
                            use_container_width=True
                        ):

                            ok, output, result, fig, error = execute_code(
                                edited_code,
                                st.session_state.python_env
                            )

                            if ok:

                                st.session_state.notebook_outputs[i] = {
                                    "output": output,
                                    "result": result,
                                    "fig": fig
                                }

                            else:

                                st.session_state.notebook_outputs[i] = {
                                    "error": error,
                                    "output": output
                                }

                            st.rerun()

                    with c2:

                        if st.button(
                            f"🗑 Delete Cell {i + 1}",
                            key=f"delete_notebook_{i}",
                            use_container_width=True
                        ):

                            st.session_state.notebook_cells.pop(i)

                            st.session_state.notebook_outputs = {
                                k: v
                                for k, v
                                in st.session_state.notebook_outputs.items()
                                if k != i
                            }

                            st.rerun()

                    cell_result = st.session_state.notebook_outputs.get(i)

                    if cell_result:

                        if "error" in cell_result:

                            st.error("❌ Cell execution failed")

                            st.code(
                                cell_result["error"],
                                language="text"
                            )

                        else:

                            st.success("✅ Cell executed successfully")

                            if cell_result.get("output"):
                                st.code(
                                    cell_result["output"],
                                    language="text"
                                )

                            if cell_result.get("result") is not None:
                                display_result(
                                    cell_result["result"]
                                )

                            if cell_result.get("fig") is not None:
                                st.pyplot(
                                    cell_result["fig"]
                                )

                    st.divider()

                if st.button(
                    "➕ Add New Notebook Cell",
                    use_container_width=False
                ):

                    st.session_state.notebook_cells.append(
                        "# Write Python code here"
                    )

                    st.rerun()


# ============================================================
# 2. PYTHON DATA MANIPULATION
# ============================================================

elif page == "2. Python Data Manipulation":

    st.header("🐼 2. Python Data Manipulation")

    task = st.selectbox(
        "Choose a practice task",
        [
            "Task 1 — Display first 5 rows",
            "Task 2 — Find number of rows",
            "Task 3 — Find average amount",
            "Task 4 — Filter records",
            "Task 5 — Group and aggregate"
        ]
    )

    if task.startswith("Task 1"):
        instruction = "**Task:** Display the first 5 rows using Pandas."
        default_code = "df.head()"

    elif task.startswith("Task 2"):
        instruction = "**Task:** Find the number of rows."
        default_code = "df.shape[0]"

    elif task.startswith("Task 3"):
        instruction = "**Task:** Find the average of the `amount` column."
        default_code = 'df["amount"].mean()'

    elif task.startswith("Task 4"):
        instruction = "**Task:** Filter records where `amount` is greater than 3000."
        default_code = 'df[df["amount"] > 3000]'

    else:
        instruction = "**Task:** Group by `region` and calculate total `amount`."
        default_code = 'df.groupby("region")["amount"].sum()'

    st.info(instruction)

    files = st.file_uploader(
        "Upload CSV dataset(s)",
        type=["csv"],
        accept_multiple_files=True,
        key="data_lab_upload"
    )

    if files:

        dataframes = {}

        for file in files:

            dataframes[
                clean_name(file.name)
            ] = pd.read_csv(file)

        st.success(
            f"✅ {len(dataframes)} dataset(s) uploaded."
        )

        first = next(iter(dataframes))

        st.info(
            f"Use `df` or `{first}` in your Python code."
        )

        for name, df in dataframes.items():

            with st.expander(name):

                st.dataframe(
                    df.head(10),
                    use_container_width=True
                )

        code = st.text_area(
            "Write Python Code",
            value=default_code,
            height=220,
            key="task_python_code"
        )

        if st.button(
            "▶ Run & Check Answer",
            type="primary",
            use_container_width=True
        ):

            ok, output, result, fig, error = execute_code(
                code,
                make_env(dataframes)
            )

            if not ok:

                st.error(
                    "❌ Incorrect / Code Error"
                )

                st.code(error)

            else:

                if output:
                    st.code(output)

                if result is not None:
                    st.subheader("Your Result")
                    display_result(result)

                if fig is not None:
                    st.pyplot(fig)

                df = next(iter(dataframes.values()))
                correct = False

                try:

                    if task.startswith("Task 1"):
                        correct = (
                            isinstance(result, pd.DataFrame)
                            and result.equals(df.head())
                        )

                    elif task.startswith("Task 2"):
                        correct = result == df.shape[0]

                    elif task.startswith("Task 3"):
                        correct = (
                            "amount" in df.columns
                            and np.isclose(
                                float(result),
                                float(df["amount"].mean())
                            )
                        )

                    elif task.startswith("Task 4"):

                        expected = (
                            df[df["amount"] > 3000]
                            .reset_index(drop=True)
                        )

                        correct = (
                            isinstance(result, pd.DataFrame)
                            and result.reset_index(drop=True).equals(
                                expected
                            )
                        )

                    elif task.startswith("Task 5"):

                        expected = (
                            df.groupby("region")["amount"]
                            .sum()
                            .sort_index()
                        )

                        correct = (
                            isinstance(result, pd.Series)
                            and result.sort_index().equals(expected)
                        )

                except Exception:
                    correct = False

                if correct:
                    st.success(
                        "🎉 CORRECT! Your answer matches the expected result."
                    )
                else:
                    st.warning(
                        "⚠️ Code ran, but the result does not match the expected answer."
                    )


# ============================================================
# 3. SQL LAB
# ============================================================

elif page == "3. SQL Lab":

    st.header("🗄️ 3. SQL Practice Lab")

    task = st.selectbox(
        "Choose SQL task",
        [
            "Task 1 — Select first 5 rows",
            "Task 2 — Count rows",
            "Task 3 — Average amount",
            "Task 4 — Filter amount > 3000",
            "Task 5 — Group by region"
        ]
    )

    files = st.file_uploader(
        "Upload CSV dataset(s)",
        type=["csv"],
        accept_multiple_files=True,
        key="sql_upload"
    )

    if files:

        tables = {}

        for file in files:
            tables[
                clean_name(file.name)
            ] = pd.read_csv(file)

        first_table = next(iter(tables))

        if task.startswith("Task 1"):
            instruction = f"Display first 5 rows from `{first_table}`."
            default_sql = f"SELECT * FROM {first_table} LIMIT 5;"

        elif task.startswith("Task 2"):
            instruction = f"Find number of rows in `{first_table}`."
            default_sql = f"SELECT COUNT(*) FROM {first_table};"

        elif task.startswith("Task 3"):
            instruction = f"Find average `amount` from `{first_table}`."
            default_sql = f"SELECT AVG(amount) FROM {first_table};"

        elif task.startswith("Task 4"):
            instruction = "Display records where amount > 3000."
            default_sql = f"SELECT * FROM {first_table} WHERE amount > 3000;"

        else:
            instruction = "Group by region and calculate total amount."
            default_sql = (
                f"SELECT region, SUM(amount) AS total_amount "
                f"FROM {first_table} GROUP BY region;"
            )

        st.info(instruction)

        query = st.text_area(
            "Write SQL",
            value=default_sql,
            height=220,
            key="sql_query_editor"
        )

        if st.button(
            "▶ Run & Check SQL",
            type="primary",
            use_container_width=True
        ):

            try:

                conn = sqlite3.connect(":memory:")

                for table, df in tables.items():

                    df.to_sql(
                        table,
                        conn,
                        index=False,
                        if_exists="replace"
                    )

                result = pd.read_sql_query(
                    query,
                    conn
                )

                conn.close()

                st.success(
                    "✅ SQL executed successfully."
                )

                st.dataframe(
                    result,
                    use_container_width=True
                )

                source = tables[first_table]

                if task.startswith("Task 1"):
                    expected = source.head(5)

                elif task.startswith("Task 2"):
                    expected = pd.DataFrame(
                        {"COUNT(*)": [len(source)]}
                    )

                elif task.startswith("Task 3"):
                    expected = pd.DataFrame(
                        {"AVG(amount)": [source["amount"].mean()]}
                    )

                elif task.startswith("Task 4"):
                    expected = (
                        source[source["amount"] > 3000]
                        .reset_index(drop=True)
                    )

                else:
                    expected = (
                        source.groupby("region")["amount"]
                        .sum()
                        .reset_index(name="total_amount")
                        .sort_values("region")
                        .reset_index(drop=True)
                    )

                actual = result.reset_index(drop=True)

                try:
                    correct = expected.shape == actual.shape

                    if correct and list(expected.columns) == list(actual.columns):
                        for col in expected.columns:
                            if pd.api.types.is_numeric_dtype(expected[col]):
                                actual[col] = pd.to_numeric(
                                    actual[col],
                                    errors="coerce"
                                )
                        correct = expected.equals(actual)
                    else:
                        correct = False

                except Exception:
                    correct = False

                if correct:
                    st.success(
                        "🎉 CORRECT! Your SQL result matches the expected answer."
                    )
                else:
                    st.warning(
                        "⚠️ SQL ran successfully, but the result does not match the expected answer."
                    )

            except Exception as e:

                st.error(
                    "❌ SQL Error"
                )

                st.code(
                    f"{type(e).__name__}: {e}"
                )
