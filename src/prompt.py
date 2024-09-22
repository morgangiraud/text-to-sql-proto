from typing import List

import outlines


@outlines.prompt
def get_base_prompt(dialect: str, database_schema: str, user_input: str):
    """
    You are an agent designed to interact with a SQL database to find a correct SQL query for the given question.
    Given an input question, generate a syntactically correct {{ dialect }} query.
    Return the SQL query between ```sql and ``` tags.

    Here are the provided information
    1. **Database Schema**: Detailed information about tables, columns, and relationships. Be careful! Table name can contain space!
    2. **User Question**: A natural language query.

    If the question does not seem related to the database, return an empty string.
    If the there is a very similar question among the fewshot examples, directly use the SQL query from the example and modify it to fit the given question and execute the query to make sure it is correct.
    The SQL query MUST have in-line comments to explain what each clause does.

    Take the time to think step by step.

    **Database Schema:**

    {{ database_schema }}

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
