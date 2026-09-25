# AI DataLab – Python & SQL Practice Lab

A lightweight Streamlit prototype for a 2-day training program with up to approximately 60 participants.

## Features

- Python/Pandas practice
- CSV and Excel upload for Python
- CSV upload for SQL
- DuckDB SQL execution
- Dataset preview
- Execution output and errors
- SQL result download as CSV

## 1. Create environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

## 2. Install packages

```bash
pip install -r requirements.txt
```

## 3. Run

```bash
streamlit run app.py
```

Open the URL shown by Streamlit, normally:

```text
http://localhost:8501
```

## 4. Example Python

```python
print(df.head())
print(df.shape)
print(df["Sales"].mean())
```

## 5. Example SQL

The uploaded CSV is available as `sales`:

```sql
SELECT Region,
       SUM(Sales) AS Total_Sales
FROM sales
GROUP BY Region
ORDER BY Total_Sales DESC;
```

## Production safety note

The Python runner in this prototype is intentionally limited, but it still uses Python `exec()`.

Do NOT expose this prototype directly to untrusted/public users.

For an online 60-participant lab, replace the Python execution component with an isolated sandbox/container execution service before production deployment. Apply CPU, memory, execution-time, filesystem, package and network restrictions.

## Suggested training use

Day 1:
- Python fundamentals
- Pandas
- Dataset upload
- Data analysis

Day 2:
- SQL
- Aggregations
- Joins
- Data analysis

Future enhancements:
- Login/participant IDs
- Exercise bank
- Hints
- Automatic answer checking
- Submission tracking
- Scores
- Trainer dashboard
- Coding evaluation integration
