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

st.set_page_config(
    page_title="ICICI Data Analytics Lab",
    page_icon="💻",
    layout="wide"
)

st.title("💻 ICICI Data Analytics Lab")
st.caption("Browser-based Python & SQL Practice Environment")


# ============================================================
# SAFE PYTHON ENVIRONMENT
# ============================================================

def make_env(dataframes=None):
    dataframes = dataframes or {}
    original_import = builtins.__import__

    def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
        allowed = {"pandas", "numpy", "matplotlib"}
        if name.split(".")[0] not in allowed:
            raise ImportError(
                f"Import of '{name}' is not allowed in this lab."
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
    """
    Executes code and captures:
    - print output
    - last expression
    - DataFrame / Series result
    - charts
    """

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
                exec(
                    code,
                    env,
                    env
                )

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


def clean_name(filename):

    name = re.sub(
        r"\W+",
        "_",
        filename.rsplit(".", 1)[0]
    )

    name = re.sub(
        r"_+",
        "_",
        name
    ).strip("_")

    if not name:
        name = "dataset"

    if name[0].isdigit():
        name = "dataset_" + name

    return name


# ============================================================
# SESSION STATE
# ============================================================

if "basic_env" not in st.session_state:
    st.session_state.basic_env = make_env()

if "dataframes" not in st.session_state:
    st.session_state.dataframes = {}

if "python_code" not in st.session_state:
    st.session_state.python_code = ""

if "sql_query" not in st.session_state:
    st.session_state.sql_query = ""


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
This browser-based lab allows participants to practice Python and SQL
without installing software.

### Participant Flow

```text
1. Write Python Code
        ↓
2. Run Code
        ↓
3. Check Result
        ↓
4. Upload Dataset
        ↓
5. Perform Data Manipulation
        ↓
6. Check Correct / Incorrect
        ↓
7. Practice SQL
```

No API key is required.
""")


# ============================================================
# 1. PYTHON CODING
# ============================================================

elif page == "1. Python Coding":

    st.header("🐍 1. Python Coding")

    st.info(
        "Start here. No dataset is required for basic Python practice."
    )

    st.subheader("Write Your Python Code")

    st.markdown("""
### Try this first:

```python
print("Hello World!")
```

You can then try:

```python
x = 10
y = 20
print(x + y)
```

or:

```python
numbers = [10, 20, 30, 40, 50]
print(sum(numbers))
```
""")

    code = st.text_area(
        "Python Code",
        value=st.session_state.python_code,
        height=300,
        placeholder="Type your Python code here...",
        key="python_editor"
    )

    st.session_state.python_code = code

    if st.button(
        "▶ Run Code",
        type="primary",
        use_container_width=True
    ):

        ok, output, result, fig, error = execute_code(
            code,
            st.session_state.basic_env
        )

        if ok:

            st.success("✅ Code executed successfully.")

            if output:

                st.subheader("Output")

                st.code(
                    output,
                    language="text"
                )

            if result is not None:

                st.subheader("Result")

                display_result(result)

            if fig is not None:

                st.subheader("Chart")

                st.pyplot(fig)

        else:

            st.error(
                "❌ Code execution failed"
            )

            st.code(
                error,
                language="text"
            )

    st.divider()

    st.subheader("What does Correct / Incorrect mean?")

    st.info("""
For this section, the application checks whether the code executes
successfully.

**Green:** Code executed successfully.

**Red:** Python error or syntax error occurred.

For a training exercise where we need to determine whether the
participant's answer is actually correct, use the task-based checking
available in the Data Manipulation and SQL sections.
""")


# ============================================================
# 2. PYTHON DATA MANIPULATION
# ============================================================

elif page == "2. Python Data Manipulation":

    st.header("🐼 2. Python Data Manipulation")

    # --------------------------------------------------------
    # STEP 1: TASK
    # --------------------------------------------------------

    st.subheader("Step 1 — Select an Exercise")

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

        instruction = """
**Task:** Display the first 5 rows of the dataset.

Expected approach:

```python
df.head()
```
"""

    elif task.startswith("Task 2"):

        instruction = """
**Task:** Find the number of rows in the dataset.

Expected approach:

```python
df.shape[0]
```
"""

    elif task.startswith("Task 3"):

        instruction = """
**Task:** Find the average of the `amount` column.

Expected approach:

```python
df["amount"].mean()
```
"""

    elif task.startswith("Task 4"):

        instruction = """
**Task:** Filter records where `amount` is greater than 3000.

Expected approach:

```python
df[df["amount"] > 3000]
```
"""

    else:

        instruction = """
**Task:** Group by `region` and calculate total `amount`.

Expected approach:

```python
df.groupby("region")["amount"].sum()
```
"""

    st.markdown(instruction)

    # --------------------------------------------------------
    # STEP 2: UPLOAD DATA
    # --------------------------------------------------------

    st.subheader("Step 2 — Upload Dataset")

    uploaded_files = st.file_uploader(
        "Upload CSV dataset(s)",
        type=["csv"],
        accept_multiple_files=True,
        key="python_dataset_upload"
    )

    if uploaded_files:

        dataframes = {}

        for file in uploaded_files:

            try:

                dataframes[
                    clean_name(file.name)
                ] = pd.read_csv(file)

            except Exception as e:

                st.error(
                    f"Could not read {file.name}: {e}"
                )

        st.session_state.dataframes = dataframes

    dataframes = st.session_state.dataframes

    if dataframes:

        st.success(
            f"✅ {len(dataframes)} dataset(s) uploaded."
        )

        for name, df in dataframes.items():

            with st.expander(
                f"📄 {name} — "
                f"{len(df):,} rows × "
                f"{len(df.columns):,} columns"
            ):

                st.dataframe(
                    df.head(10),
                    use_container_width=True
                )

                st.write(
                    "Columns:",
                    list(df.columns)
                )

        # ----------------------------------------------------
        # STEP 3: WRITE CODE
        # ----------------------------------------------------

        st.subheader("Step 3 — Write Your Code")

        first_name = next(
            iter(dataframes)
        )

        st.caption(
            f"The uploaded dataset is available as `df` "
            f"and `{first_name}`."
        )

        default_code = {
            "Task 1": "df.head()",
            "Task 2": "df.shape[0]",
            "Task 3": 'df["amount"].mean()',
            "Task 4": 'df[df["amount"] > 3000]',
            "Task 5": 'df.groupby("region")["amount"].sum()'
        }

        task_key = task.split("—")[0].strip()

        if (
            not st.session_state.get(
                "last_task"
            )
            == task
        ):

            st.session_state.data_code = (
                default_code.get(
                    task_key,
                    ""
                )
            )

            st.session_state.last_task = task

        code = st.text_area(
            "Python Code",
            value=st.session_state.get(
                "data_code",
                ""
            ),
            height=220,
            key="data_code_editor"
        )

        st.session_state.data_code = code

        # ----------------------------------------------------
        # STEP 4: RUN + CHECK
        # ----------------------------------------------------

        if st.button(
            "▶ Run & Check Answer",
            type="primary",
            use_container_width=True
        ):

            env = make_env(dataframes)

            ok, output, result, fig, error = (
                execute_code(
                    code,
                    env
                )
            )

            if not ok:

                st.error(
                    "❌ Incorrect / Code Error"
                )

                st.code(
                    error,
                    language="text"
                )

            else:

                st.success(
                    "✅ Code executed successfully."
                )

                if output:

                    st.subheader("Output")

                    st.code(
                        output,
                        language="text"
                    )

                if result is not None:

                    st.subheader("Your Result")

                    display_result(result)

                if fig is not None:

                    st.pyplot(fig)

                # --------------------------------------------
                # TASK VALIDATION
                # --------------------------------------------

                expected_ok = False

                try:

                    df = next(
                        iter(dataframes.values())
                    )

                    # Task 1
                    if task.startswith("Task 1"):

                        expected = df.head()

                        expected_ok = (
                            isinstance(
                                result,
                                pd.DataFrame
                            )
                            and result.equals(expected)
                        )

                    # Task 2
                    elif task.startswith("Task 2"):

                        expected = df.shape[0]

                        expected_ok = (
                            result == expected
                        )

                    # Task 3
                    elif task.startswith("Task 3"):

                        if "amount" in df.columns:

                            expected = df["amount"].mean()

                            expected_ok = (
                                result is not None
                                and np.isclose(
                                    float(result),
                                    float(expected)
                                )
                            )

                    # Task 4
                    elif task.startswith("Task 4"):

                        if "amount" in df.columns:

                            expected = (
                                df[df["amount"] > 3000]
                                .reset_index(drop=True)
                            )

                            if isinstance(
                                result,
                                pd.DataFrame
                            ):

                                actual = (
                                    result
                                    .reset_index(drop=True)
                                )

                                expected_ok = (
                                    actual.equals(expected)
                                )

                    # Task 5
                    elif task.startswith("Task 5"):

                        if (
                            "region" in df.columns
                            and "amount" in df.columns
                        ):

                            expected = (
                                df.groupby(
                                    "region"
                                )["amount"]
                                .sum()
                                .sort_index()
                            )

                            if isinstance(
                                result,
                                pd.Series
                            ):

                                actual = (
                                    result
                                    .sort_index()
                                )

                                expected_ok = (
                                    actual.equals(expected)
                                )

                except Exception:

                    expected_ok = False

                if expected_ok:

                    st.success(
                        "🎉 CORRECT! Your answer matches the expected result."
                    )

                else:

                    st.warning(
                        "⚠️ Code ran successfully, but the result "
                        "does not match the expected answer for this task."
                    )


# ============================================================
# 3. SQL LAB
# ============================================================

elif page == "3. SQL Lab":

    st.header("🗄️ 3. SQL Practice Lab")

    st.subheader("Step 1 — Select an Exercise")

    sql_task = st.selectbox(
        "Choose SQL task",
        [
            "Task 1 — Select first 5 rows",
            "Task 2 — Count rows",
            "Task 3 — Average amount",
            "Task 4 — Filter amount > 3000",
            "Task 5 — Group by region"
        ]
    )

    st.subheader("Step 2 — Upload Dataset")

    files = st.file_uploader(
        "Upload CSV dataset(s)",
        type=["csv"],
        accept_multiple_files=True,
        key="sql_dataset_upload"
    )

    if files:

        tables = {}

        for file in files:

            try:

                tables[
                    clean_name(file.name)
                ] = pd.read_csv(file)

            except Exception as e:

                st.error(
                    f"Could not read {file.name}: {e}"
                )

        if tables:

            st.success(
                f"✅ {len(tables)} table(s) loaded."
            )

            for table, df in tables.items():

                st.write(
                    f"**{table}** — "
                    f"{len(df):,} rows"
                )

            first_table = next(
                iter(tables)
            )

            if sql_task.startswith("Task 1"):

                sql_instruction = (
                    f"Display the first 5 rows from `{first_table}`."
                )

                default_sql = (
                    f"SELECT * FROM {first_table} LIMIT 5;"
                )

            elif sql_task.startswith("Task 2"):

                sql_instruction = (
                    f"Find the number of rows in `{first_table}`."
                )

                default_sql = (
                    f"SELECT COUNT(*) FROM {first_table};"
                )

            elif sql_task.startswith("Task 3"):

                sql_instruction = (
                    f"Find the average `amount` from `{first_table}`."
                )

                default_sql = (
                    f"SELECT AVG(amount) FROM {first_table};"
                )

            elif sql_task.startswith("Task 4"):

                sql_instruction = (
                    f"Display records where `amount` > 3000."
                )

                default_sql = (
                    f"SELECT * FROM {first_table} "
                    f"WHERE amount > 3000;"
                )

            else:

                sql_instruction = (
                    f"Group by `region` and calculate "
                    f"total `amount`."
                )

                default_sql = (
                    f"SELECT region, SUM(amount) AS total_amount "
                    f"FROM {first_table} "
                    f"GROUP BY region;"
                )

            st.info(
                sql_instruction
            )

            st.subheader("Step 3 — Write SQL")

            query = st.text_area(
                "SQL Query",
                value=default_sql,
                height=220,
                key="sql_editor"
            )

            if st.button(
                "▶ Run & Check SQL",
                type="primary",
                use_container_width=True
            ):

                try:

                    conn = sqlite3.connect(
                        ":memory:"
                    )

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

                    st.subheader(
                        "Your Result"
                    )

                    st.dataframe(
                        result,
                        use_container_width=True
                    )

                    # ----------------------------
                    # SQL validation
                    # ----------------------------

                    source_df = tables[first_table]

                    if sql_task.startswith("Task 1"):

                        expected = source_df.head(5)

                    elif sql_task.startswith("Task 2"):

                        expected = pd.DataFrame(
                            {"COUNT(*)": [len(source_df)]}
                        )

                    elif sql_task.startswith("Task 3"):

                        expected = pd.DataFrame(
                            {"AVG(amount)": [
                                source_df["amount"].mean()
                            ]}
                        )

                    elif sql_task.startswith("Task 4"):

                        expected = (
                            source_df[
                                source_df["amount"] > 3000
                            ]
                            .reset_index(drop=True)
                        )

                    else:

                        expected = (
                            source_df
                            .groupby("region")["amount"]
                            .sum()
                            .reset_index(name="total_amount")
                            .sort_values("region")
                            .reset_index(drop=True)
                        )

                    actual = (
                        result
                        .reset_index(drop=True)
                    )

                    # Numeric comparison
                    if (
                        expected.shape == actual.shape
                        and list(expected.columns)
                        == list(actual.columns)
                    ):

                        try:

                            expected_compare = expected.copy()
                            actual_compare = actual.copy()

                            for col in expected_compare.columns:

                                if (
                                    pd.api.types
                                    .is_numeric_dtype(
                                        expected_compare[col]
                                    )
                                ):

                                    actual_compare[col] = pd.to_numeric(
                                        actual_compare[col],
                                        errors="coerce"
                                    )

                            correct = (
                                expected_compare.equals(
                                    actual_compare
                                )
                            )

                        except Exception:

                            correct = False

                    else:

                        correct = False

                    if correct:

                        st.success(
                            "🎉 CORRECT! "
                            "Your SQL result matches the expected answer."
                        )

                    else:

                        st.warning(
                            "⚠️ SQL ran successfully, but the result "
                            "does not match the expected answer."
                        )

                except Exception as e:

                    st.error(
                        "❌ SQL Error"
                    )

                    st.code(
                        f"{type(e).__name__}: {e}",
                        language="text"
                    )
