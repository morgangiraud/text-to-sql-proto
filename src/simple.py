from typing import List
import re
import torch
import outlines
from transformers import AutoTokenizer, AutoModelForCausalLM


class SimpleChatBot:
    def __init__(self, dialect: str, db_schema: str, attempts: int, logger):
        self.attempts = attempts
        self.logger = logger

        self.tokenizer = AutoTokenizer.from_pretrained(
            # "mistralai/Mamba-Codestral-7B-v0.1",
            "mistralai/Mistral-7B-Instruct-v0.3",
            padding_side="left",
        )

        self.model = AutoModelForCausalLM.from_pretrained(
            # "mistralai/Mamba-Codestral-7B-v0.1",
            "mistralai/Mistral-7B-Instruct-v0.3",
            device_map="auto",
            torch_dtype=torch.bfloat16,
        )

    def __call__(self, user_prompt: str):
        return self.think(user_prompt)

    def think(self, prompt: str):
        with torch.inference_mode():
            model_inputs = self.tokenizer(prompt, return_tensors="pt").to("cuda")
            generated_ids = self.model.generate(**model_inputs, max_length=4096)
            completion = self.tokenizer.batch_decode(
                generated_ids, skip_special_tokens=True
            )[0]
            sql_query = self._extract_sql_from_output(completion)
        return sql_query

    def _extract_sql_from_output(self, generated_text):
        self.logger.debug("Extracting SQL from model output")

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


@outlines.prompt
def get_base_prompt(dialect: str, db_schema: str, user_input: str):
    """
    You are an agent designed to interact with a SQL database to find a correct SQL query for the given question.
    Given an input question, generate a syntactically correct {{ dialect }} query.
    Return the SQL query between ```sql and ``` tags.

    Here are the provided information:
    1. **Database Schema**: Detailed information about tables, columns, and relationships. Be careful! Table name can contain space!
    2. **User Question**: A natural language query.

    If the question does not seem related to the database, return an empty string.
    If the there is a very similar question among the fewshot examples, directly use the SQL query from the example and modify it to fit the given question and execute the query to make sure it is correct.
    The SQL query MUST have in-line comments to explain what each clause does.

    Take the time to think step by step.

    ##

    **Database Schema:**

    {{ db_schema }}

    **User Question:**

    {{ user_input }}"""


@outlines.prompt
def extend_prompt_with_errors(base_prompt: str, errors: List[str] = []):
    """
    {{ base_prompt }}

    {% if errors|length > 0 %}
    {% for error in errors %}

    **Previously generated SQL Query:**
    ```{{ error.sql_query }}```

    **Returned Error:**
    ```{{ error.message }}```
    {% endfor %}

    Use all errors to correct the previously proposed SQL querys and propose a new one.
    {% endif %}

    **Generated SQL Query:**
    """
