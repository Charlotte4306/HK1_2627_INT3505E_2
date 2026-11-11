"""Lab 1: four API behavior tests and one JSON Schema bonus test."""
import pytest
from jsonschema import ValidationError, validate


@pytest.fixture()
def book_response_schema():
    # JSON Schema uses null types, not OpenAPI 3.0's nullable keyword.
    # Keep Lab 1 independent of the intentional year defect in Lab 2.
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["id", "title", "author", "year", "isbn"],
        "properties": {
            "id": {"type": "integer", "minimum": 1},
            "title": {"type": "string", "minLength": 1, "maxLength": 200},
            "author": {"type": "string", "minLength": 1, "maxLength": 200},
            "year": {"type": ["integer", "null"]},
            "isbn": {"type": ["string", "null"], "pattern": r"^\d{13}$"},
        },
    }


@pytest.fixture()
def extra_book_fields():
    """Simulate an accidental sensitive field in a response copy."""
    return {"password_hash": "fake-hash-for-testing"}


def test_get_books_empty_database(client):
    response = client.get("/books")

    assert response.status_code == 200
    assert response.is_json
    assert response.get_json() == []


def test_get_missing_book_returns_not_found(client):
    response = client.get("/books/9999")

    assert response.status_code == 404
    assert response.is_json
    assert response.get_json()["code"] == "NOT_FOUND"


def test_create_book_without_title_returns_validation_error(client):
    response = client.post("/books", json={"author": "J.J. Geewax"})

    assert response.status_code == 400
    assert response.is_json
    payload = response.get_json()
    assert payload["code"] == "VALIDATION_ERROR"
    assert any(error["field"] == "title" for error in payload["errors"])


def test_get_book_after_delete_returns_not_found(client):
    created = client.post(
        "/books", json={"title": "API Design Patterns", "author": "J.J. Geewax"}
    )
    assert created.status_code == 201
    book_id = created.get_json()["id"]

    deleted = client.delete(f"/books/{book_id}")
    assert deleted.status_code == 204
    assert deleted.data == b""

    response = client.get(f"/books/{book_id}")
    assert response.status_code == 404
    assert response.get_json()["code"] == "NOT_FOUND"


def test_response_extra_field_blocked(
    client, sample_book, book_response_schema, extra_book_fields
):
    response = client.get(f"/books/{sample_book}")
    assert response.status_code == 200
    payload = response.get_json()

    # Check the real response first, then reject a corrupted copy.
    validate(instance=payload, schema=book_response_schema)
    assert "password_hash" not in payload

    unsafe_payload = {**payload, **extra_book_fields}
    with pytest.raises(ValidationError) as exc_info:
        validate(instance=unsafe_payload, schema=book_response_schema)
    assert exc_info.value.validator == "additionalProperties"
    assert "password_hash" in exc_info.value.message
