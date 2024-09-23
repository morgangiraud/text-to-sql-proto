import logging

from flask import Flask, render_template, request
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

from src.prompt import get_base_prompt, extend_prompt_with_errors
from src.utils import (
    scan_db_schema,
    extract_sql_from_output,
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


tokenizer = AutoTokenizer.from_pretrained(
    # "mistralai/Mamba-Codestral-7B-v0.1",
    "mistralai/Mistral-7B-Instruct-v0.3",
    padding_side="left",
)


model = AutoModelForCausalLM.from_pretrained(
    # "mistralai/Mamba-Codestral-7B-v0.1",
    "mistralai/Mistral-7B-Instruct-v0.3",
    device_map="auto",
    torch_dtype=torch.bfloat16,
)


def generate_sql(prompt: str):
    with torch.inference_mode():
        model_inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
        generated_ids = model.generate(**model_inputs, max_length=4096)
        completion = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        sql_query = extract_sql_from_output(completion)

    return sql_query


dialect = "sqlite3"

# Quick debug
# user_input = "Get me all the categories"
# query = generate_sql(get_prompt(db_schema, user_input))
# print(validate_sql(query))


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        user_input = request.form["user_input"]
        logger.info("Received user input: %s", user_input)

        base_prompt = get_base_prompt(dialect, db_schema, user_input)
        error_message = ""
        attempts = 5
        errors = []
        for attempt in range(attempts):
            logger.debug("Attempt %d to generate SQL query", attempt + 1)

            prompt = extend_prompt_with_errors(base_prompt, errors)

            # print("\n\n---\n" + prompt + "\n\n")

            sql_query = generate_sql(prompt)
            sql_query = hardcoded_check_order_details_table_name(sql_query)

            logger.debug("Generated SQL Query:\n%s", sql_query)
            is_valid, error_message = validate_sql(sql_query)
            if is_valid:
                logger.debug("SQL Query Valid: %s", is_valid)

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
