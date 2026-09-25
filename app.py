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
        # Common Python built-in functions/types for participant practice
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
        "zip": zip,
        "map": map,
        "filter": filter,
        "all": all,
        "any": any,
        "reversed": reversed,

        # Type / conversion functions
        "type": type,
        "isinstance": isinstance,
        "issubclass": issubclass,
        "int": int,
        "float": float,
        "str": str,
        "bool": bool,
        "list": list,
        "dict": dict,
        "set": set,
        "tuple": tuple,
        "bytes": bytes,

        # Inspection / utility
        "dir": dir,
        "help": help,
        "repr": repr,
        "id": id,
        "hash": hash,

        # Interactive console input
        "input": input,

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

if "python_cells" not in st.session_state:
    st.session_state.python_cells = ['print("Hello World!")']

if "python_cell_outputs" not in st.session_state:
    st.session_state.python_cell_outputs = {}

if "sql_cells" not in st.session_state:
    st.session_state.sql_cells = [
        "SELECT * FROM table_name LIMIT 5;"
    ]

if "sql_cell_outputs" not in st.session_state:
    st.session_state.sql_cell_outputs = {}

# ------------------------------------------------------------
# Gamification state
# ------------------------------------------------------------
if "participant_name" not in st.session_state:
    st.session_state.participant_name = ""

if "score" not in st.session_state:
    st.session_state.score = 0

if "successful_python_runs" not in st.session_state:
    st.session_state.successful_python_runs = 0

if "successful_sql_runs" not in st.session_state:
    st.session_state.successful_sql_runs = 0

if "datasets_uploaded" not in st.session_state:
    st.session_state.datasets_uploaded = 0

if "notebook_runs" not in st.session_state:
    st.session_state.notebook_runs = 0

if "badges" not in st.session_state:
    st.session_state.badges = []

# Stable IDs prevent delete/reorder from breaking Streamlit widget state.
if "python_cell_ids" not in st.session_state:
    st.session_state.python_cell_ids = [
        "py_1"
    ]

if "sql_cell_ids" not in st.session_state:
    st.session_state.sql_cell_ids = [
        "sql_1"
    ]

if "next_cell_id" not in st.session_state:
    st.session_state.next_cell_id = 2


# ============================================================
# SIDEBAR
# ============================================================

