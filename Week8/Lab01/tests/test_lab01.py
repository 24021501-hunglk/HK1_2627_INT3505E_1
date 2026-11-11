"""LAB 1 — add your five tests here. Do not delete the smoke tests.

A. GET /books, empty database -> HTTP 200 and []
B. GET /books/9999 -> HTTP 404, JSON code == NOT_FOUND
C. POST /books with only author -> HTTP 400, errors contains title
D. POST valid book, DELETE it, GET same id -> HTTP 404
BONUS. Validate a Book response using JSON Schema; add an unknown
       field to a *copy* of the response and assert ValidationError.

Useful imports:
    from jsonschema import validate, ValidationError
    import pytest
    from tools import get_book_schema

Do not depend on test execution order. Fixtures: client, app, sample_book.
"""
from jsonschema import validate, ValidationError
import pytest, copy
from tools import get_book_schema


def jsonschema_compatible(schema):
    schema = copy.deepcopy(schema)

    if isinstance(schema, dict):
        nullable = schema.pop("nullable", False)

        # Điều chỉnh kiểu dữ liệu của trường year
        if "properties" in schema and "year" in schema["properties"]:
            schema["properties"]["year"]["type"] = "integer"

        for key, value in list(schema.items()):
            schema[key] = jsonschema_compatible(value)

        if nullable and isinstance(schema.get("type"), str):
            schema["type"] = [schema["type"], "null"]

    elif isinstance(schema, list):
        schema = [jsonschema_compatible(item) for item in schema]

    return schema

#test/test_list_book.py
def test_list_books_empty(client):
    response = client.get("/books")
    assert response.status_code == 200
    assert response.json == []
    
def test_get_book_not_found(client):
    response = client.get("/books/9999")
    assert response.status_code == 404
    assert response.json["code"] == "NOT_FOUND"

def test_create_book_missing_title(client, sample_book):
    # Create a book without a title
    response = client.post("/books", json = {
        "author": "ABCD"
    })
    assert response.status_code == 400
    data = response.get_json()
    assert "errors" in data
    assert any(
        error["field"] == "title"
        for error in data["errors"]
    )

def test_post_valid_book(client, sample_book):
    response = client.post("/books", json={
        "title": "CDEF",
        "author": "ABCD"
    })
    assert response.status_code == 201
    data = response.get_json()
    
    assert data["title"] == "CDEF"
    assert data["author"] == "ABCD"

def test_delete_book(client, sample_book):
    # First, create a book
    create_response = client.post("/books", json={
        "title": "CDEF",
        "author": "ABCD"
    })
    assert create_response.status_code == 201
    book_id = create_response.get_json()["id"]

    # Then, delete it
    delete_response = client.delete(f"/books/{book_id}")
    assert delete_response.status_code == 204

    # Finally, try to get it (should return 404)
    get_response = client.get(f"/books/{book_id}")
    assert get_response.status_code == 404
    
def test_response_extra_field_blocked(client, sample_book):
    response = client.get(f"/books/{sample_book}")

    assert response.status_code == 200

    book_data = response.get_json()

    assert "password_hash" not in book_data

    schema = jsonschema_compatible(get_book_schema())

    validate(instance=book_data, schema=schema)

    invalid_book = copy.deepcopy(book_data)
    invalid_book["password_hash"] = "fake_hash_value"

    with pytest.raises(ValidationError):
        validate(instance=invalid_book, schema=schema)