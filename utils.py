import re
import sqlite3
import base64
import logging

DB_PATH = "northwind-SQLite3/dist/northwind.db"

logger = logging.getLogger(__name__)


def get_prompt(database_schema: str, user_input: str):
    prompt = f"""You are an expert database (sqlite3) assistant. Given:
1. **Database Schema**: Detailed information about tables, columns, and relationships.
2. **User Question**: A natural language query.

Your task is to generate a correct and optimized SQL query that answers the question using the provided schema. Enclose your query in ```sql ... ```

**Database Schema:**

{database_schema}

**User Question:**

{user_input}

**Generated SQL Query:**
"""
    return prompt


def extract_sql_from_output(generated_text):
    logger.debug("Extracting SQL from model output")

    pattern = r"```sql(.*?)```"

    sql_start = generated_text.find("Generated SQL Query:")
    if sql_start != -1:
        generated_text = generated_text[
            sql_start + len("Generated SQL Query:") :
        ].strip()
        matches = re.search(pattern, generated_text, re.DOTALL | re.IGNORECASE)
        if matches:
            sql_code = matches.group(1).strip()
            return sql_code
        else:
            return generated_text
    else:
        return generated_text


def extract_database_schema():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    schema = "Tables and Columns:\n\n"
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
    )
    tables = cursor.fetchall()
    for table_name in tables:
        table_name = table_name[0]
        cursor.execute(f"PRAGMA table_info('{table_name}');")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        schema += f"- {table_name}({', '.join(column_names)})\n"
    conn.close()
    return schema


def validate_sql(sql_query):
    logger.debug("Validating SQL query")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("EXPLAIN QUERY PLAN " + sql_query)
        conn.close()
        return True, ""
    except Exception as e:
        return False, str(e)


def execute_sql(sql_query):
    conn = sqlite3.connect(DB_PATH)
    conn.text_factory = bytes  # Ensure that BLOB data is returned as bytes
    cursor = conn.cursor()
    cursor.execute(sql_query)
    results = cursor.fetchall()
    columns_info = cursor.description
    conn.close()

    columns = [description[0] for description in columns_info]

    processed_results = []
    for row in results:
        processed_row = []
        for idx, value in enumerate(row):
            column_name = columns[idx]
            if isinstance(value, bytes) and column_name.lower() == "picture":
                base64_str = base64.b64encode(value).decode("utf-8")
                mime_type = "image/jpeg"
                data_uri = f"data:{mime_type};base64,{base64_str}"
                processed_row.append(data_uri)
            else:
                processed_row.append(value)
        processed_results.append(processed_row)

    return processed_results, columns
