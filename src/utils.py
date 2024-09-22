import re
import sqlite3
import base64
import logging

DB_PATH = "northwind-SQLite3/dist/northwind.db"

logger = logging.getLogger(__name__)


def scan_database_schema():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    schema = ""

    # Get all table names
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
    )
    tables = cursor.fetchall()

    for table in tables:
        table_name = table[0]
        schema += f'Table: "{table_name}"\n'
        schema += "Columns:\n"

        # Get column details
        cursor.execute(f"PRAGMA table_info('{table_name}');")
        columns = cursor.fetchall()
        for column in columns:
            # cid = column[0]
            name = column[1]
            data_type = column[2]
            not_null = bool(column[3])
            default_value = column[4]
            is_pk = bool(column[5])

            schema += f"  - {name} ({data_type})"
            if is_pk:
                schema += " [PRIMARY KEY]"
            if not_null and not is_pk:
                schema += " NOT NULL"
            if default_value is not None:
                schema += f" DEFAULT {default_value}"
            schema += "\n"

        # Get foreign key constraints
        cursor.execute(f"PRAGMA foreign_key_list('{table_name}');")
        foreign_keys = cursor.fetchall()
        if foreign_keys:
            schema += "Foreign Keys:\n"
            for fk in foreign_keys:
                # id = fk[0]
                # seq = fk[1]
                fk_table = fk[2]
                fk_from = fk[3]
                fk_to = fk[4]
                # on_update = fk[5]
                # on_delete = fk[6]
                # match = fk[7]
                schema += (
                    f"  - FOREIGN KEY ({fk_from}) REFERENCES {fk_table}({fk_to})\n"
                )

        schema += "\n"

    conn.close()
    return schema


def extract_sql_from_output(generated_text):
    logger.debug("Extracting SQL from model output")

    pattern = r"```sql(.*?)```"

    sql_start = generated_text.find("**Generated SQL Query:**")
    if sql_start != -1:
        generated_text = generated_text[
            sql_start + len("**Generated SQL Query:**") :
        ].strip()
        matches = re.search(pattern, generated_text, re.DOTALL | re.IGNORECASE)
        if matches:
            sql_code = matches.group(1).strip()
            return sql_code
        else:
            return generated_text
    else:
        return generated_text


def validate_sql(sql_query: str):
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

    if columns_info:
        columns = [description[0] for description in columns_info]

        processed_results = []
        for row in results:
            processed_row = []
            for idx, value in enumerate(row):
                column_name = columns[idx]
                if isinstance(value, bytes):
                    if column_name.lower() == "picture":
                        base64_str = base64.b64encode(value).decode("utf-8")
                        mime_type = "image/jpeg"
                        data_uri = f"data:{mime_type};base64,{base64_str}"
                        processed_row.append(data_uri)
                    else:
                        decoded_value = value.decode("utf-8", "ignore")
                        processed_row.append(decoded_value)
                else:
                    processed_row.append(value)
            processed_results.append(processed_row)

        return processed_results, columns

    return results, []


def hardcoded_check_order_details_table_name(sql_query):
    """
    Very good examples of Mistral limitation:
    - I do not easily force Mistral to output the proper name table Order Details enclosed in '"'
    - So I need to monkey patch it, in case it is used in the query
    """
    pattern = r"(?i)\border(?:_?[dD]etails|[A-Z]etails)\b"
    replacement = '"Order Details"'

    return re.sub(pattern, replacement, sql_query)
