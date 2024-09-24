import logging
from flask import Flask, render_template, request

from src.simple import SimpleChatBot, get_base_prompt, extend_prompt_with_errors
from src.utils import (
    scan_db_schema,
    validate_sql,
    execute_sql,
    hardcoded_check_order_details_table_name,
)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

db_schema = scan_db_schema()
dialect = "sqlite3"
attempts = 5
bot = SimpleChatBot(dialect, db_schema, attempts, logger)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        user_input = request.form["user_input"]
        logger.info(f"\x1b[36m -- Received user input: {user_input}\x1b[0m")

        base_prompt = get_base_prompt(dialect, db_schema, user_input)
        error_message = ""
        attempts = 5
        errors = []
        for attempt in range(attempts):
            logger.info(
                f"\x1b[36m -- Attempt {attempt + 1} to generate SQL query\x1b[0m"
            )

            prompt = extend_prompt_with_errors(base_prompt, errors)
            logger.debug(f"""User prompt:
---
{prompt}
---
""")

            sql_query = bot(prompt)
            sql_query = hardcoded_check_order_details_table_name(sql_query)

            logger.info(f"\x1b[33m Generated SQL Query: {sql_query}\x1b[0m")
            is_valid, error_message = validate_sql(sql_query)
            if is_valid:
                logger.info(f"\x1b[33m SQL Query Valid: {is_valid}\x1b[0m")

                results, columns = execute_sql(sql_query)
                return render_template(
                    "index.html",
                    results=results,
                    columns=columns,
                    query=user_input,
                    sql_query=sql_query,
                    zip=zip,
                    db_schema=db_schema,
                )
            else:
                errors.append(
                    {
                        "sql_query": sql_query,
                        "message": error_message,
                    }
                )
                logger.warning("SQL Query failed validation: %s", error_message)

        error_display = (
            f"Failed to generate a valid SQL query after {attempts} attempts.<br><br>"
            f"<strong>Last attempted SQL query:</strong><br><pre>{sql_query}</pre><br>"
            f"<strong>Error message:</strong><br>{error_message}"
        )
        logger.error("All attempts failed. Error message: %s", error_message)
        return render_template(
            "index.html",
            error=error_display,
            query=user_input,
            db_schema=db_schema,
        )

    return render_template("index.html", db_schema=db_schema)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
