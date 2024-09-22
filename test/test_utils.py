from src.utils import validate_sql


def test_valid_sql_query():
    """Test with a valid SQL query."""

    sql_query = "SELECT * FROM Customers;"
    is_valid, error_message = validate_sql(sql_query)
    assert is_valid
    assert error_message == ""


def test_invalid_sql_query():
    """Test with an invalid SQL query (syntax error)."""

    sql_query = "SELEC * FROM Customers;"  # 'SELECT' misspelled
    is_valid, error_message = validate_sql(sql_query)
    assert not is_valid
    assert "syntax error" in error_message.lower()


def test_nonexistent_table():
    """Test with a SQL query referencing a nonexistent table."""

    sql_query = "SELECT * FROM non_existent_table;"
    is_valid, error_message = validate_sql(sql_query)
    assert not is_valid
    assert "no such table" in error_message.lower()


def test_empty_sql_query():
    """Test with an empty SQL query."""

    sql_query = ""
    is_valid, error_message = validate_sql(sql_query)
    assert not is_valid

    # Error message may vary based on SQLite version
    assert (
        "incomplete input" in error_message.lower()
        or "syntax error" in error_message.lower()
    )


def test_multi_query_injection_attempt():
    """Test with multiple SQL queries."""

    sql_query = "SELECT * FROM Customers; DROP TABLE test_table;"
    is_valid, error_message = validate_sql(sql_query)
    assert not is_valid
    assert "can only execute one" in error_message.lower()


def test_order_details():
    """Test order details."""

    sql_query = 'SELECT * FROM "Order details"'
    is_valid, error_message = validate_sql(sql_query)
    print(is_valid, error_message)
