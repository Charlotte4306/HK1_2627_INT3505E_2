import json
import os

from flask import Blueprint, jsonify, request, url_for
from jsonschema import ValidationError, validate
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from models import Author, Book, Category, db

bp = Blueprint("books", __name__, url_prefix="/api/v1/books")

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..",
                           "schemas", "book.json")
with open(SCHEMA_PATH, encoding="utf-8") as f:
    BOOK_SCHEMA = json.load(f)
    
PATH_SCHEMA = {**BOOK_SCHEMA, "required": []}

DEFAULT_LIMIT, MAX_LIMIT = 20, 100

#Validate body theo schema, error thi response 400
def validate_payload(payload, schema):
    try:
        validate(payload, schema)
    except ValidationError as e:
        return jsonify({
            "error": "validation_failed",
            "field": list(e.path),
            "message": e.message
        }), 400
    return None

#Kiểm tra category_id và author_ids có tồn tại trong DB không
def check_references(payload):
    category_id = payload.get("category_id")
    if category_id is not None and db.session.get(Category, category_id) is None:
        return jsonify(error=f"category {category_id} not found"), 400
    for author_id in payload.get("author_ids", []):
        if db.session.get(Author, author_id) is None:
            return jsonify(error=f"author {author_id} not found"), 400
    return None
    
#Lấy danh sách book, phân trang offset/limit
@bp.get("")
def list_books():
    offset = request.args.get("offset", 0, type=int)
    limit = min(request.args.get("limit", DEFAULT_LIMIT, type=int), MAX_LIMIT)
    total = db.session.scalar(select(func.count(Book.id)))
    rows = db.session.scalars(
        select(Book).order_by(Book.id).offset(offset).limit(limit)
    ).all()
    return jsonify({
        "data": [book.to_dict() for book in rows],
        "pagination": {
            "offset": offset,
            "limit": limit,
            "total": total,
            "has_next": offset + limit < total
        }
    }), 200
    
#Lấy book theo id
@bp.get("/<int:book_id>")
def get_book(book_id):
    book = db.session.get(Book, book_id)
    if book is None:
        return jsonify(error="Book not found"), 404
    return jsonify(book.to_dict()), 200

@bp.post("")
def create_book():
    payload = request.get_json(silent=True)
    error = validate_payload(payload, BOOK_SCHEMA) or check_references(payload)
    if error:
        return error
    book = Book.from_payload(payload)
    db.session.add(book)
    try:
        db.session.commit()
    except IntegrityError:
        #isbn bị trùng
        db.session.rollback()
        return jsonify(error="isbn already exists"), 409
    location = url_for("books.get_book", book_id=book.id, _external=True)
    return jsonify(book.to_dict()), 201, {"Location": location}

@bp.patch("/<int:book_id>")
def update_book(book_id):
    book = db.session.get(Book, book_id)
    if book is None:
        return jsonify(error="Book not found"), 404
    payload = request.get_json(silent=True)
    error = validate_payload(payload, PATH_SCHEMA) or check_references(payload)
    if error: 
        return error
    for field in ["title", "isbn", "price_vnd", "stock", "category_id"]:
        if field in payload:
            setattr(book, field, payload[field])
    if "author_ids" in payload:
        book.authors = [db.session.get(Author, author_id) for
                        author_id in payload["author_ids"]]
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(error="isbn already exists"), 409
    return jsonify(book.to_dict()), 200

@bp.delete("/<int:book_id>")
def delete_book(book_id):
    book = db.session.get(Book, book_id)
    if book is None:
        return jsonify(error="Book not found"), 404
    db.session.delete(book)
    db.session.commit()
    return "", 204
    