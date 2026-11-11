"""Lab 2: validate actual Book responses against the corrected OpenAPI schema."""
from copy import deepcopy

import pytest
from jsonschema import validate

from tools import get_book_schema


@pytest.fixture()
def contract_book_schema():
    schema = deepcopy(get_book_schema())
    # Translate OpenAPI 3.0 nullable into JSON Schema null unions.
    # Preserve declared types so an incorrect year type still fails the test.
    for definition in schema["properties"].values():
        if definition.pop("nullable", False):
            definition["type"] = [definition["type"], "null"]
    return schema


@pytest.mark.parametrize("operation", ["list", "get", "create", "update"])
@pytest.mark.parametrize("optional_fields", [
    {"year": 2021, "isbn": "9781617295850"},
    {"year": None, "isbn": None},
])
def test_book_response_matches_openapi(client, contract_book_schema, operation, optional_fields):
    data = {"title": "API Design Patterns", "author": "J.J. Geewax", **optional_fields}
    created = client.post("/books", json=data)
    assert created.status_code == 201
    book_id = created.get_json()["id"]

    if operation == "create":
        response = created
    elif operation == "list":
        response = client.get("/books")
    elif operation == "get":
        response = client.get(f"/books/{book_id}")
    else:
        response = client.put(f"/books/{book_id}", json=data)

    assert response.status_code == (201 if operation == "create" else 200)
    assert response.is_json
    payload = response.get_json()
    if operation == "list":
        assert isinstance(payload, list)
        assert len(payload) == 1
        payload = payload[0]
    validate(instance=payload, schema=contract_book_schema)
