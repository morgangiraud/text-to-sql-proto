import logging
import json

from src.react import ReactChatBot, generate_user_prompt, extend_user_prompt
from src.utils import (
    scan_db_schema,
    validate_sql,
    execute_sql,
)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

db_schema = scan_db_schema()
dialect = "sqlite3"

bot = ReactChatBot(dialect, db_schema, attempts=5)

# question = "List all products with their names and unit prices."
question = "Get the total number of orders placed in 1997."
user_prompt = generate_user_prompt(question)

previous_actions = []
for attempt in range(bot.attempts):
    logger.debug(f"""User prompt:
---
{user_prompt}
---
""")
    result = bot(user_prompt)
    json_result = json.loads(result)
    decision = json_result["Decision"]
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
            is_valid = ""
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

        user_prompt = extend_user_prompt(
            user_prompt, scratchpad, thought, action, action_input, observation
        )

    else:
        thought = decision["Final_Thought"]
        sql_query = decision["Final_Answer"]
        logger.info(f"\x1b[34m Final thought: {thought} \x1b[0m")
        logger.info(f"\x1b[34m Final Answer: {sql_query} \x1b[0m")

        is_valid, error = validate_sql(sql_query)
        if is_valid:
            outputs = execute_sql(sql_query)
        break