page = st.sidebar.radio(
    "Select Lab",
    [
        "Home",
        "🏆 Gamification",
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

elif page == "🏆 Gamification":

    st.header("🏆 Gamification")

    name = st.text_input(
        "Participant Name",
        value=st.session_state.participant_name,
        placeholder="Enter your name"
    )

    st.session_state.participant_name = name

    score = st.session_state.score
    progress = min(score / 100, 1.0)

    st.metric(
        "⭐ Points",
        score
    )

    st.progress(
        progress,
        text=f"Progress: {int(progress * 100)}%"
    )

    st.subheader("Badges")

    badges = st.session_state.badges

    if badges:
        for badge in badges:
            st.success(f"🏅 {badge}")
    else:
        st.info(
            "Run Python code, upload data, or execute SQL "
            "to start earning badges."
        )

    st.subheader("Activity")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            "Python Runs",
            st.session_state.successful_python_runs
        )

    with c2:
        st.metric(
            "SQL Runs",
            st.session_state.successful_sql_runs
        )

    with c3:
        st.metric(
            "Datasets",
            st.session_state.datasets_uploaded
        )

    st.info(
        "Current gamification is session-based. "
        "A shared cross-participant leaderboard requires a "
        "central database or shared storage."
    )

if page == "1. Python Coding":

    st.header("🐍 Python Lab")

    st.info(
        "Start by writing and running Python code. "
        "Upload a dataset or Jupyter Notebook only when you need them."
    )

    # ========================================================
    # OPTION 1 — WRITE AND RUN PYTHON CODE FIRST
    # ========================================================

    st.subheader("Option 1 — Write & Run Python Code")

    st.caption(
        "Start typing Python here. Use + Add Code to create multiple cells."
    )

    if st.button(
        "➕ Add Code",
        key="add_python_cell_top",
        use_container_width=False
    ):
        new_id = f"py_{st.session_state.next_cell_id}"
        st.session_state.next_cell_id += 1
        st.session_state.python_cells.append(
            "# Write Python code here"
        )
        st.session_state.python_cell_ids.append(new_id)
        st.rerun()

    for i, cell_id in enumerate(list(st.session_state.python_cell_ids)):

        st.markdown(f"### Python Cell {i + 1}")

        code = st.text_area(
            f"Code {i + 1}",
            value=st.session_state.python_cells[i],
            height=180,
            key=f"python_basic_cell_{cell_id}"
        )

        st.session_state.python_cells[i] = code

        c1, c2, c3 = st.columns(3)

        with c1:
            if st.button(
                f"▶ Run Cell {i + 1}",
                key=f"run_python_basic_{cell_id}",
                use_container_width=True
            ):

                ok, output, result, fig, error = execute_code(
                    code,
                    st.session_state.python_env
                )

                if ok:
                    st.session_state.python_cell_outputs[i] = {
                        "output": output,
                        "result": result,
                        "fig": fig
                    }

                    st.session_state.successful_python_runs += 1
                    st.session_state.score += 5

                    if "Python Starter" not in st.session_state.badges:
                        st.session_state.badges.append("Python Starter")

                    if (
                        st.session_state.successful_python_runs >= 10
                        and "Practice Pro"
                        not in st.session_state.badges
                    ):
                        st.session_state.badges.append("Practice Pro")

                else:
                    st.session_state.python_cell_outputs[i] = {
                        "error": error,
                        "output": output
                    }

                st.rerun()

        with c2:
            if st.button(
                f"＋ Add After {i + 1}",
                key=f"add_python_after_{cell_id}",
                use_container_width=True
            ):
                new_id = f"py_{st.session_state.next_cell_id}"
                st.session_state.next_cell_id += 1

                st.session_state.python_cells.insert(
                    i + 1,
                    "# Write Python code here"
                )
                st.session_state.python_cell_ids.insert(
                    i + 1,
                    new_id
                )
                st.rerun()

        with c3:
            if st.button(
                f"🗑 Delete {i + 1}",
                key=f"delete_python_basic_{cell_id}",
                use_container_width=True
            ):
                if len(st.session_state.python_cells) > 1:
                    st.session_state.python_cells.pop(i)
                    st.session_state.python_cell_ids.pop(i)

                    # Rebuild output mapping because cell positions changed.
                    old_outputs = st.session_state.python_cell_outputs
                    st.session_state.python_cell_outputs = {
                        new_i: old_outputs.get(old_i)
                        for new_i, old_i in enumerate(
                            [x for x in range(len(st.session_state.python_cells) + 1)
                             if x != i]
                        )
                        if old_outputs.get(old_i) is not None
                    }

                st.rerun()

        cell_result = st.session_state.python_cell_outputs.get(i)

        if cell_result:
            if "error" in cell_result:
                st.error("❌ Code execution failed")
                st.code(
                    cell_result["error"],
                    language="text"
                )
            else:
                st.success("✅ Code executed successfully")

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
        "➕ Add Code",
        key="add_python_cell_bottom",
        use_container_width=False
    ):
        new_id = f"py_{st.session_state.next_cell_id}"
        st.session_state.next_cell_id += 1
        st.session_state.python_cells.append(
            "# Write Python code here"
        )
        st.session_state.python_cell_ids.append(new_id)
        st.rerun()

    # ========================================================
    # OPTION 2 — UPLOAD DATASET
    # ========================================================

    st.subheader("Option 2 — Upload Dataset")

    st.caption(
        "➕ Add one or more CSV datasets. Select multiple files "
        "in the upload window if required."
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
        "Upload an .ipynb file and run cells individually or all cells "
        "while keeping variables between cells."
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

                # Create the environment only once for this notebook.
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

                # ------------------------------------------------
                # FAST RUN-ALL
                # ------------------------------------------------

                run_all = st.button(
                    "⚡ Run All Notebook Cells",
                    type="primary",
                    use_container_width=False,
                    key="fast_run_all_notebook"
                )

                if run_all:

                    st.session_state.notebook_outputs = {}

                    total = len(cells)

                    progress = st.progress(
                        0,
                        text=f"Preparing {total} cells..."
                    )

                    # IMPORTANT:
                    # Reuse ONE Python environment for all cells.
                    # Do NOT recreate make_env() inside the loop.
                    env = st.session_state.python_env

                    for i, cell_code in enumerate(cells):

                        # Skip empty cells quickly.
                        if not cell_code.strip():

                            st.session_state.notebook_outputs[i] = {
                                "output": "",
                                "result": None,
                                "fig": None
                            }

                            progress.progress(
                                (i + 1) / total,
                                text=f"Skipping empty cell {i + 1}/{total}"
                            )

                            continue

                        ok, output, result, fig, error = execute_code(
                            cell_code,
                            env
                        )

                        if ok:

                            # Store only what is needed.
                            # Figures are retained only when a figure exists.
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

                            # Stop on the first error instead of spending
                            # time executing cells that depend on failed code.
                            progress.progress(
                                (i + 1) / total,
                                text=f"Stopped at cell {i + 1}/{total}"
                            )

                            st.error(
                                f"❌ Notebook execution stopped at Cell {i + 1}"
                            )

                            break

                        progress.progress(
                            (i + 1) / total,
                            text=f"Executing cell {i + 1}/{total}"
                        )

                    else:

                        progress.progress(
                            1.0,
                            text=f"✅ Completed {total}/{total} cells"
                        )

                        st.success(
                            f"✅ All {total} notebook cells executed."
                        )

                    # Gamification is updated ONCE after the complete run,
                    # rather than once per cell.
                    successful_cells = sum(
                        1
                        for v in st.session_state.notebook_outputs.values()
                        if "error" not in v
                    )

                    if successful_cells:

                        st.session_state.notebook_runs += 1
                        st.session_state.score += 15

                        if (
                            "Notebook Explorer"
                            not in st.session_state.badges
                        ):
                            st.session_state.badges.append(
                                "Notebook Explorer"
                            )

                    # No st.rerun() here.
                    # This avoids a second full Streamlit render of 100+
                    # notebook editors immediately after execution.

                # ------------------------------------------------
                # OUTPUT SUMMARY
                # ------------------------------------------------

                if st.session_state.notebook_outputs:

                    successful = sum(
                        1
                        for v in st.session_state.notebook_outputs.values()
                        if "error" not in v
                    )

                    failed = sum(
                        1
                        for v in st.session_state.notebook_outputs.values()
                        if "error" in v
                    )

                    c1, c2 = st.columns(2)

                    with c1:
                        st.metric(
                            "Executed",
                            successful
                        )

                    with c2:
                        st.metric(
                            "Errors",
                            failed
                        )

                st.divider()

                # ------------------------------------------------
                # NOTEBOOK CELL DISPLAY
                # ------------------------------------------------

                # Rendering 124 text areas itself can be slow.
                # Therefore use expanders and only open cells with output.
                show_all = st.checkbox(
                    "Show all notebook cells",
                    value=False,
                    key="show_all_notebook_cells"
                )

                for i in range(len(st.session_state.notebook_cells)):

                    cell_result = (
                        st.session_state.notebook_outputs.get(i)
                    )

                    has_output = cell_result is not None

                    # After Run All, only cells with output/errors are
                    # expanded unless the participant chooses Show All.
                    expanded = (
                        show_all
                        or has_output
                    )

                    with st.expander(
                        f"Notebook Cell {i + 1}",
                        expanded=expanded
                    ):

                        edited_code = st.text_area(
                            f"Cell {i + 1} Code",
                            value=st.session_state.notebook_cells[i],
                            height=160,
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

                                ok, output, result, fig, error = (
                                    execute_code(
                                        edited_code,
                                        st.session_state.python_env
                                    )
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

                                # Rebuild output indexes after deletion.
                                old_outputs = (
                                    st.session_state.notebook_outputs
                                )

                                st.session_state.notebook_outputs = {
                                    new_i: old_outputs.get(old_i)
                                    for new_i, old_i in enumerate(
                                        [
                                            x
                                            for x in range(
                                                len(
                                                    st.session_state.notebook_cells
                                                ) + 1
                                            )
                                            if x != i
                                        ]
                                    )
                                    if old_outputs.get(old_i) is not None
                                }

                                st.rerun()

                        if cell_result:

                            if "error" in cell_result:

                                st.error(
                                    "❌ Cell execution failed"
                                )

                                st.code(
                                    cell_result["error"],
                                    language="text"
                                )

                            else:

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

        except Exception as e:

            st.error(
                f"Could not load notebook: {type(e).__name__}: {e}"
            )


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

    st.header("🗄️ SQL Lab")

    st.info(
        "Upload your dataset, write any SQL query, and run one, "
        "multiple, or all SQL cells. No predefined tasks are required."
    )

    st.subheader("1. Upload Dataset(s)")

    files = st.file_uploader(
        "Upload one or more CSV datasets",
        type=["csv"],
        accept_multiple_files=True,
        key="sql_upload"
    )

    if files:

        tables = {}

        for file in files:
            try:
                tables[clean_name(file.name)] = pd.read_csv(file)
            except Exception as e:
                st.error(f"Could not read {file.name}: {e}")

        if tables:

            st.session_state.datasets_uploaded = len(tables)

            if "Data Explorer" not in st.session_state.badges:
                st.session_state.badges.append("Data Explorer")
                st.session_state.score += 10

            st.success(
                f"✅ {len(tables)} dataset(s) loaded successfully."
            )

            st.info(
                "Use the dataset filename (without .csv) as the SQL table name."
            )

            for table_name, df in tables.items():
                with st.expander(
                    f"📄 {table_name} — "
                    f"{len(df):,} rows × {len(df.columns):,} columns"
                ):
                    st.dataframe(df.head(10), use_container_width=True)
                    st.write("Columns:", list(df.columns))

            st.divider()
            st.subheader("2. Write SQL Code")

            st.caption(
                "Write any SQL query. Create multiple cells if you "
                "want to practice multiple queries."
            )

            if st.button(
                "➕ Add SQL Code",
                key="add_sql_cell_top",
                use_container_width=False
            ):
                first_table = next(iter(tables))
                new_id = f"sql_{st.session_state.next_cell_id}"
                st.session_state.next_cell_id += 1

                st.session_state.sql_cells.append(
                    f"-- Write SQL query here\n"
                    f"SELECT * FROM {first_table} LIMIT 5;"
                )
                st.session_state.sql_cell_ids.append(new_id)
                st.rerun()

            for i, cell_id in enumerate(list(st.session_state.sql_cell_ids)):

                st.markdown(f"### SQL Cell {i + 1}")

                sql_code = st.text_area(
                    f"SQL Code {i + 1}",
                    value=st.session_state.sql_cells[i],
                    height=160,
                    key=f"sql_cell_editor_{cell_id}"
                )

                st.session_state.sql_cells[i] = sql_code

                c1, c2 = st.columns(2)

                with c1:
                    if st.button(
                        f"＋ Add After {i + 1}",
                        key=f"add_sql_after_{cell_id}",
                        use_container_width=True
                    ):
                        first_table = next(iter(tables))
                        new_id = f"sql_{st.session_state.next_cell_id}"
                        st.session_state.next_cell_id += 1

                        st.session_state.sql_cells.insert(
                            i + 1,
                            f"-- Write SQL query here\n"
                            f"SELECT * FROM {first_table} LIMIT 5;"
                        )
                        st.session_state.sql_cell_ids.insert(
                            i + 1,
                            new_id
                        )
                        st.rerun()

                with c2:
                    if st.button(
                        f"🗑 Delete {i + 1}",
                        key=f"delete_sql_{cell_id}",
                        use_container_width=True
                    ):
                        if len(st.session_state.sql_cells) > 1:
                            st.session_state.sql_cells.pop(i)
                            st.session_state.sql_cell_ids.pop(i)
                            st.session_state.sql_cell_outputs = {}
                        st.rerun()

                cell_output = st.session_state.sql_cell_outputs.get(i)

                if cell_output:
                    if "error" in cell_output:
                        st.error("❌ SQL execution failed")
                        st.code(
                            cell_output["error"],
                            language="text"
                        )
                    else:
                        st.success("✅ SQL executed successfully")
                        result = cell_output.get("result")
                        if result is not None:
                            st.dataframe(
                                result,
                                use_container_width=True
                            )

                st.divider()

            if st.button(
                "➕ Add SQL Code",
                key="add_sql_cell_bottom",
                use_container_width=False
            ):
                first_table = next(iter(tables))
                new_id = f"sql_{st.session_state.next_cell_id}"
                st.session_state.next_cell_id += 1

                st.session_state.sql_cells.append(
                    f"-- Write SQL query here\n"
                    f"SELECT * FROM {first_table} LIMIT 5;"
                )
                st.session_state.sql_cell_ids.append(new_id)
                st.rerun()

            st.subheader("3. Execute SQL")

            cell_options = [
                f"SQL Cell {i + 1}"
                for i in range(len(st.session_state.sql_cells))
            ]

            selected_cells = st.multiselect(
                "Select SQL code to execute",
                options=cell_options,
                default=cell_options[:1],
                key="selected_sql_cells"
            )

            e1, e2 = st.columns(2)

            with e1:
                run_selected = st.button(
                    "▶ Run Selected",
                    type="primary",
                    use_container_width=True
                )

            with e2:
                run_all = st.button(
                    "▶ Run All",
                    use_container_width=True
                )

            def run_sql_cells(indices):

                results = {}
                conn = sqlite3.connect(":memory:")

                try:
                    for table, df in tables.items():
                        df.to_sql(
                            table,
                            conn,
                            index=False,
                            if_exists="replace"
                        )

                    for idx in indices:

                        query = st.session_state.sql_cells[idx].strip()

                        if not query or all(
                            line.strip().startswith("--")
                            or not line.strip()
                            for line in query.splitlines()
                        ):
                            results[idx] = {
                                "error": "SQL cell is empty."
                            }
                            continue

                        query = query.rstrip(";").strip()

                        try:
                            result = pd.read_sql_query(
                                query,
                                conn
                            )

                            results[idx] = {
                                "result": result
                            }

                        except Exception as cell_error:
                            results[idx] = {
                                "error": (
                                    f"{type(cell_error).__name__}: "
                                    f"{cell_error}"
                                )
                            }

                finally:
                    conn.close()

                return results

            if run_selected:

                if not selected_cells:
                    st.warning(
                        "Please select at least one SQL cell."
                    )
                else:
                    indices = [
                        int(x.split()[-1]) - 1
                        for x in selected_cells
                    ]

                    outputs = run_sql_cells(indices)
                    st.session_state.sql_cell_outputs = outputs

                    successful = sum(
                        1
                        for v in outputs.values()
                        if "error" not in v
                    )

                    st.session_state.successful_sql_runs += successful
                    st.session_state.score += successful * 5

                    if successful and "SQL Explorer" not in st.session_state.badges:
                        st.session_state.badges.append("SQL Explorer")

                    if (
                        st.session_state.successful_sql_runs >= 10
                        and "Practice Pro"
                        not in st.session_state.badges
                    ):
                        st.session_state.badges.append("Practice Pro")

                    st.rerun()

            if run_all:

                indices = list(
                    range(len(st.session_state.sql_cells))
                )

                outputs = run_sql_cells(indices)
                st.session_state.sql_cell_outputs = outputs

                successful = sum(
                    1
                    for v in outputs.values()
                    if "error" not in v
                )

                st.session_state.successful_sql_runs += successful
                st.session_state.score += successful * 5

                if successful and "SQL Explorer" not in st.session_state.badges:
                    st.session_state.badges.append("SQL Explorer")

                if (
                    st.session_state.successful_sql_runs >= 10
                    and "Practice Pro"
                    not in st.session_state.badges
                ):
                    st.session_state.badges.append("Practice Pro")

                st.rerun()

