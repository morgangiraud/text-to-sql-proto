# text-to-sql-proto
A text-to-SQL prototype on the northwind sqlite dataset

Database: https://github.com/jpwhite3/northwind-SQLite3

Base model used: https://huggingface.co/mistralai/Mamba-Codestral-7B-v0.1

## Install

For GPU on linux:
```sh
make install
```

## Usage

1. **Run the Flask App**:

```bash
python app.py
```
or 
```bash
python app_react.py # To use the ReAct Agent
```

2. **Open in Browser**:

   Navigate to `http://localhost:5000/`.

3. **Verify the Schema Display**:

   - The left sidebar should display your database schema.
   - The right side should contain the application form and any results.

4. **Submit a Query**:

   - Enter a natural language query in the input field.
   - Verify that results are displayed correctly and the schema remains visible.
