from src.prompt import get_base_prompt, extend_prompt_with_errors


def test_get_base_prompt():
    dialect = "sqlite3"
    database_schema = "users (id, name, age)"
    user_input = "Find all users older than 30"

    result = get_base_prompt(dialect, database_schema, user_input)

    assert dialect in result
    assert database_schema in result
    assert user_input in result


def test_extend_prompt_with_errors():
    dialect = "sqlite3"
    database_schema = "users (id, name, age)"
    user_input = "Find all users older than 30"
    errors = [{"sql_query": "Select * from ?;", "message": "Syntax error near 'from'"}]

    base_prompt = get_base_prompt(dialect, database_schema, user_input)
    result = extend_prompt_with_errors(base_prompt, errors)

    assert "Select * from ?;" in result
    assert "Syntax error near 'from'" in result
