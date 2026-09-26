from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

app = Flask(__name__)

class ProblemError(Exception):
    def __init__(self, status, title, detail, type_="about:blank"):
        super().__init__(detail)
        self.status = status
        self.title = title
        self.detail = detail
        self.type = type_
        
def problem_response(status, title, detail, type_="about:blank"):
    response = jsonify({
        "type": type_,
        "title": title,
        "status": status,
        "detail": detail,
        "instance": request.path
    })
    response.status_code = status
    response.content_type = "application/problem+json"
    return response

@app.errorhandler(ProblemError)
def handle_problem_error(e):
    return problem_response(e.status, e.title, e.detail, e.type)

@app.errorhandler(HTTPException)
def handle_http_exception(e):
    return problem_response(e.code, e.name, e.description)

@app.errorhandler(Exception)
def handle_unexpected_exception(e):
    app.logger.exception("Unhandled exception: %s %s", request.method, request.path)
    return problem_response(500, "Internal Server Error", "An unexpected error occurred.")

@app.get("/resources/<int:resource_id>")
def get_resource(resource_id):
    if resource_id != 1:
        raise ProblemError(
            status=404,
            title="Resource Not Found",
            detail=f"Resource {resource_id} was not found"
        )
    return jsonify({"id": 1, "name": "Example resource"}), 200

@app.get("/raise-error")
def raise_error():
    raise RuntimeError("This message is logged server-side only")

if __name__ == "__main__":
    app.run(port=5000, debug=True)
