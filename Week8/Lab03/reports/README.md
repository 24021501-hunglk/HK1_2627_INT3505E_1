## Lab 3 — Newman-runnable Postman Collection

### 1. Prerequisites

- Python environment and dependencies required by Books API.
- Node.js and npm.
- Newman.

Install Newman:

```bash
npm install -g newman
```

### 2. Start Books API

Open a terminal at the `Lab03` directory, activate the Python virtual environment and start the API:

```bash
python app.py
```

Keep this terminal running.

The API is expected to be available at:

```text
http://127.0.0.1:5000
```

### 3. Run Postman Collection with Newman

Open another terminal at the `Lab03` directory and execute:

```bash
newman run postman/books-api.postman_collection.json -e postman/local.postman_environment.json -r cli,junit --reporter-junit-export reports/junit.xml
```

### 4. Test Coverage

The collection contains:

- **books**: 5 happy-path requests (GET, POST, GET by ID, PUT, DELETE).
- **error-cases**: 2 error-path requests (POST with missing title, GET `/books/9999`).

The POST request stores the created book ID in the collection variable `book_id`. Subsequent requests use `{{book_id}}` to access the created book.

### 5. JUnit Report

After Newman finishes, the JUnit report is generated at:

```text
reports/junit.xml
```

The report can be used by CI systems or opened with a compatible JUnit report viewer.