"""
ReAct agent from https://arxiv.org/abs/2210.03629
"""

import logging
import json
from flask import Flask, render_template, request


from src.react import ReactChatBot, generate_user_prompt, extend_user_prompt
from src.utils import scan_db_schema, validate_sql, execute_sql

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
bot = ReactChatBot(dialect, db_schema, attempts)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        user_input = request.form["user_input"]
        logger.info(f"\x1b[36m -- Received user input: {user_input}\x1b[0m")

        user_prompt = generate_user_prompt(user_input)
        errors = []
        previous_actions = []
        agent_outputs = []
        for attempt in range(bot.attempts):
            logger.info(
                f"\x1b[36m -- Attempt {attempt + 1} to generate SQL query\x1b[0m"
            )
            logger.debug(f"""User prompt:
---
{user_prompt}
---
""")

            json_result = bot(user_prompt)
            data = json.loads(json_result)
            decision = data["Decision"]
            if "Final_Answer" not in list(decision.keys()):
                scratchpad = decision["Scratchpad"]
                thought = decision["Thought"]
                action = decision["Action"]
                action_input = decision["Action_Input"]
                logger.info(f"\x1b[34m Scratchpad: {scratchpad} \x1b[0m")
                logger.info(f"\x1b[34m Thought: {thought} \x1b[0m")
                logger.info(
                    f"\x1b[36m  -- running action: {action} with inputs: {action_input}\x1b[0m"
                )
                if action + ": " + str(action_input) in previous_actions:
                    observation = (
                        "You already run that action. **TRY A DIFFERENT ACTION INPUT.**"
                    )
                else:
                    if action == "verify":
                        is_valid, error = validate_sql(action_input)
                        if is_valid:
                            observation = f"Validity: {is_valid}"
                        else:
                            observation = f"Validity: {is_valid}, Error: {error}"
                logger.info(f"\x1b[33m Observation: {observation} \x1b[0m")
                previous_actions.append(action + ": " + str(action_input))
                agent_outputs.append(
                    {
                        "scratchpad": scratchpad,
                        "thought": thought,
                        "action": action,
                        "action_input": action_input,
                        "observation": observation,
                    }
                )

                user_prompt = extend_user_prompt(
                    user_prompt, scratchpad, thought, action, action_input, observation
                )

            else:
                thought = decision["Final_Thought"]
                sql_query = decision["Final_Answer"]
                logger.info(f"\x1b[34m Final thought: {thought} \x1b[0m")
                logger.info(f"\x1b[34m Final Answer: {sql_query} \x1b[0m")
                agent_outputs.append(
                    {"final_thought": thought, "final_answer": sql_query}
                )

                is_valid, error_message = validate_sql(sql_query)
                if is_valid:
                    results, columns = execute_sql(sql_query)
                    return render_template(
                        "react_index.html",
                        results=results,
                        columns=columns,
                        query=user_input,
                        sql_query=sql_query,
                        zip=zip,
                        db_schema=db_schema,
                        agent_outputs=agent_outputs,
                    )
                else:
                    errors.append(
                        {
                            "sql_query": sql_query,
                            "message": error_message,
                        }
                    )
                    logger.warning("SQL Query failed validation: %s", error_message)
                break

        error_display = (
            f"Failed to generate a valid SQL query after {bot.attempts} attempts.<br><br>"
            f"<strong>Last attempted SQL query:</strong><br><pre>{sql_query}</pre><br>"
            f"<strong>Error message:</strong><br>{error_message}"
        )
        logger.error("All attempts failed. Error message: %s", error_message)
        return render_template(
            "react_index.html",
            error=error_display,
            query=user_input,
            db_schema=db_schema,
            agent_outputs=agent_outputs,
        )

    return render_template("react_index.html", db_schema=db_schema)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
