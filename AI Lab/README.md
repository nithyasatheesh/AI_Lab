# AI DataLab – Simple Streamlit Deployment

This version is intentionally simplified for Streamlit Community Cloud.

## Dependencies

Only Streamlit is listed in `requirements.txt`.

- pandas and numpy are available through Streamlit's dependency environment.
- SQLite is part of Python's standard library.
- No DuckDB.
- No openpyxl.
- No additional Linux packages.

## GitHub structure

```text
ai_lab/
├── app.py
├── requirements.txt
├── README.md
└── datasets/
    └── sample_sales.csv
```

## Deploy

1. Push these files to GitHub.
2. Open Streamlit Community Cloud.
3. Select the repository.
4. Select `app.py` as the main file.
5. Use Python 3.12.
6. Deploy.

## Test SQL

```sql
SELECT Region,
       SUM(Sales) AS Total_Sales
FROM sales
GROUP BY Region
ORDER BY Total_Sales DESC;
```

## Important security note

This is a prototype/training application. The Python code runner uses `exec()`.

Do not expose unrestricted Python execution to untrusted users in production. For a real 60-participant public lab, use an isolated execution sandbox/container with CPU, memory, time, filesystem, and network restrictions.
