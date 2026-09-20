from flask import Flask, jsonify, request

app = Flask(__name__)

BOOKS = [
    {"id":1, "title":"Clean Code", "author":"R. Martin", "year":2008},
    {"id":2, "title":"RESTful Web APIs", "author":"L. Richardson", "year": 2013},
    {"id":3, "title":"API Design Patterns", "author":"JJ Geewax", "year":2021},
    {"id":4, "title":"RESTful API Design", "author":"Matthias Biehl", "year":2015}
]

_next = max(book["id"] for book in BOOKS) + 1

def find(bid):
    return next((b for b in BOOKS if b["id"]==bid), None)

@app.route("/books", methods=["GET"])
def list_books():
    n = int(request.args.get("limit", 100))
    query = request.args.get("q", "").strip().lower()
    sort_by = request.args.get("sort", "").strip().lower()
    books = BOOKS
    if query:
        books = [
            book
            for book in books
            if query in book["title"].lower()
            or query in book["author"].lower()
        ]
    if sort_by == "title":
        books = sorted(
            books,
            key=lambda book: book["title"].lower(),
        )
    books = books[:n]
    return jsonify(books), 200

@app.route("/books/<int:bid>", methods=["GET"])
def get_book(bid):
    book = find(bid)
    if not book:
        return {"error":"not found"}, 404
    return jsonify(book), 200

@app.route("/books", methods=["POST"])
def create_book():
    global _next
    body = request.get_json(silent=True) or {}
    t, a , y = body.get("title"), body.get("author"), body.get("year")
    if not t or not a or not y:
        return {"error":"need title + author + year"}, 400
    if not isinstance(y, int) or y < 1900:
        return {"error": "year must be an integer >= 1900"}, 400
    book = {"id":_next, "title":t, "author":a, "year":y}
    _next += 1; BOOKS.append(book)
    return jsonify(book), 201, {"Location":f"/books/{book['id']}"}

@app.route("/books/<int:bid>", methods=["PUT", "DELETE"])
def modify_book(bid):
    book = find(bid)
    if not book:
        return {"error":"not found"}, 404
    if request.method == "PUT":
        book.update(request.get_json(silent=True) or {})
        return jsonify(book), 200
    BOOKS.remove(book)
    return"", 204

if __name__ == "__main__":
    app.run(port=5000, debug=True)