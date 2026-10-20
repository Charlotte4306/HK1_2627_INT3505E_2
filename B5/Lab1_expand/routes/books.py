import base64
import json
import os

from flask import Blueprint, jsonify, request, url_for
from jsonschema import ValidationError, validate
from sqlalchemy import func, select, and_, or_
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
    

#Phần chỉnh sửa thêm khác với Lab1
SORT_FIELDS = {
    "id": Book.id,
    "title": Book.title,
    "price": Book.price_vnd,
    "stock": Book.stock,
}
STRATEGIES = ("offset", "cursor")

def parse_sort(raw):
    keys = []
    for part in raw.split(","):
        part = part.strip()
        desc = part.startswith("-")
        name = part.lstrip("-")
        if name not in SORT_FIELDS or name in [k for k, _ in keys]:
            return None
        keys.append((name, desc))
        
    if "id" not in [k for k, _ in keys]:
        keys.append(("id", False))
    return keys

def build_order_by(keys):
    return [SORT_FIELDS[name].desc() if desc
            else SORT_FIELDS[name].asc() for name, desc in keys]
    
def apply_genre(query, raw):
    if not raw:
        return query
    slugs = [s.strip() for s in raw.split(",") if s.strip()]
    return query.join(Book.category).where(Category.slug.in_(slugs))

def encode_cursor(data):
    return base64.urlsafe_b64encode(
        json.dumps(data).encode("utf-8")
    ).decode("utf-8").rstrip("=")

#Giải mã cursor, sai định dạng thì trả None
def decode_cursor(raw):
    try:
        pad = "=" * (-len(raw) % 4)
        data = json.loads(base64.urlsafe_b64decode(raw + pad))
    except (ValueError, TypeError):
        return None
    if not isinstance(data, dict) or not {"s", "v"} <= data.keys():
        return None
    if not isinstance(data["v"], list):
        return None
    return data

#Điều kiện keyset cho sort nhiều cột, mỗi cột có chiều riêng:
#(a > va) OR (a = va AND b < vb) OR (a = va AND b = vb AND id > vi)
def keyset_condition(keys, values):
    branches = []
    for i, (name, desc) in enumerate(keys):
        column = SORT_FIELDS[name]
        equals = [SORT_FIELDS[n] == values[j] for j, (n, _) in enumerate(keys[:i])]
        compare = column < values[i] if desc else column > values[i]
        branches.append(and_(*equals, compare))
    return or_(*branches)

def cursor_values(book, keys):
    return [getattr(book, SORT_FIELDS[name].key) for name, _ in keys]

#Phân trang offset/limit
def paginate_offset(query, limit):
    offset = request.args.get("offset", 0, type=int)
    if offset < 0:
        return jsonify(error="offset must be >= 0"), 400
    total = db.session.scalar(
        select(func.count()).select_from(query.order_by(None).subquery())
    )
    rows = db.session.scalars(query.offset(offset).limit(limit)).all()
    return jsonify({
        "data": [book.to_dict() for book in rows],
        "pagination": {
            "strategy": "offset",
            "offset": offset,
            "limit": limit,
            "total": total,
            "has_next": offset + limit < total
        }
    }), 200

#Phân trang cursor: lấy limit + 1 dòng để biết còn trang sau không
def paginate_cursor(query, limit, keys, sort):
    raw = request.args.get("cursor")
    if raw:
        cursor = decode_cursor(raw)
        if cursor is None:
            return jsonify(error="invalid_cursor"), 400
        if cursor["s"] != sort:
            return jsonify(error="sort_changed"), 400
        if len(cursor["v"]) != len(keys):
            return jsonify(error="invalid_cursor"), 400
        query = query.where(keyset_condition(keys, cursor["v"]))

    rows = db.session.scalars(query.limit(limit + 1)).all()
    has_more = len(rows) > limit
    items = rows[:limit]
    next_cursor = None
    if items and has_more:
        next_cursor = encode_cursor({"s": sort, "v": cursor_values(items[-1], keys)})
    return jsonify({
        "data": [book.to_dict() for book in items],
        "pagination": {
            "strategy": "cursor",
            "limit": limit,
            "next_cursor": next_cursor,
            "has_more": has_more
        }
    }), 200

#Lấy danh sách book: chọn strategy offset/cursor + lọc genre + sort nhiều cột
@bp.get("")
def list_books():
    strategy = request.args.get("strategy", "offset")
    limit = request.args.get("limit", DEFAULT_LIMIT, type=int)
    sort = request.args.get("sort", "id")

    if strategy not in STRATEGIES:
        return jsonify(error="bad_strategy", allowed=list(STRATEGIES)), 400
    if limit < 1:
        return jsonify(error="limit must be at least 1"), 400
    limit = min(limit, MAX_LIMIT)
    keys = parse_sort(sort)
    if keys is None:
        return jsonify(error="bad_sort", allowed=list(SORT_FIELDS),
                       example="-price,title"), 400

    query = select(Book).order_by(*build_order_by(keys))
    query = apply_genre(query, request.args.get("genre"))

    if strategy == "offset":
        return paginate_offset(query, limit)
    return paginate_cursor(query, limit, keys, sort)

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
    